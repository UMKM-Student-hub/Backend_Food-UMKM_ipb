from typing import List, Optional
from app.domain.umkm import UMKM
from app.repositories.interfaces.i_menu_item_repository import IMenuItemRepository
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.repositories.interfaces.i_promotion_repository import IPromotionRepository
from app.domain.menu_item import MenuItem
from app.schemas.menu_item_schema import MenuItemCreateRequest, MenuItemResponse
from app.core.exceptions import NotFoundError, PermissionDeniedError, BusinessRuleViolationError

class CatalogService:
    def __init__(self, menu_repo: IMenuItemRepository, umkm_repo: IUMKMRepository, promo_repo: IPromotionRepository):
        self._menu_repo = menu_repo
        self._umkm_repo = umkm_repo
        self._promo_repo = promo_repo

    async def list_all_umkm(self) -> List[UMKM]:
        """Mengambil semua daftar UMKM (US-C01)."""
        return await self._umkm_repo.find_all()

    async def get_umkm_detail(self, umkm_id: int) -> UMKM:
        """Mengambil detail profil 1 UMKM spesifik untuk header halaman."""
        umkm = await self._umkm_repo.find_by_id(umkm_id)
        if not umkm:
            raise NotFoundError(f"Kantin/UMKM dengan ID {umkm_id} tidak ditemukan.")
        return umkm

    async def get_umkm_menu(self, umkm_id: int, keyword: Optional[str] = None, category: Optional[str] = None):
        """Melihat menu UMKM dengan dukungan filter lokal (US-C01)."""
        products = await self._menu_repo.find_by_umkm(umkm_id)
        
        if keyword:
            kw = keyword.lower()
            products = [
                p for p in products 
                if kw in p.name.lower() or (p.description and kw in p.description.lower())
            ]
            
        if category:
            cat = category.lower()
            products = [
                p for p in products 
                if (hasattr(p.category, 'value') and p.category.value.lower() == cat) or (str(p.category).lower() == cat)
            ]
        
        results = []
        for p in products:
            promos = await self._promo_repo.find_active_by_menu_item(p.id)
            active_promo = promos[0] if promos else None
            results.append(MenuItemResponse.from_domain(p, active_promo))
            
        return results

    async def search_products(self, keyword: Optional[str], category: Optional[str]):
        """Mencari produk secara global dan menyisipkan data promo (US-C02)."""
        products = await self._menu_repo.search(keyword, category)
        
        results = []
        for p in products:
            promos = await self._promo_repo.find_active_by_menu_item(p.id)
            active_promo = promos[0] if promos else None
            results.append(MenuItemResponse.from_domain(p, active_promo))
            
        return results
        
    async def get_product_detail(self, item_id: int) -> MenuItem:
        """Mengambil detail satu produk spesifik (US-C03)."""
        item = await self._menu_repo.find_by_id(item_id)
        if not item:
            raise NotFoundError("Produk tidak ditemukan di katalog.")
        return item

    async def add_product(self, owner_id: int, request: MenuItemCreateRequest) -> MenuItem:
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise BusinessRuleViolationError("Anda harus mendaftarkan toko UMKM terlebih dahulu sebelum menambah produk.")
        
        new_item = MenuItem(
            umkm_id=umkm.id,
            name=request.name,
            price=request.price,
            stock=request.stock,
            description=request.description,
            photo_url=request.photo_url,
            category=request.category
        )
        return await self._menu_repo.save(new_item)

    async def update_stock(self, owner_id: int, item_id: int, new_stock: int) -> MenuItem:
        item = await self._menu_repo.find_by_id(item_id)
        if not item:
            raise NotFoundError("Produk tidak ditemukan.")
            
        umkm = await self._umkm_repo.find_by_id(item.umkm_id)
        if not umkm or not umkm.is_owned_by(owner_id):
            raise PermissionDeniedError("Anda tidak memiliki akses untuk mengubah produk ini.")
            
        if new_stock < 0:
            raise BusinessRuleViolationError("Stok tidak boleh kurang dari 0.")
            
        item.stock = new_stock
        return await self._menu_repo.update(item)

    async def delete_product(self, owner_id: int, item_id: int) -> MenuItem:
        item = await self._menu_repo.find_by_id(item_id)
        if not item:
            raise NotFoundError("Produk tidak ditemukan.")
            
        umkm = await self._umkm_repo.find_by_id(item.umkm_id)
        if not umkm or not umkm.is_owned_by(owner_id):
            raise PermissionDeniedError("Anda tidak berhak menghapus produk ini.")
            
        item.deactivate_product()
        return await self._menu_repo.update(item)
    
    async def reactivate_product(self, owner_id: int, item_id: int) -> MenuItem:
        item = await self._menu_repo.find_by_id(item_id)
        if not item:
            raise NotFoundError("Produk tidak ditemukan.")
            
        umkm = await self._umkm_repo.find_by_id(item.umkm_id)
        if not umkm or not umkm.is_owned_by(owner_id):
            raise PermissionDeniedError("Anda tidak berhak mengaktifkan produk ini.")
            
        item.activate_product()
        return await self._menu_repo.update(item)