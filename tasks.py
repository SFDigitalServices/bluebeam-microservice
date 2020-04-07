"""defining celery task for background processing of bluebeam-microservice"""

# import sys
# import traceback
import os
from datetime import datetime
import urllib.request
from urllib.parse import urlparse
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
        try:
            # update submission's export_guid in db
            submission.export_status_guid = export_obj.guid

            # create project in bluebeam
            now = datetime.now()
            project_name = now.strftime('%Y-%m%d-%H%M%S') + submission.data['address']
            project_id = bluebeam.create_project(access_code, project_name)

            # create directory structure
            pdf_folder_id = bluebeam.create_directories(
                access_code,
                project_id,
                bluebeam.DIRECTORY_STRUCTURE
            )

            # upload pdf to new folder in new project
            if pdf_folder_id is not None:
                for file_url in submission.data['files']:
                    response = urllib.request.urlopen(file_url)
                    file_download = response.read()
                    file_name = os.path.basename(urlparse(file_url).path)

                    is_upload_successful = bluebeam.upload_file(
                        access_code,
                        project_id,
                        file_name,
                        file_download,
                        pdf_folder_id
                    )
                    if not is_upload_successful:
                        raise Exception("Unable to upload file")

                # finished exporting this submission
                statuses['success'].append(submission.id)
                submission.date_exported = datetime.utcnow()
                submission.bluebeam_project_id = project_id
            else:
                raise Exception("There wasn't a folder_id to upload pdfs to")

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
