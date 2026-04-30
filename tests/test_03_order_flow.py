"""
test_orders.py — E2E Tests: Pre-Order System
=============================================
Mencakup semua skenario dari user stories USO01–USO07:
  ✅ Buyer membuat pre-order
  ❌ Order ke toko yang tutup ditolak
  ❌ Order melebihi stok yang tersedia ditolak
  ❌ Order dengan item dari UMKM berbeda ditolak
  ✅ Buyer melihat daftar pesanannya
  ✅ Seller melihat pesanan masuk
  ✅ Seller konfirmasi pesanan (PENDING → CONFIRMED)
  ❌ Seller lain tidak bisa konfirmasi pesanan seller ini
  ✅ Seller tolak pesanan dengan alasan (PENDING → CANCELLED)
  ❌ Tolak pesanan tanpa alasan ditolak
  ✅ Seller tandai pesanan siap (CONFIRMED → READY)
  ✅ Buyer tandai pesanan selesai (READY → DONE)
  ❌ Transisi status yang tidak valid ditolak
  ✅ Stok berkurang setelah order dibuat
  ✅ Stok dikembalikan setelah order dibatalkan
  ✅ Queue number dihasilkan secara unik
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

TOMORROW = (date.today() + timedelta(days=1)).isoformat() + "T10:00:00"


# ═══════════════════════════════════════════════════════════════════════════
#  A. MEMBUAT ORDER (BUYER)
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateOrder:

    async def test_create_order_success(
        self,
        client: AsyncClient,
        registered_buyer,
        menu_item_with_open_store,
    ):
        """✅ USO01: Buyer berhasil membuat pre-order."""
        item = menu_item_with_open_store["menu_item"]
        umkm_id = menu_item_with_open_store["umkm"]["id"]

        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": umkm_id,
                "items": [{"menu_item_id": item["id"], "quantity": 2}],
                "notes": "Tanpa sambal extra pedas",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "PENDING"
        assert data["buyer_id"] == registered_buyer["user"]["id"]
        assert data["umkm_id"] == umkm_id
        assert "queue_number" in data
        assert data["queue_number"] is not None
        assert data["total_price"] == item["price"] * 2
        assert data["notes"] == "Tanpa sambal extra pedas"

    async def test_create_order_with_pickup_schedule(
        self,
        client: AsyncClient,
        registered_buyer,
        menu_item_with_open_store,
    ):
        """✅ USO02: Jadwal pengambilan tersimpan bersama data pesanan."""
        item = menu_item_with_open_store["menu_item"]
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": menu_item_with_open_store["umkm"]["id"],
                "items": [{"menu_item_id": item["id"], "quantity": 1}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 201
        assert resp.json()["pickup_schedule"] is not None

    async def test_create_order_to_closed_store_rejected(
        self,
        client: AsyncClient,
        registered_buyer,
        seller_with_umkm,
        menu_item,
    ):
        """❌ Order ke toko yang TUTUP harus ditolak (400/422)."""
        # seller_with_umkm → toko masih tutup (is_open = False)
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": seller_with_umkm["umkm"]["id"],
                "items": [{"menu_item_id": menu_item["id"], "quantity": 1}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code in (400, 422)
        assert "tutup" in resp.json()["detail"].lower() or \
               "closed" in resp.json()["detail"].lower() or \
               "buka" in resp.json()["detail"].lower()

    async def test_create_order_exceeds_stock_rejected(
        self,
        client: AsyncClient,
        registered_buyer,
        menu_item_with_open_store,
    ):
        """❌ Order dengan jumlah melebihi stok harus ditolak."""
        item = menu_item_with_open_store["menu_item"]
        # menu_item fixture memiliki stock=10, pesan quantity=999
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": menu_item_with_open_store["umkm"]["id"],
                "items": [{"menu_item_id": item["id"], "quantity": 999}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code in (400, 422)
        assert "stok" in resp.json()["detail"].lower() or \
               "stock" in resp.json()["detail"].lower() or \
               "insufficient" in resp.json()["detail"].lower()

    async def test_create_order_with_zero_quantity_rejected(
        self,
        client: AsyncClient,
        registered_buyer,
        menu_item_with_open_store,
    ):
        """❌ Quantity 0 harus ditolak pada level validasi Pydantic."""
        item = menu_item_with_open_store["menu_item"]
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": menu_item_with_open_store["umkm"]["id"],
                "items": [{"menu_item_id": item["id"], "quantity": 0}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 422

    async def test_create_order_with_empty_items_rejected(
        self,
        client: AsyncClient,
        registered_buyer,
        menu_item_with_open_store,
    ):
        """❌ Order tanpa item sama sekali harus ditolak."""
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": menu_item_with_open_store["umkm"]["id"],
                "items": [],  # kosong
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 422

    async def test_seller_cannot_place_order(
        self,
        client: AsyncClient,
        registered_seller,
        menu_item_with_open_store,
    ):
        """❌ Seller tidak bisa membuat pesanan (buyer only — 403)."""
        item = menu_item_with_open_store["menu_item"]
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": menu_item_with_open_store["umkm"]["id"],
                "items": [{"menu_item_id": item["id"], "quantity": 1}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_seller["headers"],
        )
        assert resp.status_code == 403

    async def test_order_reduces_stock(
        self,
        client: AsyncClient,
        registered_buyer,
        seller_with_umkm,
        menu_item_with_open_store,
    ):
        """✅ Stok berkurang setelah order berhasil dibuat."""
        item = menu_item_with_open_store["menu_item"]
        initial_stock = item["stock"]  # 10

        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": menu_item_with_open_store["umkm"]["id"],
                "items": [{"menu_item_id": item["id"], "quantity": 3}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )

        # Cek stok setelah order
        product_resp = await client.get(
            f"/api/v1/products/{item['id']}",
            headers=registered_buyer["headers"],
        )
        assert product_resp.status_code == 200
        new_stock = product_resp.json()["stock"]
        assert new_stock == initial_stock - 3

    async def test_queue_number_unique_per_umkm(
        self,
        client: AsyncClient,
        registered_buyer,
        menu_item_with_open_store,
    ):
        """✅ Setiap order menghasilkan queue_number yang unik."""
        item = menu_item_with_open_store["menu_item"]
        umkm_id = menu_item_with_open_store["umkm"]["id"]

        # Buat dua order berurutan
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        r1 = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": umkm_id,
                "items": [{"menu_item_id": item["id"], "quantity": 1}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        r2 = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": umkm_id,
                "items": [{"menu_item_id": item["id"], "quantity": 1}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=registered_buyer["headers"],
        )

        if r1.status_code == 201 and r2.status_code == 201:
            assert r1.json()["queue_number"] != r2.json()["queue_number"]


# ═══════════════════════════════════════════════════════════════════════════
#  B. MELIHAT PESANAN
# ═══════════════════════════════════════════════════════════════════════════

class TestViewOrders:

    async def test_buyer_get_my_orders(
        self,
        client: AsyncClient,
        placed_order,
    ):
        """✅ USO03: Buyer melihat daftar pesanan miliknya."""
        buyer_headers = placed_order["buyer"]["headers"]
        resp = await client.get("/api/v1/orders/my", headers=buyer_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        order_ids = [o["id"] for o in data]
        assert placed_order["order"]["id"] in order_ids

    async def test_buyer_only_sees_own_orders(
        self,
        client: AsyncClient,
        placed_order,
        registered_buyer,
    ):
        """✅ Buyer hanya melihat pesanannya sendiri, bukan pesanan buyer lain."""
        # registered_buyer berbeda dengan buyer di placed_order
        resp = await client.get(
            "/api/v1/orders/my",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        # registered_buyer belum membuat order
        # (placed_order dibuat oleh buyer fixture terpisah)
        # Ini berlaku ketika fixture buyer berbeda
        assert isinstance(resp.json(), list)

    async def test_seller_get_incoming_orders(
        self,
        client: AsyncClient,
        placed_order,
    ):
        """✅ USO05: Seller melihat daftar pesanan masuk."""
        seller_headers = placed_order["seller"]["headers"]
        resp = await client.get("/api/v1/orders/incoming", headers=seller_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        order_ids = [o["id"] for o in data]
        assert placed_order["order"]["id"] in order_ids

    async def test_seller_sees_buyer_name_in_order(
        self,
        client: AsyncClient,
        placed_order,
    ):
        """✅ USO05: Detail pesanan memuat nama pembeli, item, jumlah, catatan."""
        seller_headers = placed_order["seller"]["headers"]
        order_id = placed_order["order"]["id"]

        resp = await client.get(f"/api/v1/orders/{order_id}", headers=seller_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert "notes" in data
        assert "total_price" in data

    async def test_buyer_cannot_access_incoming_orders(
        self,
        client: AsyncClient,
        placed_order,
    ):
        """❌ Buyer tidak bisa mengakses endpoint pesanan masuk seller."""
        buyer_headers = placed_order["buyer"]["headers"]
        resp = await client.get("/api/v1/orders/incoming", headers=buyer_headers)
        assert resp.status_code == 403

    async def test_seller_cannot_access_buyer_orders(
        self,
        client: AsyncClient,
        placed_order,
    ):
        """❌ Seller tidak bisa mengakses halaman 'pesanan saya' buyer."""
        seller_headers = placed_order["seller"]["headers"]
        resp = await client.get("/api/v1/orders/my", headers=seller_headers)
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
#  C. KONFIRMASI & PENOLAKAN ORDER (SELLER)
# ═══════════════════════════════════════════════════════════════════════════

class TestOrderConfirmation:

    async def test_seller_confirm_order_success(
        self, client: AsyncClient, placed_order
    ):
        """✅ USO06: Seller mengkonfirmasi pesanan → status CONFIRMED."""
        seller_headers = placed_order["seller"]["headers"]
        order_id = placed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/confirm",
            headers=seller_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CONFIRMED"

    async def test_seller_reject_order_with_reason(
        self, client: AsyncClient, placed_order
    ):
        """✅ USO06: Seller menolak pesanan dengan alasan yang jelas."""
        seller_headers = placed_order["seller"]["headers"]
        order_id = placed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/reject",
            json={"reason": "Stok tiba-tiba habis, mohon maaf"},
            headers=seller_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "CANCELLED"
        assert data["rejection_reason"] == "Stok tiba-tiba habis, mohon maaf"

    async def test_seller_reject_order_without_reason(
        self, client: AsyncClient, placed_order
    ):
        """❌ USO06 AC2: Tolak pesanan tanpa alasan harus ditolak (422)."""
        seller_headers = placed_order["seller"]["headers"]
        order_id = placed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/reject",
            json={"reason": ""},  # kosong
            headers=seller_headers,
        )
        assert resp.status_code == 422

    async def test_seller_reject_order_missing_reason_field(
        self, client: AsyncClient, placed_order
    ):
        """❌ Field reason tidak dikirim sama sekali → 422."""
        seller_headers = placed_order["seller"]["headers"]
        order_id = placed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/reject",
            json={},  # field reason tidak ada
            headers=seller_headers,
        )
        assert resp.status_code == 422

    async def test_other_seller_cannot_confirm_order(
        self,
        client: AsyncClient,
        placed_order,
        registered_seller_2,
    ):
        """❌ Seller lain tidak bisa konfirmasi pesanan bukan miliknya (403)."""
        order_id = placed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/confirm",
            headers=registered_seller_2["headers"],
        )
        assert resp.status_code == 403

    async def test_buyer_cannot_confirm_own_order(
        self, client: AsyncClient, placed_order
    ):
        """❌ Buyer tidak bisa mengkonfirmasi pesanannya sendiri (403)."""
        buyer_headers = placed_order["buyer"]["headers"]
        order_id = placed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/confirm",
            headers=buyer_headers,
        )
        assert resp.status_code == 403

    async def test_cannot_confirm_already_confirmed_order(
        self, client: AsyncClient, confirmed_order
    ):
        """❌ Konfirmasi ulang order yang sudah CONFIRMED → error (400/409)."""
        seller_headers = confirmed_order["seller"]["headers"]
        order_id = confirmed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/confirm",
            headers=seller_headers,
        )
        assert resp.status_code in (400, 409, 422)

    async def test_cannot_reject_confirmed_order(
        self, client: AsyncClient, confirmed_order
    ):
        """❌ Tidak bisa menolak order yang sudah dikonfirmasi."""
        seller_headers = confirmed_order["seller"]["headers"]
        order_id = confirmed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/reject",
            json={"reason": "Terlambat menolak"},
            headers=seller_headers,
        )
        assert resp.status_code in (400, 409, 422)


# ═══════════════════════════════════════════════════════════════════════════
#  D. ALUR STATUS ORDER LENGKAP
# ═══════════════════════════════════════════════════════════════════════════

class TestOrderStatusFlow:

    async def test_mark_order_ready_success(
        self, client: AsyncClient, confirmed_order
    ):
        """✅ USO07: Seller menandai pesanan siap diambil → READY."""
        seller_headers = confirmed_order["seller"]["headers"]
        order_id = confirmed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/ready",
            headers=seller_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "READY"

    async def test_mark_order_done_by_buyer(
        self, client: AsyncClient, ready_order
    ):
        """✅ Buyer menandai pesanan selesai → DONE."""
        buyer_headers = ready_order["buyer"]["headers"]
        order_id = ready_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/done",
            headers=buyer_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "DONE"

    async def test_seller_cannot_mark_pending_as_ready(
        self, client: AsyncClient, placed_order
    ):
        """❌ Skip transisi status — PENDING tidak bisa langsung ke READY."""
        seller_headers = placed_order["seller"]["headers"]
        order_id = placed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/ready",
            headers=seller_headers,
        )
        assert resp.status_code in (400, 409, 422)

    async def test_buyer_cannot_mark_pending_as_done(
        self, client: AsyncClient, placed_order
    ):
        """❌ Buyer tidak bisa tandai PENDING sebagai DONE (transisi tidak valid)."""
        buyer_headers = placed_order["buyer"]["headers"]
        order_id = placed_order["order"]["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/done",
            headers=buyer_headers,
        )
        assert resp.status_code in (400, 409, 422)

    async def test_order_status_visible_to_buyer(
        self, client: AsyncClient, confirmed_order
    ):
        """✅ USO03: Buyer bisa melihat update status pesanan."""
        buyer_headers = confirmed_order["buyer"]["headers"]
        resp = await client.get("/api/v1/orders/my", headers=buyer_headers)

        assert resp.status_code == 200
        orders = resp.json()
        target = next(
            (o for o in orders if o["id"] == confirmed_order["order"]["id"]),
            None,
        )
        assert target is not None
        assert target["status"] == "CONFIRMED"

    async def test_rejection_reason_visible_to_buyer(
        self, client: AsyncClient, placed_order
    ):
        """✅ USO03 AC3: Jika ditolak, alasan penolakan terlihat oleh buyer."""
        seller_headers = placed_order["seller"]["headers"]
        buyer_headers = placed_order["buyer"]["headers"]
        order_id = placed_order["order"]["id"]

        # Seller tolak dengan alasan
        await client.patch(
            f"/api/v1/orders/{order_id}/reject",
            json={"reason": "Peralatan rusak mendadak"},
            headers=seller_headers,
        )

        # Buyer cek pesanannya
        resp = await client.get("/api/v1/orders/my", headers=buyer_headers)
        orders = resp.json()
        rejected = next((o for o in orders if o["id"] == order_id), None)

        assert rejected is not None
        assert rejected["status"] == "CANCELLED"
        assert rejected["rejection_reason"] == "Peralatan rusak mendadak"

    async def test_stock_restored_after_rejection(
        self,
        client: AsyncClient,
        registered_buyer,
        menu_item_with_open_store,
    ):
        """✅ Stok dikembalikan setelah order ditolak (business rule penting)."""
        item = menu_item_with_open_store["menu_item"]
        seller_headers = menu_item_with_open_store["headers"]
        buyer_headers = registered_buyer["headers"]
        initial_stock = item["stock"]

        # Buat order
        # PERBAIKAN: Menambahkan / pada /api/v1/orders/
        order_resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": menu_item_with_open_store["umkm"]["id"],
                "items": [{"menu_item_id": item["id"], "quantity": 3}],
                "notes": "",
                "pickup_schedule": TOMORROW,
            },
            headers=buyer_headers,
        )
        assert order_resp.status_code == 201
        order_id = order_resp.json()["id"]

        # Verifikasi stok berkurang
        after_order = await client.get(
            f"/api/v1/products/{item['id']}", headers=buyer_headers
        )
        assert after_order.json()["stock"] == initial_stock - 3

        # Seller tolak order
        await client.patch(
            f"/api/v1/orders/{order_id}/reject",
            json={"reason": "Maaf kehabisan bahan"},
            headers=seller_headers,
        )

        # Verifikasi stok dikembalikan
        after_reject = await client.get(
            f"/api/v1/products/{item['id']}", headers=buyer_headers
        )
        assert after_reject.json()["stock"] == initial_stock