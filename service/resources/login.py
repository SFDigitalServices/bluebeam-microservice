"""login module"""
#pylint: disable=too-few-public-methods

import falcon
from service.resources.export import Export
from service.resources.utils import create_url
import service.resources.bluebeam as bluebeam

class Login():
    """ Login class """
    def on_get(self, _req, resp):
        #pylint: disable=no-self-use
        """
            redirect to bluebeam for auth
            /export is still the redirect url so processing of the auth token is finished there
        """
        bluebeam_auth_url = create_url(
            bluebeam.BLUEBEAM_AUTHSERVER,
            bluebeam.BLUEBEAM_AUTH_PATH,
            {
                'response_type': 'code',
                'client_id': bluebeam.BLUEBEAM_CLIENT_ID,
                'scope': 'full_user',
                'redirect_uri': Export.create_redirect_url(
                    _req.forwarded_scheme,
                    _req.forwarded_host,
                    _req.port
                )
            }
        )

        # redirect to bluebeam for auth
        raise falcon.HTTPSeeOther(bluebeam_auth_url)
        # resp.status = falcon.HTTP_303
        # resp.set_header('Location', bluebeam_auth_url)
