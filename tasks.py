"""defining celery task for background processing of bluebeam-microservice"""
# pylint: disable=too-many-locals,too-many-branches,too-many-statements

import os
from io import BytesIO
from datetime import datetime
from urllib.parse import urlparse
import tempfile
import zipfile
import shutil
import traceback
import requests
from dateutil import parser
import pytz
import celery
from kombu import serialization
import celeryconfig
import service.resources.bluebeam as bluebeam
from service.resources.models import SubmissionModel, ExportStatusModel, UserModel
from service.resources.db import create_session

TEMP_DIR = 'tmp'
serialization.register_pickle()
serialization.enable_insecure_serializers()

# pylint: disable=invalid-name
celery_app = celery.Celery('bluebeam-microservice')
celery_app.config_from_object(celeryconfig)
# pylint: enable=invalid-name

SPREADSHEETS_URL = os.environ.get('SPREADSHEETS_MICROSERVICE_URL').rstrip('/')
SPREADSHEETS_API_KEY = os.environ.get('SPREADSHEETS_MICROSERVICE_API_KEY')

ERR_UPLOAD_FAIL = "Unable to upload file"
ERR_INVALID_PROJECT_ID = "Invalid Bluebeam project id"

@celery_app.task(name="tasks.bluebeam_export", bind=True)
def bluebeam_export(self, export_obj, access_token):
    # pylint: disable=unused-argument
    """
        exports unexported submissions to bluebeam
    """
    print("export:guid - {0}".format(export_obj.guid))

    session = create_session()
    db_session = session()
    submissions_to_export = db_session.query(SubmissionModel).filter( # pylint: disable=no-member
        SubmissionModel.export_status_guid.is_(None)
    )
    statuses = {
        'success': [],
        'failure': []
    }

    for submission in submissions_to_export:
        # might have to renew access token
        now = datetime.utcnow().astimezone(pytz.UTC)
        expiration_date = parser.parse(access_token['.expires'])
        if now > expiration_date:
            access_token = bluebeam.refresh_token(access_token['refresh_token'])

        # update submission's export_guid in db
        submission.export_status_guid = export_obj.guid

        project_id = submission.data.get('project_id', None)
        upload_dir_id = None
        try:
            if project_id and project_id is not None:
                # resubmission
                print("export:resubmission - {0}".format(submission.id))
                print("project_id: {0}".format(project_id))
                if bluebeam.project_exists(access_token, project_id):
                    upload_dir_id = bluebeam.get_upload_dir_id(access_token, project_id)
                    upload_files(
                        project_id,
                        upload_dir_id,
                        submission.data.get('files'),
                        access_token
                    )
                else:
                    print(ERR_INVALID_PROJECT_ID)
                    raise Exception(ERR_INVALID_PROJECT_ID)
            else:
                # create bluebeam project
                try:
                    print("export:submission - {0}".format(submission.id))

                    # generate project name and
                    # create project in bluebeam
                    if 'building_permit_number' in submission.data:
                        project_name = "{0} - {1}".format(
                            submission.data['project_name'],
                            submission.data['building_permit_number']
                        )
                    else:
                        project_name = submission.data['project_name']
                    project_id = bluebeam.create_project(access_token, project_name)

                    # create directory structure
                    upload_dir_id = bluebeam.create_directories(
                        access_token,
                        project_id,
                        bluebeam.DIRECTORY_STRUCTURE
                    )
                    upload_files(
                        project_id,
                        upload_dir_id,
                        submission.data.get('files'),
                        access_token
                    )

                    # assign user permissions
                    users = db_session.query(UserModel).all()
                    bluebeam.assign_user_permissions(access_token, project_id, users)
                except Exception as err: # pylint: disable=broad-except
                    # delete project in bluebeam if it was created
                    if project_id is not None:
                        bluebeam.delete_project(access_token, project_id)
                    raise err

            # log success to google sheets
            if 'logger' in submission.data:
                log_status(project_id, submission.data)

            # finished exporting this submission
            statuses['success'].append({
                'submission_id': submission.id,
                'bluebeam_id': project_id
            })
            submission.date_exported = datetime.utcnow()
            submission.bluebeam_project_id = project_id

        except Exception as err: # pylint: disable=broad-except
            err_msg = "{0}".format(err)
            print('Encountered error exporting submission with id: {0}'.format(submission.id))
            print(err_msg)
            print(traceback.format_exc())
            submission.error_message = err_msg
            statuses['failure'].append({
                'id': submission.id,
                'data': submission.data,
                'err': err_msg
            })

            # log error to google sheets
            try:
                if 'logger' in submission.data:
                    log_status('Error: {}'.format(err_msg), submission.data)
            except Exception as err: # pylint: disable=broad-except
                pass

        # commit update this submission immediately
        db_session.commit()

    # finished export
    export_status = db_session.query(ExportStatusModel).filter(
        ExportStatusModel.guid == export_obj.guid
    ).first()
    export_status.date_finished = datetime.utcnow()
    export_status.result = statuses

    db_session.commit()
    db_session.close()

