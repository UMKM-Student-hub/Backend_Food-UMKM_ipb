# app/controllers/catalog_controller.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import require_seller 
from app.schemas.menu_item_schema import MenuItemCreateRequest, MenuItemResponse
from app.services.catalog_service import CatalogService
from app.repositories.impl.menu_item_repository import MenuItemRepositoryImpl
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.repositories.impl.promotion_repository import PromotionRepositoryImpl
from app.schemas.umkm_schema import UMKMResponse
from app.core.exceptions import BusinessRuleViolationError, NotFoundError

router = APIRouter(prefix="/products", tags=["Catalog"])

def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    return CatalogService(
        menu_repo=MenuItemRepositoryImpl(db), 
        umkm_repo=UMKMRepositoryImpl(db), 
        promo_repo=PromotionRepositoryImpl(db)
    )

@router.get("/", response_model=List[UMKMResponse])
async def list_all_umkm(service: CatalogService = Depends(get_catalog_service)):
    """Menampilkan semua UMKM di katalog."""
    umkms = await service.list_all_umkm()
    return [UMKMResponse.from_domain(u) for u in umkms]

@router.get("/store/{umkm_id}", response_model=UMKMResponse)
async def get_umkm_profile(
    umkm_id: int,
    service: CatalogService = Depends(get_catalog_service)
):
    """Mendapatkan profil spesifik 1 kantin/UMKM (Untuk header halaman)."""
    try:
        umkm = await service.get_umkm_detail(umkm_id) 
        return UMKMResponse.from_domain(umkm)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/umkm/{umkm_id}", response_model=List[MenuItemResponse])
async def get_umkm_menu(
    umkm_id: int,
    keyword: Optional[str] = Query(None, description="Cari menu di kantin ini"),
    category: Optional[str] = Query(None, description="Filter kategori menu"),
    service: CatalogService = Depends(get_catalog_service)
):
    """Melihat menu dari satu UMKM spesifik dengan dukungan search bar & kategori."""
    items = await service.get_umkm_menu(umkm_id, keyword=keyword, category=category)
    return items

@router.get("/search", response_model=List[MenuItemResponse])
async def search_products_global(
    keyword: Optional[str] = Query(None, description="Cari berdasarkan nama menu"),
    category: Optional[str] = Query(None, description="Filter berdasarkan kategori"),
    service: CatalogService = Depends(get_catalog_service)
):
    """Mencari produk secara global di seluruh kampus."""
    items = await service.search_products(keyword=keyword, category=category)
    return items

@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_product_detail(
    item_id: int,
    service: CatalogService = Depends(get_catalog_service)
):
    """Melihat detail satu produk."""
    try:
        item = await service.get_product_detail(item_id)
        return MenuItemResponse.from_domain(item)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def add_product(
    request: MenuItemCreateRequest,
    seller_payload: dict = Depends(require_seller), 
    service: CatalogService = Depends(get_catalog_service)
):
    owner_id = int(seller_payload.get("sub"))
    item = await service.add_product(owner_id=owner_id, request=request)
    return MenuItemResponse.from_domain(item)

@router.patch("/{item_id}/stock", response_model=MenuItemResponse)
async def update_stock(
    item_id: int,
    new_stock: int = Query(..., ge=0, description="Jumlah stok terbaru"),
    seller_payload: dict = Depends(require_seller),
    service: CatalogService = Depends(get_catalog_service)
):
    owner_id = int(seller_payload.get("sub"))
    item = await service.update_stock(owner_id=owner_id, item_id=item_id, new_stock=new_stock)
    return MenuItemResponse.from_domain(item)

@router.delete("/{item_id}", response_model=MenuItemResponse)
async def delete_product(
    item_id: int,
    seller_payload: dict = Depends(require_seller),
    service: CatalogService = Depends(get_catalog_service)
):
    owner_id = int(seller_payload.get("sub"))
    item = await service.delete_product(owner_id=owner_id, item_id=item_id)
    return MenuItemResponse.from_domain(item)

@router.patch("/{item_id}/reactivate", response_model=MenuItemResponse)
async def reactivate_product(
    item_id: int,
    seller_payload: dict = Depends(require_seller),
    service: CatalogService = Depends(get_catalog_service)
):
    owner_id = int(seller_payload.get("sub"))
    item = await service.reactivate_product(owner_id=owner_id, item_id=item_id)
    return MenuItemResponse.from_domain(item)