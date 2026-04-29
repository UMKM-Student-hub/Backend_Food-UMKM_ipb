from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Mengecek apakah password input cocok dengan hash di database."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    """Mengenkripsi password sebelum disimpan ke database."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8') 

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Membuat tiket masuk (JWT) yang akan dibawa oleh Frontend."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=1)
        
    to_encode.update({"exp": expire})
    
    secret_key = getattr(settings, "SECRET_KEY", "unibites_super_secret_key_123")
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt