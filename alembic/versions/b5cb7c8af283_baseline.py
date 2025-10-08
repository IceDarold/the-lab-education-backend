"""baseline

Revision ID: b5cb7c8af283
Revises: ebf0b3dace54
Create Date: 2025-10-08 21:59:03.568085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5cb7c8af283'
down_revision: Union[str, Sequence[str], None] = 'ebf0b3dace54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
