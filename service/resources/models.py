"""Data Models"""

import datetime
import uuid
from urllib.parse import urlparse
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

BASE = declarative_base()

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
    if 'project_name' not in json_params:
        raise Exception("project_name is a required field")

    if 'files' not in json_params or len(json_params['files']) == 0:
        raise Exception("at least one file is required")

    for f in json_params['files']: #pylint: disable=invalid-name
        if not 'url' in f or not is_url(f['url']):
            raise Exception("invalid file url")
        if not 'originalName' in f:
            raise Exception("missing originalName in file json")

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
