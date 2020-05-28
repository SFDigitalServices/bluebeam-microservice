"""Bluebeam module"""
#pylint: disable=too-few-public-methods, invalid-name
import os
import datetime
from time import perf_counter
import requests
from service.resources.utils import create_url
# from oauthlib.oauth2 import LegacyApplicationClient
# from requests_oauthlib import OAuth2Session

BLUEBEAM_CLIENT_ID = os.environ.get('BLUEBEAM_CLIENT_ID')
BLUEBEAM_CLIENT_SECRET = os.environ.get('BLUEBEAM_CLIENT_SECRET')
BLUEBEAM_AUTHSERVER = os.environ.get('BLUEBEAM_AUTHSERVER')
BLUEBEAM_AUTH_PATH = '/auth/oauth/authorize'
BLUEBEAM_TOKEN_PATH = '/auth/token'

# USERNAME = os.environ.get('BLUEBEAM_USERNAME')
# PASSWORD = os.environ.get('BLUEBEAM_PASSWORD')
BLUEBEAM_API_BASE_URL = os.environ.get('BLUEBEAM_API_BASE_URL')

UPLOAD_DIR_NAME = "2.DOCUMENTS FOR REVIEW"
SUBMITTAL_DIR_NAME = "SUBMITTAL"
DIRECTORY_STRUCTURE = [
    {"name": "CCSF EPR", "subdirs":[
        {"name": "A.PERMIT SUBMITTAL", "subdirs":[
            {"name": "1.PERMIT FORMS"},
            {"name": UPLOAD_DIR_NAME, "pdf_uploads": True} # there can be only one
        ]},
        {"name": "B.APPROVED DOCUMENTS", "subdirs":[
            {"name": "1.BUILDING PERMIT DOCUMENTS"}
        ]}
    ]}
]

ERR_NO_UPLOAD_DIR_FOUND = "Could not find the upload directory on Bluebeam"

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
def create_project(access_token, project_name):
    """
        creates project in bluebeam
    """
    response = bluebeam_request(
        'post',
        BLUEBEAM_API_BASE_URL + "/projects",
        headers={
            'Authorization': 'Bearer ' + access_token
        },
        json={
            "Name": project_name,
            "Notification": True,
            "Restricted": True
        })
    response_json = response.json()

    if response.status_code != 200:
        raise Exception("Error creating project in Bluebeam.  ErrorCode:{0}".format(
            response_json['ErrorCode']
        ))
    idee = response_json['Id']
    print("Created project id:{0}".format(idee))
    return idee

@timer
def delete_project(access_token, project_id):
    """
        deletes project in bluebeam
    """
    bluebeam_request(
        'delete',
        BLUEBEAM_API_BASE_URL + "/projects/" + str(project_id),
        headers={
            'Authorization': 'Bearer ' + access_token
        }
    )

@timer
def project_exists(access_token, project_id):
    """
        determines if a project_id is valid
    """
    response = bluebeam_request(
        'get',
        BLUEBEAM_API_BASE_URL + "/projects/" + str(project_id),
        headers={
            'Authorization': 'Bearer ' + access_token
        }
    )
    return response.status_code == 200

@timer
def create_folder(access_token, project_id, folder_name, comment='', parent_folder_id=0):
    """
        creates a folder in a project
    """
    print("bluebeam.create_folder:{0}".format(folder_name))
    response = bluebeam_request(
        'post',
        BLUEBEAM_API_BASE_URL + "/projects/" + str(project_id) + "/folders",
        headers={
            'Authorization': 'Bearer ' + access_token
        },
        json={
            "Name": folder_name,
            "ParentFolderId": parent_folder_id,
            "Comment": comment
        })
    idee = response.json()['Id']
    print("Created folder id:{0}".format(idee))
    return idee

@timer
def get_folders(access_token, project_id):
    """
        gets all folders in a project
    """
    print("bluebeam.get_folders")
    response = bluebeam_request(
        'get',
        BLUEBEAM_API_BASE_URL + "/projects/" + str(project_id) + "/folders",
        headers={
            'Authorization': 'Bearer ' + access_token
        }
    )
    response_json = response.json()
    return response_json['ProjectFolders']

def get_upload_dir_id(access_token, project_id):
    """
        finds the upload folder id of a bluebeam project
    """
    dir_id = dir_exists(UPLOAD_DIR_NAME, project_id, access_token)
    if not dir_id:
        raise Exception(ERR_NO_UPLOAD_DIR_FOUND)

    return dir_id

