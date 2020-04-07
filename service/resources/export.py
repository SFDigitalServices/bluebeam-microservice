"""Export module"""
#pylint: disable=too-few-public-methods

import json
from urllib.parse import urlparse, urlunparse, urlencode
import jsend
import falcon
from mako.template import Template
import requests
from service.resources.models import create_export, SubmissionModel, ExportStatusModel
from tasks import bluebeam_export
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
                bluebeam_token_url = create_url(
                    bluebeam.BLUEBEAM_AUTHSERVER,
                    bluebeam.BLUEBEAM_TOKEN_PATH
                )
                auth_response = requests.post(
                    bluebeam_token_url,
                    {
                        'grant_type': 'authorization_code',
                        'code': _req.params['code'],
                        'client_id': bluebeam.BLUEBEAM_CLIENT_ID,
                        'client_secret': bluebeam.BLUEBEAM_CLIENT_SECRET,
                        'redirect_uri': self.create_redirect_url(
                            _req.forwarded_scheme,
                            _req.forwarded_host,
                            _req.port
                        )
                    }
                )
                auth_response_json = json.loads(auth_response.text)

                if 'access_token' not in auth_response_json:
                    # didn't get access token from bluebeam
                    raise Exception(auth_response_json['error'])

                # happy path
                # show spinner ui which will poll for export status
                export_obj = create_export(self.session, auth_response_json['userName']) # pylint: disable=no-member

                resp.status = falcon.HTTP_200
                template = Template(filename='templates/exporting.html')
                resp.body = template.render(export_id=export_obj.guid)

                print("access_token:{0}".format(auth_response_json['access_token']))
                bluebeam_export.apply_async(
                    (export_obj, auth_response_json['access_token']),
                    serializer='pickle',
                )
            except Exception as err: # pylint: disable=broad-except
                # error in scheduling
                # present error ui
                err_string = "{0}".format(err)
                print("error:")
                print(err_string)
                resp.status = falcon.HTTP_500
                template = Template(filename='templates/exporting_error.html')
                resp.body = template.render(error_message=err_string)
        else:
            resp.status = falcon.HTTP_200

            # is there an export in progress?
            exports = self.session.query(ExportStatusModel).filter( # pylint: disable=no-member
                ExportStatusModel.date_finished.is_(None)
            )

            if exports.count() == 0:
                # is there something to export?
                submissions = self.session.query(SubmissionModel).filter( # pylint: disable=no-member
                    SubmissionModel.date_exported.is_(None)
                )

                if submissions.count() > 0:
                    # present ui to redirect to bluebeam for auth
                    bluebeam_auth_url = create_url(
                        bluebeam.BLUEBEAM_AUTHSERVER,
                        bluebeam.BLUEBEAM_AUTH_PATH,
                        {
                            'response_type': 'code',
                            'client_id': bluebeam.BLUEBEAM_CLIENT_ID,
                            'scope': 'full_prime',
                            'redirect_uri': self.create_redirect_url(
                                _req.forwarded_scheme,
                                _req.forwarded_host,
                                _req.port
                            )
                        }
                    )
                    template = Template(filename='templates/export.html')
                    resp.body = template.render(bluebeam_auth_url=bluebeam_auth_url)
                else:
                    # nothing to export
                    template = Template(filename='templates/nothing_to_export.html')
                    resp.body = template.render()
            else:
                export_obj = exports.first()
                template = Template(filename='templates/exporting.html')
                resp.body = template.render(export_id=export_obj.guid)

    def create_redirect_url(self, scheme, host, port):
        #pylint: disable=no-self-use
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
        if 'export_id' in _req.params:
            export_id = _req.params['export_id']
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
                    'success_count': len(export_status.result['success']),
                    'failures': export_status.result['failure']
                }))
            else:
                resp.status = falcon.HTTP_500
                resp.body = json.dumps(jsend.error("Invalid export_id"))
        else:
            resp.status = falcon.HTTP_500
            resp.body = json.dumps(jsend.error("export_id is required"))

def create_url(base_url, path, args_dict=None):
    """ helper for creating urls """
    if args_dict is None:
        args_dict = {}
    url_parts = list(urlparse(base_url))
    url_parts[2] = path
    url_parts[4] = urlencode(args_dict)
    return urlunparse(url_parts)
