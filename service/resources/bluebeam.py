"""Bluebeam module"""
#pylint: disable=too-few-public-methods, invalid-name
import os
import datetime
import re
from time import perf_counter
import json
from dateutil import parser
import pytz
import requests
from service.resources.utils import create_url, encrypt, decrypt
from service.resources.models import TokenModel
# from oauthlib.oauth2 import LegacyApplicationClient
# from requests_oauthlib import OAuth2Session

BLUEBEAM_CLIENT_ID = os.environ.get('BLUEBEAM_CLIENT_ID')
BLUEBEAM_CLIENT_SECRET = os.environ.get('BLUEBEAM_CLIENT_SECRET')
BLUEBEAM_AUTHSERVER = os.environ.get('BLUEBEAM_AUTHSERVER')
BLUEBEAM_AUTH_PATH = '/auth/oauth/authorize'
BLUEBEAM_TOKEN_PATH = '/auth/token'
BLUEBEAM_API_BASE_URL = os.environ.get('BLUEBEAM_API_BASE_URL')

UPLOAD_DIR_NAME = "3.DOCUMENTS FOR REVIEW"
SUBMITTAL_DIR_NAME = "SUBMITTAL"
DIRECTORY_STRUCTURE = [
    {"name": "CCSF EPR", "subdirs":[
        {"name": "A.PERMIT SUBMITTAL", "subdirs":[
            {"name": "1.PERMIT FORMS"},
            {"name": "2.ROUTING FORMS"},
            {"name": UPLOAD_DIR_NAME, "pdf_uploads": True} # there can be only one
        ]},
        {"name": "B.APPROVED DOCUMENTS", "subdirs":[
            {"name": "1.BUILDING PERMIT DOCUMENTS"}
        ]}
    ]}
]

ERR_NO_UPLOAD_DIR_FOUND = "Could not find the upload directory on Bluebeam"
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY").encode()

def timer(func):
    """
        decorator to calculate runtime
    """
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        result = func(*args, **kwargs)
        end_time = perf_counter()
        run_time = end_time - start_time
        print(f"{func.__name__!r} finished in {run_time:.4f} secs")
        return result
    return wrapper

# def get_token():
#     """
#         retrieves oauth2 token via password grant
#     """
#     oauth = OAuth2Session(client=LegacyApplicationClient(client_id=BLUEBEAM_CLIENT_ID))
#     return oauth.fetch_token(
#         token_url=BLUEBEAM_AUTHSERVER+BLUEBEAM_TOKEN_PATH,
#         username=USERNAME,
#         password=PASSWORD,
#         client_id=BLUEBEAM_CLIENT_ID
#     )

# @timer
# def get_projects(access_token):
#     """
#         gets all project in bluebeam
#     """
#     response = requests.get(
#         BLUEBEAM_API_BASE_URL + "/projects",
#         headers={
#             'Authorization': 'Bearer ' + access_token
#         })
#     return response.json()

@timer
def get_access_token_response(auth_code, redirect_uri):
    """
        Get access_token from bluebeam
    """
    bluebeam_token_url = create_url(
        BLUEBEAM_AUTHSERVER,
        BLUEBEAM_TOKEN_PATH
    )
    auth_response = bluebeam_request(
        'post',
        bluebeam_token_url,
        data={
            'grant_type': 'authorization_code',
            'code': auth_code,
            'client_id': BLUEBEAM_CLIENT_ID,
            'client_secret': BLUEBEAM_CLIENT_SECRET,
            'redirect_uri': redirect_uri
        }
    )
    auth_response_json = auth_response.json()
    if 'access_token' not in auth_response_json:
        # didn't get access token from bluebeam
        raise Exception(auth_response_json['error'])
    return auth_response_json

@timer
def refresh_token(token):
    """
        get new token with refresh token
    """
    bluebeam_token_url = create_url(
        BLUEBEAM_AUTHSERVER,
        BLUEBEAM_TOKEN_PATH
    )
    response = bluebeam_request(
        'post',
        bluebeam_token_url,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': token,
            'client_id': BLUEBEAM_CLIENT_ID,
            'client_secret': BLUEBEAM_CLIENT_SECRET
        }
    )
    return response.json()

def get_auth_token(dbSession):
    """
        retrieve auth token from db
    """
    token_query = dbSession.query(TokenModel)
    if token_query.count() > 0:
        token = token_query.first()
        # convert to json
        token = json.loads(decrypt(ENCRYPTION_KEY, token.value))

        # maybe refresh token
        now = datetime.datetime.utcnow().astimezone(pytz.UTC)
        expiration_date = parser.parse(token['.expires'])
        if now > expiration_date:
            token = refresh_token(token['refresh_token'])
            save_auth_token(dbSession, token)

        return token

    return None

