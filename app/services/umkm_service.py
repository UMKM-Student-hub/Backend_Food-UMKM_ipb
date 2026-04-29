from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.domain.umkm import UMKM
from app.schemas.umkm_schema import UMKMCreateRequest
from app.core.exceptions import BusinessRuleViolationError, PermissionDeniedError, NotFoundError

class UMKMService:
    def __init__(self, umkm_repo: IUMKMRepository):
        self._umkm_repo = umkm_repo

    async def register_umkm(self, owner_id: int, request: UMKMCreateRequest) -> UMKM:
        existing_umkm = await self._umkm_repo.find_by_owner(owner_id)
        if existing_umkm:
            raise BusinessRuleViolationError("Satu akun hanya boleh mendaftarkan satu UMKM.")

        new_umkm = UMKM(
            owner_id=owner_id,
            name=request.name,
            description=request.description,
            location=request.location
        )
        return await self._umkm_repo.save(new_umkm)

    async def toggle_status(self, umkm_id: int, requester_id: int) -> UMKM:
        umkm = await self._umkm_repo.find_by_id(umkm_id)
        if not umkm:
            raise NotFoundError("Toko UMKM tidak ditemukan.")
            
        if not umkm.is_owned_by(requester_id):
            raise PermissionDeniedError("Anda tidak memiliki akses untuk mengubah toko ini.")

        if umkm.is_open:
            umkm.close_store()
        else:
            umkm.open_store()

        return await self._umkm_repo.update(umkm)