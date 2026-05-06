import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select

# 1. Setup Logging agar proses terlihat jelas di terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Import Engine & Security
from app.core.database import engine
from app.core.security import get_password_hash

# 3. Import Enum Sesuai Dokumen Sistem
from app.domain.user import UserRole           #[cite: 51]
from app.domain.menu_item import ProductCategory #[cite: 46]

# 4. Import ORM Models 
# Sesuaikan import ini dengan file tempat kamu mendefinisikan class ORM-nya.
# Berdasarkan dokumen arsitektur, biasanya disatukan di app.orm_models atau dipisah per file:
from app.orm_models.user import UserORM
from app.orm_models.umkm import UMKMORM
from app.orm_models.menu_item import MenuItemORM

# 5. Setup Async Session Maker
SessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def seed_data():
    """Fungsi idempoten untuk menanamkan data dummy secara asinkron."""
    logger.info("Mulai proses seeding data...")
    
    async with SessionLocal() as session:
        try:
            # ==========================================
            # A. IDEMPOTENCY CHECK
            # ==========================================
            stmt = select(UserORM).where(UserORM.email == "seller_dummy@ipb.ac.id")
            result = await session.execute(stmt)
            existing_seller = result.scalars().first()
            
            if existing_seller:
                logger.info("✅ Data dummy sudah ada di database. Seeding dilewati.")
                return

            # ==========================================
            # B. SEEDING USERS (SELLER & BUYER)
            # ==========================================
            logger.info("Menanamkan data User (Seller & Buyer)...")
            
            seller = UserORM(
                name="Ibu Kantin Dummy",
                email="seller_dummy@ipb.ac.id",
                password_hash=get_password_hash("Pass123!"),
                phone="081111111111",
                role=UserRole.SELLER # Menggunakan Enum asli[cite: 51]
            )
            session.add(seller)
            
            buyer = UserORM(
                name="Mahasiswa Dummy",
                email="buyer_dummy@ipb.ac.id",
                password_hash=get_password_hash("Pass123!"),
                phone="082222222222",
                role=UserRole.BUYER # Menggunakan Enum asli[cite: 51]
            )
            session.add(buyer)
            
            # Commit bertahap agar kita mendapatkan ID untuk relasi selanjutnya
            await session.commit()
            await session.refresh(seller)
            await session.refresh(buyer)

            # ==========================================
            # C. SEEDING UMKM
            # ==========================================
            logger.info("Menanamkan data UMKM...")
            umkm = UMKMORM(
                owner_id=seller.id, # Berelasi dengan seller.id[cite: 50]
                name="Kantin Fasilkom Dummy",
                description="Menjual makanan bergizi untuk mahasiswa",
                location="Gedung FMIPA IPB",
                is_open=True # Toko dalam keadaan buka[cite: 50]
            )
            session.add(umkm)
            await session.commit()
            await session.refresh(umkm)

            # ==========================================
            # D. SEEDING PRODUCTS (MENU ITEMS)
            # ==========================================
            logger.info("Menanamkan data Produk/Menu...")
            products = [
                MenuItemORM(
                    umkm_id=umkm.id,
                    name="Ayam Geprek Spesial",
                    description="Ayam geprek level 5 dengan nasi hangat",
                    price=15000,
                    stock=50,
                    category=ProductCategory.MAKANAN,
                    is_active=True
                ),
                MenuItemORM(
                    umkm_id=umkm.id,
                    name="Es Teh Manis",
                    description="Es teh manis segar",
                    price=5000,
                    stock=100,
                    category=ProductCategory.MINUMAN,
                    is_active=True
                )
            ]
            session.add_all(products)
            await session.commit()

            logger.info("🎉 Seeding data berhasil diselesaikan dengan aman!")

        except Exception as e:
            logger.error(f"❌ Terjadi kesalahan saat seeding: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_data())