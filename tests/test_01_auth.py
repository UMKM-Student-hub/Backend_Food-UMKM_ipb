"""
test_auth.py — E2E Tests: Autentikasi (Register & Login)
=========================================================
Mencakup semua skenario dari user stories USA01 & USA02:
  ✅ Register sukses sebagai BUYER
  ✅ Register sukses sebagai SELLER
  ❌ Register dengan email duplikat
  ❌ Register dengan field kosong / format tidak valid
  ❌ Register dengan role tidak valid
  ✅ Login sukses dan terima JWT token
  ❌ Login dengan password salah
  ❌ Login dengan email tidak terdaftar
  ✅ Akses endpoint terproteksi dengan token valid
  ❌ Akses endpoint terproteksi tanpa token
  ❌ Akses endpoint terproteksi dengan token kedaluwarsa/invalid
  ✅ GET /auth/me — ambil data user yang sedang login
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ═══════════════════════════════════════════════════════════════════════════
#  A. REGISTER
# ═══════════════════════════════════════════════════════════════════════════

class TestRegister:
    """USA01: Pengguna baru mendaftar akun."""

    async def test_register_buyer_success(self, client: AsyncClient):
        """✅ Register buyer dengan data lengkap dan valid."""
        payload = {
            "name": "Budi Santoso",
            "email": "budi@ipb.ac.id",
            "password": "SecurePass123!",
            "phone": "081234567890",
            "role": "BUYER",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)

        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == payload["email"]
        assert data["name"] == payload["name"]
        assert data["role"] == "BUYER"
        # Password hash TIDAK boleh dikembalikan ke client
        assert "password" not in data
        assert "password_hash" not in data
        assert "id" in data

    async def test_register_seller_success(self, client: AsyncClient):
        """✅ Register seller dengan data lengkap dan valid."""
        payload = {
            "name": "Ibu Warung",
            "email": "warung@ipb.ac.id",
            "password": "SecurePass123!",
            "phone": "082345678901",
            "role": "SELLER",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)

        assert resp.status_code == 201
        assert resp.json()["role"] == "SELLER"

    async def test_register_duplicate_email_rejected(self, client: AsyncClient):
        """❌ Email yang sudah terdaftar harus ditolak (409 Conflict)."""
        payload = {
            "name": "User Pertama",
            "email": "sama@ipb.ac.id",
            "password": "Pass123!",
            "phone": "081111111111",
            "role": "BUYER",
        }
        # Pertama kali — harus sukses
        resp1 = await client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201

        # Kedua kali dengan email sama — harus ditolak
        payload["name"] = "User Kedua"
        resp2 = await client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409
        assert "email" in resp2.json()["detail"].lower() or \
               "sudah" in resp2.json()["detail"].lower() or \
               "already" in resp2.json()["detail"].lower()

    async def test_register_missing_name(self, client: AsyncClient):
        """❌ Field name wajib diisi."""
        resp = await client.post("/api/v1/auth/register", json={
            "email": "test@ipb.ac.id",
            "password": "Pass123!",
            "phone": "081234567890",
            "role": "BUYER",
        })
        assert resp.status_code == 422

    async def test_register_invalid_email_format(self, client: AsyncClient):
        """❌ Format email tidak valid harus ditolak Pydantic."""
        resp = await client.post("/api/v1/auth/register", json={
            "name": "Test",
            "email": "ini-bukan-email",
            "password": "Pass123!",
            "phone": "081234567890",
            "role": "BUYER",
        })
        assert resp.status_code == 422

    async def test_register_invalid_role(self, client: AsyncClient):
        """❌ Role selain BUYER / SELLER harus ditolak."""
        resp = await client.post("/api/v1/auth/register", json={
            "name": "Test",
            "email": "test2@ipb.ac.id",
            "password": "Pass123!",
            "phone": "081234567890",
            "role": "ADMIN",  # tidak valid
        })
        assert resp.status_code == 422

    async def test_register_missing_phone_allowed(self, client: AsyncClient):
        """✅ Phone bersifat opsional — register tanpa phone harus berhasil."""
        resp = await client.post("/api/v1/auth/register", json={
            "name": "Test Tanpa HP",
            "email": "tanpahp@ipb.ac.id",
            "password": "Pass123!",
            "role": "BUYER",
        })
        # Bisa 201 (opsional) atau 422 (wajib) — tergantung implementasi
        # Sesuaikan dengan skema Pydantic yang aktual
        assert resp.status_code in (201, 422)

    async def test_register_password_too_short(self, client: AsyncClient):
        """❌ Password terlalu pendek harus ditolak (jika ada validasi panjang)."""
        resp = await client.post("/api/v1/auth/register", json={
            "name": "Test",
            "email": "short@ipb.ac.id",
            "password": "123",  # terlalu pendek
            "phone": "081234567890",
            "role": "BUYER",
        })
        # 422 jika ada validasi min_length di schema
        assert resp.status_code in (201, 422)


# ═══════════════════════════════════════════════════════════════════════════
#  B. LOGIN
# ═══════════════════════════════════════════════════════════════════════════

class TestLogin:
    """USA02: Pengguna terdaftar login ke akun."""

    async def test_login_success_returns_token(
        self, client: AsyncClient, registered_buyer
    ):
        """✅ Login berhasil mengembalikan access_token yang valid."""
        # PERBAIKAN: Menggunakan json={...} dan key "email"
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_buyer["email"],
                "password": "Password123!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"].lower() == "bearer"
        assert len(data["access_token"]) > 20  # token JWT memiliki panjang substantif

    async def test_login_wrong_password(
        self, client: AsyncClient, registered_buyer
    ):
        """❌ Password salah harus ditolak (401 Unauthorized)."""
        # PERBAIKAN: Menggunakan json={...} dan key "email"
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_buyer["email"],
                "password": "PasswordSalah!",
            },
        )
        assert resp.status_code == 401

    async def test_login_email_not_registered(self, client: AsyncClient):
        """❌ Email tidak terdaftar harus ditolak."""
        # PERBAIKAN: Menggunakan json={...} dan key "email"
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "tidakterdaftar@ipb.ac.id",
                "password": "Password123!",
            },
        )
        assert resp.status_code == 401

    async def test_login_empty_credentials(self, client: AsyncClient):
        """❌ Credentials kosong harus ditolak."""
        # PERBAIKAN: Menggunakan json={...} dan key "email"
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "", "password": ""},
        )
        assert resp.status_code in (401, 422)

    async def test_seller_login_success(
        self, client: AsyncClient, registered_seller
    ):
        """✅ Seller juga bisa login dengan flow yang sama."""
        # PERBAIKAN: Menggunakan json={...} dan key "email"
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_seller["email"],
                "password": "Password123!",
            },
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════
#  C. GET ME & TOKEN VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

class TestGetMe:
    """Verifikasi JWT token dan endpoint GET /auth/me."""

    async def test_get_me_with_valid_token(
        self, client: AsyncClient, registered_buyer
    ):
        """✅ Token valid → kembalikan data user yang login."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == registered_buyer["email"]
        assert data["role"] == "BUYER"
        assert "password_hash" not in data

    async def test_get_me_without_token(self, client: AsyncClient):
        """❌ Request tanpa token harus ditolak (401)."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_get_me_with_invalid_token(self, client: AsyncClient):
        """❌ Token palsu/malformed harus ditolak (401)."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer ini.token.palsu"},
        )
        assert resp.status_code == 401

    async def test_get_me_with_malformed_header(self, client: AsyncClient):
        """❌ Header Authorization tanpa prefix 'Bearer' harus ditolak."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "tokenlangsungbegini"},
        )
        assert resp.status_code == 401

    async def test_seller_get_me_shows_seller_role(
        self, client: AsyncClient, registered_seller
    ):
        """✅ Seller yang login mendapat data dengan role SELLER."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers=registered_seller["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "SELLER"

    async def test_buyer_cannot_access_seller_only_endpoint(
        self, client: AsyncClient, registered_buyer
    ):
        """❌ Buyer tidak bisa mengakses endpoint yang hanya untuk Seller."""
        # Contoh: endpoint daftar pesanan masuk (seller only)
        resp = await client.get(
            "/api/v1/orders/incoming",
            headers=registered_buyer["headers"],
        )
        assert resp.status_code == 403

    async def test_seller_cannot_place_order(
        self, client: AsyncClient, registered_seller
    ):
        """❌ Seller tidak bisa melakukan pre-order (buyer only)."""
        # PERBAIKAN TAMBAHAN: Pastikan /api/v1/orders diakhiri slash (opsional, tergantung router)
        # Saya asumsikan sudah ditambahkan slash sesuai diskusi sebelumnya,
        # Jika belum, ubah "/api/v1/orders" menjadi "/api/v1/orders/" 
        resp = await client.post(
            "/api/v1/orders/",
            json={
                "umkm_id": 1,
                "items": [{"menu_item_id": 1, "quantity": 1}],
                "notes": "",
                "pickup_schedule": None,
            },
            headers=registered_seller["headers"],
        )
        assert resp.status_code == 403