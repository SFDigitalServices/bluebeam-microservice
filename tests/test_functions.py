"""Test functions"""
import datetime
from unittest.mock import patch
import pytest
from cryptography.fernet import Fernet
import service.resources.bluebeam as bluebeam
from service.resources.db import create_session
from service.resources.models import is_url, TokenModel
import service.resources.utils as utils
import tests.mocks as mocks
import tests.utils as test_utils
from tasks import format_project_id

session = create_session() # pylint: disable=invalid-name
db = session() # pylint: disable=invalid-name

def test_invalid_file_name():
    """ test uploading a file with an invalid filename """
    with patch('service.resources.bluebeam.requests.request') as mock_post:
        mock_post.return_value.json.return_value = mocks.INIT_FILE_UPLOAD_INVALID_NAME_RESPONSE
        mock_post.return_value.status_code = 200

        with pytest.raises(Exception):
            bluebeam.initiate_upload('access_code', '123', '"<>|:*?\\/', '123')

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

def test_cryptography():
    """ Test the encrypt and decrypt functions """
    secret = "The worst thing about prison was the dementors."
    key = Fernet.generate_key()

    encrypted_message = utils.encrypt(key, secret)
    decrypted_message = utils.decrypt(key, encrypted_message)

    assert decrypted_message == secret

def test_no_stored_token():
    """ Test case where no token is stored in db """
    # delete token in db
    db.query(TokenModel).delete()

    # get token from db
    token = bluebeam.get_auth_token(db)

    assert token is None

def test_save_get_token():
    """ Test saving and retrieving token from db """
    token = mocks.ACCESS_TOKEN_RESPONSE.copy()

    # expired token
    hour_past = test_utils.NOW - datetime.timedelta(hours=1)
    token['.expires'] = hour_past.strftime("%a, %d %b %Y %H:%M:%S %Z")
    bluebeam.save_auth_token(db, token)
    with patch('service.resources.bluebeam.requests.request') as mock_token_request:
        mock_token_request.return_value.json.return_value = test_utils.BLUEBEAM_ACCESS_TOKEN
        mock_token_request.return_value.status_code = 200
        retrieved_token = bluebeam.get_auth_token(db)

    assert test_utils.BLUEBEAM_ACCESS_TOKEN == retrieved_token

def test_format_project_id():
    """ Test the format_project_id function from tasks.py """
    project_id = format_project_id("123456789")
    assert project_id == "123-456-789"

    input_id = "12345"
    project_id = format_project_id(input_id)
    assert project_id == input_id

    input_id = "1234567890"
    project_id = format_project_id(input_id)
    assert project_id == input_id

    input_id = "ABCDEFG"
    project_id = format_project_id(input_id)
    assert project_id == input_id
