from app.core.exceptions import NotFoundError
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.menu_item_schema import MenuItemCreateRequest, MenuItemResponse
from app.services.catalog_service import CatalogService
from app.repositories.impl.menu_item_repository import MenuItemRepositoryImpl
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.repositories.impl.promotion_repository import PromotionRepositoryImpl
from app.schemas.umkm_schema import UMKMResponse

router = APIRouter(prefix="/products", tags=["Catalog"])

def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    menu_repo = MenuItemRepositoryImpl(db)
    umkm_repo = UMKMRepositoryImpl(db)
    promo_repo = PromotionRepositoryImpl(db)
    return CatalogService(menu_repo=menu_repo, umkm_repo=umkm_repo, promo_repo=promo_repo)

@router.get("/search", response_model=List[MenuItemResponse])
async def search_products(
    keyword: Optional[str] = Query(None, description="Cari berdasarkan nama menu"),
    category: Optional[str] = Query(None, description="Filter berdasarkan kategori"),
    service: CatalogService = Depends(get_catalog_service)
):
    items = await service.search_products(keyword=keyword, category=category)
    return items

@router.get("/umkm/{umkm_id}", response_model=List[MenuItemResponse])
async def get_umkm_menu(
    umkm_id: int,
    service: CatalogService = Depends(get_catalog_service)
):
    items = await service.get_umkm_menu(umkm_id)
    return items

@router.post("/", response_model=MenuItemResponse)
async def add_product(
    request: MenuItemCreateRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: CatalogService = Depends(get_catalog_service)
):
    item = await service.add_product(owner_id=current_user_id, request=request)
    return MenuItemResponse.from_domain(item)

@router.patch("/{item_id}/stock", response_model=MenuItemResponse)
async def update_stock(
    item_id: int,
    new_stock: int = Query(..., ge=0, description="Jumlah stok terbaru"),
    current_user_id: int = Depends(get_current_user_id),
    service: CatalogService = Depends(get_catalog_service)
):
    item = await service.update_stock(owner_id=current_user_id, item_id=item_id, new_stock=new_stock)
    return MenuItemResponse.from_domain(item)

@router.delete("/{item_id}", response_model=MenuItemResponse)
async def delete_product(
    item_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: CatalogService = Depends(get_catalog_service)
):
    item = await service.delete_product(owner_id=current_user_id, item_id=item_id)
    return MenuItemResponse.from_domain(item)

@router.patch("/{item_id}/reactivate", response_model=MenuItemResponse)
async def reactivate_product(
    item_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: CatalogService = Depends(get_catalog_service)
):
    item = await service.reactivate_product(owner_id=current_user_id, item_id=item_id)
    return MenuItemResponse.from_domain(item)

@router.get("/", response_model=List[UMKMResponse])
async def list_all_umkm(
    service: CatalogService = Depends(get_catalog_service)
):
    umkms = await service.list_all_umkm()
    return [UMKMResponse.from_domain(u) for u in umkms]

@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_product_detail(
    item_id: int,
    service: CatalogService = Depends(get_catalog_service)
):
    item = await service.get_product_detail(item_id)
    return MenuItemResponse.from_domain(item)