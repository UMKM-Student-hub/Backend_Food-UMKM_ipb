"""replace_is_open_with_operating_hours

Revision ID: a1b2c3d4e5f6
Revises: 781a084657e9
Create Date: 2026-05-31 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '781a084657e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Pakai IF NOT EXISTS — aman meski kolom sudah terlanjur ada
    op.execute("ALTER TABLE umkm ADD COLUMN IF NOT EXISTS operating_hours TEXT")
    # Pakai IF EXISTS — aman meski is_open sudah terlanjur dihapus
    op.execute("ALTER TABLE umkm DROP COLUMN IF EXISTS is_open")

def downgrade() -> None:
    op.execute(
        "ALTER TABLE umkm ADD COLUMN IF NOT EXISTS is_open BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute("ALTER TABLE umkm DROP COLUMN IF EXISTS operating_hours")