"""initial schema

Revision ID: 20241010_0001
Revises: 
Create Date: 2025-10-10 10:35:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20241010_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    def ensure_enum(name: str, values: list[str]) -> postgresql.ENUM:
        enum_type = postgresql.ENUM(*values, name=name, create_type=False)
        enum_type.create(bind, checkfirst=True)
        return enum_type

    user_role_enum = ensure_enum("user_role_enum", ["STUDENT", "ADMIN"])
    user_status_enum = ensure_enum("user_status_enum", ["ACTIVE", "BLOCKED"])
    activity_type_enum = ensure_enum(
        "activity_type_enum",
        ["LOGIN", "LESSON_COMPLETED", "QUIZ_ATTEMPT", "CODE_EXECUTION"],
    )

    uuid_type = postgresql.UUID(as_uuid=True)

    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", user_role_enum, nullable=False, server_default="STUDENT"),
        sa.Column("status", user_status_enum, nullable=False, server_default="ACTIVE"),
        sa.Column("registration_date", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "enrollments",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("course_slug", sa.String(length=100), nullable=False),
        sa.Column("enrollment_date", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_enrollments_course_slug", "enrollments", ["course_slug"], unique=False)

    op.create_table(
        "user_activity_logs",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("activity_type", activity_type_enum, nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_activity_logs_timestamp", "user_activity_logs", ["timestamp"], unique=False)

    op.create_table(
        "user_lesson_progress",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("course_slug", sa.String(length=100), nullable=False),
        sa.Column("lesson_slug", sa.String(length=100), nullable=False),
        sa.Column("completion_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_lesson_progress_course_slug", "user_lesson_progress", ["course_slug"], unique=False)
    op.create_index("ix_user_lesson_progress_lesson_slug", "user_lesson_progress", ["lesson_slug"], unique=False)

    op.create_table(
        "profiles",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, server_default="student"),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("refresh_token_hash", sa.String(), nullable=False),
        sa.Column("device_info", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("refresh_token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_table("profiles")

    op.drop_constraint("user_lesson_progress_user_id_fkey", "user_lesson_progress", type_="foreignkey")
    op.drop_index("ix_user_lesson_progress_lesson_slug", table_name="user_lesson_progress")
    op.drop_index("ix_user_lesson_progress_course_slug", table_name="user_lesson_progress")
    op.drop_table("user_lesson_progress")

    op.drop_constraint("user_activity_logs_user_id_fkey", "user_activity_logs", type_="foreignkey")
    op.drop_index("ix_user_activity_logs_timestamp", table_name="user_activity_logs")
    op.drop_table("user_activity_logs")

    op.drop_constraint("enrollments_user_id_fkey", "enrollments", type_="foreignkey")
    op.drop_index("ix_enrollments_course_slug", table_name="enrollments")
    op.drop_table("enrollments")

    op.drop_constraint("users_role_fkey", "users", type_="foreignkey", existing=False)
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    sa.Enum(name="activity_type_enum").drop(bind, checkfirst=True)
    sa.Enum(name="user_status_enum").drop(bind, checkfirst=True)
    sa.Enum(name="user_role_enum").drop(bind, checkfirst=True)
