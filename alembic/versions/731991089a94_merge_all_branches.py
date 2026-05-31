"""merge_all_branches

Revision ID: 731991089a94
Revises: 461e8a43d156, a1b2c3d4e5f6
Create Date: 2026-05-31 17:16:57.126608

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '731991089a94'
down_revision: Union[str, Sequence[str], None] = ('461e8a43d156', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
