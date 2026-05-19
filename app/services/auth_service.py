from typing import Optional
from datetime import timedelta
from app.repositories.interfaces.i_user_repository import IUserRepository
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.domain.user import User
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import BusinessRuleViolationError, NotFoundError

class AuthService:
    def __init__(self, user_repo: IUserRepository, umkm_repo: Optional[IUMKMRepository] = None):
        self._user_repo = user_repo
        self._umkm_repo = umkm_repo

    async def register(self, request: RegisterRequest) -> User:
        existing_user = await self._user_repo.find_by_email(request.email)
        if existing_user:
            raise BusinessRuleViolationError("Email ini sudah terdaftar.")

        new_user = User(
            name=request.name,
            email=request.email,
            password_hash=get_password_hash(request.password),
            phone=request.phone,
            role=request.role
        )
        
        new_user.validate()
        return await self._user_repo.save(new_user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self._user_repo.find_by_email(request.email)
        if not user or not verify_password(request.password, user.password_hash):
            raise BusinessRuleViolationError("Email atau password salah.")

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        return TokenResponse(
            access_token=access_token,
            role=user.role
        )
        
    async def get_current_user(self, user_id: int) -> User:
        user = await self._user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("User tidak ditemukan.")
        return user

    async def update_user_profile(self, user_id: int, data: dict) -> User:
        user = await self._user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("User tidak ditemukan.")
        
        if "name" in data and data["name"] is not None:
            user.name = data["name"]
        if "phone" in data and data["phone"] is not None:
            user.phone = data["phone"]
            
        await self._user_repo.update(user)
        return user

    async def get_seller_profile(self, user_id: int) -> dict:
        user = await self._user_repo.find_by_id(user_id)
        umkm = await self._umkm_repo.find_by_owner(user_id)
        
        if not user or not umkm:
            raise NotFoundError("Data profil atau UMKM tidak ditemukan.")
            
        return {
            "umkmName": umkm.name,
            "email": user.email,
            "ownerName": user.name,
            "phone": user.phone,
            "location": umkm.location or ""
        }

    async def update_seller_profile(self, user_id: int, data: dict) -> dict:
        user = await self._user_repo.find_by_id(user_id)
        umkm = await self._umkm_repo.find_by_owner(user_id)
        
        if not user or not umkm:
            raise NotFoundError("Data profil atau UMKM tidak ditemukan.")
            
        if "ownerName" in data and data["ownerName"] is not None:
            user.name = data["ownerName"]
        if "phone" in data and data["phone"] is not None:
            user.phone = data["phone"]
        await self._user_repo.update(user)
        
        if "umkmName" in data and data["umkmName"] is not None:
            umkm.name = data["umkmName"]
        if "location" in data and data["location"] is not None:
            umkm.location = data["location"]
        await self._umkm_repo.update(umkm)
        
        return {
            "umkmName": umkm.name,
            "email": user.email,
            "ownerName": user.name,
            "phone": user.phone,
            "location": umkm.location or ""
        }