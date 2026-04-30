"""
conftest.py — UniBites E2E Test Configuration
=============================================
Menyediakan fixtures bersama untuk seluruh test suite:
  - Test database (SQLite async — tidak butuh PostgreSQL saat CI/CD)
  - AsyncClient yang terhubung ke test app
  - Helper fixtures: registered buyer, registered seller, authenticated headers
  - Fixtures domain: umkm, menu item, order, promo, review yang siap pakai
"""

import asyncio
from datetime import date, timedelta
from typing import AsyncGenerator, Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session")
async def setup_database():
    async with test_engine.begin() as conn:
        import app.orm_models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_database):
    yield
    async with TestSessionLocal() as session:
        from sqlalchemy import text
        for table in [
            "reviews", "order_items", "orders",
            "promotions", "menu_items", "umkm", "users",
        ]:
            await session.execute(text(f"DELETE FROM {table}"))
        await session.commit()

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ════════════════════════════════════════════════════════════════════════════
#  USER FIXTURES
# ════════════════════════════════════════════════════════════════════════════

BUYER_DATA = {
    "name": "Aldi Mahasiswa", "email": "aldi@mahasiswa.ipb.ac.id",
    "password": "Password123!", "phone": "081234567890", "role": "BUYER",
}

SELLER_DATA = {
    "name": "Bu Sari UMKM", "email": "sari@umkm.ipb.ac.id",
    "password": "Password123!", "phone": "082345678901", "role": "SELLER",
}

SELLER_2_DATA = {
    "name": "Pak Budi UMKM", "email": "budi@umkm.ipb.ac.id",
    "password": "Password123!", "phone": "083456789012", "role": "SELLER",
}

@pytest_asyncio.fixture
async def registered_buyer(client: AsyncClient) -> Dict:
    resp = await client.post("/api/v1/auth/register", json=BUYER_DATA)
    assert resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": BUYER_DATA["email"], "password": BUYER_DATA["password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    return {
        "user": resp.json(), "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "email": BUYER_DATA["email"], "password": BUYER_DATA["password"],
    }

@pytest_asyncio.fixture
async def registered_seller(client: AsyncClient) -> Dict:
    resp = await client.post("/api/v1/auth/register", json=SELLER_DATA)
    assert resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": SELLER_DATA["email"], "password": SELLER_DATA["password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    return {
        "user": resp.json(), "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "email": SELLER_DATA["email"], "password": SELLER_DATA["password"],
    }

@pytest_asyncio.fixture
async def registered_seller_2(client: AsyncClient) -> Dict:
    resp = await client.post("/api/v1/auth/register", json=SELLER_2_DATA)
    assert resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": SELLER_2_DATA["email"], "password": SELLER_2_DATA["password"]},
    )
    token = login_resp.json()["access_token"]
    return {
        "user": resp.json(), "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }

# ════════════════════════════════════════════════════════════════════════════
#  DOMAIN FIXTURES (DENGAN PERBAIKAN TRAILING SLASH)
# ════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def seller_with_umkm(client: AsyncClient, registered_seller: Dict) -> Dict:
    headers = registered_seller["headers"]
    # PERBAIKAN: Menambahkan / pada /api/v1/umkm/
    resp = await client.post(
        "/api/v1/umkm/",
        json={
            "name": "Warung Sari Rasa",
            "description": "Masakan rumahan halal dan lezat",
            "location": "Kantin Gedung C, IPB Dramaga",
        },
        headers=headers,
    )
    assert resp.status_code == 201, f"Register UMKM gagal: {resp.text}"
    return {**registered_seller, "umkm": resp.json()}

@pytest_asyncio.fixture
async def open_umkm(client: AsyncClient, seller_with_umkm: Dict) -> Dict:
    headers = seller_with_umkm["headers"]
    resp = await client.patch("/api/v1/umkm/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_open"] is True
    return {**seller_with_umkm, "umkm": resp.json()}

@pytest_asyncio.fixture
async def menu_item(client: AsyncClient, seller_with_umkm: Dict) -> Dict:
    headers = seller_with_umkm["headers"]
    # PERBAIKAN: Menambahkan / pada /api/v1/products/
    resp = await client.post(
        "/api/v1/products/",
        json={
            "name": "Nasi Goreng Spesial",
            "description": "Nasi goreng dengan telur dan ayam",
            "price": 15000,
            "stock": 10,
            "category": "MAKANAN",
        },
        headers=headers,
    )
    assert resp.status_code == 201, f"Tambah produk gagal: {resp.text}"
    return resp.json()

@pytest_asyncio.fixture
async def menu_item_with_open_store(
    client: AsyncClient, open_umkm: Dict, menu_item: Dict
) -> Dict:
    return {**open_umkm, "menu_item": menu_item}

@pytest_asyncio.fixture
async def placed_order(
    client: AsyncClient, registered_buyer: Dict, menu_item_with_open_store: Dict,
) -> Dict:
    buyer_headers = registered_buyer["headers"]
    item = menu_item_with_open_store["menu_item"]
    tomorrow = (date.today() + timedelta(days=1)).isoformat() + "T10:00:00"

    # PERBAIKAN: Menambahkan / pada /api/v1/orders/
    resp = await client.post(
        "/api/v1/orders/",
        json={
            "umkm_id": menu_item_with_open_store["umkm"]["id"],
            "items": [{"menu_item_id": item["id"], "quantity": 2}],
            "notes": "Tanpa sambal",
            "pickup_schedule": tomorrow,
        },
        headers=buyer_headers,
    )
    assert resp.status_code == 201, f"Buat order gagal: {resp.text}"
    return {
        "order": resp.json(),
        "buyer": registered_buyer,
        "seller": menu_item_with_open_store,
        "menu_item": item,
    }

@pytest_asyncio.fixture
async def confirmed_order(client: AsyncClient, placed_order: Dict) -> Dict:
    seller_headers = placed_order["seller"]["headers"]
    order_id = placed_order["order"]["id"]

    resp = await client.patch(
        f"/api/v1/orders/{order_id}/confirm",
        headers=seller_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED"
    return {**placed_order, "order": resp.json()}

@pytest_asyncio.fixture
async def ready_order(client: AsyncClient, confirmed_order: Dict) -> Dict:
    seller_headers = confirmed_order["seller"]["headers"]
    order_id = confirmed_order["order"]["id"]

    resp = await client.patch(
        f"/api/v1/orders/{order_id}/ready",
        headers=seller_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "READY"
    return {**confirmed_order, "order": resp.json()}

@pytest_asyncio.fixture
async def done_order(client: AsyncClient, ready_order: Dict) -> Dict:
    buyer_headers = ready_order["buyer"]["headers"]
    order_id = ready_order["order"]["id"]

    resp = await client.patch(
        f"/api/v1/orders/{order_id}/done",
        headers=buyer_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DONE"
    return {**ready_order, "order": resp.json()}

@pytest_asyncio.fixture
async def active_promo(
    client: AsyncClient, seller_with_umkm: Dict, menu_item: Dict
) -> Dict:
    headers = seller_with_umkm["headers"]
    today = date.today()
    # PERBAIKAN: Menambahkan / pada /api/v1/promos/
    resp = await client.post(
        "/api/v1/promos/",
        json={
            "menu_item_id": menu_item["id"],
            "name": "Promo Makan Siang",
            "discount_type": "PERCENTAGE",
            "discount_value": 20,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=7)).isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 201, f"Buat promo gagal: {resp.text}"
    return resp.json()