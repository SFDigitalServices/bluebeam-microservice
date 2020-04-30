# pylint: skip-file
"""create export status table

Revision ID: afc36c789b78
Revises: 27a4d2c98234
Create Date: 2020-03-31 16:24:39.269836

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = 'afc36c789b78'
down_revision = '27a4d2c98234'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'export_status',
        sa.Column('guid', UUID(), primary_key=True, nullable=False),
        sa.Column('bluebeam_username', sa.String(255)),
        sa.Column('date_started', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('date_finished', sa.DateTime(timezone=True)),
        sa.Column('result', sa.JSON)
    )
    op.add_column('submission',
        sa.Column('export_guid', UUID())
    )
    op.create_foreign_key(
        'fk_submission_export_id',
        'submission',
        'export_status',
        ['export_guid'],
        ['guid']
    )

def downgrade():
    op.drop_column('submission', 'export_id')
    op.drop_table('export_status')
