""" utility functions for tests """
import datetime
import pytz
from service.resources.models import create_export
from service.resources.db import create_session, db_engine

session = create_session() # pylint: disable=invalid-name
db = session() # pylint: disable=invalid-name

NOW = datetime.datetime.utcnow().astimezone(pytz.UTC)
HOUR_FUTURE = NOW + datetime.timedelta(hours=1)
BLUEBEAM_ACCESS_TOKEN = {
    "access_token":"secret",
    "token_type":"bearer",
    "expires_in":3599,
    "refresh_token":"secret2",
    "userName":"user@test.com",
    "client_id":"client_id",
    "scope":"scope",
    "refresh_token_expires_in":"5184000",
    ".issued":NOW.strftime("%a, %d %b %Y %H:%M:%S %Z"),
    ".expires":HOUR_FUTURE.strftime("%a, %d %b %Y %H:%M:%S %Z")
}

def finish_submissions_exports():
    """
        sets the date_exported on all existing submissions and
        date_finished on all export_status in the database
    """
    export_obj = create_export(db)

    with db_engine.connect() as con:
        sql = "UPDATE submission SET date_exported=now() at time zone 'utc', " +\
            "export_guid='" + str(export_obj.guid) + "' " +\
            "WHERE date_exported IS NULL"
        con.execute(sql)

        sql = "UPDATE export_status set date_finished=now() at time zone 'utc' " +\
            "WHERE date_finished IS NULL"
        con.execute(sql)
