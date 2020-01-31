"""Project module"""
#pylint: disable=too-few-public-methods
import json
from datetime import datetime
import falcon
import jsend
import service.resources.bluebeam as bluebeam
from .hooks import validate_access

@falcon.before(validate_access)
class Project():
    """Project class"""
    def on_post(self, _req, resp):
        #pylint: disable=no-self-use
        """
            Create a project in Bluebeam and upload plans
        """
        # folders = {
        #     "folders": ["folder1"]
        # }

        # get api token
        token = bluebeam.get_token()
        api_key = token['access_token']

        # create project
        now = datetime.now()
        project_name = "project" + now.strftime('%Y%m%d_%H%M%S')
        new_project = bluebeam.create_project(api_key, project_name)
        project_id = new_project['Id']
        # print("api_key:")
        # print(api_key)

        # get list of projects
        projects = bluebeam.get_projects(api_key)

        # create folder in new project
        new_folder = bluebeam.create_folder(api_key, project_id, 'my-awesome-folder')

        # get all folders in new project
        all_folders = bluebeam.get_folders(api_key, project_id)

        # upload pdf to new folder in new project
        is_upload_successful = bluebeam.upload_file(api_key, project_id,\
                'docs/misc/sfgov.pdf', new_folder['Id'])

        response_object = {
            'access_token': api_key,
            'new_id': new_project['Id'],
            'all_projects': projects,
            'all_folders': all_folders,
            'upload_success': is_upload_successful
        }
        resp.body = json.dumps(jsend.success(response_object))
        resp.status = falcon.HTTP_200
