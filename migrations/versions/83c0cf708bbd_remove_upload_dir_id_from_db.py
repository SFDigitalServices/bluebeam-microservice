# pylint: skip-file
"""remove upload dir id from db

Revision ID: 83c0cf708bbd
Revises: 2c76c101e8eb
Create Date: 2020-05-18 16:34:10.195705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83c0cf708bbd'
down_revision = '2c76c101e8eb'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('submission', 'upload_dir_id')


def downgrade():
    op.add_column('submission',
        sa.Column('upload_dir_id', sa.Integer)
    )
