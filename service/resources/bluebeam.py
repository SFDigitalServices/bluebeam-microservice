"""Bluebeam module"""
#pylint: disable=too-few-public-methods, invalid-name
import os
import requests
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

TOKEN_URL = "https://authserver.bluebeam.com/auth/token"
USERNAME = os.environ.get('BLUEBEAM_USERNAME')
PASSWORD = os.environ.get('BLUEBEAM_PASSWORD')
CLIENT_ID = os.environ.get('BLUEBEAM_CLIENT_ID')
CLIENT_SECRET = os.environ.get('BLUEBEAM_CLIENT_SECRET')
BASE_URL = "https://studioapi.bluebeam.com:443/publicapi/v1"

oauth = OAuth2Session(client=LegacyApplicationClient(client_id=CLIENT_ID))
extra = {
    'client_id': CLIENT_ID,
    'client_secrent': CLIENT_SECRET
}

def get_token():
    """
        retrieves oauth2 token
    """
    return oauth.fetch_token(token_url=TOKEN_URL,\
            username=USERNAME,\
            password=PASSWORD,\
            client_id=CLIENT_ID)

def get_projects(access_token):
    """
        gets all project in bluebeam
    """
    response = requests.get(BASE_URL + "/projects?api_key=" + access_token)
    return response.json()

def create_project(access_token, project_name):
    """
        creates project in bluebeam
    """
    response = requests.post(BASE_URL + "/projects?api_key=" + access_token,\
            json={
                "Name": project_name,
                "Notification": True,
                "Restricted": True
            })
    return response.json()['Id']

def create_folder(access_token, project_id, folder_name, comment='', parent_folder_id=0):
    """
        creates a folder in a project
    """
    response = requests.post(BASE_URL + "/projects/" + project_id +\
                    "/folders?api_key=" + access_token,\
                    json={
                        "Name": folder_name,
                        "ParentFolderId": parent_folder_id,
                        "Comment": comment
                    })
    return response.json()['Id']

def get_folders(access_token, project_id):
    """
        gets all folders in a project
    """
    response = requests.get(BASE_URL + "/projects/" + project_id +\
                    "/folders?api_key=" + access_token)
    return response.json()

def upload_file(access_token, project_id, filepath, folder_id):
    """
        uploads a file to bluebeam for given project_id and folder_id
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError

    # find out where to upload file
    response = requests.post(BASE_URL + "/projects/" + project_id +\
                    "/files?api_key=" + access_token,\
                    json={
                        "Name": os.path.basename(filepath),
                        "ParentFolderId": folder_id
                    })
    response_json = response.json()
    upload_url = response_json['UploadUrl']
    file_id = response_json['Id']
    upload_content_type = response_json['UploadContentType']

    # upload file
    response = requests.put(upload_url, data=open(filepath, 'rb'),\
            headers={
                'Content-type': upload_content_type,
                'x-amz-server-side-encryption': 'AES256'
            })

    # confirm upload
    response = requests.post(BASE_URL + "/projects/" + project_id +\
                    "/files/" + str(file_id) + "/confirm-upload" +\
                    "?api_key=" + access_token)

    return response.status_code == 204
