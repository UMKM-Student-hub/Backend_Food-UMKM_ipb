from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings

security = HTTPBearer()

async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Satpam yang memverifikasi keaslian dan masa berlaku JWT."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sesi Anda telah berakhir, silakan login kembali.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kredensial tidak valid.")

async def get_current_user_id(payload: dict = Depends(get_current_user_token)) -> int:
    """Mengambil ID User dari tiket JWT yang sudah divalidasi."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Informasi user tidak ditemukan di dalam token.")
    return int(user_id)

async def require_seller(payload: dict = Depends(get_current_user_token)) -> dict:
    """Membatasi akses khusus hanya untuk penjual (UMKM)."""
    if payload.get("role") != "SELLER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak. Fitur ini khusus penjual.")
    return payload