"""google billing records

Revision ID: b5c4bf4603be
Revises: e541a3e6fa99
Create Date: 2016-05-03 15:53:26.306026

"""

# revision identifiers, used by Alembic.
revision = 'b5c4bf4603be'
down_revision = 'e541a3e6fa99'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('google_cloud_identity',
        sa.Column('id',          sa.Integer,       nullable=False),
        sa.Column('id_user',     sa.Integer,       nullable=False),
        sa.Column('email',       sa.String(255),   nullable=False),
        sa.Column('credentials', sa.String(4095),  nullable=False),
        sa.Column('last_validated', sa.DateTime(), nullable=True),
        sa.Column('last_errored',   sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_user'], ['user.id']),
    )

    op.create_table('google_cloud_identity_registration_token',
        sa.Column('id',      sa.String(24), nullable=False),
        sa.Column('id_user', sa.Integer,    nullable=False),
        sa.Column('expires', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_user'], ['user.id']),
    )

    op.create_table('google_cloud_project',
        sa.Column('id',             sa.Integer,    nullable=False),
        sa.Column('id_identity',    sa.Integer,    nullable=False),
        sa.Column('code',           sa.String(64), nullable=False),
        sa.Column('number',         sa.BigInteger, nullable=False),
        sa.Column('name',           sa.String(64), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_identity'], ['google_cloud_identity.id']),
    )

    op.create_table('google_cloud_billing_bucket',
        sa.Column('id',         sa.Integer,     nullable=False),
        sa.Column('id_project', sa.Integer,     nullable=False),
        sa.Column('name',       sa.String(224), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_project'], ['google_cloud_project.id']),
        sa.UniqueConstraint('id_project', 'name'),
    )

    op.create_table('google_cloud_billing_file',
        sa.Column('id',         sa.Integer,      nullable=False),
        sa.Column('id_bucket',  sa.Integer,      nullable=False),
        sa.Column('bucket',     sa.String(224),  nullable=False),
        sa.Column('name',       sa.String(224),  nullable=False),
        sa.Column('md5',        sa.Binary(16),   nullable=False),
        sa.Column('media_link', sa.String(1023), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_bucket'], ['google_cloud_billing_bucket.id']),
        sa.UniqueConstraint(
            'id_bucket',
            'name',
        ),
    )

    op.create_table('google_cloud_billing_record',
        sa.Column('id',         sa.Integer,        nullable=False),
        sa.Column('id_file',    sa.Integer,        nullable=False),
        sa.Column('start',      sa.DateTime(),     nullable=False),
        sa.Column('end',        sa.DateTime(),     nullable=False),
        sa.Column('item',       sa.String(255),    nullable=False),
        sa.Column('cost',       sa.Numeric(15, 6), nullable=False),
        sa.Column('currency',   sa.String(3),      nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_file'], ['google_cloud_billing_file.id']),
        sa.UniqueConstraint(
            'id_file',
            'start',
            'end',
            'item',
        )
    )

    op.create_table('google_cloud_billing_measurement',
        sa.Column('id',          sa.Integer,      nullable=False),
        sa.Column('id_record',   sa.Integer,      nullable=False),
        sa.Column('measurement', sa.String(255),  nullable=False),
        sa.Column('sum',         sa.BigInteger(), nullable=False),
        sa.Column('unit',        sa.String(63),   nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_record'], ['google_cloud_billing_record.id']),
    )

def downgrade():
    op.drop_table('google_cloud_billing_measurement')
    op.drop_table('google_cloud_billing_record')
    op.drop_table('google_cloud_billing_file')
    op.drop_table('google_cloud_billing_bucket')
    op.drop_table('google_cloud_project')
    op.drop_table('google_cloud_identity_registration_token')
    op.drop_table('google_cloud_identity')
