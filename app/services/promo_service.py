from typing import List
from app.repositories.interfaces.i_promotion_repository import IPromotionRepository
from app.repositories.interfaces.i_menu_item_repository import IMenuItemRepository
from app.domain.promotion import Promotion
from app.schemas.promo_schema import PromoCreateRequest
from app.core.exceptions import NotFoundError, BusinessRuleViolationError

class PromoService:
    def __init__(self, promo_repo: IPromotionRepository, menu_repo: IMenuItemRepository):
        self._promo_repo = promo_repo
        self._menu_repo = menu_repo

    async def list_active_promos(self) -> List[Promotion]:
        """US-P01: Mengambil semua promo yang sedang aktif."""
        return await self._promo_repo.find_active()

    async def get_promos_by_umkm(self, owner_id: int) -> List[Promotion]:
        """US-P02 (opsional): Mengambil daftar promo buatan UMKM ini."""
        return await self._promo_repo.find_by_umkm(owner_id)

    async def create_promo(self, owner_id: int, request: PromoCreateRequest) -> Promotion:
        """US-P03: Membuat promo baru."""
        menu_item = await self._menu_repo.find_by_id(request.menu_item_id)
        if not menu_item:
            raise NotFoundError("Menu item tidak ditemukan.")
        
        promo = Promotion(
            umkm_id=owner_id, 
            menu_item_id=request.menu_item_id,
            name=request.name,
            discount_type=request.discount_type,
            discount_value=request.discount_value,
            start_date=request.start_date,
            end_date=request.end_date
        )
        promo.validate()
        
        return await self._promo_repo.save(promo)

    async def deactivate_promo(self, promo_id: int, owner_id: int) -> Promotion:
        """US-P04: Menonaktifkan promo sebelum tanggalnya kedaluwarsa."""
        promo = await self._promo_repo.find_by_id(promo_id)
        if not promo:
            raise NotFoundError("Promo tidak ditemukan.")
        
        promo.deactivate()
        return await self._promo_repo.update(promo)