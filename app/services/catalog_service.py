import os
from typing import List, Optional
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

from app.domain.umkm import UMKM
from app.repositories.interfaces.i_menu_item_repository import IMenuItemRepository
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.repositories.interfaces.i_promotion_repository import IPromotionRepository
from app.domain.menu_item import MenuItem
from app.schemas.menu_item_schema import MenuItemResponse
from app.core.exceptions import NotFoundError, PermissionDeniedError, BusinessRuleViolationError

class CatalogService:
    def __init__(self, menu_repo: IMenuItemRepository, umkm_repo: IUMKMRepository, promo_repo: IPromotionRepository):
        self._menu_repo = menu_repo
        self._umkm_repo = umkm_repo
        self._promo_repo = promo_repo

    async def list_all_umkm(self) -> List[UMKM]:
        return await self._umkm_repo.find_all()

    async def get_umkm_detail(self, umkm_id: int) -> UMKM:
        umkm = await self._umkm_repo.find_by_id(umkm_id)
        if not umkm:
            raise NotFoundError(f"Kantin dengan ID {umkm_id} tidak ditemukan.")
        return umkm

    async def get_product_detail(self, item_id: int) -> MenuItem:
        item = await self._menu_repo.find_by_id(item_id)
        if not item:
            raise NotFoundError(f"Menu dengan ID {item_id} tidak ditemukan.")
        return item

    async def get_umkm_menu(self, umkm_id: int, keyword: Optional[str] = None, category: Optional[str] = None):
        products = await self._menu_repo.find_by_umkm(umkm_id)
        
        if keyword:
            kw = keyword.lower()
            products = [p for p in products if kw in p.name.lower() or (p.description and kw in p.description.lower())]
            
        if category:
            cat = category.lower()
            products = [p for p in products if str(p.category).lower() == cat]
        
        return [MenuItemResponse.from_domain(p, (await self._promo_repo.find_active_by_menu_item(p.id))[0] if (await self._promo_repo.find_active_by_menu_item(p.id)) else None) for p in products]

    async def get_my_products(self, owner_id: int):
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise BusinessRuleViolationError("Anda belum mendaftarkan toko UMKM.")
            
        products = await self._menu_repo.find_by_umkm(umkm.id)
        
        results = []
        for p in products:
            promos = await self._promo_repo.find_active_by_menu_item(p.id)
            active_promo = promos[0] if promos else None
            results.append(MenuItemResponse.from_domain(p, active_promo))
            
        return results

    async def add_product_v2(self, owner_id, name, price, stock, category, description, photo: Optional[UploadFile]):
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise BusinessRuleViolationError("Daftarkan UMKM terlebih dahulu.")
        
        photo_url = None
        if photo and photo.filename:
            result = cloudinary.uploader.upload(
                photo.file,
                folder="unibites/menus"
            )
            photo_url = result["secure_url"]

        new_item = MenuItem(
            umkm_id=umkm.id, name=name, price=price, 
            stock=stock, category=category, description=description, 
            photo_url=photo_url
        )
        return await self._menu_repo.save(new_item)

    async def update_product_v2(self, owner_id, item_id, name, price, stock, category, description, photo: Optional[UploadFile]):
        item = await self._menu_repo.find_by_id(item_id)
        if not item:
            raise NotFoundError("Produk tidak ditemukan.")
            
        umkm = await self._umkm_repo.find_by_id(item.umkm_id)
        if not umkm or not umkm.is_owned_by(owner_id):
            raise PermissionDeniedError("Anda tidak memiliki akses.")

        if photo and photo.filename:
            result = cloudinary.uploader.upload(
                photo.file,
                folder="unibites/menus"
            )
            item.photo_url = result["secure_url"]

        item.name = name
        item.price = price
        item.stock = stock
        item.category = category
        item.description = description
        
        return await self._menu_repo.update(item)

    async def delete_product(self, owner_id: int, item_id: int) -> MenuItem:
        item = await self._menu_repo.find_by_id(item_id)
        if not item or not (await self._umkm_repo.find_by_id(item.umkm_id)).is_owned_by(owner_id):
            raise PermissionDeniedError("Akses ditolak.")
            
        item.deactivate_product()
        return await self._menu_repo.update(item)