"""Add the Prospect table.

Revision ID: f83b7adaf523
Revises: b6533e0a4e58
Create Date: 2017-03-20 02:19:21.162055

"""

# revision identifiers, used by Alembic.
revision = 'f83b7adaf523'
down_revision = 'b6533e0a4e58'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('prospect',
        sa.Column('id',             sa.Integer,     nullable=False),
        sa.Column('name',           sa.String(255), nullable=False),
        sa.Column('email',          sa.String(255), nullable=False),
        sa.Column('phone_number',   sa.String(255), nullable=True),
        sa.Column('company_name',   sa.String(255), nullable=True),
        sa.Column('address',        sa.String(255), nullable=True),
        sa.Column('which_cloud',    sa.String(255), nullable=True),
        sa.Column('employees',      sa.Integer,     nullable=True),
        sa.Column('annual_revenue', sa.Integer,     nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('cloud_concern',
        sa.Column('id',          sa.Integer,     nullable=False),
        sa.Column('id_prospect', sa.Integer,     nullable=False),
        sa.Column('concern',     sa.String(255), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_prospect'], ['prospect.id']),
    )

def downgrade():
    op.drop_table('cloud_concern')
    op.drop_table('prospect')