def save_auth_token(dbSession, json_token):
    """
        save auth token to db
    """
    token_query = dbSession.query(TokenModel)
    token = None
    if token_query.count() > 0:
        token = token_query.first()
    else:
        token = TokenModel()
        dbSession.add(token)

    token.value = encrypt(ENCRYPTION_KEY, json.dumps(json_token))
    dbSession.commit()

@timer
def create_project(access, project_name):
    """
        creates project in bluebeam
    """
    response = bluebeam_request(
        'post',
        "{0}/projects".format(BLUEBEAM_API_BASE_URL),
        json={
            "Name": project_name,
            "Notification": True,
            "Restricted": True
        },
        access=access)
    response_json = response.json()

    idee = response_json['Id']
    print("Created project id:{0}".format(idee))
    return idee

@timer
def delete_project(access, project_id):
    """
        deletes project in bluebeam
    """
    bluebeam_request(
        'delete',
        '{0}/projects/{1}'.format(BLUEBEAM_API_BASE_URL, project_id),
        access=access
    )

@timer
def project_exists(access, project_id):
    """
        determines if a project_id is valid
    """
    response = bluebeam_request(
        'get',
        '{0}/projects/{1}'.format(BLUEBEAM_API_BASE_URL, project_id),
        access=access
    )
    return response.status_code == 200

@timer
def create_folder(access, project_id, folder_name, comment='', parent_folder_id=0):
    """
        creates a folder in a project
    """
    print("bluebeam.create_folder:{0}".format(folder_name))
    response = bluebeam_request(
        'post',
        '{0}/projects/{1}/folders'.format(BLUEBEAM_API_BASE_URL, project_id),
        json={
            "Name": folder_name,
            "ParentFolderId": parent_folder_id,
            "Comment": comment
        },
        access=access)
    idee = response.json()['Id']
    print("Created folder id:{0}".format(idee))
    return idee

@timer
def get_folders(access, project_id):
    """
        gets all folders in a project
    """
    print("bluebeam.get_folders")
    response = bluebeam_request(
        'get',
        '{0}/projects/{1}/folders'.format(BLUEBEAM_API_BASE_URL, project_id),
        access=access
    )
    response_json = response.json()
    return response_json['ProjectFolders']

def get_upload_dir_id(access, project_id):
    """
        finds the upload folder id of a bluebeam project
    """
    dir_id = dir_exists(UPLOAD_DIR_NAME, project_id, access)
    if not dir_id:
        raise Exception(ERR_NO_UPLOAD_DIR_FOUND)

    return dir_id

def dir_exists(name, project_id, access, dirs_array=None):
    """
        returns directory id if it exists in the project, false otherwise
    """
    if dirs_array is None:
        dirs_array = get_folders(access, project_id)

    for folder in dirs_array:
        if folder['Name'] == name:
            return folder['Id']
    return False

def upload_file(access, project_id, file_name, file_path, folder_id):
    """
        uploads a file to bluebeam for given project_id and folder_id
    """
    print("bluebeam.upload_file:{0}".format(file_name))
    # remove illegal characters
    file_name = re.sub(r'["<>\|:\*\?\\/]', '_', file_name)

    upload_dir_of_the_day = "{0} {1}".format(SUBMITTAL_DIR_NAME, datetime.date.today())
    upload_dir_of_the_day_id = dir_exists(upload_dir_of_the_day, project_id, access)
    if not upload_dir_of_the_day_id:
        upload_dir_of_the_day_id = create_folder(
            access,
            project_id,
            upload_dir_of_the_day,
            parent_folder_id=folder_id
        )

    # find out where to upload file
    response_json = initiate_upload(
        access,
        project_id,
        file_name,
        upload_dir_of_the_day_id
    )
    upload_url = response_json['UploadUrl']
    file_id = response_json['Id']
    upload_content_type = response_json['UploadContentType']

    # upload file
    upload(upload_url, file_path, upload_content_type)

    # confirm upload
    return confirm_upload(access, project_id, file_id)

@timer
def initiate_upload(access, project_id, file_name, folder_id):
    """
        initate file upload with bluebeam
    """
    print("bluebeam.initiate_upload")
    response = bluebeam_request(
        'post',
        '{0}/projects/{1}/files'.format(BLUEBEAM_API_BASE_URL, project_id),
        json={
            "Name": file_name,
            "ParentFolderId": folder_id
        },
        access=access
    )

    return response.json()

