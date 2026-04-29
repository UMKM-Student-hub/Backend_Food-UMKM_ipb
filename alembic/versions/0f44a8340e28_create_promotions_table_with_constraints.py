"""create_promotions_table_with_constraints

Revision ID: 0f44a8340e28
Revises: 781a084657e9
Create Date: 2026-04-23 16:05:19.915752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0f44a8340e28'
down_revision: Union[str, Sequence[str], None] = '781a084657e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Buat tipe ENUM di database
    discounttype_enum = postgresql.ENUM('PERCENTAGE', 'NOMINAL', name='discounttype')
    discounttype_enum.create(op.get_bind())

    # 2. Reset paksa data lama (jika ada) agar tidak error saat konversi
    op.execute("UPDATE promotions SET discount_type = 'PERCENTAGE'")

    # 3. Ubah tipe kolomnya
    op.alter_column('promotions', 'discount_type',
               existing_type=sa.VARCHAR(length=15),
               type_=sa.Enum('PERCENTAGE', 'NOMINAL', name='discounttype'),
               postgresql_using="discount_type::discounttype", # <-- Sangat penting
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # (Biarkan kode op.alter_column dll di atasnya tetap utuh)
    
    op.alter_column('promotions', 'discount_type',
               existing_type=sa.Enum('PERCENTAGE', 'NOMINAL', name='discounttype'),
               type_=sa.VARCHAR(length=15),
               existing_nullable=False)

    # Tambahkan penghapusan ENUM di akhir downgrade
    discounttype_enum = postgresql.ENUM('PERCENTAGE', 'NOMINAL', name='discounttype')
    discounttype_enum.drop(op.get_bind())
    # ### end Alembic commands ###
