"""db module"""
import os
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

db_engine = sa.create_engine(os.environ.get('DATABASE_URL'), echo=True) # pylint: disable=invalid-name

def create_session():
    """creates database session"""
    return sessionmaker(bind=db_engine)