@timer
def upload(upload_url, file_path, content_type):
    """
        uploads file
    """
    print("bluebeam.upload")
    with open(file_path, 'rb') as file_obj:
        bluebeam_request(
            'put',
            upload_url,
            data=file_obj,
            headers={
                'Content-Type': content_type,
                'x-amz-server-side-encryption': 'AES256'
            }
        )

@timer
def confirm_upload(access, project_id, file_id):
    """
        true/false confirm upload with bluebeam
    """
    print("bluebeam.confirm_upload")
    response = bluebeam_request(
        'post',
        '{0}/projects/{1}/files/{2}/confirm-upload'.format(
            BLUEBEAM_API_BASE_URL,
            project_id,
            file_id),
        access=access
    )
    return response.status_code == 204

def create_directories(access, project_id, directories, parent_folder_id=0):
    """
        Recursive function for creating directories
        Returns pdf upload directory id if it was created, otherwise None
    """
    print("bluebeam.create_directories")
    pdf_folder_id = None
    for folder in directories:
        folder_id = create_folder(access,\
                project_id,\
                folder["name"],\
                parent_folder_id=parent_folder_id)

        if "subdirs" in folder:
            possible_pdf_folder_id = create_directories(
                access,
                project_id,
                folder["subdirs"],
                folder_id
            )
            if possible_pdf_folder_id is not None:
                pdf_folder_id = possible_pdf_folder_id

        if "pdf_uploads" in folder and folder["pdf_uploads"]:
            pdf_folder_id = folder_id
    return pdf_folder_id

def assign_user_permissions(access, project_id, users):
    """
        assigns full access to each email in users
    """
    print("assign_user_permissions")
    emails = list(map(lambda user: user.email, users))
    added_user_emails = []
    for email in emails:
        # add the user to the project
        try:
            add_project_user(access, project_id, email)
            added_user_emails.append(email)
        except Exception as err:    # pylint: disable=broad-except
            # non blocking error
            print("Unable to add {0} to the project".format(email))

    # give the users full access
    project_users = get_project_users(access, project_id)
    print("project_users: {0}".format(project_users))
    if 'ProjectUsers' in project_users:
        for project_user in project_users['ProjectUsers']:
            # looking for users which were just added
            if project_user['Email'] in added_user_emails:
                try:
                    user_id = project_user['Id']
                    set_full_access_for_user(access, project_id, user_id)
                except Exception as err:    # pylint: disable=broad-except
                    # non blocking error
                    # print out error and continue
                    print("Encountered error giving access to {0}:{1}".format(
                        project_user['Email'],
                        err
                    ))

@timer
def add_project_user(access, project_id, email):
    """
        adds a user to a project
    """
    print("add_project_user:{0}".format(email))
    bluebeam_request(
        'post',
        '{0}/projects/{1}/users'.format(BLUEBEAM_API_BASE_URL, project_id),
        json={
            "Email": email,
            "SendEmail": False,
            "Message": "You've been added to Bluebeam project {0}".format(project_id)
        },
        access=access
    )

@timer
def set_full_access_for_user(access, project_id, user_id):
    """
        sets full access to allow for user_id
    """
    bluebeam_request(
        'put',
        '{0}/projects/{1}/users/{2}/permissions'.format(
            BLUEBEAM_API_BASE_URL,
            project_id,
            user_id
        ),
        json={
            "Type": "FullControl",
            "Allow": "Allow"
        },
        access=access
    )

@timer
def get_project_users(access, project_id):
    """
        gets users for a project
    """
    response = bluebeam_request(
        'get',
        '{0}/projects/{1}/users'.format(
            BLUEBEAM_API_BASE_URL,
            project_id
        ),
        access=access
    )
    return response.json()

def bluebeam_request(method, url, data=None, json=None, headers=None, access=None): #pylint: disable=too-many-arguments,redefined-outer-name
    """ prints bluebeam requests info to log """
    print("endpoint: {0}".format(url))
    print("method: {0}".format(method))
    print("request header: {0}".format(headers))
    if data is not None:
        print("request body: {0}".format(data))
    if json is not None:
        print("request body: {0}".format(json))

    if access is not None:
        if headers is None:
            headers = {}
        headers['Authorization'] = 'Bearer {0}'.format(access['access_token'])

    print("start timestamp: {0}".format(datetime.datetime.now()))
    response = requests.request(method=method, url=url, data=data, json=json, headers=headers)
    print("end timestamp: {0}".format(datetime.datetime.now()))
    print("response header: {0}".format(response.headers))
    print("response body: {0}".format(response.text))
    response.raise_for_status()
    return response
