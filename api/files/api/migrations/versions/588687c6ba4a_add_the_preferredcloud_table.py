"""Add the PreferredCloud table.

Revision ID: 588687c6ba4a
Revises: f83b7adaf523
Create Date: 2017-03-20 16:39:04.282582

"""

# revision identifiers, used by Alembic.
revision = '588687c6ba4a'
down_revision = 'f83b7adaf523'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('prospect', 'employees',
        existing_type=sa.Integer,
        type_=sa.String(255),
    )
    op.drop_column('prospect', 'which_cloud')
    op.create_table('which_cloud',
        sa.Column('id',          sa.Integer,     nullable=False),
        sa.Column('id_prospect', sa.Integer,     nullable=False),
        sa.Column('cloud',       sa.String(255), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_prospect'], ['prospect.id']),
    )


def downgrade():
    op.drop_table('which_cloud')
    op.add_column('prospect',
        sa.Column('which_cloud',    sa.String(255), nullable=True),
    )
    op.alter_column('prospect', 'employees',
        type_=sa.Integer,
        existing_type=sa.String(255),
    )
