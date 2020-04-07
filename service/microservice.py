"""Main application module"""
import os
import json
import jsend
import sentry_sdk
import falcon
from .resources.db import create_session
from .resources.welcome import Welcome
from .resources.submission import Submission
from .resources.export import Export, ExportStatus

def start_service():
    """Start this service
    set SENTRY_DSN environmental variable to enable logging with Sentry
    """
    # Initialize Sentry
    sentry_sdk.init(os.environ.get('SENTRY_DSN'))
    # Initialize Falcon
    api = falcon.API(middleware=[SQLAlchemySessionManager(create_session())])
    api.add_route('/welcome', Welcome())
    api.add_route('/submission', Submission())
    api.add_route('/export/status', ExportStatus())
    api.add_route('/export', Export())
    api.add_static_route('/static', os.path.abspath('static'))
    api.add_sink(default_error, '^((?!static).)*$')
    return api

def default_error(_req, resp):
    """Handle default error"""
    resp.status = falcon.HTTP_404
    msg_error = jsend.error('404 - Not Found')

    sentry_sdk.capture_message(msg_error)
    resp.body = json.dumps(msg_error)

class SQLAlchemySessionManager:
    """
    Create a session for every request and close it when the request ends.
    """

    def __init__(self, Session):
        self.Session = Session # pylint: disable=invalid-name

    def process_resource(self, req, resp, resource, params):
        # pylint: disable=unused-argument
        """attach a db session for every resource"""
        resource.session = self.Session()

    def process_response(self, req, resp, resource, req_succeeded):
        # pylint: disable=no-self-use, unused-argument
        """close db session for every resource"""
        if hasattr(resource, 'session'):
            resource.session.close()
