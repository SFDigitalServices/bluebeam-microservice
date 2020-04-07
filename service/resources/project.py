# pylint: skip-file
"""Project module"""
# pylint: disable=too-few-public-methods
import json
from datetime import datetime
import falcon
import jsend
import service.resources.bluebeam as bluebeam
from .hooks import validate_access

class Project():
    """Project class"""

    directory_structure = [
        {"name": "CCSF EPR", "folders":[
            {"name": "A.PERMIT SUBMITTAL", "folders":[
                {"name": "1.PERMIT FORMS"},
                {"name": "2.ROUTING FORMS"},
                {"name": "3.DOCUMENTS FOR REVIEW", "pdf_uploads": True} # there can be only one
            ]},
            {"name": "B.APPROVED DOCUMENTS", "folders":[
                {"name": "1.BUILDING PERMIT DOCUMENTS"}
            ]}
        ]}
    ]

    # stores id of folder when pdf uploads go
    pdf_folder_id = None

    def on_get(self, _req, resp):
        access_key = _req.params["key"]
        projects = bluebeam.get_projects(access_key)
        resp.status = falcon.HTTP_200
        resp.body = json.dumps(projects)

    def on_post(self, _req, resp):
        #pylint: disable=no-self-use
        """
            Create a project in Bluebeam and upload plans
        """

        # get api token
        token = bluebeam.get_token()
        api_key = token['access_token']

        # create project
        now = datetime.now()
        project_name = now.strftime('%Y-%m%d-%H%M%S') + "49 S. Van Ness"
        project_id = bluebeam.create_project(api_key, project_name)
        # print("api_key:")
        # print(api_key)

        # get list of projects
        projects = bluebeam.get_projects(api_key)

        # create folder structure in new project
        self.create_directories(api_key, project_id, self.directory_structure)

        # get all folders in new project
        all_folders = bluebeam.get_folders(api_key, project_id)

        # upload pdf to new folder in new project
        if self.pdf_folder_id is not None:
            is_upload_successful = bluebeam.upload_file(api_key, project_id,\
                    'docs/misc/sfgov.pdf', self.pdf_folder_id)

            response_object = {
                'access_token': api_key,
                'new_id': project_id,
                'all_projects': projects,
                'all_folders': all_folders,
                'upload_success': is_upload_successful
            }
            resp.body = json.dumps(jsend.success(response_object))
            resp.status = falcon.HTTP_200
        else:
            resp.body = json.dumps(jsend.error("There wasn't a folder_id to upload pdfs to"))
            resp.status = falcon.HTTP_500

    def create_directories(self, api_key, project_id, directories, parent_folder_id=0):
        """
            Recursive function for creating directories
        """
        for folder in directories:
            folder_id = bluebeam.create_folder(api_key,\
                    project_id,\
                    folder["name"],\
                    parent_folder_id=parent_folder_id)

            if "pdf_uploads" in folder and folder["pdf_uploads"]:
                self.pdf_folder_id = folder_id

            if "folders" in folder:
                self.create_directories(api_key, project_id, folder["folders"], folder_id)
