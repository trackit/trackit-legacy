"""compare providers

Revision ID: 6261d01a8a89
Revises: b5c4bf4603be
Create Date: 2016-05-25 08:33:09.061411

"""

# revision identifiers, used by Alembic.
revision = '6261d01a8a89'
down_revision = 'b5c4bf4603be'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.create_table('providers_comparison_aws',
        sa.Column('id',          sa.Integer,       nullable=False),
        sa.Column('id_aws_key',     sa.Integer,       nullable=False),
        sa.Column('value', sa.BLOB(length=16000000), nullable=False),
        sa.Column('date',   sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_aws_key'], ['aws_key.id']),
    )


def downgrade():
    op.drop_table('providers_comparison_aws')
