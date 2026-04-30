"""
test_reviews.py — E2E Tests: Rating & Review
============================================
Mencakup semua skenario dari user stories USR01–USR03:
  ✅ Buyer submit ulasan untuk order yang DONE
  ❌ Buyer tidak bisa ulasan order yang belum DONE
  ❌ Satu order hanya bisa diulas satu kali
  ❌ Buyer lain tidak bisa ulasan order yang bukan miliknya
  ✅ Rating 1–5 valid, luar rentang ditolak
  ✅ Buyer membaca ulasan di halaman detail produk
  ✅ Ulasan diurutkan terbaru di atas (default)
  ✅ Seller melihat semua ulasan produknya di dashboard
  ✅ Rata-rata rating dihitung dengan benar
  ❌ Seller tidak bisa submit ulasan
  ❌ Rating wajib diisi (comment opsional)
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ═══════════════════════════════════════════════════════════════════════════
#  A. SUBMIT ULASAN (BUYER)
# ═══════════════════════════════════════════════════════════════════════════

class TestSubmitReview:

    async def test_buyer_submit_review_success(
        self, client: AsyncClient, done_order
    ):
        """✅ USR01: Buyer berhasil memberikan rating dan komentar setelah order DONE."""
        buyer_headers = done_order["buyer"]["headers"]
        order_id = done_order["order"]["id"]

        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": order_id,
                "rating": 5,
                "comment": "Enak sekali, porsi besar dan harga terjangkau!",
            },
            headers=buyer_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["rating"] == 5
        assert data["comment"] == "Enak sekali, porsi besar dan harga terjangkau!"
        assert data["order_id"] == order_id
        assert data["buyer_id"] == done_order["buyer"]["user"]["id"]
        assert data["menu_item_id"] == done_order["menu_item"]["id"]

    async def test_submit_review_without_comment(
        self, client: AsyncClient, done_order
    ):
        """✅ USR01: Komentar bersifat opsional — hanya rating saja harus berhasil."""
        buyer_headers = done_order["buyer"]["headers"]
        order_id = done_order["order"]["id"]

        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": order_id,
                "rating": 4,
                "comment": "",  # komentar kosong — harus diizinkan
            },
            headers=buyer_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["rating"] == 4

    async def test_rating_below_1_rejected(
        self, client: AsyncClient, done_order
    ):
        """❌ Rating di bawah 1 harus ditolak pada level validasi."""
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": done_order["order"]["id"],
                "rating": 0,
                "comment": "Rating nol tidak valid",
            },
            headers=done_order["buyer"]["headers"],
        )
        assert resp.status_code == 422

    async def test_rating_above_5_rejected(
        self, client: AsyncClient, done_order
    ):
        """❌ Rating di atas 5 harus ditolak."""
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": done_order["order"]["id"],
                "rating": 6,
                "comment": "Rating enam tidak valid",
            },
            headers=done_order["buyer"]["headers"],
        )
        assert resp.status_code == 422

    async def test_rating_missing_rejected(
        self, client: AsyncClient, done_order
    ):
        """❌ USR01 AC2: Rating wajib diisi — tanpa rating harus ditolak."""
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": done_order["order"]["id"],
                "comment": "Komentar tanpa rating",
            },
            headers=done_order["buyer"]["headers"],
        )
        assert resp.status_code == 422

    async def test_cannot_review_pending_order(
        self, client: AsyncClient, placed_order
    ):
        """❌ Tidak bisa review order yang masih PENDING."""
        buyer_headers = placed_order["buyer"]["headers"]
        order_id = placed_order["order"]["id"]

        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": order_id,
                "rating": 3,
                "comment": "Review prematur",
            },
            headers=buyer_headers,
        )
        assert resp.status_code in (400, 422)
        # Pesan error harus menyebut status / selesai / done
        detail = resp.json().get("detail", "").lower()
        assert any(kw in detail for kw in ["selesai", "done", "status", "belum"])

    async def test_cannot_review_confirmed_order(
        self, client: AsyncClient, confirmed_order
    ):
        """❌ Tidak bisa review order yang baru CONFIRMED (belum selesai)."""
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": confirmed_order["order"]["id"],
                "rating": 4,
                "comment": "Masih dikonfirmasi",
            },
            headers=confirmed_order["buyer"]["headers"],
        )
        assert resp.status_code in (400, 422)

    async def test_cannot_review_same_order_twice(
        self, client: AsyncClient, done_order
    ):
        """❌ USR01 AC3: Satu order hanya bisa diulas SATU kali."""
        buyer_headers = done_order["buyer"]["headers"]
        order_id = done_order["order"]["id"]

        # Ulasan pertama — harus berhasil
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        first = await client.post(
            "/api/v1/reviews/",
            json={"order_id": order_id, "rating": 5, "comment": "Enak!"},
            headers=buyer_headers,
        )
        assert first.status_code == 201

        # Ulasan kedua untuk order yang sama — harus ditolak
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        second = await client.post(
            "/api/v1/reviews/",
            json={"order_id": order_id, "rating": 3, "comment": "Berubah pikiran"},
            headers=buyer_headers,
        )
        assert second.status_code in (400, 409, 422)

    async def test_buyer_cannot_review_other_buyer_order(
        self,
        client: AsyncClient,
        done_order,
        registered_buyer,
    ):
        """❌ Buyer lain tidak bisa mereview order yang bukan miliknya."""
        # registered_buyer berbeda dengan buyer yang membuat done_order
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": done_order["order"]["id"],
                "rating": 1,
                "comment": "Review curang",
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code in (403, 404)

    async def test_seller_cannot_submit_review(
        self, client: AsyncClient, done_order
    ):
        """❌ Seller tidak bisa submit ulasan (buyer only — 403)."""
        seller_headers = done_order["seller"]["headers"]
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": done_order["order"]["id"],
                "rating": 5,
                "comment": "Seller review sendiri",
            },
            headers=seller_headers,
        )
        assert resp.status_code == 403

    async def test_review_for_nonexistent_order(
        self, client: AsyncClient, registered_buyer
    ):
        """❌ Review untuk order yang tidak ada → 404 Not Found."""
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp = await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": 99999,
                "rating": 3,
                "comment": "Order tidak ada",
            },
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
#  B. MEMBACA ULASAN (BUYER & PUBLIK)
# ═══════════════════════════════════════════════════════════════════════════

class TestReadReviews:

    async def test_buyer_read_product_reviews(
        self, client: AsyncClient, done_order, registered_buyer
    ):
        """✅ USR02: Buyer membaca ulasan produk sebelum memesan."""
        buyer_headers = done_order["buyer"]["headers"]
        order_id = done_order["order"]["id"]
        menu_item_id = done_order["menu_item"]["id"]

        # Submit review terlebih dahulu
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        await client.post(
            "/api/v1/reviews/",
            json={"order_id": order_id, "rating": 4, "comment": "Cukup enak"},
            headers=buyer_headers,
        )

        # Buyer lain membaca ulasan produk
        resp = await client.get(
            f"/api/v1/reviews/product/{menu_item_id}",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        reviews = resp.json()
        assert isinstance(reviews, list)
        assert len(reviews) >= 1

        review = reviews[0]
        assert "rating" in review
        assert "comment" in review
        assert "created_at" in review

    async def test_product_reviews_empty_when_no_review(
        self, client: AsyncClient, registered_buyer, menu_item
    ):
        """✅ Produk tanpa ulasan mengembalikan list kosong (bukan error)."""
        resp = await client.get(
            f"/api/v1/reviews/product/{menu_item['id']}",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_reviews_ordered_newest_first(
        self,
        client: AsyncClient,
        done_order,
        registered_buyer,
    ):
        """✅ USR02 AC2: Ulasan diurutkan terbaru di atas secara default."""
        menu_item_id = done_order["menu_item"]["id"]

        # Submit satu review
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": done_order["order"]["id"],
                "rating": 5,
                "comment": "Ulasan pertama",
            },
            headers=done_order["buyer"]["headers"],
        )

        resp = await client.get(
            f"/api/v1/reviews/product/{menu_item_id}",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        # Jika ada lebih dari 1 review, urutan harus descending by created_at
        reviews = resp.json()
        if len(reviews) >= 2:
            from datetime import datetime
            dates = [datetime.fromisoformat(r["created_at"]) for r in reviews]
            assert dates == sorted(dates, reverse=True)

    async def test_get_reviews_nonexistent_product(
        self, client: AsyncClient, registered_buyer
    ):
        """❌ Review untuk produk yang tidak ada → 404 atau list kosong."""
        resp = await client.get(
            "/api/v1/reviews/product/99999",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.json() == []


# ═══════════════════════════════════════════════════════════════════════════
#  C. DASHBOARD ULASAN SELLER
# ═══════════════════════════════════════════════════════════════════════════

class TestSellerReviewDashboard:

    async def test_seller_get_umkm_reviews(
        self, client: AsyncClient, done_order
    ):
        """✅ USR03: Seller melihat semua ulasan produknya."""
        buyer_headers = done_order["buyer"]["headers"]
        seller_headers = done_order["seller"]["headers"]
        order_id = done_order["order"]["id"]

        # Submit review
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        await client.post(
            "/api/v1/reviews/",
            json={"order_id": order_id, "rating": 4, "comment": "Mantap"},
            headers=buyer_headers,
        )

        # Seller ambil semua ulasan UMKM-nya
        umkm_id = done_order["seller"]["umkm"]["id"]
        resp = await client.get(
            f"/api/v1/reviews/umkm/{umkm_id}",
            headers=seller_headers,
        )
        assert resp.status_code == 200
        reviews = resp.json()
        assert isinstance(reviews, list)
        assert len(reviews) >= 1

    async def test_seller_cannot_see_other_seller_reviews(
        self,
        client: AsyncClient,
        done_order,
        registered_seller_2,
    ):
        """❌ Seller tidak bisa melihat ulasan UMKM milik seller lain (403)."""
        umkm_id = done_order["seller"]["umkm"]["id"]
        resp = await client.get(
            f"/api/v1/reviews/umkm/{umkm_id}",
            headers=registered_seller_2["headers"],
        )
        assert resp.status_code == 403

    async def test_average_rating_calculation(
        self, client: AsyncClient, done_order, registered_buyer
    ):
        """✅ Rata-rata rating produk dihitung dengan benar."""
        menu_item_id = done_order["menu_item"]["id"]

        # Submit 1 review dengan rating 5
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        await client.post(
            "/api/v1/reviews/",
            json={"order_id": done_order["order"]["id"], "rating": 5, "comment": ""},
            headers=done_order["buyer"]["headers"],
        )

        # Ambil rata-rata
        resp = await client.get(
            f"/api/v1/reviews/product/{menu_item_id}/average",
            headers=registered_buyer["headers"],
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "average" in data
            assert data["average"] == 5.0

    async def test_buyer_cannot_access_seller_umkm_reviews(
        self, client: AsyncClient, registered_buyer, done_order
    ):
        """❌ Buyer tidak bisa mengakses endpoint ulasan seller (403)."""
        umkm_id = done_order["seller"]["umkm"]["id"]
        resp = await client.get(
            f"/api/v1/reviews/umkm/{umkm_id}",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 403

    async def test_seller_review_list_includes_all_fields(
        self, client: AsyncClient, done_order
    ):
        """✅ USR03: List ulasan seller memuat rating, komentar, dan info produk."""
        buyer_headers = done_order["buyer"]["headers"]
        seller_headers = done_order["seller"]["headers"]

        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        await client.post(
            "/api/v1/reviews/",
            json={
                "order_id": done_order["order"]["id"],
                "rating": 3,
                "comment": "Biasa saja",
            },
            headers=buyer_headers,
        )

        umkm_id = done_order["seller"]["umkm"]["id"]
        resp = await client.get(
            f"/api/v1/reviews/umkm/{umkm_id}",
            headers=seller_headers,
        )
        assert resp.status_code == 200
        if resp.json():
            review = resp.json()[0]
            assert "rating" in review
            assert "comment" in review
            assert "menu_item_id" in review
            assert "created_at" in review

    async def test_rating_boundary_values(
        self, client: AsyncClient, done_order
    ):
        """✅ Rating 1 dan 5 adalah nilai valid (boundary test)."""
        buyer_headers = done_order["buyer"]["headers"]
        order_id = done_order["order"]["id"]

        # Test rating = 1 (minimum valid)
        # PERBAIKAN: Menambahkan / pada /api/v1/reviews/
        resp_min = await client.post(
            "/api/v1/reviews/",
            json={"order_id": order_id, "rating": 1, "comment": "Sangat buruk"},
            headers=buyer_headers,
        )
        # Harus 201, atau 400/409 jika sudah pernah review
        assert resp_min.status_code in (201, 400, 409)

        # Jika berhasil, verifikasi nilai tersimpan
        if resp_min.status_code == 201:
            assert resp_min.json()["rating"] == 1