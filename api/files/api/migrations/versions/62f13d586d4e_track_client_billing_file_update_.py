"""Track client billing file update schedule.

Revision ID: 62f13d586d4e
Revises: 56c64544a182
Create Date: 2017-05-29 05:00:30.117014

"""

# revision identifiers, used by Alembic.
revision = '62f13d586d4e'
down_revision = '56c64544a182'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('aws_key', sa.Column(
        'next_s3_bill_import',
        sa.DateTime(),
        nullable=True
    ))


def downgrade():
    op.drop_column('aws_key', 'next_s3_bill_import')
