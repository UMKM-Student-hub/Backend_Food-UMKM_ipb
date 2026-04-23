from typing import List, Optional
from app.domain.umkm import UMKM
from app.repositories.interfaces.i_menu_item_repository import IMenuItemRepository
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.domain.menu_item import MenuItem
from app.schemas.menu_item_schema import MenuItemCreateRequest
from app.core.exceptions import NotFoundError, PermissionDeniedError, BusinessRuleViolationError

class CatalogService:
    def __init__(self, menu_repo: IMenuItemRepository, umkm_repo: IUMKMRepository):
        self._menu_repo = menu_repo
        self._umkm_repo = umkm_repo

    async def search_products(self, keyword: Optional[str] = None, category: Optional[str] = None) -> List[MenuItem]:
        return await self._menu_repo.search(keyword=keyword, category=category)

    async def get_umkm_menu(self, umkm_id: int) -> List[MenuItem]:
        umkm = await self._umkm_repo.find_by_id(umkm_id)
        if not umkm:
            raise NotFoundError("Toko UMKM tidak ditemukan.")
        return await self._menu_repo.find_by_umkm(umkm_id)

    async def add_product(self, owner_id: int, request: MenuItemCreateRequest) -> MenuItem:
        # 1. Cari UMKM milik penjual yang sedang login
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise BusinessRuleViolationError("Anda harus mendaftarkan toko UMKM terlebih dahulu sebelum menambah produk.")
        
        # 2. Buat objek domain produk baru
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
            
        # Validasi keamanan: Pastikan produk ini benar milik penjual yang sedang login
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
            
        # Menerapkan Soft Delete memanggil method domain
        item.deactivate_product()
        return await self._menu_repo.update(item)
    
    async def reactivate_product(self, owner_id: int, item_id: int) -> MenuItem:
        item = await self._menu_repo.find_by_id(item_id)
        if not item:
            raise NotFoundError("Produk tidak ditemukan.")
            
        # Validasi keamanan: Pastikan produk ini benar milik penjual yang sedang login
        umkm = await self._umkm_repo.find_by_id(item.umkm_id)
        if not umkm or not umkm.is_owned_by(owner_id):
            raise PermissionDeniedError("Anda tidak berhak mengaktifkan produk ini.")
            
        # Memanggil method domain untuk mengubah is_active = True
        item.activate_product()
        return await self._menu_repo.update(item)
    
    async def list_all_umkm(self) -> List[UMKM]:
        return await self._umkm_repo.find_all()
    
    async def get_product_detail(self, item_id: int) -> MenuItem:
        """Mengambil detail satu produk spesifik (US-C03)."""
        item = await self._menu_repo.find_by_id(item_id)
        if not item:
            raise NotFoundError("Produk tidak ditemukan di katalog.")
        return item