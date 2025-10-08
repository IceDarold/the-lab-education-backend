"""change columns to snake_case

Revision ID: abc123def456
Revises: 51ddc645ddc5
Create Date: 2025-10-08 22:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, Sequence[str], None] = '51ddc645ddc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename columns to snake_case
    op.alter_column('users', 'fullName', new_column_name='full_name', existing_type=sa.String(length=100), existing_nullable=False)
    op.alter_column('users', 'registrationDate', new_column_name='registration_date', existing_type=sa.DateTime(), existing_nullable=True, existing_server_default=sa.text('now()'))


def downgrade() -> None:
    """Downgrade schema."""
    # Rename columns back to camelCase
    op.alter_column('users', 'full_name', new_column_name='fullName', existing_type=sa.String(length=100), existing_nullable=False)
    op.alter_column('users', 'registration_date', new_column_name='registrationDate', existing_type=sa.DateTime(), existing_nullable=True, existing_server_default=sa.text('now()'))