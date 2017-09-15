"""google sign in

Revision ID: e541a3e6fa99
Revises: 93d33c6f7725
Create Date: 2016-04-26 09:12:38.833343

"""

# revision identifiers, used by Alembic.
revision = 'e541a3e6fa99'
down_revision = '93d33c6f7725'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('auth_google', sa.String(120), nullable=True))


def downgrade():
    op.drop_column('user', 'auth_google')
