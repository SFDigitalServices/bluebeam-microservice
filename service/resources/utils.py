"""Utils module"""
from urllib.parse import urlparse, urlunparse, urlencode
from uuid import UUID
from cryptography.fernet import Fernet

def create_url(base_url, path, args_dict=None):
    """ helper for creating urls """
    if args_dict is None:
        args_dict = {}
    url_parts = list(urlparse(base_url))
    url_parts[2] = path
    url_parts[4] = urlencode(args_dict)
    return urlunparse(url_parts)

def is_valid_uuid(uuid_to_test, version=4):
    """
        Check if uuid_to_test is a valid UUID.
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test

def encrypt(key, message):
    """
        encrypt the message with key
    """
    return Fernet(key).encrypt(message.encode())

def decrypt(key, token):
    """
        decrypt the token with key
    """
    return Fernet(key).decrypt(token).decode()

def get_files(submission_json):
    """ find the json files blob since in can be in several different places """
    upload_fields = [
        'addendaUploads',
        'optionalUploads',
        'requiredUploads',
        'uploads'
    ]
    uploads = []
    submission_data = submission_json.get('data')
    for field in upload_fields:
        field_value = submission_data.get(field)
        if field_value is not None and len(field_value) > 0:
            uploads += submission_data.get(field)

    return uploads
