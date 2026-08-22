"""add users.timezone

Revision ID: 7c9d2e4f8a1b
Revises: a8b94cf33df1
Create Date: 2026-08-22 22:10:45.318210

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c9d2e4f8a1b'
down_revision = 'a8b94cf33df1'
branch_labels = None
depends_on = None


def upgrade():
    # IANA timezone name used to interpret natural-language scheduling
    # (e.g. "Asia/Kolkata"); existing users default to UTC.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('timezone', sa.String(length=64), nullable=False, server_default='UTC')
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('timezone')
