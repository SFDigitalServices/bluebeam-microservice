"""Export module"""
#pylint: disable=too-few-public-methods

import json
from datetime import datetime
import jsend
import falcon
from mako.template import Template
from service.resources.models import create_export, SubmissionModel, ExportStatusModel
from service.resources.utils import create_url, is_valid_uuid
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
            export_obj = None
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

                # happy path
                # show spinner ui which will poll for export status
                export_obj = create_export(self.session, access_response['userName']) # pylint: disable=no-member

                resp.status = falcon.HTTP_200
                template = Template(filename='templates/exporting.html')
                resp.body = template.render(export_id=export_obj.guid)

                bluebeam_export.apply_async(
                    (export_obj, access_response),
                    serializer='pickle',
                )
            except Exception as err: # pylint: disable=broad-except
                # error in scheduling
                err_string = "{0}".format(err)

                # finish this export
                if export_obj is not None:
                    export_obj.date_finished = datetime.utcnow()
                    export_obj.result = err_string
                    self.session.commit() # pylint: disable=no-member

                # present error ui
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
                            'scope': 'full_user',
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
