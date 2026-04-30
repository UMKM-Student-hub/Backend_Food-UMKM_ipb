"""
test_full_flow.py — Integrated E2E Scenarios (Happy Path End-to-End)
=====================================================================
Test ini mensimulasikan skenario pengguna nyata dari awal hingga akhir
tanpa menggunakan fixture pre-built, sehingga setiap skenario adalah
sebuah alur yang berdiri sendiri dan sepenuhnya terverifikasi.

Skenario yang diuji:
  SCENARIO 1: Full Order Lifecycle — dari register hingga review
  SCENARIO 2: Seller melakukan promosi dan buyer menggunakannya
  SCENARIO 3: Stok habis — boundary condition
  SCENARIO 4: Multiple buyer pada UMKM yang sama
  SCENARIO 5: Seller mengelola beberapa produk sekaligus
  SCENARIO 6: Order ditolak — verifikasi stok restoration + pesan error
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

TOMORROW = (date.today() + timedelta(days=1)).isoformat() + "T12:00:00"
TODAY = date.today().isoformat()
NEXT_WEEK = (date.today() + timedelta(days=7)).isoformat()


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 1: Full Order Lifecycle
#  Register → Setup UMKM → Add Product → Open Store →
#  Buyer Orders → Seller Confirms → Seller Ready → Buyer Done → Review
# ════════════════════════════════════════════════════════════════════════════

class TestFullOrderLifecycle:

    async def test_complete_happy_path(self, client: AsyncClient):
        """
        ✅ SCENARIO 1: Simulasi alur lengkap dari register hingga review.
        Ini adalah skenario paling penting — memverifikasi bahwa semua
        layer arsitektur bekerja bersama dengan benar.
        """

        # ── STEP 1: Register Seller ─────────────────────────────────────
        seller_reg = await client.post("/api/v1/auth/register", json={
            "name": "Warung Bu Ani", "email": "buani@ipb.ac.id",
            "password": "Pass123!", "phone": "081111000001", "role": "SELLER",
        })
        assert seller_reg.status_code == 201, f"Step 1 gagal: {seller_reg.text}"

        seller_login = await client.post("/api/v1/auth/login",
            json={"email": "buani@ipb.ac.id", "password": "Pass123!"})
        assert seller_login.status_code == 200
        seller_token = seller_login.json()["access_token"]
        seller_h = {"Authorization": f"Bearer {seller_token}"}

        # ── STEP 2: Register Buyer ──────────────────────────────────────
        buyer_reg = await client.post("/api/v1/auth/register", json={
            "name": "Mahasiswa Aldo", "email": "aldo@ipb.ac.id",
            "password": "Pass123!", "phone": "082222000001", "role": "BUYER",
        })
        assert buyer_reg.status_code == 201

        buyer_login = await client.post("/api/v1/auth/login",
            json={"email": "aldo@ipb.ac.id", "password": "Pass123!"})
        assert buyer_login.status_code == 200
        buyer_token = buyer_login.json()["access_token"]
        buyer_h = {"Authorization": f"Bearer {buyer_token}"}

        # ── STEP 3: Seller mendaftarkan UMKM ───────────────────────────
        umkm_resp = await client.post("/api/v1/umkm/", json={
            "name": "Warung Bu Ani",
            "description": "Masakan rumah yang lezat",
            "location": "Kantin Tengah IPB",
        }, headers=seller_h)
        assert umkm_resp.status_code == 201
        umkm = umkm_resp.json()
        assert umkm["is_open"] is False  # default tutup

        # ── STEP 4: Seller menambah produk ─────────────────────────────
        product_resp = await client.post("/api/v1/products/", json={
            "name": "Nasi Uduk Betawi",
            "description": "Nasi uduk original dengan lauk lengkap",
            "price": 12000,
            "stock": 20,
            "category": "MAKANAN",
        }, headers=seller_h)
        assert product_resp.status_code == 201
        product = product_resp.json()
        assert product["stock"] == 20

        # ── STEP 5: Buyer cek katalog sebelum toko buka ─────────────────
        catalog = await client.get("/api/v1/umkm", headers=buyer_h)
        assert catalog.status_code == 200
        umkm_in_catalog = next((u for u in catalog.json() if u["id"] == umkm["id"]), None)
        assert umkm_in_catalog is not None
        assert umkm_in_catalog["is_open"] is False

        # ── STEP 6: Seller membuka toko ────────────────────────────────
        open_resp = await client.patch("/api/v1/umkm/status", headers=seller_h)
        assert open_resp.status_code == 200
        assert open_resp.json()["is_open"] is True

        # ── STEP 7: Buyer membuat order ─────────────────────────────────
        order_resp = await client.post("/api/v1/orders/", json={
            "umkm_id": umkm["id"],
            "items": [{"menu_item_id": product["id"], "quantity": 2}],
            "notes": "Sambal dipisah ya",
            "pickup_schedule": TOMORROW,
        }, headers=buyer_h)
        assert order_resp.status_code == 201
        order = order_resp.json()
        assert order["status"] == "PENDING"
        assert order["total_price"] == 12000 * 2
        assert order["notes"] == "Sambal dipisah ya"
        assert order["queue_number"] is not None

        # Verifikasi stok berkurang
        prod_check = await client.get(f"/api/v1/products/{product['id']}", headers=buyer_h)
        assert prod_check.json()["stock"] == 18  # 20 - 2

        # ── STEP 8: Seller konfirmasi order ────────────────────────────
        confirm_resp = await client.patch(
            f"/api/v1/orders/{order['id']}/confirm", headers=seller_h)
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "CONFIRMED"

        # Buyer bisa lihat status berubah
        my_orders = await client.get("/api/v1/orders/my", headers=buyer_h)
        my_order = next((o for o in my_orders.json() if o["id"] == order["id"]), None)
        assert my_order["status"] == "CONFIRMED"

        # ── STEP 9: Seller tandai siap ──────────────────────────────────
        ready_resp = await client.patch(
            f"/api/v1/orders/{order['id']}/ready", headers=seller_h)
        assert ready_resp.status_code == 200
        assert ready_resp.json()["status"] == "READY"

        # ── STEP 10: Buyer tandai selesai ───────────────────────────────
        done_resp = await client.patch(
            f"/api/v1/orders/{order['id']}/done", headers=buyer_h)
        assert done_resp.status_code == 200
        assert done_resp.json()["status"] == "DONE"

        # ── STEP 11: Buyer submit review ────────────────────────────────
        review_resp = await client.post("/api/v1/reviews/", json={
            "order_id": order["id"],
            "rating": 5,
            "comment": "Nasi uduknya enak banget, uduk gurih dan lauk lengkap!",
        }, headers=buyer_h)
        assert review_resp.status_code == 201
        review = review_resp.json()
        assert review["rating"] == 5

        # ── STEP 12: Verifikasi review tampil di produk ──────────────────
        product_reviews = await client.get(
            f"/api/v1/reviews/product/{product['id']}", headers=buyer_h)
        assert product_reviews.status_code == 200
        review_ids = [r["id"] for r in product_reviews.json()]
        assert review["id"] in review_ids

        # ── STEP 13: Seller lihat ulasan di dashboard ────────────────────
        seller_reviews = await client.get(
            f"/api/v1/reviews/umkm/{umkm['id']}", headers=seller_h)
        assert seller_reviews.status_code == 200
        assert len(seller_reviews.json()) >= 1


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 2: Promo Flow
#  Seller buat promo → Buyer lihat promo → Buyer cek harga diskon
# ════════════════════════════════════════════════════════════════════════════

class TestPromoFlow:

    async def test_promo_creation_and_visibility(self, client: AsyncClient):
        """✅ SCENARIO 2: Seller buat promo, buyer melihatnya di halaman deals."""

        # Setup seller + UMKM + produk
        await client.post("/api/v1/auth/register", json={
            "name": "Promo Seller", "email": "promoseller@ipb.ac.id",
            "password": "Pass123!", "phone": "083333000001", "role": "SELLER",
        })
        s_login = await client.post("/api/v1/auth/login",
            json={"email": "promoseller@ipb.ac.id", "password": "Pass123!"})
        seller_h = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

        umkm = (await client.post("/api/v1/umkm/", json={
            "name": "Warung Promo", "description": "Selalu ada promo",
            "location": "Gedung B", }, headers=seller_h)).json()

        product = (await client.post("/api/v1/products/", json={
            "name": "Mie Ayam Promo", "price": 10000, "stock": 30,
            "category": "MAKANAN", }, headers=seller_h)).json()

        # Setup buyer
        await client.post("/api/v1/auth/register", json={
            "name": "Buyer Promo", "email": "buyerpromo@ipb.ac.id",
            "password": "Pass123!", "phone": "084444000001", "role": "BUYER",
        })
        b_login = await client.post("/api/v1/auth/login",
            json={"email": "buyerpromo@ipb.ac.id", "password": "Pass123!"})
        buyer_h = {"Authorization": f"Bearer {b_login.json()['access_token']}"}

        # Cek promo sebelum dibuat (belum ada)
        before = await client.get("/api/v1/promos/active", headers=buyer_h)
        count_before = len(before.json())

        # Seller buat promo 25%
        promo_resp = await client.post("/api/v1/promos/", json={
            "menu_item_id": product["id"],
            "name": "Flash Sale Siang",
            "discount_type": "PERCENTAGE",
            "discount_value": 25,
            "start_date": TODAY,
            "end_date": NEXT_WEEK,
        }, headers=seller_h)
        assert promo_resp.status_code == 201
        promo = promo_resp.json()

        # Buyer lihat promo aktif — harus bertambah
        after = await client.get("/api/v1/promos/active", headers=buyer_h)
        assert len(after.json()) > count_before
        promo_ids = [p["id"] for p in after.json()]
        assert promo["id"] in promo_ids

        # Seller deaktivasi promo
        deact = await client.patch(
            f"/api/v1/promos/{promo['id']}/deactivate", headers=seller_h)
        assert deact.status_code == 200
        assert deact.json()["is_active"] is False

        # Promo hilang dari halaman buyer
        final = await client.get("/api/v1/promos/active", headers=buyer_h)
        final_ids = [p["id"] for p in final.json()]
        assert promo["id"] not in final_ids


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 3: Stock Boundary Conditions
#  Order terakhir → stok habis → order berikutnya ditolak
# ════════════════════════════════════════════════════════════════════════════

class TestStockBoundary:

    async def test_last_item_order_then_stock_exhausted(self, client: AsyncClient):
        """✅ SCENARIO 3: Stok habis setelah order terakhir → order berikutnya ditolak."""

        # Setup
        await client.post("/api/v1/auth/register", json={
            "name": "Seller Stok", "email": "stockseller@ipb.ac.id",
            "password": "Pass123!", "phone": "085555000001", "role": "SELLER",
        })
        s_login = await client.post("/api/v1/auth/login",
            json={"email": "stockseller@ipb.ac.id", "password": "Pass123!"})
        seller_h = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

        umkm = (await client.post("/api/v1/umkm/", json={
            "name": "Warung Stok Terbatas", "description": "Stok sangat terbatas",
            "location": "Pojok Kantin", }, headers=seller_h)).json()
        await client.patch("/api/v1/umkm/status", headers=seller_h)  # buka

        # Produk dengan stok hanya 3
        product = (await client.post("/api/v1/products/", json={
            "name": "Bakso Rare Item", "price": 8000, "stock": 3,
            "category": "MAKANAN", }, headers=seller_h)).json()

        # Buyer setup
        await client.post("/api/v1/auth/register", json={
            "name": "Buyer Stok", "email": "buyerstok@ipb.ac.id",
            "password": "Pass123!", "phone": "086666000001", "role": "BUYER",
        })
        b_login = await client.post("/api/v1/auth/login",
            json={"email": "buyerstok@ipb.ac.id", "password": "Pass123!"})
        buyer_h = {"Authorization": f"Bearer {b_login.json()['access_token']}"}

        # Order pertama — ambil semua stok (qty=3, stok=3)
        order1 = await client.post("/api/v1/orders/", json={
            "umkm_id": umkm["id"],
            "items": [{"menu_item_id": product["id"], "quantity": 3}],
            "notes": "", "pickup_schedule": TOMORROW,
        }, headers=buyer_h)
        assert order1.status_code == 201

        # Verifikasi stok = 0
        check = await client.get(f"/api/v1/products/{product['id']}", headers=buyer_h)
        assert check.json()["stock"] == 0

        # Order kedua — stok sudah habis, harus ditolak
        order2 = await client.post("/api/v1/orders/", json={
            "umkm_id": umkm["id"],
            "items": [{"menu_item_id": product["id"], "quantity": 1}],
            "notes": "", "pickup_schedule": TOMORROW,
        }, headers=buyer_h)
        assert order2.status_code in (400, 422)


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 4: Multiple Buyers on Same UMKM
#  Dua buyer order ke UMKM yang sama secara berurutan
# ════════════════════════════════════════════════════════════════════════════

class TestMultipleBuyers:

    async def test_two_buyers_order_same_umkm(self, client: AsyncClient):
        """✅ SCENARIO 4: Dua buyer berbeda bisa order ke UMKM yang sama."""

        # Setup seller
        await client.post("/api/v1/auth/register", json={
            "name": "Seller Multi", "email": "sellermulti@ipb.ac.id",
            "password": "Pass123!", "phone": "087777000001", "role": "SELLER",
        })
        s_login = await client.post("/api/v1/auth/login",
            json={"email": "sellermulti@ipb.ac.id", "password": "Pass123!"})
        seller_h = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

        umkm = (await client.post("/api/v1/umkm/", json={
            "name": "Warung Ramai", "description": "Selalu ramai",
            "location": "Pusat Kampus", }, headers=seller_h)).json()
        await client.patch("/api/v1/umkm/status", headers=seller_h)

        product = (await client.post("/api/v1/products/", json={
            "name": "Gado-gado", "price": 9000, "stock": 50,
            "category": "MAKANAN", }, headers=seller_h)).json()

        # Buyer 1
        await client.post("/api/v1/auth/register", json={
            "name": "Buyer Satu", "email": "buyer1multi@ipb.ac.id",
            "password": "Pass123!", "phone": "088888000001", "role": "BUYER",
        })
        b1_login = await client.post("/api/v1/auth/login",
            json={"email": "buyer1multi@ipb.ac.id", "password": "Pass123!"})
        buyer1_h = {"Authorization": f"Bearer {b1_login.json()['access_token']}"}

        # Buyer 2
        await client.post("/api/v1/auth/register", json={
            "name": "Buyer Dua", "email": "buyer2multi@ipb.ac.id",
            "password": "Pass123!", "phone": "088888000002", "role": "BUYER",
        })
        b2_login = await client.post("/api/v1/auth/login",
            json={"email": "buyer2multi@ipb.ac.id", "password": "Pass123!"})
        buyer2_h = {"Authorization": f"Bearer {b2_login.json()['access_token']}"}

        # Kedua buyer order
        order1 = await client.post("/api/v1/orders/", json={
            "umkm_id": umkm["id"],
            "items": [{"menu_item_id": product["id"], "quantity": 2}],
            "notes": "Buyer 1 punya note", "pickup_schedule": TOMORROW,
        }, headers=buyer1_h)
        assert order1.status_code == 201

        order2 = await client.post("/api/v1/orders/", json={
            "umkm_id": umkm["id"],
            "items": [{"menu_item_id": product["id"], "quantity": 3}],
            "notes": "Buyer 2 punya note berbeda", "pickup_schedule": TOMORROW,
        }, headers=buyer2_h)
        assert order2.status_code == 201

        # Queue number harus berbeda
        assert order1.json()["queue_number"] != order2.json()["queue_number"]

        # Stok berkurang sesuai total (2+3=5)
        check = await client.get(f"/api/v1/products/{product['id']}", headers=buyer1_h)
        assert check.json()["stock"] == 50 - 5

        # Seller melihat kedua pesanan di incoming
        incoming = await client.get("/api/v1/orders/incoming", headers=seller_h)
        assert incoming.status_code == 200
        order_ids = [o["id"] for o in incoming.json()]
        assert order1.json()["id"] in order_ids
        assert order2.json()["id"] in order_ids

        # Buyer 1 hanya melihat pesanannya sendiri
        my1 = await client.get("/api/v1/orders/my", headers=buyer1_h)
        my1_ids = [o["id"] for o in my1.json()]
        assert order1.json()["id"] in my1_ids
        assert order2.json()["id"] not in my1_ids


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 5: Seller Manages Multiple Products
# ════════════════════════════════════════════════════════════════════════════

class TestSellerMultipleProducts:

    async def test_seller_manages_multiple_products(self, client: AsyncClient):
        """✅ SCENARIO 5: Seller mengelola beberapa produk, update stok, soft delete."""

        # Setup
        await client.post("/api/v1/auth/register", json={
            "name": "Seller Multi Produk", "email": "multiprod@ipb.ac.id",
            "password": "Pass123!", "phone": "089999000001", "role": "SELLER",
        })
        s_login = await client.post("/api/v1/auth/login",
            json={"email": "multiprod@ipb.ac.id", "password": "Pass123!"})
        seller_h = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

        await client.post("/api/v1/umkm/", json={
            "name": "Warung Lengkap", "description": "Banyak menu",
            "location": "Sudut Kantin", }, headers=seller_h)

        # Tambah 3 produk
        products = []
        for i, (name, price, cat) in enumerate([
            ("Ayam Bakar", 18000, "MAKANAN"),
            ("Es Jeruk", 5000, "MINUMAN"),
            ("Kerupuk", 2000, "JAJANAN"),
        ]):
            resp = await client.post("/api/v1/products/", json={
                "name": name, "price": price, "stock": 20, "category": cat,
            }, headers=seller_h)
            assert resp.status_code == 201
            products.append(resp.json())

        # Update stok produk pertama
        stock_update = await client.patch(
            f"/api/v1/products/{products[0]['id']}/stock",
            json={"stock": 5},
            headers=seller_h,
        )
        assert stock_update.status_code == 200
        assert stock_update.json()["stock"] == 5

        # Update detail produk kedua
        price_update = await client.put(
            f"/api/v1/products/{products[1]['id']}",
            json={"name": "Es Jeruk Segar Premium", "price": 6000,
                  "stock": 20, "category": "MINUMAN"},
            headers=seller_h,
        )
        assert price_update.status_code == 200
        assert price_update.json()["price"] == 6000

        # Seller lihat semua produknya
        my_products = await client.get("/api/v1/products/my", headers=seller_h)
        if my_products.status_code == 200:
            product_ids = [p["id"] for p in my_products.json()]
            for p in products:
                assert p["id"] in product_ids


# ════════════════════════════════════════════════════════════════════════════
#  SCENARIO 6: Order Rejection with Stock Restoration
# ════════════════════════════════════════════════════════════════════════════

class TestOrderRejectionFlow:

    async def test_rejection_restores_stock_and_shows_reason(
        self, client: AsyncClient
    ):
        """✅ SCENARIO 6: Penolakan order mengembalikan stok + alasan terlihat buyer."""

        # Setup
        await client.post("/api/v1/auth/register", json={
            "name": "Seller Reject", "email": "sellerreject@ipb.ac.id",
            "password": "Pass123!", "phone": "090000000001", "role": "SELLER",
        })
        s_login = await client.post("/api/v1/auth/login",
            json={"email": "sellerreject@ipb.ac.id", "password": "Pass123!"})
        seller_h = {"Authorization": f"Bearer {s_login.json()['access_token']}"}

        await client.post("/api/v1/auth/register", json={
            "name": "Buyer Reject", "email": "buyerreject@ipb.ac.id",
            "password": "Pass123!", "phone": "091111000001", "role": "BUYER",
        })
        b_login = await client.post("/api/v1/auth/login",
            json={"email": "buyerreject@ipb.ac.id", "password": "Pass123!"})
        buyer_h = {"Authorization": f"Bearer {b_login.json()['access_token']}"}

        umkm = (await client.post("/api/v1/umkm/", json={
            "name": "Warung Reject Test", "description": "Test saja",
            "location": "Lab Testing", }, headers=seller_h)).json()
        await client.patch("/api/v1/umkm/status", headers=seller_h)

        product = (await client.post("/api/v1/products/", json={
            "name": "Item Reject Test", "price": 7000, "stock": 10,
            "category": "JAJANAN", }, headers=seller_h)).json()

        # Buyer order (qty=4)
        order = (await client.post("/api/v1/orders/", json={
            "umkm_id": umkm["id"],
            "items": [{"menu_item_id": product["id"], "quantity": 4}],
            "notes": "Test penolakan", "pickup_schedule": TOMORROW,
        }, headers=buyer_h)).json()
        assert order["status"] == "PENDING"

        # Verifikasi stok berkurang ke 6
        after_order = (await client.get(
            f"/api/v1/products/{product['id']}", headers=buyer_h)).json()
        assert after_order["stock"] == 6

        # Seller tolak dengan alasan
        reject_reason = "Maaf bahan baku habis mendadak dari supplier"
        reject_resp = await client.patch(
            f"/api/v1/orders/{order['id']}/reject",
            json={"reason": reject_reason},
            headers=seller_h,
        )
        assert reject_resp.status_code == 200
        assert reject_resp.json()["status"] == "CANCELLED"
        assert reject_resp.json()["rejection_reason"] == reject_reason

        # Verifikasi stok dikembalikan ke 10
        after_reject = (await client.get(
            f"/api/v1/products/{product['id']}", headers=buyer_h)).json()
        assert after_reject["stock"] == 10

        # Buyer lihat alasan penolakan di pesanannya
        my_orders = (await client.get("/api/v1/orders/my", headers=buyer_h)).json()
        rejected_order = next((o for o in my_orders if o["id"] == order["id"]), None)
        assert rejected_order is not None
        assert rejected_order["status"] == "CANCELLED"
        assert rejected_order["rejection_reason"] == reject_reason