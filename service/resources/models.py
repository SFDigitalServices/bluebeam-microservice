"""Data Models"""

import json
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
from sqlalchemy.sql import func

BASE = declarative_base()

class SubmissionModel(BASE):
    # pylint: disable=too-few-public-methods
    """Map Submission object to db"""

    __tablename__ = 'submission'
    id = sa.Column('id', sa.Integer, primary_key=True)
    data = sa.Column('data', sa.Text, nullable=False)
    date_received = sa.Column(
        'date_received',
        sa.DateTime(timezone=True),
        server_default=func.now()
    )
    date_exported = sa.Column('date_exported', sa.DateTime(timezone=True))
    bluebeam_project_id = sa.Column('bluebeam_project_id', sa.String(11))
    error_message = sa.Column('error_message', sa.String(255))

def create_submission(db_session, json_data):
    '''helper function for creating a submission'''
    submission = SubmissionModel(data=json.dumps(json_data))
    db_session.add(submission)
    db_session.commit()
    return submission
