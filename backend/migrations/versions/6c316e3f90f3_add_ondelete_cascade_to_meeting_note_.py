"""add ondelete cascade to meeting/note/log foreign keys

Revision ID: 6c316e3f90f3
Revises: 7c9d2e4f8a1b
Create Date: 2026-08-23 12:45:24.523811

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c316e3f90f3'
down_revision = '7c9d2e4f8a1b'
branch_labels = None
depends_on = None

# The existing foreign keys are unnamed, so they cannot be dropped by name.
# SQLite also has no ALTER TABLE support for foreign keys at all. Instead,
# batch mode recreates each table wholesale from the explicit definitions
# below (``copy_from`` + ``recreate="always"``, since an empty batch with
# ``recreate="auto"`` is a no-op), replacing the old unnamed FKs with named
# ON DELETE CASCADE ones.


def _base_columns():
    return [
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    ]


def _meetings(ondelete):
    return sa.Table(
        'meetings',
        sa.MetaData(),
        *_base_columns(),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ['owner_id'], ['users.id'], name='fk_meetings_owner_id_users',
            ondelete=ondelete,
        ),
        sa.Index('ix_meetings_owner_id', 'owner_id'),
        sa.Index('ix_meetings_start_time', 'start_time'),
    )


def _notes(ondelete):
    return sa.Table(
        'notes',
        sa.MetaData(),
        *_base_columns(),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], name='fk_notes_user_id_users',
            ondelete=ondelete,
        ),
    )


def _logs(ondelete):
    return sa.Table(
        'logs',
        sa.MetaData(),
        *_base_columns(),
        sa.Column('level', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=120), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], name='fk_logs_user_id_users',
            ondelete=ondelete,
        ),
    )


def upgrade():
    # Recreate each child table with ON DELETE CASCADE foreign keys,
    # preserving all rows.
    with op.batch_alter_table('meetings', copy_from=_meetings('CASCADE'), recreate="always") as batch_op:
        pass

    with op.batch_alter_table('notes', copy_from=_notes('CASCADE'), recreate="always") as batch_op:
        pass

    with op.batch_alter_table('logs', copy_from=_logs('CASCADE'), recreate="always") as batch_op:
        pass


def downgrade():
    with op.batch_alter_table('meetings', copy_from=_meetings('NO ACTION'), recreate="always") as batch_op:
        pass

    with op.batch_alter_table('notes', copy_from=_notes('NO ACTION'), recreate="always") as batch_op:
        pass

    with op.batch_alter_table('logs', copy_from=_logs('NO ACTION'), recreate="always") as batch_op:
        pass
