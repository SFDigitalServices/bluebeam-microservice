"""Data Models"""

import datetime
import uuid
from urllib.parse import urlparse
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

BASE = declarative_base()

REQUIRED_LOGGER_PARAMS = [
        'spreadsheet_key',
        'worksheet_title',
        'id_column_label',
        'status_column_label'
    ]

class SubmissionModel(BASE):
    # pylint: disable=too-few-public-methods
    """Map Submission object to db"""

    __tablename__ = 'submission'
    id = sa.Column('id', sa.Integer, primary_key=True)
    data = sa.Column('data', sa.JSON, nullable=False)
    date_received = sa.Column(
        'date_received',
        sa.DateTime(timezone=True),
        server_default=func.now()
    )
    date_exported = sa.Column('date_exported', sa.DateTime(timezone=True))
    bluebeam_project_id = sa.Column('bluebeam_project_id', sa.String(11))
    error_message = sa.Column('error_message', sa.String(255))
    export_status_guid = sa.Column(
        'export_guid',
        UUID(as_uuid=True),
        sa.ForeignKey('export_status.guid')
    )
    export_status = relationship('ExportStatusModel', foreign_keys=[export_status_guid])

    @validates('error_message')
    def validate_code(self, key, value):
        """enforces maxlength by truncating the value"""
        max_len = getattr(self.__class__, key).prop.columns[0].type.length
        if value and len(value) > max_len:
            return value[:max_len]
        return value

def create_submission(db_session, json_data):
    """helper function for creating a submission"""
    validate(json_data)
    submission = SubmissionModel(data=json_data)
    db_session.add(submission)
    db_session.commit()
    return submission

def validate(json_params):
    """enforce validation rules"""
    #pylint: disable=unused-argument

    # either project_name or project_id is required
    # project_name required for new bluebeam projects
    # project_id required for resubmissions
    if 'project_name' not in json_params and 'project_id' not in json_params:
        raise Exception("Either project_name or project_id is required")

    # when uploading files to bluebeam, need url and orginal_name
    if 'files' in json_params and len(json_params['files']) > 0:
        for f in json_params['files']: #pylint: disable=invalid-name
            if not 'url' in f or not is_url(f['url']):
                raise Exception("invalid file url")
            if not 'originalName' in f:
                raise Exception("missing originalName in file json")

    # _id is required for logging
    if 'logger' in json_params:
        if '_id' not in json_params:
            raise Exception("_id is required for logging")
        if 'google_sheets' in json_params['logger']:
            missing_msg = "Missing {0} setting in google sheets logger"

            for param in REQUIRED_LOGGER_PARAMS:
                if param not in json_params['logger']['google_sheets']:
                    raise Exception(missing_msg.format(param))

    return json_params

def is_url(url):
    """checks that a string is a valid url"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception: # pylint: disable=broad-except
        return False

class ExportStatusModel(BASE):
    # pylint: disable=too-few-public-methods
    """Map ExportStatus object to db"""
    __tablename__ = "export_status"
    guid = sa.Column('guid', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bluebeam_username = sa.Column('bluebeam_username', sa.String(255))
    date_started = sa.Column('date_started', sa.DateTime, default=datetime.datetime.utcnow)
    date_finished = sa.Column('date_finished', sa.DateTime)
    result = sa.Column('result', sa.JSON)

def create_export(db_session, bluebeam_username):
    """helper function to create a bluebeam export"""
    guid = uuid.uuid4()
    export = ExportStatusModel(guid=guid, bluebeam_username=bluebeam_username)
    db_session.add(export)
    db_session.commit()
    return export

class UserModel(BASE):
    # pylint: disable=too-few-public-methods
    """Map User object to db"""
    __tablename__ = "user"
    id = sa.Column('id', sa.Integer, primary_key=True)
    email = sa.Column('email', sa.String(256))
