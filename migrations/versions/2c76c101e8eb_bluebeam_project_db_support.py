# pylint: skip-file
"""bluebeam project db support

Revision ID: 2c76c101e8eb
Revises: afc36c789b78
Create Date: 2020-05-08 13:49:56.473672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c76c101e8eb'
down_revision = 'afc36c789b78'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('submission',
        sa.Column('upload_dir_id', sa.Integer)
    )


def downgrade():
    op.drop_column('submission', 'upload_dir_id')
