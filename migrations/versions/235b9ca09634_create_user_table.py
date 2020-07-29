# pylint: skip-file
"""create user table

Revision ID: 235b9ca09634
Revises: 83c0cf708bbd
Create Date: 2020-07-27 16:07:19.342708

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '235b9ca09634'
down_revision = '83c0cf708bbd'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(256), nullable=False)
    )


def downgrade():
    op.drop_table('user')
