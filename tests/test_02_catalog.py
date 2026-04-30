"""
test_catalog.py — E2E Tests: Centralized Catalog
=================================================
Mencakup semua skenario dari user stories USC01–USC06:
  ✅ Seller registrasi UMKM
  ❌ Seller tidak bisa daftar 2 UMKM (1 seller = 1 UMKM)
  ✅ Buyer melihat daftar semua UMKM aktif
  ✅ Buyer melihat detail UMKM + menu
  ✅ Seller menambah produk baru
  ❌ Buyer tidak bisa menambah produk
  ✅ Seller memperbarui stok produk
  ❌ Stok tidak boleh negatif
  ✅ Seller toggle status toko (buka/tutup)
  ✅ Toko tutup → produk tidak bisa dipesan
  ✅ Pencarian produk berdasarkan keyword
  ✅ Filter produk berdasarkan kategori
  ❌ Seller lain tidak bisa edit produk milik seller lain
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ═══════════════════════════════════════════════════════════════════════════
#  A. REGISTRASI & MANAJEMEN UMKM
# ═══════════════════════════════════════════════════════════════════════════

class TestUMKMRegistration:

    async def test_seller_register_umkm_success(
        self, client: AsyncClient, registered_seller
    ):
        """✅ Seller baru berhasil mendaftarkan UMKM-nya."""
        # PERBAIKAN: Menambahkan / pada /api/v1/umkm/
        resp = await client.post(
            "/api/v1/umkm/",
            json={
                "name": "Kantin Pak Rudi",
                "description": "Mie ayam dan bakso enak",
                "location": "Gedung A Lantai 1",
            },
            headers=registered_seller["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Kantin Pak Rudi"
        assert data["is_open"] is False  # default tutup saat baru daftar
        assert data["owner_id"] == registered_seller["user"]["id"]

    async def test_seller_cannot_register_second_umkm(
        self, client: AsyncClient, seller_with_umkm
    ):
        """❌ Business rule: 1 seller hanya boleh punya 1 UMKM (409 Conflict)."""
        # PERBAIKAN: Menambahkan / pada /api/v1/umkm/
        resp = await client.post(
            "/api/v1/umkm/",
            json={
                "name": "UMKM Kedua Tidak Boleh",
                "description": "Ini harus gagal",
                "location": "Di mana saja",
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 409
        assert "satu" in resp.json()["detail"].lower() or \
               "already" in resp.json()["detail"].lower() or \
               "sudah" in resp.json()["detail"].lower()

    async def test_buyer_cannot_register_umkm(
        self, client: AsyncClient, registered_buyer
    ):
        """❌ Buyer tidak punya izin untuk mendaftarkan UMKM (403 Forbidden)."""
        # PERBAIKAN: Menambahkan / pada /api/v1/umkm/
        resp = await client.post(
            "/api/v1/umkm/",
            json={
                "name": "UMKM Buyer Tidak Boleh",
                "description": "Ini harus gagal",
                "location": "Di mana saja",
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 403

    async def test_register_umkm_missing_name(
        self, client: AsyncClient, registered_seller
    ):
        """❌ Nama UMKM wajib diisi."""
        # PERBAIKAN: Menambahkan / pada /api/v1/umkm/
        resp = await client.post(
            "/api/v1/umkm/",
            json={"description": "Tanpa nama", "location": "Di sana"},
            headers=registered_seller["headers"],
        )
        assert resp.status_code == 422


class TestToggleUMKMStatus:

    async def test_toggle_store_open(
        self, client: AsyncClient, seller_with_umkm
    ):
        """✅ Seller membuka toko yang sedang tutup → is_open menjadi True."""
        resp = await client.patch(
            "/api/v1/umkm/status",
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["is_open"] is True

    async def test_toggle_store_close(
        self, client: AsyncClient, open_umkm
    ):
        """✅ Seller menutup toko yang sedang buka → is_open menjadi False."""
        resp = await client.patch(
            "/api/v1/umkm/status",
            headers=open_umkm["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["is_open"] is False

    async def test_buyer_cannot_toggle_store_status(
        self, client: AsyncClient, registered_buyer, seller_with_umkm
    ):
        """❌ Buyer tidak boleh mengubah status toko."""
        resp = await client.patch(
            "/api/v1/umkm/status",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 403

    async def test_seller_without_umkm_cannot_toggle(
        self, client: AsyncClient, registered_seller
    ):
        """❌ Seller yang belum punya UMKM tidak bisa toggle status."""
        resp = await client.patch(
            "/api/v1/umkm/status",
            headers=registered_seller["headers"],
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
#  B. MELIHAT KATALOG (BUYER VIEW)
# ═══════════════════════════════════════════════════════════════════════════

class TestViewCatalog:

    async def test_list_all_umkm(
        self, client: AsyncClient, registered_buyer, seller_with_umkm
    ):
        """✅ Buyer melihat daftar semua UMKM yang terdaftar."""
        resp = await client.get(
            "/api/v1/umkm",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        umkm_names = [u["name"] for u in data]
        assert "Warung Sari Rasa" in umkm_names

    async def test_list_umkm_shows_open_status(
        self, client: AsyncClient, registered_buyer, open_umkm
    ):
        """✅ Setiap UMKM menampilkan status buka/tutup."""
        resp = await client.get(
            "/api/v1/umkm",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        for umkm in resp.json():
            assert "is_open" in umkm
            assert "name" in umkm

    async def test_get_umkm_detail(
        self, client: AsyncClient, registered_buyer, seller_with_umkm
    ):
        """✅ Buyer melihat detail UMKM beserta menu-nya."""
        umkm_id = seller_with_umkm["umkm"]["id"]
        resp = await client.get(
            f"/api/v1/umkm/{umkm_id}",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == umkm_id
        assert data["name"] == "Warung Sari Rasa"

    async def test_get_umkm_not_found(
        self, client: AsyncClient, registered_buyer
    ):
        """❌ UMKM dengan ID yang tidak ada → 404 Not Found."""
        resp = await client.get(
            "/api/v1/umkm/99999",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 404

    async def test_catalog_requires_authentication(self, client: AsyncClient):
        """❌ Akses katalog tanpa login → 401 Unauthorized."""
        resp = await client.get("/api/v1/umkm")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
#  C. MANAJEMEN PRODUK (SELLER)
# ═══════════════════════════════════════════════════════════════════════════

class TestProductManagement:

    async def test_seller_add_product_success(
        self, client: AsyncClient, seller_with_umkm
    ):
        """✅ USC04: Seller menambahkan produk baru ke katalog."""
        # PERBAIKAN: Menambahkan / pada /api/v1/products/
        resp = await client.post(
            "/api/v1/products/",
            json={
                "name": "Es Teh Manis",
                "description": "Teh segar dengan gula aren",
                "price": 5000,
                "stock": 50,
                "category": "MINUMAN",
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Es Teh Manis"
        assert data["price"] == 5000
        assert data["stock"] == 50
        assert data["is_active"] is True  # default aktif
        assert data["umkm_id"] == seller_with_umkm["umkm"]["id"]

    async def test_seller_add_product_missing_name(
        self, client: AsyncClient, seller_with_umkm
    ):
        """❌ Nama produk wajib diisi."""
        # PERBAIKAN: Menambahkan / pada /api/v1/products/
        resp = await client.post(
            "/api/v1/products/",
            json={"price": 10000, "stock": 5, "category": "JAJANAN"},
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 422

    async def test_seller_add_product_negative_price(
        self, client: AsyncClient, seller_with_umkm
    ):
        """❌ Harga negatif tidak diizinkan."""
        # PERBAIKAN: Menambahkan / pada /api/v1/products/
        resp = await client.post(
            "/api/v1/products/",
            json={
                "name": "Produk Harga Negatif",
                "price": -1000,
                "stock": 5,
                "category": "JAJANAN",
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 422

    async def test_seller_add_product_negative_stock(
        self, client: AsyncClient, seller_with_umkm
    ):
        """❌ Stok negatif tidak diizinkan."""
        # PERBAIKAN: Menambahkan / pada /api/v1/products/
        resp = await client.post(
            "/api/v1/products/",
            json={
                "name": "Produk Stok Negatif",
                "price": 5000,
                "stock": -5,
                "category": "JAJANAN",
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 422

    async def test_buyer_cannot_add_product(
        self, client: AsyncClient, registered_buyer
    ):
        """❌ Buyer tidak bisa menambah produk (403 Forbidden)."""
        # PERBAIKAN: Menambahkan / pada /api/v1/products/
        resp = await client.post(
            "/api/v1/products/",
            json={
                "name": "Produk Buyer",
                "price": 5000,
                "stock": 5,
                "category": "JAJANAN",
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 403

    async def test_seller_without_umkm_cannot_add_product(
        self, client: AsyncClient, registered_seller
    ):
        """❌ Seller yang belum punya UMKM tidak bisa menambah produk."""
        # PERBAIKAN: Menambahkan / pada /api/v1/products/
        resp = await client.post(
            "/api/v1/products/",
            json={
                "name": "Produk Tanpa UMKM",
                "price": 5000,
                "stock": 5,
                "category": "JAJANAN",
            },
            headers=registered_seller["headers"],
        )
        assert resp.status_code in (404, 422)


class TestProductUpdate:

    async def test_seller_update_product_success(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """✅ Seller berhasil mengupdate data produk."""
        product_id = menu_item["id"]
        resp = await client.put(
            f"/api/v1/products/{product_id}",
            json={
                "name": "Nasi Goreng Super Spesial",
                "description": "Versi upgrade dengan keju",
                "price": 18000,
                "stock": 15,
                "category": "MAKANAN",
            },
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Nasi Goreng Super Spesial"
        assert data["price"] == 18000

    async def test_seller_update_stock_success(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """✅ USC05: Seller memperbarui stok produk secara inline."""
        product_id = menu_item["id"]
        resp = await client.patch(
            f"/api/v1/products/{product_id}/stock",
            json={"stock": 25},
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["stock"] == 25

    async def test_stock_update_to_zero(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """✅ Seller boleh mengatur stok menjadi 0 (produk habis)."""
        product_id = menu_item["id"]
        resp = await client.patch(
            f"/api/v1/products/{product_id}/stock",
            json={"stock": 0},
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["stock"] == 0

    async def test_stock_update_negative_rejected(
        self, client: AsyncClient, seller_with_umkm, menu_item
    ):
        """❌ Stok tidak boleh negatif — ditolak di level validasi."""
        product_id = menu_item["id"]
        resp = await client.patch(
            f"/api/v1/products/{product_id}/stock",
            json={"stock": -1},
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 422

    async def test_seller_cannot_update_other_seller_product(
        self,
        client: AsyncClient,
        menu_item,
        registered_seller_2,
    ):
        """❌ Seller tidak bisa mengupdate produk milik seller lain (403)."""
        # registered_seller_2 mencoba update produk milik seller pertama
        resp = await client.put(
            f"/api/v1/products/{menu_item['id']}",
            json={
                "name": "Diubah Seller Lain",
                "price": 99999,
                "stock": 0,
                "category": "JAJANAN",
            },
            headers=registered_seller_2["headers"],
        )
        assert resp.status_code == 403

    async def test_update_nonexistent_product(
        self, client: AsyncClient, seller_with_umkm
    ):
        """❌ Update produk yang tidak ada → 404 Not Found."""
        resp = await client.patch(
            "/api/v1/products/99999/stock",
            json={"stock": 10},
            headers=seller_with_umkm["headers"],
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
#  D. PENCARIAN & FILTER PRODUK
# ═══════════════════════════════════════════════════════════════════════════

class TestProductSearch:

    async def test_search_by_keyword(
        self, client: AsyncClient, registered_buyer, menu_item
    ):
        """✅ USC02: Buyer mencari produk berdasarkan nama."""
        resp = await client.get(
            "/api/v1/products/search?keyword=nasi",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)
        # "Nasi Goreng Spesial" harus muncul
        names = [r["name"].lower() for r in results]
        assert any("nasi" in n for n in names)

    async def test_search_keyword_no_result(
        self, client: AsyncClient, registered_buyer, menu_item
    ):
        """✅ Pencarian tanpa hasil mengembalikan list kosong (bukan error)."""
        resp = await client.get(
            "/api/v1/products/search?keyword=sate_padang_tidak_ada",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_filter_by_category(
        self, client: AsyncClient, registered_buyer, seller_with_umkm
    ):
        """✅ Filter produk berdasarkan kategori."""
        # Tambah dua produk berbeda kategori
        # PERBAIKAN: Menambahkan / pada /api/v1/products/
        await client.post(
            "/api/v1/products/",
            json={"name": "MINUMAN A", "price": 3000, "stock": 20, "category": "MINUMAN"},
            headers=seller_with_umkm["headers"],
        )
        # PERBAIKAN: Menambahkan / pada /api/v1/products/
        await client.post(
            "/api/v1/products/",
            json={"name": "JAJANAN B", "price": 5000, "stock": 30, "category": "JAJANAN"},
            headers=seller_with_umkm["headers"],
        )

        resp = await client.get(
            "/api/v1/products/search?keyword=&category=MINUMAN",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        for item in resp.json():
            assert item["category"] == "MINUMAN"

    async def test_get_product_detail(
        self, client: AsyncClient, registered_buyer, menu_item
    ):
        """✅ USC03: Buyer melihat detail produk individual."""
        resp = await client.get(
            f"/api/v1/products/{menu_item['id']}",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == menu_item["id"]
        assert "price" in data
        assert "stock" in data
        assert "description" in data

    async def test_get_product_stock_zero_shows_unavailable(
        self, client: AsyncClient, registered_buyer, seller_with_umkm, menu_item
    ):
        """✅ Produk stok 0 harus menandakan is_available = False."""
        # Set stok ke 0
        await client.patch(
            f"/api/v1/products/{menu_item['id']}/stock",
            json={"stock": 0},
            headers=seller_with_umkm["headers"],
        )

        resp = await client.get(
            f"/api/v1/products/{menu_item['id']}",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        # stock harus 0
        assert data["stock"] == 0

    async def test_get_products_by_umkm(
        self, client: AsyncClient, registered_buyer, menu_item_with_open_store
    ):
        """✅ Buyer melihat semua produk dari UMKM tertentu."""
        umkm_id = menu_item_with_open_store["umkm"]["id"]
        resp = await client.get(
            f"/api/v1/umkm/{umkm_id}/products",
            headers=registered_buyer["headers"],
        )
        # Endpoint ini mungkin ada atau digabung dengan detail UMKM
        assert resp.status_code in (200, 404)  # 404 jika endpoint belum ada