def upload_files(project_id, upload_dir_id, files, access_token):
    """
        upload all the files to the upload dir of a project
    """
    print("tasks.upload_files:{0}".format(files))
    cloudstorage_url = os.environ.get('CLOUDSTORAGE_URL')
    cloudstorage_api_key = os.environ.get('CLOUDSTORAGE_API_KEY')
    bucketeer_domain = os.environ.get('BUCKETEER_DOMAIN')

    if files is None:
        files = []

    for f in files: #pylint: disable=invalid-name
        print("tasks.upload_files file: {0}".format(f))
        file_url = f['url']
        file_url_parsed = urlparse(file_url)

        # use cloudstorage api to retrieve file
        response = None
        if file_url_parsed.netloc == bucketeer_domain:
            response = requests.get(
                cloudstorage_url,
                params={
                    'name':file_url_parsed.path[1:],
                    'apikey':cloudstorage_api_key
                },
                stream=True
            )
            print("upload_files cloud path:{0}".format(file_url_parsed.path[1:]))
        else:
            response = requests.get(file_url, stream=True)
        response.raise_for_status()
        file_name = f['originalName']

        # write downloaded file locally
        tmp_dir = tempfile.mkdtemp()
        file_path = os.path.join(tmp_dir, file_name)
        downloaded_file = open(file_path, 'wb')
        shutil.copyfileobj(BytesIO(response.content), downloaded_file)
        del response
        downloaded_file.close()

        # handle zips
        if file_name.endswith('.zip'):
            upload_zip(
                access_token,
                project_id,
                file_path,
                upload_dir_id
            )
        else:
            bluebeam.upload_file(
                access_token,
                project_id,
                file_name,
                file_path,
                upload_dir_id
            )

        # cleanup
        shutil.rmtree(tmp_dir)

def log_status(status, submission_data):
    """
        log status to google sheets
    """
    try:
        logger_settings = submission_data.get('logger')
        google_settings = None
        if logger_settings is not None and 'google_sheets' in logger_settings:
            google_settings = logger_settings.get('google_sheets')
            google_settings['label_value_map'] = {
                google_settings['status_column_label']:status
            }
            response = requests.patch(
                '{0}/rows/{1}'.format(SPREADSHEETS_URL, submission_data['_id']),
                headers={'x-apikey':SPREADSHEETS_API_KEY},
                json=google_settings
            )
            response.raise_for_status()
    except Exception as err: # pylint: disable=broad-except
        print("Encountered error in log_status:{0}".format(err))
        print("log data:{0}".format(google_settings))
        raise err

def upload_zip(access_token, project_id, file_path, upload_dir_id):
    """
        unzips file and uploads pdfs to bluebeam
    """
    tmp_dir = tempfile.mkdtemp()

    # extract zip file
    with zipfile.ZipFile(file_path, "r") as zip_file:
        zip_file.extractall(tmp_dir)

    # upload only pdfs
    files = os.listdir(tmp_dir)
    for f in files: # pylint: disable=invalid-name
        if f.endswith(".pdf"):
            bluebeam.upload_file(
                access_token,
                project_id,
                f,
                os.path.join(tmp_dir, f),
                upload_dir_id
            )
    # cleanup
    shutil.rmtree(tmp_dir)
