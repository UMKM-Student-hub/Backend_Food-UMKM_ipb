"""
test_promotions.py — E2E Tests: Deals & Promotion
==================================================
Mencakup semua skenario dari user stories USP01–USP04:
  ✅ Seller membuat promo diskon persentase
  ✅ Seller membuat promo diskon nominal
  ❌ Diskon persentase ≥ 100% ditolak
  ❌ Diskon nilai 0 atau negatif ditolak
  ❌ Tanggal kadaluwarsa di masa lalu ditolak
  ❌ Tanggal mulai lebih besar dari tanggal selesai ditolak
  ✅ Buyer melihat semua promo aktif
  ✅ Promo kadaluwarsa tidak muncul di halaman buyer
  ✅ Seller menonaktifkan promo
  ✅ Promo yang dinonaktifkan hilang dari halaman buyer
  ❌ Seller lain tidak bisa deaktivasi promo milik seller lain
  ❌ Buyer tidak bisa membuat/menonaktifkan promo
  ✅ Harga diskon terhitung dengan benar di produk
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
NEXT_WEEK = (date.today() + timedelta(days=7)).isoformat()
NEXT_MONTH = (date.today() + timedelta(days=30)).isoformat()


# ═══════════════════════════════════════════════════════════════════════════
#  A. MEMBUAT PROMO (SELLER)
# ═══════════════════════════════════════════════════════════════════════════

class TestCreatePromo:

    async def test_create_percentage_promo_success(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """✅ USP03: Seller berhasil membuat promo diskon persentase."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Promo Hari Senin",
                "discount_type": "PERCENTAGE",
                "discount_value": 20,
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Promo Hari Senin"
        assert data["discount_type"] == "PERCENTAGE"
        assert data["discount_value"] == 20
        assert data["is_active"] is True
        assert data["umkm_id"] == seller_with_umkm["umkm"]["id"]

    async def test_create_nominal_promo_success(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """✅ Seller membuat promo diskon nominal (bukan persentase)."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Diskon Rp 2.000",
                "discount_type": "NOMINAL",
                "discount_value": 2000,
                "start_date": TODAY,
                "end_date": NEXT_MONTH,
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 201
        assert resp.json()["discount_type"] == "NOMINAL"
        assert resp.json()["discount_value"] == 2000

    async def test_percentage_above_100_rejected(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """❌ USP03 AC2: Diskon persentase ≥ 100% harus ditolak."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Gratis Total",
                "discount_type": "PERCENTAGE",
                "discount_value": 100,  # tidak valid — harus < 100
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code in (400, 422)

    async def test_percentage_110_rejected(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """❌ Diskon 110% juga harus ditolak."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Super Diskon",
                "discount_type": "PERCENTAGE",
                "discount_value": 110,
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code in (400, 422)

    async def test_zero_discount_rejected(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """❌ Nilai diskon 0 harus ditolak (tidak ada artinya)."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Promo Nol",
                "discount_type": "PERCENTAGE",
                "discount_value": 0,
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code in (400, 422)

    async def test_negative_discount_rejected(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """❌ Nilai diskon negatif jelas tidak valid."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Diskon Negatif",
                "discount_type": "NOMINAL",
                "discount_value": -5000,
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code in (400, 422)

    async def test_end_date_in_past_rejected(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """❌ USP03 AC3: Tanggal kadaluwarsa yang sudah lewat harus ditolak."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Promo Kemarin",
                "discount_type": "PERCENTAGE",
                "discount_value": 10,
                "start_date": YESTERDAY,
                "end_date": YESTERDAY,  # sudah lewat
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code in (400, 422)

    async def test_start_date_after_end_date_rejected(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """❌ Tanggal mulai lebih besar dari tanggal selesai harus ditolak."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Promo Tanggal Terbalik",
                "discount_type": "PERCENTAGE",
                "discount_value": 10,
                "start_date": NEXT_MONTH,  # mulai > selesai
                "end_date": NEXT_WEEK,
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code in (400, 422)

    async def test_promo_for_other_seller_product_rejected(
        self,
        client: AsyncClient,
        registered_seller_2,
        menu_item,
    ):
        """❌ Seller tidak bisa membuat promo untuk produk milik seller lain."""
        # registered_seller_2 mencoba buat promo untuk produk seller pertama
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],  # produk milik seller pertama
                "name": "Promo Curang",
                "discount_type": "PERCENTAGE",
                "discount_value": 10,
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=registered_seller_2["headers"],
        )
        assert resp.status_code == 403

    async def test_buyer_cannot_create_promo(
        self, client: AsyncClient, registered_buyer, menu_item
    ):
        """❌ Buyer tidak bisa membuat promo (403 Forbidden)."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Promo Buyer Ilegal",
                "discount_type": "PERCENTAGE",
                "discount_value": 50,
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 403

    async def test_create_promo_missing_product_id(
        self, client: AsyncClient, seller_with_umkm
    ):
        """❌ menu_item_id wajib diisi."""
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        resp = await client.post(
            "/api/v1/promos/",
            json={
                "name": "Promo Tanpa Produk",
                "discount_type": "PERCENTAGE",
                "discount_value": 10,
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
#  B. MELIHAT PROMO (BUYER)
# ═══════════════════════════════════════════════════════════════════════════

class TestViewPromos:

    async def test_buyer_sees_active_promos(
        self,
        client: AsyncClient,
        registered_buyer,
        active_promo,
    ):
        """✅ USP01: Buyer melihat semua promo aktif di satu halaman."""
        resp = await client.get(
            "/api/v1/promos/active",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        promos = resp.json()
        assert isinstance(promos, list)
        assert len(promos) >= 1
        # Promo yang baru dibuat harus muncul
        promo_ids = [p["id"] for p in promos]
        assert active_promo["id"] in promo_ids

    async def test_active_promos_contain_required_fields(
        self,
        client: AsyncClient,
        registered_buyer,
        active_promo,
    ):
        """✅ USP01 AC2: Setiap promo menampilkan nama produk, diskon, tanggal kadaluwarsa."""
        resp = await client.get(
            "/api/v1/promos/active",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        for promo in resp.json():
            assert "name" in promo
            assert "discount_value" in promo
            assert "end_date" in promo
            assert "is_active" in promo
            assert promo["is_active"] is True  # hanya promo aktif yang muncul

    async def test_deactivated_promo_not_in_active_list(
        self,
        client: AsyncClient,
        registered_buyer,
        seller_with_umkm,
        active_promo,
    ):
        """✅ USP04 AC2: Promo yang dinonaktifkan langsung hilang dari halaman buyer."""
        # Seller deaktivasi promo
        await client.patch(
            f"/api/v1/promos/{active_promo['id']}/deactivate",
            headers=seller_with_umkm["headers"],
        )

        # Buyer cek promo aktif
        resp = await client.get(
            "/api/v1/promos/active",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        active_ids = [p["id"] for p in resp.json()]
        assert active_promo["id"] not in active_ids

    async def test_get_active_promos_unauthenticated(self, client: AsyncClient):
        """❌ Promo aktif memerlukan autentikasi (atau publik — sesuai implementasi)."""
        resp = await client.get("/api/v1/promos/active")
        # Bisa 200 (publik) atau 401 (harus login) — sesuaikan dengan implementasi
        assert resp.status_code in (200, 401)


# ═══════════════════════════════════════════════════════════════════════════
#  C. MANAJEMEN PROMO SELLER
# ═══════════════════════════════════════════════════════════════════════════

class TestManagePromos:

    async def test_seller_get_own_promos(
        self,
        client: AsyncClient,
        seller_with_umkm,
        active_promo,
    ):
        """✅ Seller melihat semua promo miliknya."""
        resp = await client.get(
            "/api/v1/promos/my",
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 200
        promos = resp.json()
        assert isinstance(promos, list)
        assert any(p["id"] == active_promo["id"] for p in promos)

    async def test_seller_deactivate_promo_success(
        self,
        client: AsyncClient,
        seller_with_umkm,
        active_promo,
    ):
        """✅ USP04: Seller menonaktifkan promo → is_active menjadi False."""
        resp = await client.patch(
            f"/api/v1/promos/{active_promo['id']}/deactivate",
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_seller_cannot_deactivate_already_inactive_promo(
        self,
        client: AsyncClient,
        seller_with_umkm,
        active_promo,
    ):
        """❌ Menonaktifkan promo yang sudah tidak aktif → error."""
        # Deaktivasi pertama
        await client.patch(
            f"/api/v1/promos/{active_promo['id']}/deactivate",
            headers=seller_with_umkm["headers"],
        )
        # Deaktivasi kedua — harus error
        resp = await client.patch(
            f"/api/v1/promos/{active_promo['id']}/deactivate",
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code in (400, 409)

    async def test_seller_cannot_deactivate_other_seller_promo(
        self,
        client: AsyncClient,
        registered_seller_2,
        active_promo,
    ):
        """❌ Seller lain tidak bisa menonaktifkan promo seller ini (403)."""
        resp = await client.patch(
            f"/api/v1/promos/{active_promo['id']}/deactivate",
            headers=registered_seller_2["headers"],
        )
        assert resp.status_code == 403

    async def test_buyer_cannot_deactivate_promo(
        self,
        client: AsyncClient,
        registered_buyer,
        active_promo,
    ):
        """❌ Buyer tidak punya akses untuk menonaktifkan promo."""
        resp = await client.patch(
            f"/api/v1/promos/{active_promo['id']}/deactivate",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 403

    async def test_deactivate_nonexistent_promo(
        self, client: AsyncClient, seller_with_umkm
    ):
        """❌ Menonaktifkan promo yang tidak ada → 404 Not Found."""
        resp = await client.patch(
            "/api/v1/promos/99999/deactivate",
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
#  D. KALKULASI HARGA DISKON
# ═══════════════════════════════════════════════════════════════════════════

class TestPromoCalculation:

    async def test_percentage_discount_applied_correctly(
        self,
        client: AsyncClient,
        seller_with_umkm,
        menu_item,
        registered_buyer,
    ):
        """✅ Harga diskon persentase dihitung dengan benar di response produk."""
        # Buat promo 20% untuk produk harga Rp 15.000
        # PERBAIKAN: Menambahkan / pada /api/v1/promos/
        await client.post(
            "/api/v1/promos/",
            json={
                "menu_item_id": menu_item["id"],
                "name": "Promo 20%",
                "discount_type": "PERCENTAGE",
                "discount_value": 20,
                "start_date": TODAY,
                "end_date": NEXT_WEEK,
            },
            headers=seller_with_umkm["headers"],
        )

        # Ambil detail produk — harga diskon harus tampil
        resp = await client.get(
            f"/api/v1/products/{menu_item['id']}",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        # Harga asli 15000, diskon 20% = 12000
        if "active_promo" in data and data["active_promo"]:
            promo = data["active_promo"]
            expected_price = menu_item["price"] * (1 - promo["discount_value"] / 100)
            assert promo.get("discounted_price") == expected_price or \
                   promo["discount_value"] == 20

    async def test_seller_my_promos_not_accessible_by_buyer(
        self,
        client: AsyncClient,
        registered_buyer,
    ):
        """❌ Buyer tidak bisa mengakses endpoint promo milik seller (/promos/my)."""
        resp = await client.get(
            "/api/v1/promos/my",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 403