"""Submission module"""
#pylint: disable=too-few-public-methods
import json
from dateutil import tz
import falcon
import jsend
from .hooks import validate_access
from .models import create_submission

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
            json_params = _req.media
            validate(json_params)
            submission = create_submission(self.session, json_params) # pylint: disable=no-member

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

def validate(json_params):
    """enforce validation rules"""
    #pylint: disable=unused-argument
    if "address" not in json_params:
        raise Exception("address is a required field")
    return True
