"""aws error status

Revision ID: b6a1dba48f9a
Revises: 6261d01a8a89
Create Date: 2016-05-31 08:44:48.449051

"""

# revision identifiers, used by Alembic.
revision = 'b6a1dba48f9a'
down_revision = '6261d01a8a89'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column('aws_key', sa.Column('error_status', sa.Unicode(length=32), nullable=True))


def downgrade():
    op.drop_column('aws_key', 'error_status')
