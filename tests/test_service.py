# pylint: disable=redefined-outer-name
"""Tests for microservice"""
import json
from unittest.mock import patch, Mock
import jsend
import pytest
from falcon import testing
import service.microservice
import service.resources.bluebeam as bluebeam
import tests.mocks as mocks

CLIENT_HEADERS = {
    "ACCESS_KEY": "1234567"
}

@pytest.fixture()
def client():
    """ client fixture """
    return testing.TestClient(app=service.microservice.start_service(), headers=CLIENT_HEADERS)

@pytest.fixture
def mock_env_access_key(monkeypatch):
    """ mock environment access key """
    monkeypatch.setenv("ACCESS_KEY", CLIENT_HEADERS["ACCESS_KEY"])

@pytest.fixture
def mock_env_no_access_key(monkeypatch):
    """ mock environment with no access key """
    monkeypatch.delenv("ACCESS_KEY", raising=False)

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

def test_create_project(client, mock_env_access_key):
    # pylint: disable=unused-argument
    """Test the project post endpoint"""

    with patch('service.resources.bluebeam.requests.get') as mock_get:
        fake_get_responses = [Mock(), Mock()]
        # get projects
        fake_get_responses[0].json.return_value = mocks.GET_PROJECTS_RESPONSE
        # get folders
        fake_get_responses[1].json.return_value = mocks.GET_FOLDERS_RESPONSE
        mock_get.side_effect = fake_get_responses

        with patch('service.resources.bluebeam.oauth.fetch_token') as mock_fetch_token:
            mock_fetch_token.return_value = mocks.FETCH_TOKEN_RESPONSE

            with patch('service.resources.bluebeam.requests.post') as mock_post:
                fake_post_responses = [Mock()] * 10
                # create project
                fake_post_responses[0].json.return_value = mocks.CREATE_PROJECT_RESPONSE
                # create folders
                i = 1
                while i < 8:
                    fake_post_responses[i].json.return_value = mocks.CREATE_FOLDER_RESPONSE
                    i += 1
                # initiate upload
                fake_post_responses[8].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
                # confirm upload
                fake_post_responses[9].status_code.return_value = 204
                mock_post.side_effect = fake_post_responses

                with patch('service.resources.bluebeam.requests.put') as mock_put:
                    # upload pdf
                    mock_put.return_value.status_code = 200

                    response = client.simulate_post('/project')

                    assert response.status_code == 200

def test_file_not_found():
    """Test that exception is thrown with nonexisting file"""
    with patch('service.resources.bluebeam.requests.post') as mock_post:
        fake_post_responses = [Mock(), Mock()]
        # initiate upload
        fake_post_responses[0].json.return_value = mocks.INIT_FILE_UPLOAD_RESPONSE
        #confirm uplaod
        fake_post_responses[1].status_code.return_value = 204
        mock_post.side_effect = fake_post_responses

        with patch('service.resources.bluebeam.requests.put') as mock_put:
            # upload pdf
            mock_put.return_value.status_code = 200

            with pytest.raises(FileNotFoundError):
                bluebeam.upload_file("123", "abc", "docs/misc/nonexisting.pdf", "987")
