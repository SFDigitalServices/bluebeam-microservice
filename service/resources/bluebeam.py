"""Bluebeam module"""
#pylint: disable=too-few-public-methods, invalid-name
import os
from time import perf_counter
import requests
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

BLUEBEAM_CLIENT_ID = os.environ.get('BLUEBEAM_CLIENT_ID')
BLUEBEAM_CLIENT_SECRET = os.environ.get('BLUEBEAM_CLIENT_SECRET')
BLUEBEAM_AUTHSERVER = os.environ.get('BLUEBEAM_AUTHSERVER')
BLUEBEAM_AUTH_PATH = '/auth/oauth/authorize'
BLUEBEAM_TOKEN_PATH = '/auth/token'

USERNAME = os.environ.get('BLUEBEAM_USERNAME')
PASSWORD = os.environ.get('BLUEBEAM_PASSWORD')
BLUEBEAM_API_BASE_URL = os.environ.get('BLUEBEAM_API_BASE_URL')

DIRECTORY_STRUCTURE = [
    {"name": "CCSF EPR", "subdirs":[
        {"name": "A.PERMIT SUBMITTAL", "subdirs":[
            {"name": "1.PERMIT FORMS"},
            {"name": "2.ROUTING FORMS"},
            {"name": "3.DOCUMENTS FOR REVIEW", "pdf_uploads": True} # there can be only one
        ]},
        {"name": "B.APPROVED DOCUMENTS", "subdirs":[
            {"name": "1.BUILDING PERMIT DOCUMENTS"}
        ]}
    ]}
]

def get_token():
    """
        retrieves oauth2 token via password grant
    """
    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=BLUEBEAM_CLIENT_ID))
    return oauth.fetch_token(
        token_url=BLUEBEAM_AUTHSERVER+BLUEBEAM_TOKEN_PATH,
        username=USERNAME,
        password=PASSWORD,
        client_id=BLUEBEAM_CLIENT_ID
    )

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

@timer
def get_projects(access_token):
    """
        gets all project in bluebeam
    """
    response = requests.get(
        BLUEBEAM_API_BASE_URL + "/projects",
        headers={
            'Authorization': 'Bearer ' + access_token
        })
    return response.json()

@timer
def create_project(access_token, project_name):
    """
        creates project in bluebeam
    """
    response = requests.post(
        BLUEBEAM_API_BASE_URL + "/projects",
        headers={
            'Authorization': 'Bearer ' + access_token
        },
        json={
            "Name": project_name,
            "Notification": True,
            "Restricted": True
        })
    idee = response.json()['Id']
    print("Created project id:{0}".format(idee))
    return idee

@timer
def create_folder(access_token, project_id, folder_name, comment='', parent_folder_id=0):
    """
        creates a folder in a project
    """
    response = requests.post(
        BLUEBEAM_API_BASE_URL + "/projects/" + project_id + "/folders",
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
    response = requests.get(
        BLUEBEAM_API_BASE_URL + "/projects/" + project_id + "/folders",
        headers={
            'Authorization': 'Bearer ' + access_token
        },
    )
    return response.json()

@timer
def upload_file(access_token, project_id, file_name, file_content, folder_id):
    """
        uploads a file to bluebeam for given project_id and folder_id
    """

    # find out where to upload file
    response = requests.post(
        BLUEBEAM_API_BASE_URL + "/projects/" + project_id + "/files",
        headers={
            'Authorization': 'Bearer ' + access_token
        },
        json={
            "Name": file_name,
            "ParentFolderId": folder_id
        }
    )
    response_json = response.json()
    upload_url = response_json['UploadUrl']
    file_id = response_json['Id']
    upload_content_type = response_json['UploadContentType']

    # upload file
    response = requests.put(
        upload_url,
        data=file_content,
        headers={
            'Content-type': upload_content_type,
            'x-amz-server-side-encryption': 'AES256'
        }
    )

    # confirm upload
    response = requests.post(
        BLUEBEAM_API_BASE_URL + "/projects/" + project_id +
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
