import os
import shutil
from uuid import uuid4
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import UploadFile

from app.repositories.interfaces.i_promotion_repository import IPromotionRepository
from app.repositories.interfaces.i_menu_item_repository import IMenuItemRepository
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.domain.promotion import Promotion
from app.core.exceptions import NotFoundError, BusinessRuleViolationError, PermissionDeniedError

class PromoService:
    def __init__(self, promo_repo: IPromotionRepository, menu_repo: IMenuItemRepository, umkm_repo: IUMKMRepository):
        self._promo_repo = promo_repo
        self._menu_repo = menu_repo
        self._umkm_repo = umkm_repo

    async def list_active_promos(self) -> List[Promotion]:
        return await self._promo_repo.find_active()

    async def get_promos_by_umkm(self, owner_id: int) -> List[Promotion]:
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise NotFoundError("Profil Kantin tidak ditemukan. Silakan atur kantin terlebih dahulu.")
        return await self._promo_repo.find_by_umkm(umkm.id)

    async def create_promo_with_file(
        self, 
        owner_id: int, 
        menu_item_id: int, 
        name: str, 
        discount_type: str, 
        discount_value: Decimal, 
        start_date: date, 
        end_date: date, 
        photo: Optional[UploadFile]
    ) -> Promotion:
        
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise BusinessRuleViolationError("Anda harus mengatur profil Kantin terlebih dahulu sebelum dapat membuat promo.")

        menu_item = await self._menu_repo.find_by_id(menu_item_id)
        if not menu_item:
            raise NotFoundError("Menu tidak ditemukan.")
        if menu_item.umkm_id != umkm.id:
            raise PermissionDeniedError("Akses ditolak. Menu ini bukan milik kantin Anda.")

        photo_url = None
        if photo and photo.filename:
            file_ext = os.path.splitext(photo.filename)[1].lower()
            allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
            if file_ext not in allowed_exts:
                raise BusinessRuleViolationError("Format gambar tidak didukung. Gunakan JPG, PNG, atau WEBP.")
                
            unique_name = f"{uuid4()}{file_ext}"
            directory = "static/uploads/promos"
            path = os.path.join(directory, unique_name)
            
            os.makedirs(directory, exist_ok=True)
            with open(path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
            
            photo_url = f"/{path}".replace("\\", "/")

        promo = Promotion(
            umkm_id=umkm.id, 
            menu_item_id=menu_item_id,
            name=name,
            photo_url=photo_url,
            discount_type=discount_type,
            discount_value=discount_value,
            start_date=start_date,
            end_date=end_date
        )
        promo.validate()
        
        return await self._promo_repo.save(promo)

    async def deactivate_promo(self, promo_id: int, owner_id: int) -> Promotion:
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise NotFoundError("Profil Kantin tidak ditemukan.")

        promo = await self._promo_repo.find_by_id(promo_id)
        if not promo:
            raise NotFoundError("Promo tidak ditemukan.")
        
        if promo.umkm_id != umkm.id:
            raise PermissionDeniedError("Akses ditolak. Anda tidak berhak menonaktifkan promo ini.")
            
        promo.is_active = False
        return await self._promo_repo.update(promo)