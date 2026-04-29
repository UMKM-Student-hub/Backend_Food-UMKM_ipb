import pytest
from httpx import AsyncClient, ASGITransport
from main import app

# Siapkan data dummy yang akan digunakan lintas tes
DUMMY_USER = {
    "name": "Mahasiswa Lapar",
    "email": "mahasiswa@student.ipb.ac.id",
    "password": "passwordAman123",
    "phone": "081234567890",
    "role": "BUYER"
}

# Variabel global untuk menyimpan token hasil login
ACCESS_TOKEN = ""

@pytest.mark.asyncio
async def test_health_check():
    """Tes 1: Memastikan API menyala dengan baik."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_e2e_register_buyer():
    """Tes 2: Skenario pendaftaran akun baru (US-A01)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/register", json=DUMMY_USER)
        
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == DUMMY_USER["email"]
    assert data["role"] == "BUYER"
    assert "password" not in data # Pastikan password tidak bocor

@pytest.mark.asyncio
async def test_e2e_login_buyer():
    """Tes 3: Skenario login untuk mendapatkan JWT (US-A02)."""
    global ACCESS_TOKEN
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/login", json={
            "email": DUMMY_USER["email"],
            "password": DUMMY_USER["password"]
        })
        
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Simpan token untuk digunakan di tes selanjutnya
    ACCESS_TOKEN = data["access_token"]

@pytest.mark.asyncio
async def test_e2e_access_protected_route():
    """Tes 4: Skenario mengakses endpoint dengan Authorization Header."""
    # Kita tes menembak endpoint pencarian produk (US-C02) 
    # Pastikan endpoint ini di controller membutuhkan 'get_current_user_id'
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Menembak endpoint search dengan header JWT
        response = await ac.get("/api/v1/products/search?keyword=ayam", headers=headers)
        
    # Asumsi: Jika token valid, minimal akan mengembalikan status 200 (walaupun list produknya kosong)
    assert response.status_code == 200 
    assert isinstance(response.json(), list) # Harus mengembalikan bentuk Array/List