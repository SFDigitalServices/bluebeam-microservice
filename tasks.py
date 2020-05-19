"""defining celery task for background processing of bluebeam-microservice"""
# pylint: disable=too-many-locals

# import sys
# import traceback
from datetime import datetime
import urllib.request
import celery
from kombu import serialization
import celeryconfig
import service.resources.bluebeam as bluebeam
from service.resources.models import SubmissionModel, ExportStatusModel
from service.resources.db import create_session

TEMP_DIR = 'tmp'
serialization.register_pickle()
serialization.enable_insecure_serializers()

# pylint: disable=invalid-name
celery_app = celery.Celery('bluebeam-microservice')
celery_app.config_from_object(celeryconfig)
# pylint: enable=invalid-name

ERR_UPLOAD_FAIL = "Unable to upload file"
ERR_INVALID_PROJECT_ID = "Invalid Bluebeam project id"

@celery_app.task(name="tasks.bluebeam_export", bind=True)
def bluebeam_export(self, export_obj, access_code):
    # pylint: disable=unused-argument
    """
        exports unexported submissions to bluebeam
    """
    print("export:guid - {0}".format(export_obj.guid))

    session = create_session()
    db_session = session()
    submissions_to_export = db_session.query(SubmissionModel).filter( # pylint: disable=no-member
        SubmissionModel.date_exported.is_(None)
    )
    statuses = {
        'success': [],
        'failure': []
    }

    for submission in submissions_to_export:
        project_id = submission.data.get('project_id', None)
        upload_dir_id = None
        try:
            if project_id is not None:
                # resubmission
                print("export:resubmission - {0}".format(submission.id))
                print("project_id: {0}".format(project_id))
                if bluebeam.project_exists(access_code, project_id):
                    upload_dir_id = bluebeam.get_upload_dir_id(access_code, project_id)
                    upload_files(project_id, upload_dir_id, submission.data['files'], access_code)
                else:
                    print(ERR_INVALID_PROJECT_ID)
                    raise Exception(ERR_INVALID_PROJECT_ID)
            else:
                # create bluebeam project
                try:
                    print("export:submission - {0}".format(submission.id))
                    # update submission's export_guid in db
                    submission.export_status_guid = export_obj.guid

                    # generate project name and
                    # create project in bluebeam
                    if 'building_permit_number' in submission.data:
                        project_name = "{0} - {1}".format(
                            submission.data['project_name'],
                            submission.data['building_permit_number']
                        )
                    else:
                        project_name = submission.data['project_name']
                    project_id = bluebeam.create_project(access_code, project_name)

                    # create directory structure
                    upload_dir_id = bluebeam.create_directories(
                        access_code,
                        project_id,
                        bluebeam.DIRECTORY_STRUCTURE
                    )
                    upload_files(project_id, upload_dir_id, submission.data['files'], access_code)
                except Exception as err: # pylint: disable=broad-except
                    # delete project in bluebeam if it was created
                    if project_id is not None:
                        bluebeam.delete_project(access_code, project_id)
                    raise err

            # finished exporting this submission
            statuses['success'].append(submission.id)
            submission.date_exported = datetime.utcnow()
            submission.bluebeam_project_id = project_id

        except Exception as err: # pylint: disable=broad-except
            err_msg = "{0}".format(err)
            print('Encountered error exporting submission with id: {0}'.format(submission.id))
            print(err_msg)
            submission.error_message = err_msg
            statuses['failure'].append({
                'id': submission.id,
                'err': err_msg
            })

    # finished export
    export_status = db_session.query(ExportStatusModel).filter(
        ExportStatusModel.guid == export_obj.guid
    ).first()
    export_status.date_finished = datetime.utcnow()
    export_status.result = statuses

    db_session.commit()
    db_session.close()

def upload_files(project_id, upload_dir_id, files, access_code):
    """
        upload all the files to the upload dir of a project
    """
    for f in files: #pylint: disable=invalid-name
        file_url = f['url']
        response = urllib.request.urlopen(file_url)
        file_download = response.read()
        file_name = f['original_name']

        is_upload_successful = bluebeam.upload_file(
            access_code,
            project_id,
            file_name,
            file_download,
            upload_dir_id
        )
        if not is_upload_successful:
            print(ERR_UPLOAD_FAIL)
            raise Exception(ERR_UPLOAD_FAIL)
