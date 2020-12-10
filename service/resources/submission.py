"""Submission module"""
#pylint: disable=too-few-public-methods
import os
import json
from dateutil import tz
import falcon
import jsend
from tasks import bluebeam_export
from service.resources.db import create_session
from .models import create_submission, create_export
from .hooks import validate_access

LOCAL_TZ = tz.gettz("America/Los_Angeles")

@falcon.before(validate_access)
class Submission():
    """Submission class"""

    def on_post(self, _req, resp):
        #pylint: disable=no-self-use
        """
            Record post into the database
        """
        try:
            request_body = _req.bounded_stream.read()
            json_params = json.loads(request_body)
            export_id = None

            # if this is webhook, automatically start export
            if '_webhook' in json_params and 'type' in json_params['_webhook']:
                # verify if webhook supported
                if os.environ.get("WEBHOOK_{0}_URL".format(json_params['_webhook']['type'])):
                    session = create_session()
                    db_session = session()
                    export_obj = create_export(db_session)
                    export_id = export_obj.guid
                    db_session.commit()

                else:
                    resp.status = falcon.HTTP_500
                    resp.body = json.dumps(jsend.error(
                        "Webhook {0} not supported".format(json_params['_webhook']['type'])
                    ))
                    return

            submission = create_submission(self.session, json_params, export_id) # pylint: disable=no-member

            if export_id:
                bluebeam_export.apply_async(
                    args=(export_id,),
                    serializer='pickle'
                )

            resp.status = falcon.HTTP_200
            resp.body = json.dumps(jsend.success({
                'submission_id': submission.id,
                'date_received': submission.date_received.astimezone(LOCAL_TZ).strftime(
                    "%Y/%m/%d, %H:%M:%S"
                )
            }))
        except Exception as err: # pylint: disable=broad-except
            print("error:")
            print("{0}".format(err))
            resp.status = falcon.HTTP_500
            resp.body = json.dumps(jsend.error("{0}".format(err)))
