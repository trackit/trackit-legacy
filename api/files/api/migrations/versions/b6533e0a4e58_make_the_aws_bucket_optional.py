"""Make the AWS bucket optional.

Revision ID: b6533e0a4e58
Revises: eca04db5c363
Create Date: 2017-02-06 02:16:03.926797

"""

# revision identifiers, used by Alembic.
revision = 'b6533e0a4e58'
down_revision = 'eca04db5c363'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('aws_key',
        column_name='billing_bucket_name',
        existing_type=sa.String(length=63),
        nullable=True,
    )


def downgrade():
    op.alter_column('aws_key',
        column_name='billing_bucket_name',
        existing_type=sa.String(length=63),
        nullable=False,
    )
