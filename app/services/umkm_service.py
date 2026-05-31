from typing import List
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.domain.umkm import UMKM
from app.schemas.umkm_schema import UMKMCreateRequest, OperatingHoursUpdate
from app.core.exceptions import NotFoundError, BusinessRuleViolationError

class UMKMService:
    def __init__(self, umkm_repo: IUMKMRepository):
        self._umkm_repo = umkm_repo

    async def create_umkm(self, owner_id: int, request: UMKMCreateRequest) -> UMKM:
        existing = await self._umkm_repo.find_by_owner(owner_id)
        if existing:
            raise BusinessRuleViolationError("Satu akun hanya boleh mendaftarkan satu UMKM.")
        new_umkm = UMKM(
            owner_id=owner_id,
            name=request.name,
            description=request.description,
            location=request.location,
        )
        return await self._umkm_repo.save(new_umkm)

    async def register_umkm(self, owner_id: int, request: UMKMCreateRequest) -> UMKM:
        return await self.create_umkm(owner_id, request)

    async def get_my_store(self, owner_id: int) -> UMKM:
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise NotFoundError("Anda belum mendaftarkan toko UMKM.")
        return umkm

    async def get_umkm_by_id(self, umkm_id: int) -> UMKM:
        umkm = await self._umkm_repo.find_by_id(umkm_id)
        if not umkm:
            raise NotFoundError(f"UMKM dengan ID {umkm_id} tidak ditemukan.")
        return umkm

    async def list_all_umkm(self) -> List[UMKM]:
        return await self._umkm_repo.find_all()

    async def update_operating_hours(
        self, owner_id: int, request: OperatingHoursUpdate
    ) -> UMKM:
        """
        Simpan jadwal jam operasional. is_open akan dihitung otomatis
        setiap kali data UMKM di-fetch.
        """
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise NotFoundError("UMKM tidak ditemukan untuk akun ini.")

        umkm.operating_hours = request.to_dict()
        return await self._umkm_repo.update(umkm)