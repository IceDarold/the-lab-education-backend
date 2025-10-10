"""fix_user_id_foreign_keys_to_uuid

Revision ID: 0edfd2b14ac1
Revises: abc123def456
Create Date: 2025-10-08 23:05:25.519896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0edfd2b14ac1'
down_revision: Union[str, Sequence[str], None] = 'abc123def456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_is_uuid(connection: Connection, table: str, column: str) -> bool:
    result = connection.execute(
        text(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = :table AND column_name = :column
            """
        ),
        {"table": table, "column": column}
    ).scalar()
    return result == 'uuid'


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # Tables may already contain UUID columns if recreated in previous migration.
    if _column_is_uuid(bind, 'enrollments', 'user_id'):
        return

    op.drop_constraint('enrollments_user_id_fkey', 'enrollments', type_='foreignkey')
    op.drop_constraint('user_lesson_progress_user_id_fkey', 'user_lesson_progress', type_='foreignkey')
    op.drop_constraint('user_activity_logs_user_id_fkey', 'user_activity_logs', type_='foreignkey')

    uuid_type = postgresql.UUID(as_uuid=True)
    op.alter_column('enrollments', 'user_id', type_=uuid_type)
    op.alter_column('user_lesson_progress', 'user_id', type_=uuid_type)
    op.alter_column('user_activity_logs', 'user_id', type_=uuid_type)

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
