"""add composite index on meetings (owner_id, start_time)

Revision ID: b9c87d6e5f4a
Revises: 6c316e3f90f3
Create Date: 2026-09-17 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9c87d6e5f4a'
down_revision = '6c316e3f90f3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('meetings', schema=None) as batch_op:
        batch_op.create_index('idx_meetings_owner_start', ['owner_id', 'start_time'], unique=False)


def downgrade():
    with op.batch_alter_table('meetings', schema=None) as batch_op:
        batch_op.drop_index('idx_meetings_owner_start')
