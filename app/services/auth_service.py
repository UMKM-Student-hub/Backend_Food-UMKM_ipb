from datetime import timedelta
from app.repositories.interfaces.i_user_repository import IUserRepository
from app.domain.user import User
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import BusinessRuleViolationError, NotFoundError

class AuthService:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def register(self, request: RegisterRequest) -> User:
        """US-A01: Mendaftarkan akun baru dengan password terenkripsi."""
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
        """US-A02: Autentikasi pengguna dan pemberian Token JWT."""
        user = await self._user_repo.find_by_email(request.email)
        if not user:
            raise BusinessRuleViolationError("Email atau password salah.")

        if not verify_password(request.password, user.password_hash):
            raise BusinessRuleViolationError("Email atau password salah.")

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        return TokenResponse(
            access_token=access_token,
            role=user.role
        )
        
    async def get_current_user(self, user_id: int):
        user = await self._user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("User tidak ditemukan.")
        return user