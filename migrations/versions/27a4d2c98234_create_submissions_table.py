# pylint: skip-file
"""create submissions table

Revision ID: 27a4d2c98234
Revises: 
Create Date: 2020-03-26 16:24:18.968441

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = '27a4d2c98234'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'submission',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('data', sa.Text, nullable=False),
        sa.Column('date_received', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('date_exported', sa.DateTime(timezone=True)),
        sa.Column('bluebeam_project_id', sa.String(11)),
        sa.Column('error_message', sa.String(255))
    )


def downgrade():
    op.drop_table('submission')
