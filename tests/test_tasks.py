""" tests for tasks """
#pylint: disable=too-many-statements
import os
import datetime
import copy
from unittest.mock import patch, Mock
import pytest
import tests.mocks as mocks
import tests.utils as test_utils
import service.resources.bluebeam as bluebeam
from service.resources.models import create_export, create_submission, SubmissionModel
from service.resources.db import create_session
from tasks import celery_app as queue, bluebeam_export, scheduler

session = create_session() # pylint: disable=invalid-name
db = session() # pylint: disable=invalid-name

ZIP_FILE = 'tests/resources/Archive.zip'
TEST_PDF = 'tests/resources/dummy.pdf'

@pytest.fixture(scope='session')
def celery_config():
    """ config for celery worker """
    return {
        'broker_url': os.environ['REDIS_URL'],
        'task_serializer': 'pickle',
        'accept_content': ['pickle', 'application/x-python-serialize', 'json', 'application/json']
    }

def test_export_task_new_project(mock_env_access_key):
    # pylint: disable=unused-argument
    """
        Test the export task
    """
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create a submission so there's something to export
    data = mocks.SUBMISSION_POST_DATA.copy()
    data['_id'] = "123"

    export_obj = create_export(db)
    create_submission(db, data, export_obj.guid)

    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        fake_post_responses = []
        # refresh token
        fake_post_responses.append(Mock())
        fake_post_responses[0].json.return_value = test_utils.BLUEBEAM_ACCESS_TOKEN
        fake_post_responses[0].status_code = 200
        # create project
        fake_post_responses.append(Mock())
        fake_post_responses[1].json.return_value = mocks.CREATE_PROJECT_RESPONSE
        fake_post_responses[1].status_code = 200
        # create folders
        i = 2
        while i < 8:
            fake_post_responses.append(Mock())
            fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            i += 1
        # get folders
        fake_post_responses.append(Mock())
        fake_post_responses[8].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_post_responses.append(Mock())
        fake_post_responses[9].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_post_responses.append(Mock())
        fake_post_responses[10].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_post_responses.append(Mock())
        fake_post_responses[11].return_value.status_code = 200
        # confirm upload
        fake_post_responses.append(Mock())
        fake_post_responses[12].status_code = 204
        # add user1
        fake_post_responses.append(Mock())
        fake_post_responses[13].status_code = 204
        # add user2
        fake_post_responses.append(Mock())
        fake_post_responses[14].status_code = 204
        # get project users
        fake_post_responses.append(Mock())
        fake_post_responses[15].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE
        # set access user1
        fake_post_responses.append(Mock())
        fake_post_responses[16].status_code = 204
        # set access user2
        fake_post_responses.append(Mock())
        fake_post_responses[17].status_code = 204

        mock_post.side_effect = fake_post_responses

        #patch the logger request
        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.status_code = 200

            # set an expired token to force refresh
            expired_token = test_utils.BLUEBEAM_ACCESS_TOKEN.copy()
            hour_past = test_utils.HOUR_FUTURE - datetime.timedelta(hours=1)
            expired_token['.expires'] = hour_past.strftime("%a, %d %b %Y %H:%M:%S %Z")
            bluebeam.save_auth_token(db, expired_token)

            bluebeam_export.s(
                export_id=export_obj.guid
            ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) > 0
        assert len(export_obj.result['failure']) == 0

    # clear out the queue
    queue.control.purge()

