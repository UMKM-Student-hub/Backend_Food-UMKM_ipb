"""create_users_table

Revision ID: 43dde2555e78
Revises: 0f44a8340e28
Create Date: 2026-04-29 15:01:18.668290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '43dde2555e78'
down_revision: Union[str, Sequence[str], None] = '0f44a8340e28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Buat tipe ENUM di database secara manual
    userrole_enum = postgresql.ENUM('BUYER', 'SELLER', name='userrole')
    userrole_enum.create(op.get_bind())

    # 2. Ubah tipe kolom dengan casting yang benar
    op.alter_column('users', 'role',
               existing_type=sa.VARCHAR(length=10),
               type_=sa.Enum('BUYER', 'SELLER', name='userrole'),
               postgresql_using="role::userrole", # <-- Kunci utamanya di sini
               existing_nullable=False)
               
    # (Biarkan sisa kode di bawahnya tetap utuh jika ada)


def downgrade():
    # (Biarkan kode op.alter_column dll di atasnya tetap utuh)
    
    op.alter_column('users', 'role',
               existing_type=sa.Enum('BUYER', 'SELLER', name='userrole'),
               type_=sa.VARCHAR(length=10),
               existing_nullable=False)

    # Tambahkan penghapusan ENUM di akhir downgrade
    userrole_enum = postgresql.ENUM('BUYER', 'SELLER', name='userrole')
    userrole_enum.drop(op.get_bind())
