from app.repositories.interfaces.i_user_repository import IUserRepository
from app.domain.user import User
from app.schemas.user_schema import UserRegisterRequest
from app.core.exceptions import BusinessRuleViolationError

class UserService:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def register_user(self, request: UserRegisterRequest) -> User:
        existing_user = await self._user_repo.find_by_email(request.email)
        if existing_user:
            raise BusinessRuleViolationError("Email ini sudah terdaftar.")

        new_user = User(
            name=request.name,
            email=request.email,
            password_hash=request.password,
            phone=request.phone,
            role=request.role
        )
        
        new_user.validate_before_save()

        return await self._user_repo.save(new_user)