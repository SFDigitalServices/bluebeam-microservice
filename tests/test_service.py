# pylint: disable=redefined-outer-name
# pylint: disable=too-many-lines
# pylint: disable=too-many-statements
"""Tests for microservice"""
import json
import uuid
from unittest.mock import patch, Mock
import jsend
import requests
from falcon import testing
import service.microservice
import service.resources.bluebeam as bluebeam
import tests.mocks as mocks
import tests.utils as test_utils
from service.resources.models import SubmissionModel, create_export, UserModel
from service.resources.db import create_session
from tasks import celery_app as queue

session = create_session() # pylint: disable=invalid-name
db = session() # pylint: disable=invalid-name

# create users
db.query(UserModel).delete()
user1 = UserModel(email='user1@test.com') #pylint: disable=invalid-name
user2 = UserModel(email='user2@test.com') #pylint: disable=invalid-name
db.add(user1)
db.add(user2)
db.commit()

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

def test_export_status(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """
        test the export status endpoint
    """
    # clear up entries in db
    test_utils.finish_submissions_exports()

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
    export_obj = create_export(db)
    response = client.simulate_get('/export/status?export_id=' + str(export_obj.guid))
    assert response.status_code == 200
    response_json = json.loads(response.text)
    assert not response_json['data']['is_finished']

    # clear out the queue
    queue.control.purge()

def test_long_error_message():
    """
        test that long error message gets truncated
    """
    submission = SubmissionModel(data={'foo':'bar'}, error_message='x'*1000)
    db.add(submission)
    db.commit()
    assert len(submission.error_message) == 255

def test_bluebeam_set_permission_error():
    """
        test handling of error when setting user
        permission in bluebeam
    """
    users = db.query(UserModel).all()
    with patch('service.resources.bluebeam.requests.request') as mock_reqs:
        fake_responses = []
        # add user1
        fake_responses.append(Mock())
        fake_responses[0].status_code = 204
        # add user2
        fake_responses.append(Mock())
        fake_responses[1].status_code = 204
        # get project users
        fake_responses.append(Mock())
        fake_responses[2].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE
        # set access user1
        fake_responses.append(Mock())
        fake_responses[3].status_code = 500
        fake_responses[3].raise_for_status.side_effect = requests.exceptions.HTTPError
        # set access user2
        fake_responses.append(Mock())
        fake_responses[4].status_code = 204

        mock_reqs.side_effect = fake_responses

        bluebeam.assign_user_permissions(test_utils.BLUEBEAM_ACCESS_TOKEN, '123-456-789', users)

def test_user_does_not_exist_permission_error():
    """
        test handling of error when adding user to a project
    """
    users = db.query(UserModel).all()
    with patch('service.resources.bluebeam.requests.request') as mock_req:
        fake_responses = []
        # add user1
        fake_responses.append(Mock())
        fake_responses[0].status_code = 404
        fake_responses[0].json.return_value = mocks.USER_DOES_NOT_EXIST_RESPONSE
        fake_responses[0].raise_for_status.side_effect = requests.exceptions.HTTPError
        # add user2
        fake_responses.append(Mock())
        fake_responses[1].status_code = 404
        fake_responses[1].json.return_value = mocks.USER_DOES_NOT_EXIST_RESPONSE
        fake_responses[1].raise_for_status.side_effect = requests.exceptions.HTTPError
        # get project users
        fake_responses.append(Mock())
        fake_responses[2].json.return_value = mocks.GET_PROJECT_USERS_RESPONSE

        mock_req.side_effect = fake_responses

        bluebeam.assign_user_permissions(test_utils.BLUEBEAM_ACCESS_TOKEN, '123-456-789', users)


def test_export(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """
        tests the export ui
    """
    # clear up entries in db
    test_utils.finish_submissions_exports()

    # access export directly
    # should be redirected to /login
    response = client.simulate_get('/export')
    assert response.status_code == 303

    # Redirect back from authserver with invalid grant
    with patch('service.resources.bluebeam.requests.request') as mock_auth_post:
        mock_auth_post.return_value.json.return_value = mocks.INVALID_GRANT_RESPONSE

        response = client.simulate_get('/export?code=super-secrete-code')
        assert response.status_code == 500
        assert 'Login Error' in response.text

    # Error when scheduling with celery
    # with patch('service.resources.bluebeam.requests.request') as mock_auth_post:
    #     mock_auth_post.return_value.json.return_value = mocks.ACCESS_TOKEN_RESPONSE

    #     with patch('tasks.bluebeam_export.apply_async') as mock_schedule:
    #         mock_schedule.side_effect = Exception("Couldn't schedule")

    #         response = client.simulate_get('/export?code=schedule-error')
    #         assert response.status_code == 500
    #         assert 'Export Error' in response.text

    #         exports_in_progress = db.query(ExportStatusModel).filter(
    #             ExportStatusModel.date_finished.is_(None)
    #         )
    #         assert exports_in_progress.count() == 0

    # Redirect back from authserver with valid code
    with patch('service.resources.bluebeam.requests.request') as mock_auth_post:
        mock_auth_post.return_value.json.return_value = mocks.ACCESS_TOKEN_RESPONSE

        response = client.simulate_get('/export?code=super-secret-code')
        assert response.status_code == 200
        assert 'Success!' in response.text

def test_login(mock_env_access_key, client):
    # pylint: disable=unused-argument
    """ test login page """
    response = client.simulate_get('/login')

    assert response.status_code == 303
    location_header = response.headers.get('location')
    assert "bluebeam.com" in location_header
