# pylint: disable=redefined-outer-name
"""Tests for microservice"""
import os
import json
import uuid
import datetime
from unittest.mock import patch, Mock
import copy
import jsend
import pytest
from falcon import testing
import service.microservice
import service.resources.bluebeam as bluebeam
import tests.mocks as mocks
from service.resources.models import SubmissionModel, ExportStatusModel,\
    create_export, create_submission, is_url, validate
from service.resources.db import create_session, db_engine
from tasks import celery_app as queue, bluebeam_export, ERR_UPLOAD_FAIL

CLIENT_HEADERS = {
    "ACCESS_KEY": "1234567"
}

BLUEBEAM_USERNAME = "user@sfgov.org"
BLUEBEAM_ACCESS_CODE = "secret_key"
TEST_PDF = 'tests/resources/dummy.pdf'
ZIP_FILE = 'tests/resources/Archive.zip'

session = create_session() # pylint: disable=invalid-name
db = session() # pylint: disable=invalid-name

@pytest.fixture()
def client():
    """ client fixture """
    return testing.TestClient(app=service.microservice.start_service(), headers=CLIENT_HEADERS)

@pytest.fixture
def mock_env_access_key(monkeypatch):
    """ mock environment access key """
    monkeypatch.setenv("ACCESS_KEY", CLIENT_HEADERS["ACCESS_KEY"])
    monkeypatch.setenv("BLUEBEAM_CLIENT_ID", "12345")
    monkeypatch.setenv("BLUEBEAM_CLIENT_SECRET", "12345")
    monkeypatch.setenv("BLUEBEAM_AUTHSERVER", "https://auth.test.com")
    monkeypatch.setenv("BLUEBEAM_USERNAME", BLUEBEAM_USERNAME)
    monkeypatch.setenv("BLUEBEAM_PASSWORD", "secret")
    monkeypatch.setenv("BLUEBEAM_API_BASE_URL", "https://api.test.com")
    monkeypatch.setenv("CLOUDSTORAGE_URL", "https://cloud.storage.com")
    monkeypatch.setenv("CLOUDSTORAGE_API_KEY", "12345")
    monkeypatch.setenv("BUCKETEER_DOMAIN", "bucketeer.com")
    monkeypatch.setenv("SPREADSHEETS_MICROSERVICE_URL", "https://spreadsheets.com")
    monkeypatch.setenv("SPREADSHEETS_MICROSERVICE_API_KEY", "12345")

@pytest.fixture
def mock_env_no_access_key(monkeypatch):
    """ mock environment with no access key """
    monkeypatch.delenv("ACCESS_KEY", raising=False)

@pytest.fixture(scope='session')
def celery_config():
    """ config for celery worker """
    return {
        'broker_url': os.environ['REDIS_URL'],
        'task_serializer': 'pickle',
        'accept_content': ['pickle', 'application/x-python-serialize', 'json', 'application/json']
    }

def test_welcome(client, mock_env_access_key):
    # pylint: disable=unused-argument
    # mock_env_access_key is a fixture and creates a false positive for pylint
    """Test welcome message response"""
    response = client.simulate_get('/welcome')
    assert response.status_code == 200

    expected_msg = jsend.success({'message': 'Welcome'})
    assert json.loads(response.content) == expected_msg

    # Test welcome request with no ACCESS_KEY in header
    client_no_access_key = testing.TestClient(service.microservice.start_service())
    response = client_no_access_key.simulate_get('/welcome')
    assert response.status_code == 403

def test_welcome_no_access_key(client, mock_env_no_access_key):
    # pylint: disable=unused-argument
    # mock_env_no_access_key is a fixture and creates a false positive for pylint
    """Test welcome request with no ACCESS_key environment var set"""
    response = client.simulate_get('/welcome')
    assert response.status_code == 403


def test_default_error(client, mock_env_access_key):
    # pylint: disable=unused-argument
    """Test default error response"""
    response = client.simulate_get('/some_page_that_does_not_exist')

    assert response.status_code == 404

    expected_msg_error = jsend.error('404 - Not Found')
    assert json.loads(response.content) == expected_msg_error

