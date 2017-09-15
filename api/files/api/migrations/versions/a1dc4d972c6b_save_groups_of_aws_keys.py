"""Save groups of AWS keys.

Revision ID: a1dc4d972c6b
Revises: 588687c6ba4a
Create Date: 2017-04-02 15:56:33.984774

"""

# revision identifiers, used by Alembic.
revision = 'a1dc4d972c6b'
down_revision = '588687c6ba4a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('multikey_group',
        sa.Column('id', sa.String(length=40), nullable=False),
        sa.Column('expires', sa.DateTime(), nullable=False),
        sa.Column('updates', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('multikey_key',
        sa.Column('id',                  sa.Integer(),         nullable=False),
        sa.Column('id_multikey_group',   sa.String(length=40), nullable=False),
        sa.Column('key',                 sa.String(length=20), nullable=False),
        sa.Column('billing_bucket_name', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_multikey_group'], ['multikey_group.id']),
    )

def downgrade():
    op.drop_table('multikey_key')
    op.drop_table('multikey_group')
