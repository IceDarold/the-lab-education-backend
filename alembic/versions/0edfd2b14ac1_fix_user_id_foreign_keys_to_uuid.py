"""fix_user_id_foreign_keys_to_uuid

Revision ID: 0edfd2b14ac1
Revises: abc123def456
Create Date: 2025-10-08 23:05:25.519896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0edfd2b14ac1'
down_revision: Union[str, Sequence[str], None] = 'abc123def456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop foreign key constraints
    op.drop_constraint('enrollments_user_id_fkey', 'enrollments', type_='foreignkey')
    op.drop_constraint('user_lesson_progress_user_id_fkey', 'user_lesson_progress', type_='foreignkey')
    op.drop_constraint('user_activity_logs_user_id_fkey', 'user_activity_logs', type_='foreignkey')

    # Alter user_id columns to UUID
    op.alter_column('enrollments', 'user_id', type_=sa.UUID())
    op.alter_column('user_lesson_progress', 'user_id', type_=sa.UUID())
    op.alter_column('user_activity_logs', 'user_id', type_=sa.UUID())

    # Recreate foreign key constraints
    op.create_foreign_key('enrollments_user_id_fkey', 'enrollments', 'users', ['user_id'], ['id'])
    op.create_foreign_key('user_lesson_progress_user_id_fkey', 'user_lesson_progress', 'users', ['user_id'], ['id'])
    op.create_foreign_key('user_activity_logs_user_id_fkey', 'user_activity_logs', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraints
    op.drop_constraint('enrollments_user_id_fkey', 'enrollments', type_='foreignkey')
    op.drop_constraint('user_lesson_progress_user_id_fkey', 'user_lesson_progress', type_='foreignkey')
    op.drop_constraint('user_activity_logs_user_id_fkey', 'user_activity_logs', type_='foreignkey')

    # Alter user_id columns back to Integer
    op.alter_column('enrollments', 'user_id', type_=sa.Integer())
    op.alter_column('user_lesson_progress', 'user_id', type_=sa.Integer())
    op.alter_column('user_activity_logs', 'user_id', type_=sa.Integer())

    # Recreate foreign key constraints
    op.create_foreign_key('enrollments_user_id_fkey', 'enrollments', 'users', ['user_id'], ['id'])
    op.create_foreign_key('user_lesson_progress_user_id_fkey', 'user_lesson_progress', 'users', ['user_id'], ['id'])
    op.create_foreign_key('user_activity_logs_user_id_fkey', 'user_activity_logs', 'users', ['user_id'], ['id'])