def dir_exists(name, project_id, access_token, dirs_array=None):
    """
        returns directory id if it exists in the project, false otherwise
    """
    if dirs_array is None:
        dirs_array = get_folders(access_token, project_id)

    for folder in dirs_array:
        if folder['Name'] == name:
            return folder['Id']
    return False

def upload_file(access_token, project_id, file_name, file_content, folder_id):
    """
        uploads a file to bluebeam for given project_id and folder_id
    """
    try:
        print("bluebeam.upload_file:{0}".format(file_name))

        upload_dir_of_the_day = SUBMITTAL_DIR_NAME + " " + str(datetime.date.today())
        upload_dir_of_the_day_id = dir_exists(upload_dir_of_the_day, project_id, access_token)
        if not upload_dir_of_the_day_id:
            upload_dir_of_the_day_id = create_folder(
                access_token,
                project_id,
                upload_dir_of_the_day,
                parent_folder_id=folder_id
            )

        # find out where to upload file
        response_json = initiate_upload(
            access_token,
            project_id,
            file_name,
            upload_dir_of_the_day_id
        )
        upload_url = response_json['UploadUrl']
        file_id = response_json['Id']
        upload_content_type = response_json['UploadContentType']

        # upload file
        upload(upload_url, file_content, upload_content_type)

        # confirm upload
        return confirm_upload(access_token, project_id, file_id)

    except Exception as err: # pylint: disable=broad-except
        print("Caught exception in bluebeam.upload_file: {0}".format(err))
        return False

@timer
def initiate_upload(acccess_code, project_id, file_name, folder_id):
    """
        initate file upload with bluebeam
    """
    print("bluebeam.initiate_upload")
    response = bluebeam_request(
        'post',
        BLUEBEAM_API_BASE_URL + "/projects/" + str(project_id) + "/files",
        headers={
            'Authorization': 'Bearer ' + acccess_code
        },
        json={
            "Name": file_name,
            "ParentFolderId": folder_id
        }
    )
    return response.json()

@timer
def upload(upload_url, file_contents, content_type):
    """
        uploads file
    """
    print("bluebeam.upload")
    bluebeam_request(
        'put',
        upload_url,
        data=file_contents,
        headers={
            'Content-type': content_type,
            'x-amz-server-side-encryption': 'AES256'
        }
    )

@timer
def confirm_upload(access_token, project_id, file_id):
    """
        true/false confirm upload with bluebeam
    """
    print("bluebeam.confirm_upload")
    response = bluebeam_request(
        'post',
        BLUEBEAM_API_BASE_URL + "/projects/" + str(project_id) +
        "/files/" + str(file_id) + "/confirm-upload",
        headers={
            'Authorization': 'Bearer ' + access_token
        }
    )
    return response.status_code == 204

def create_directories(access_code, project_id, directories, parent_folder_id=0):
    """
        Recursive function for creating directories
        Returns pdf upload directory id if it was created, otherwise None
    """
    print("bluebeam.create_directories")
    pdf_folder_id = None
    for folder in directories:
        folder_id = create_folder(access_code,\
                project_id,\
                folder["name"],\
                parent_folder_id=parent_folder_id)

        if "subdirs" in folder:
            possible_pdf_folder_id = create_directories(
                access_code,
                project_id,
                folder["subdirs"],
                folder_id
            )
            if possible_pdf_folder_id is not None:
                pdf_folder_id = possible_pdf_folder_id

        if "pdf_uploads" in folder and folder["pdf_uploads"]:
            pdf_folder_id = folder_id
    return pdf_folder_id

def bluebeam_request(method, url, data=None, json=None, headers=None):
    """ prints bluebeam requests info to log """
    print("endpoint: {0}".format(url))
    print("method: {0}".format(method))
    print("request header: {0}".format(headers))
    if data is not None:
        print("request body: {0}".format(data))
    if json is not None:
        print("request body: {0}".format(json))
    print("start timestamp: {0}".format(datetime.datetime.now()))
    response = requests.request(method=method, url=url, data=data, json=json, headers=headers)
    print("end timestamp: {0}".format(datetime.datetime.now()))
    print("response header: {0}".format(response.headers))
    print("response body: {0}".format(response.text))
    return response