def test_export_task_new_project_no_files(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test create a new project with no files"""
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create the export
    export_obj = create_export(db)
    # create a submission so there's something to export
    create_submission(
        db,
        {i:mocks.SUBMISSION_POST_DATA[i] for i in mocks.SUBMISSION_POST_DATA if i != 'files'},
        export_obj.guid
    )

    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        fake_post_responses = []
        # create project
        fake_post_responses.append(Mock())
        fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
        fake_post_responses[0].status_code = 200
        # create folders
        i = 1
        while i < 7:
            fake_post_responses.append(Mock())
            fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            i += 1
        # get folders
        fake_post_responses.append(Mock())
        fake_post_responses[7].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_post_responses.append(Mock())
        fake_post_responses[8].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_post_responses.append(Mock())
        fake_post_responses[9].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_post_responses.append(Mock())
        fake_post_responses[10].return_value.status_code = 200
        # confirm upload
        fake_post_responses.append(Mock())
        fake_post_responses[11].status_code = 204
        # add user1
        fake_post_responses.append(Mock())
        fake_post_responses[12].status_code = 204
        # add user2
        fake_post_responses.append(Mock())
        fake_post_responses[13].status_code = 204
        # get project users
        fake_post_responses.append(Mock())
        fake_post_responses[14].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE
        # set access user1
        fake_post_responses.append(Mock())
        fake_post_responses[12].status_code = 204
        # set access user2
        fake_post_responses.append(Mock())
        fake_post_responses[13].status_code = 204

        mock_post.side_effect = fake_post_responses

        #patch the logger request
        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.status_code = 200

            bluebeam_export.s(
                export_id=export_obj.guid
            ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) > 0
        assert len(export_obj.result['failure']) == 0

    # clear out the queue
    queue.control.purge()

def test_export_task_new_project_bucketeer(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export task"""
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create the export
    export_obj = create_export(db)
    # create a submission so there's something to export
    create_submission(db, mocks.BUCKETEER_SUBMISSION_POST_DATA, export_obj.guid)
    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        fake_post_responses = []
        # create project
        fake_post_responses.append(Mock())
        fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
        fake_post_responses[0].status_code = 200
        # create folders
        i = 1
        while i < 7:
            fake_post_responses.append(Mock())
            fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            i += 1
        # get folders
        fake_post_responses.append(Mock())
        fake_post_responses[7].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_post_responses.append(Mock())
        fake_post_responses[8].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_post_responses.append(Mock())
        fake_post_responses[9].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_post_responses.append(Mock())
        fake_post_responses[10].return_value.status_code = 200
        # confirm upload
        fake_post_responses.append(Mock())
        fake_post_responses[11].status_code = 204
        # add user1
        fake_post_responses.append(Mock())
        fake_post_responses[12].status_code = 204
        # add user2
        fake_post_responses.append(Mock())
        fake_post_responses[13].status_code = 204
        # get project users
        fake_post_responses.append(Mock())
        fake_post_responses[14].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE
        # set access user1
        fake_post_responses.append(Mock())
        fake_post_responses[12].status_code = 204
        # set access user2
        fake_post_responses.append(Mock())
        fake_post_responses[13].status_code = 204

        mock_post.side_effect = fake_post_responses

        with patch('tasks.requests.get') as mock_get:
            with open(TEST_PDF, 'rb') as f: # pylint: disable=invalid-name
                mock_get.return_value.content = f.read()

                #patch the logger request
                with patch('tasks.requests.patch') as mock_patch:
                    mock_patch.status_code = 200

                    bluebeam_export.s(
                        export_id=export_obj.guid
                    ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) > 0
        assert len(export_obj.result['failure']) == 0

    # clear out the queue
    queue.control.purge()

def test_export_task_new_project_with_permit_number(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export task"""
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create a submission so there's something to export
    submission_data_with_permit = mocks.SUBMISSION_POST_DATA.copy()
    submission_data_with_permit['building_permit_number'] = '202001011234'
    # create the export
    export_obj = create_export(db)
    create_submission(db, submission_data_with_permit, export_obj.guid)
    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        fake_post_responses = []
        # create project
        fake_post_responses.append(Mock())
        fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
        fake_post_responses[0].status_code = 200
        # create folders
        i = 1
        while i < 7:
            fake_post_responses.append(Mock())
            fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            i += 1
        # get folders
        fake_post_responses.append(Mock())
        fake_post_responses[7].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_post_responses.append(Mock())
        fake_post_responses[8].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_post_responses.append(Mock())
        fake_post_responses[9].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_post_responses.append(Mock())
        fake_post_responses[10].return_value.status_code = 200
        # confirm upload
        fake_post_responses.append(Mock())
        fake_post_responses[11].status_code = 204
        # add user1
        fake_post_responses.append(Mock())
        fake_post_responses[12].status_code = 204
        # add user2
        fake_post_responses.append(Mock())
        fake_post_responses[13].status_code = 204
        # get project users
        fake_post_responses.append(Mock())
        fake_post_responses[14].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE
        # set access user1
        fake_post_responses.append(Mock())
        fake_post_responses[12].status_code = 204
        # set access user2
        fake_post_responses.append(Mock())
        fake_post_responses[13].status_code = 204

        mock_post.side_effect = fake_post_responses

        #patch the logger request
        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.status_code = 200

            bluebeam_export.s(
                export_id=export_obj.guid
            ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) > 0
        assert len(export_obj.result['failure']) == 0

    # clear out the queue
    queue.control.purge()

def test_export_task_new_project_zip(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export task where submission has a zip attachment"""
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create the export
    export_obj = create_export(db)
    # create a submission so there's something to export
    create_submission(db, mocks.SUBMISSION_POST_DATA_ZIP, export_obj.guid)
    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        fake_post_responses = []
        # create project
        fake_post_responses.append(Mock())
        fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
        fake_post_responses[0].status_code = 200
        # create folders
        i = 1
        while i < 7:
            fake_post_responses.append(Mock())
            fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            i += 1
        # get folders
        fake_post_responses.append(Mock())
        fake_post_responses[7].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_post_responses.append(Mock())
        fake_post_responses[8].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_post_responses.append(Mock())
        fake_post_responses[9].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_post_responses.append(Mock())
        fake_post_responses[10].return_value.status_code = 200
        # confirm upload
        fake_post_responses.append(Mock())
        fake_post_responses[11].status_code = 204
        # get folders 2
        # this mock is modified to contain today's upload folder
        fake_post_responses.append(Mock())
        get_folders_updated = copy.deepcopy(mocks.GET_FOLDERS_RESPONSE)
        get_folders_updated['ProjectFolders'].append(
            {
                '$id': '8',
                'Id': '1234567',
                'Name': bluebeam.SUBMITTAL_DIR_NAME + " " + str(datetime.date.today()),
                'Path': '/path/somewhere'
            }
        )
        fake_post_responses[12].json.return_value = get_folders_updated
        # initiate upload 2
        fake_post_responses.append(Mock())
        fake_post_responses[13].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload 2
        fake_post_responses.append(Mock())
        fake_post_responses[14].return_value.status_code = 200
        # confirm upload 2
        fake_post_responses.append(Mock())
        fake_post_responses[15].status_code = 204
        # add user1
        fake_post_responses.append(Mock())
        fake_post_responses[16].status_code = 204
        # add user2
        fake_post_responses.append(Mock())
        fake_post_responses[17].status_code = 204
        # get project users
        fake_post_responses.append(Mock())
        fake_post_responses[18].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE
        # set access user1
        fake_post_responses.append(Mock())
        fake_post_responses[19].status_code = 204
        # set access user2
        fake_post_responses.append(Mock())
        fake_post_responses[20].status_code = 204

        mock_post.side_effect = fake_post_responses

        with patch('tasks.requests.get') as mock_get:
            with open(ZIP_FILE, 'rb') as f: # pylint: disable=invalid-name
                mock_get.return_value.content = f.read()

                #patch the logger request
                with patch('tasks.requests.patch') as mock_patch:
                    mock_patch.status_code = 200

                    bluebeam_export.s(
                        export_id=export_obj.guid
                    ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) > 0
        assert len(export_obj.result['failure']) == 0

    # clear out the queue
    queue.control.purge()

def test_export_task_new_project_zip_upload_err(mock_env_access_key):
    # pylint: disable=unused-argument
    """
        Test the export task where submission has a zip attachment
        One of the uploads in zip fails.
    """
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create the export
    export_obj = create_export(db)
    # create a submission so there's something to export
    create_submission(db, mocks.SUBMISSION_POST_DATA_ZIP, export_obj.guid)
    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        fake_post_responses = []
        # create project
        fake_post_responses.append(Mock())
        fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
        fake_post_responses[0].status_code = 200
        # create folders
        i = 1
        while i < 7:
            fake_post_responses.append(Mock())
            fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            i += 1
        # get folders
        fake_post_responses.append(Mock())
        fake_post_responses[7].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_post_responses.append(Mock())
        fake_post_responses[8].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_post_responses.append(Mock())
        fake_post_responses[9].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_post_responses.append(Mock())
        fake_post_responses[10].return_value.status_code = 200
        # confirm upload
        fake_post_responses.append(Mock())
        fake_post_responses[11].status_code = 204
        # get folders 2
        # this mock is modified to contain today's upload folder
        fake_post_responses.append(Mock())
        get_folders_updated = copy.deepcopy(mocks.GET_FOLDERS_RESPONSE)
        get_folders_updated['ProjectFolders'].append(
            {
                '$id': '8',
                'Id': '1234567',
                'Name': bluebeam.SUBMITTAL_DIR_NAME + " " + str(datetime.date.today()),
                'Path': '/path/somewhere'
            }
        )
        fake_post_responses[12].json.return_value = get_folders_updated
        # initiate upload 2
        fake_post_responses.append(Mock())
        fake_post_responses[13].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload 2
        fake_post_responses.append(Mock())
        fake_post_responses[14] = Exception("Generic Error")
        # confirm upload 2
        fake_post_responses.append(Mock())
        fake_post_responses[15].status_code = 204
        # delete project
        fake_post_responses.append(Mock())
        fake_post_responses[16].status_code = 204

        mock_post.side_effect = fake_post_responses

        with patch('tasks.requests.get') as mock_get:
            with open(ZIP_FILE, 'rb') as f: # pylint: disable=invalid-name
                mock_get.return_value.content = f.read()

                #patch the logger request
                with patch('tasks.requests.patch') as mock_patch:
                    mock_patch.status_code = 200

                    bluebeam_export.s(
                        export_id=export_obj.guid
                    ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) == 0
        assert len(export_obj.result['failure']) > 0

    # clear out the queue
    queue.control.purge()

def test_export_task_resubmission(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export resubmission task"""
    print("begin test_export_task_resubmission")
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create a resubmission so there's something to export
    data = mocks.RESUBMISSION_POST_DATA.copy()
    data['_id'] = "123"
    # create the export
    export_obj = create_export(db)
    create_submission(db, data, export_obj.guid)

    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_reqs:
        fake_responses = []
        # project exists
        fake_responses.append(Mock())
        fake_responses[0].status_code = 200
        # get folders
        fake_responses.append(Mock())
        fake_responses[1].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # get folders
        fake_responses.append(Mock())
        fake_responses[2].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_responses.append(Mock())
        fake_responses[3].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_responses.append(Mock())
        fake_responses[4].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_responses.append(Mock())
        fake_responses[5].return_value.status_code = 200
        # confirm upload
        fake_responses.append(Mock())
        fake_responses[6].status_code = 204
        # add user1
        fake_responses.append(Mock())
        fake_responses[7].status_code = 204
        # add user2
        fake_responses.append(Mock())
        fake_responses[8].status_code = 204
        # get project users
        fake_responses.append(Mock())
        fake_responses[9].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE
        # set access user1
        fake_responses.append(Mock())
        fake_responses[10].status_code = 204
        # set access user2
        fake_responses.append(Mock())
        fake_responses[11].status_code = 204

        mock_reqs.side_effect = fake_responses

        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.status_code = 200

            #patch the logger request
            with patch('tasks.requests.patch') as mock_patch:
                mock_patch.status_code = 200

                bluebeam_export.s(
                    export_id=export_obj.guid
                ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) > 0

    # clear out the queue
    queue.control.purge()

def test_export_task_resubmission_log_status_error(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export resubmission task with an error when logging status"""
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create a resubmission so there's something to export
    data = mocks.RESUBMISSION_POST_DATA.copy()
    data['_id'] = "123"
    # create the export
    export_obj = create_export(db)
    create_submission(db, data, export_obj.guid)

    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_reqs:
        fake_responses = []
        # project exists
        fake_responses.append(Mock())
        fake_responses[0].status_code = 200
        # get folders
        fake_responses.append(Mock())
        fake_responses[1].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # get folders
        fake_responses.append(Mock())
        fake_responses[2].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_responses.append(Mock())
        fake_responses[3].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_responses.append(Mock())
        fake_responses[4].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_responses.append(Mock())
        fake_responses[5].return_value.status_code = 200
        # confirm upload
        fake_responses.append(Mock())
        fake_responses[6].status_code = 204

        mock_reqs.side_effect = fake_responses

        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.side_effect = Exception("Patch error")

            bluebeam_export.s(
                export_id=export_obj.guid
            ).apply()

        db.refresh(export_obj)

        assert len(export_obj.result['failure']) > 0

    # clear out the queue
    queue.control.purge()

def test_export_task_resubmission_no_upload_dir(mock_env_access_key):
    # pylint: disable=unused-argument
    """
        Test the export resubmission task when cannot find upload dir
        in preexisting bluebeam project
    """
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create the export
    export_obj = create_export(db)
    # create a resubmission so there's something to export
    create_submission(db, mocks.RESUBMISSION_POST_DATA, export_obj.guid)
    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_reqs:
        fake_responses = []
        # project exists
        fake_responses.append(Mock())
        fake_responses[0].status_code = 200
        # get folders
        fake_responses.append(Mock())
        fake_responses[1].json.return_value = mocks.GET_FOLDERS_RESPONSE_NO_UPLOAD

        mock_reqs.side_effect = fake_responses

        #patch the logger request
        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.status_code = 200

            bluebeam_export.s(
                export_id=export_obj.guid
            ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) == 0
        assert len(export_obj.result['failure']) > 0

    # clear out the queue
    queue.control.purge()

def test_export_task_resubmission_no_project(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export resubmission task but project isn't found in bluebeam"""
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create the export
    export_obj = create_export(db)
    # create a resubmission so there's something to export
    create_submission(db, mocks.RESUBMISSION_POST_DATA, export_obj.guid)
    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_reqs:
        fake_responses = []
        # project exists
        fake_responses.append(Mock())
        fake_responses[0].status_code = 404

        mock_reqs.side_effect = fake_responses

        #patch the logger request
        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.status_code = 200

            bluebeam_export.s(
                export_id=export_obj.guid
            ).apply()

        db.refresh(export_obj)

        assert export_obj.date_finished is not None
        assert len(export_obj.result['success']) == 0
        assert len(export_obj.result['failure']) > 0

    # clear out the queue
    queue.control.purge()

def test_export_task_file_upload_error(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export task when there is an error in uploading to bluebeam"""
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create a submission so there's something to export
    data = mocks.SUBMISSION_POST_DATA.copy()
    data['_id'] = "123"
    # create the export
    export_obj = create_export(db)
    create_submission(db, data, export_obj.guid)
    # mock all responses for expected outbound requests
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        fake_post_responses = []
        # create project
        fake_post_responses.append(Mock())
        fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
        fake_post_responses[0].status_code = 200
        # create folders
        i = 1
        while i < 7:
            fake_post_responses.append(Mock())
            fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            i += 1
        # get folders
        fake_post_responses.append(Mock())
        fake_post_responses[7].json.return_value = mocks.GET_FOLDERS_RESPONSE
        # create folders
        fake_post_responses.append(Mock())
        fake_post_responses[8].json.return_value = mocks.CREATE_FOLDER_RESPONSE
        # initiate upload
        fake_post_responses.append(Mock())
        fake_post_responses[9].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        # upload
        fake_post_responses.append(Mock())
        fake_post_responses[10] = Exception("Generic Error")
        # confirm upload
        fake_post_responses.append(Mock())
        fake_post_responses[11].status_code = 204
        # delete project
        fake_post_responses.append(Mock())
        fake_post_responses[12].status_code = 204

        mock_post.side_effect = fake_post_responses

        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.status_code = 200

            bluebeam_export.s(
                export_id=export_obj.guid
            ).apply()

        db.refresh(export_obj)
        assert export_obj.date_finished is not None
        assert len(export_obj.result['failure']) > 0

    # clear out the queue
    queue.control.purge()

def test_export_task_no_upload_folder(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export task when there is no dir set as the uploads dir"""
    # don't include previous submission
    test_utils.finish_submissions_exports()
    # create the export
    export_obj = create_export(db)
    # create a submission so there's something to export
    create_submission(db, mocks.SUBMISSION_POST_DATA, export_obj.guid)
    # mock all responses for expected outbound requests
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        fake_post_responses = []
        # create project
        fake_post_responses.append(Mock())
        fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
        fake_post_responses[0].status_code = 200
        # create folders
        i = 1
        while i < 8:
            fake_post_responses.append(Mock())
            fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            i += 1
        # delete project
        fake_post_responses.append(Mock())
        fake_post_responses[8].status_code = 204

        mock_post.side_effect = fake_post_responses

        with patch('service.resources.bluebeam.DIRECTORY_STRUCTURE') as mock_dir_structure:
            mock_dir_structure.return_value = [
                {"name": "CCSF EPR"}
            ]

            bluebeam_export.s(
                export_id=export_obj.guid
            ).apply()

            db.refresh(export_obj)
            assert export_obj.date_finished is not None
            assert len(export_obj.result['failure']) > 0

    # clear out the queue
    queue.control.purge()

def test_scheduler(mock_env_access_key):
    # pylint: disable=unused-argument
    """ Test the scheduler chron process """
    print("begin test_scheduler")

    # number of submissions already in db
    existing_submissions_count = db.query(SubmissionModel.id).count()

    with patch('tasks.requests.get') as mock_permits_query:
        # query returns two test submissions
        mock_permits_query.return_value.json.return_value = mocks.BUILDING_PERMITS_EXPORT_QUERY
        mock_permits_query.return_value.status_code = 200

        # mock all bluebeam export requests
        with patch('service.resources.bluebeam.requests.request') as mock_post:
            fake_post_responses = []
            # create project
            fake_post_responses.append(Mock())
            fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
            fake_post_responses[0].status_code = 200
            # create folders
            i = 1
            while i < 8:
                fake_post_responses.append(Mock())
                fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
                i += 1
            # get folders
            fake_post_responses.append(Mock())
            fake_post_responses[7].json.return_value = mocks.GET_FOLDERS_RESPONSE
            # create folders
            fake_post_responses.append(Mock())
            fake_post_responses[8].json.return_value = mocks.CREATE_FOLDER_RESPONSE
            # initiate upload
            fake_post_responses.append(Mock())
            fake_post_responses[9].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
            # upload
            fake_post_responses.append(Mock())
            fake_post_responses[10].return_value.status_code = 200
            # confirm upload
            fake_post_responses.append(Mock())
            fake_post_responses[11].status_code = 204
            # add user1
            fake_post_responses.append(Mock())
            fake_post_responses[12].status_code = 204
            # add user2
            fake_post_responses.append(Mock())
            fake_post_responses[13].status_code = 204
            # get project users
            fake_post_responses.append(Mock())
            fake_post_responses[14].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE
            # set access user1
            fake_post_responses.append(Mock())
            fake_post_responses[15].status_code = 204
            # set access user2
            fake_post_responses.append(Mock())
            fake_post_responses[16].status_code = 204

            mock_post.side_effect = fake_post_responses

            #patch the logger request
            with patch('tasks.requests.patch') as mock_patch:
                mock_patch.status_code = 200

                scheduler.s().apply()

    new_submissions_count = db.query(SubmissionModel.id).count()

    assert new_submissions_count == existing_submissions_count + 2

def test_scheduler_error(mock_env_access_key):
    # pylint: disable=unused-argument
    """ Test the scheduler chron process """
    print("begin test_scheduler_error")

    # number of submissions already in db
    existing_submissions_count = db.query(SubmissionModel.id).count()

    with patch('tasks.requests.get') as mock_permits_query:
        # query returns two test submissions
        mock_permits_query.return_value.json.return_value = mocks.BUILDING_PERMITS_EXPORT_QUERY
        mock_permits_query.side_effect = Exception("Houston, we have a problem")

        scheduler.s().apply()

    new_submissions_count = db.query(SubmissionModel.id).count()

    assert new_submissions_count == existing_submissions_count
