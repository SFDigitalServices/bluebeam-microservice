# pylint: skip-file
"""create token table

Revision ID: 91c3ead7bc5f
Revises: 235b9ca09634
Create Date: 2020-09-21 13:30:55.709009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '91c3ead7bc5f'
down_revision = '235b9ca09634'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'token',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('value', sa.LargeBinary)
    )


def downgrade():
    op.drop_table('token')