def test_submission(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """Test submission"""
    response = client.simulate_post(
        '/submission',
        json=mocks.SUBMISSION_POST_DATA
    )
    assert response.status_code == 200
    response_json = json.loads(response.text)
    assert response_json["status"] == "success"

    # check that its in the db
    submission_id = response_json["data"]["submission_id"]
    s = db.query(SubmissionModel).filter(SubmissionModel.id == submission_id) # pylint: disable=invalid-name
    assert s is not None

    # test validation rules
    response = client.simulate_post(
        '/submission'
    )
    assert response.status_code == 500

    # no project_name nor project_id
    response = client.simulate_post(
        '/submission',
        json={
            i:mocks.SUBMISSION_POST_DATA[i] for i in mocks.SUBMISSION_POST_DATA if i != 'project_name' # pylint: disable=line-too-long
        }
    )
    assert response.status_code == 500

    # malformed files
    submission_post_data = mocks.SUBMISSION_POST_DATA.copy()
    submission_post_data['files'] = 'a'
    response = client.simulate_post(
        '/submission',
        json=submission_post_data
    )
    assert response.status_code == 500

    submission_post_data = mocks.SUBMISSION_POST_DATA.copy()
    submission_post_data['files'] = [{
        "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    }]
    response = client.simulate_post(
        '/submission',
        json=submission_post_data
    )
    assert response.status_code == 500

def test_logger_validation():
    """ test logger parameter rules """
    data = mocks.SUBMISSION_POST_DATA.copy()
    data['logger'] = mocks.LOGGER_PARAMETERS.copy()
    data['_id'] = "123"

    # happy path
    result = validate(data)
    assert result == data

    # missing _id
    with pytest.raises(Exception):
        validate({i:data[i] for i in data if i != '_id'})

    # missing logger parameters
    params = [
        'spreadsheet_key',
        'worksheet_title',
        'id_column_label',
        'status_column_label'
    ]
    for param in params:
        data['logger']['google_sheets'] = {
            i:mocks.LOGGER_PARAMETERS['google_sheets'][i] for i in mocks.LOGGER_PARAMETERS['google_sheets'] if i != param # pylint: disable=line-too-long
        }
        with pytest.raises(Exception):
            validate(data)

def test_is_url():
    """ test is_url function """
    assert not is_url(1)
    assert not is_url(None)
    assert not is_url('')
    assert not is_url('abcd')
    assert not is_url(True)
    assert is_url('http://foo.com')

def test_bluebeam_create_project_invalid_name():
    """ Test invalid bluebeam project name """
    with patch('service.resources.bluebeam.requests.request') as mock_request:
        mock_request.json.return_value = mocks.CREATE_PROJECT_RESPONSE_INVALID_NAME
        mock_request.status_code = 400

        with pytest.raises(Exception):
            bluebeam.create_project("access_token", "invalid/character")

def test_export_task_new_project(mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the export task"""
    # don't include previous submission
    finish_submissions_exports()
    # create a submission so there's something to export
    data = mocks.SUBMISSION_POST_DATA.copy()
    data['logger'] = mocks.LOGGER_PARAMETERS.copy()
    data['_id'] = "123"
    create_submission(db, data)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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

        mock_post.side_effect = fake_post_responses

        with patch('tasks.requests.patch') as mock_patch:
            mock_patch.status_code = 200

            bluebeam_export.s(
                export_obj=export_obj,
                access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a submission so there's something to export
    create_submission(db, {
        i:mocks.SUBMISSION_POST_DATA[i] for i in mocks.SUBMISSION_POST_DATA if i != 'files'
    })
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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

        mock_post.side_effect = fake_post_responses

        bluebeam_export.s(
            export_obj=export_obj,
            access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a submission so there's something to export
    create_submission(db, mocks.BUCKETEER_SUBMISSION_POST_DATA)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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

        mock_post.side_effect = fake_post_responses

        with patch('tasks.requests.get') as mock_get:
            with open(TEST_PDF, 'rb') as f: # pylint: disable=invalid-name
                mock_get.return_value.content = f.read()

                bluebeam_export.s(
                    export_obj=export_obj,
                    access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a submission so there's something to export
    submission_data_with_permit = mocks.SUBMISSION_POST_DATA.copy()
    submission_data_with_permit['building_permit_number'] = '202001011234'
    create_submission(db, submission_data_with_permit)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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

        mock_post.side_effect = fake_post_responses

        bluebeam_export.s(
            export_obj=export_obj,
            access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a submission so there's something to export
    create_submission(db, mocks.SUBMISSION_POST_DATA_ZIP)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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
        mock_post.side_effect = fake_post_responses

        with patch('tasks.requests.get') as mock_get:
            with open(ZIP_FILE, 'rb') as f: # pylint: disable=invalid-name
                mock_get.return_value.content = f.read()

                bluebeam_export.s(
                    export_obj=export_obj,
                    access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a submission so there's something to export
    create_submission(db, mocks.SUBMISSION_POST_DATA_ZIP)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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

                bluebeam_export.s(
                    export_obj=export_obj,
                    access_code=BLUEBEAM_ACCESS_CODE
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
    # don't include previous submission
    finish_submissions_exports()
    # create a resubmission so there's something to export
    data = mocks.RESUBMISSION_POST_DATA.copy()
    data['logger'] = mocks.LOGGER_PARAMETERS.copy()
    data['_id'] = "123"
    create_submission(db, data)

    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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
            mock_patch.status_code = 200

            bluebeam_export.s(
                export_obj=export_obj,
                access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a resubmission so there's something to export
    data = mocks.RESUBMISSION_POST_DATA.copy()
    data['logger'] = mocks.LOGGER_PARAMETERS.copy()
    data['_id'] = "123"
    create_submission(db, data)

    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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
                export_obj=export_obj,
                access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a resubmission so there's something to export
    create_submission(db, mocks.RESUBMISSION_POST_DATA)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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

        bluebeam_export.s(
            export_obj=export_obj,
            access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a resubmission so there's something to export
    create_submission(db, mocks.RESUBMISSION_POST_DATA)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
    # mock all responses for expected requests
    with patch('service.resources.bluebeam.requests.request') as mock_reqs:
        fake_responses = []
        # project exists
        fake_responses.append(Mock())
        fake_responses[0].status_code = 404

        mock_reqs.side_effect = fake_responses

        bluebeam_export.s(
            export_obj=export_obj,
            access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a submission so there's something to export
    data = mocks.SUBMISSION_POST_DATA.copy()
    data['logger'] = mocks.LOGGER_PARAMETERS.copy()
    data['_id'] = "123"
    create_submission(db, data)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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
                export_obj=export_obj,
                access_code=BLUEBEAM_ACCESS_CODE
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
    finish_submissions_exports()
    # create a submission so there's something to export
    create_submission(db, mocks.SUBMISSION_POST_DATA)
    # create the export
    export_obj = create_export(db, BLUEBEAM_USERNAME)
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
                export_obj=export_obj,
                access_code=BLUEBEAM_ACCESS_CODE
            ).apply()

            db.refresh(export_obj)
            assert export_obj.date_finished is not None
            assert len(export_obj.result['failure']) > 0

    # clear out the queue
    queue.control.purge()

def test_export(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """
        tests the export ui
    """
    # clear up entries in db
    finish_submissions_exports()

    # Nothing to export
    response = client.simulate_get('/export')
    assert response.status_code == 200
    assert 'No records to export today' in response.text

    # Submissions exist to export
    create_submission(db, mocks.SUBMISSION_POST_DATA)
    response = client.simulate_get('/export')
    assert response.status_code == 200
    assert 'Export form submissions to Bluebeam' in response.text

    # Redirect back from authserver with invalid grant
    with patch('service.resources.bluebeam.requests.request') as mock_auth_post:
        mock_auth_post.return_value.json.return_value = mocks.INVALID_GRANT_RESPONSE

        response = client.simulate_get('/export?code=super-secrete-code')
        assert response.status_code == 500
        assert 'Export Error' in response.text

        exports_in_progress = db.query(ExportStatusModel).filter(
            ExportStatusModel.date_finished.is_(None)
        )
        assert exports_in_progress.count() == 0

    # Error when scheduling with celery
    with patch('service.resources.bluebeam.requests.request') as mock_auth_post:
        mock_auth_post.return_value.json.return_value = mocks.ACCESS_TOKEN_RESPONSE

        with patch('tasks.bluebeam_export.apply_async') as mock_schedule:
            mock_schedule.side_effect = Exception("Couldn't schedule")

            response = client.simulate_get('/export?code=schedule-error')
            assert response.status_code == 500
            assert 'Export Error' in response.text

            exports_in_progress = db.query(ExportStatusModel).filter(
                ExportStatusModel.date_finished.is_(None)
            )
            assert exports_in_progress.count() == 0

    # Redirect back from authserver with valid code
    with patch('service.resources.bluebeam.requests.request') as mock_auth_post:
        mock_auth_post.return_value.json.return_value = mocks.ACCESS_TOKEN_RESPONSE

        response = client.simulate_get('/export?code=super-secret-code')
        assert response.status_code == 200
        assert 'Exporting' in response.text

        exports_in_progress = db.query(ExportStatusModel).filter(
            ExportStatusModel.date_finished.is_(None)
        )
        assert exports_in_progress.count() == 1

    # export already in progress
    response = client.simulate_get('/export')
    assert response.status_code == 200
    assert 'Exporting' in response.text

    # clear out the queue
    queue.control.purge()

def test_export_status(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """
        test the export status endpoint
    """
    # clear up entries in db
    finish_submissions_exports()

    # no export id
    response = client.simulate_get('/export/status')
    assert response.status_code == 500

    # nonexisting export id
    guid = uuid.uuid4()
    response = client.simulate_get('/export/status?export_id=' + str(guid))
    assert response.status_code == 500

    # invalid export id
    response = client.simulate_get('/export/status?export_id=123')
    assert response.status_code == 500

    # export in progress
    export_obj = create_export(db, BLUEBEAM_USERNAME)
    response = client.simulate_get('/export/status?export_id=' + str(export_obj.guid))
    assert response.status_code == 200
    response_json = json.loads(response.text)
    assert not response_json['data']['is_finished']

    # clear out the queue
    queue.control.purge()

def finish_submissions_exports():
    """
        sets the date_exported on all existing submissions and
        date_finished on all export_status in the database
    """
    export_obj = create_export(db, BLUEBEAM_USERNAME)

    with db_engine.connect() as con:
        sql = "UPDATE submission SET date_exported=now() at time zone 'utc', " +\
            "export_guid='" + str(export_obj.guid) + "' " +\
            "WHERE date_exported IS NULL"
        con.execute(sql)

        sql = "UPDATE export_status set date_finished=now() at time zone 'utc' " +\
            "WHERE date_finished IS NULL"
        con.execute(sql)
