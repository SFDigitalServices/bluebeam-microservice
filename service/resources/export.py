"""Export module"""
#pylint: disable=too-few-public-methods,too-many-statements,too-many-locals,no-member

import json
import jsend
import falcon
from mako.template import Template
from service.resources.models import ExportStatusModel
from service.resources.utils import create_url, is_valid_uuid
import service.resources.bluebeam as bluebeam
# from requests_oauthlib import OAuth2Session

class Export():
    """ Export class """
    def on_get(self, _req, resp):
        """ handle export get requests """
        resp.content_type = falcon.MEDIA_HTML
        if 'code' in _req.params:
            # handle redirect back from auth server
            try:
                # convert auth code to access token
                redirect_uri = self.create_redirect_url(
                    _req.forwarded_scheme,
                    _req.forwarded_host,
                    _req.port
                )
                access_response = bluebeam.get_access_token_response(
                    _req.params['code'],
                    redirect_uri
                )

                bluebeam.save_auth_token(self.session, access_response)

                resp.status = falcon.HTTP_200
                template = Template(filename='templates/login_success.html')
                resp.body = template.render()

            except Exception as err: # pylint: disable=broad-except
                # error in scheduling
                err_string = "{0}".format(err)

                # present error ui
                print("error:")
                print(err_string)
                resp.status = falcon.HTTP_500
                template = Template(filename='templates/login_error.html')
                resp.body = template.render(error_message=err_string)
        else:
            resp.status = falcon.HTTP_303
            resp.set_header('Location', '/login')

    @staticmethod
    def create_redirect_url(scheme, host, port):
        """ generates the redirect url for passing to oauth2 server """
        base = scheme + '://' + host
        if port:
            base = base + ':' + str(port)
        return create_url(base, '/export')

class ExportStatus():
    """ ExportStatus Class """

    def on_get(self, _req, resp):
        #pylint: disable=no-self-use
        """ returns status of the export """
        try:
            if 'export_id' in _req.params:
                export_id = _req.params['export_id']

                if not is_valid_uuid(export_id):
                    raise Exception("Invalid export_id")

                exports = self.session.query(ExportStatusModel).filter( # pylint: disable=no-member
                    ExportStatusModel.guid == export_id
                )
                if exports.count() == 1:
                    export_status = exports.first()
                    resp.status = falcon.HTTP_200

                    if export_status.result is None:
                        export_status.result = {
                            'success':[],
                            'failure':[]
                        }
                    resp.body = json.dumps(jsend.success({
                        'is_finished': export_status.date_finished is not None,
                        'success': export_status.result['success'],
                        'failure': export_status.result['failure']
                    }))
                else:
                    raise Exception("Invalid export_id")
            else:
                raise Exception("export_id is required")
        except Exception as err: # pylint: disable=broad-except
            err_msg = "{0}".format(err)
            print(err_msg)
            resp.status = falcon.HTTP_500
            resp.body = json.dumps(jsend.error(err_msg))
