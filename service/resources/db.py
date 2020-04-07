"""db module"""
import os
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

def create_session():
    """creates database session"""
    db_engine = sa.create_engine(os.environ.get('DATABASE_URL'), echo=True)
    return sessionmaker(bind=db_engine)
