from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import require_seller 
from app.schemas.menu_item_schema import MenuItemResponse
from app.services.catalog_service import CatalogService
from app.repositories.impl.menu_item_repository import MenuItemRepositoryImpl
from app.repositories.impl.umkm_repository import UMKMRepositoryImpl
from app.repositories.impl.promotion_repository import PromotionRepositoryImpl
from app.schemas.umkm_schema import UMKMResponse
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/products", tags=["Catalog"])

def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    return CatalogService(
        menu_repo=MenuItemRepositoryImpl(db), 
        umkm_repo=UMKMRepositoryImpl(db), 
        promo_repo=PromotionRepositoryImpl(db)
    )

@router.get("/my", response_model=List[MenuItemResponse])
async def get_my_products(
    seller_payload: dict = Depends(require_seller),
    service: CatalogService = Depends(get_catalog_service)
):
    """Menampilkan daftar menu khusus milik seller yang login (US-C01/C05)."""
    owner_id = int(seller_payload.get("sub"))
    return await service.get_my_products(owner_id)

@router.get("/", response_model=List[UMKMResponse])
async def list_all_umkm(service: CatalogService = Depends(get_catalog_service)):
    """Menampilkan semua UMKM aktif di katalog kampus[cite: 34]."""
    umkms = await service.list_all_umkm()
    return [UMKMResponse.from_domain(u) for u in umkms]

@router.get("/store/{umkm_id}", response_model=UMKMResponse)
async def get_umkm_profile(
    umkm_id: int,
    service: CatalogService = Depends(get_catalog_service)
):
    """Mendapatkan profil spesifik 1 kantin untuk header[cite: 34]."""
    try:
        umkm = await service.get_umkm_detail(umkm_id) 
        return UMKMResponse.from_domain(umkm)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/umkm/{umkm_id}", response_model=List[MenuItemResponse])
async def get_umkm_menu(
    umkm_id: int,
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    service: CatalogService = Depends(get_catalog_service)
):
    """Melihat menu kantin tertentu dengan filter[cite: 34]."""
    return await service.get_umkm_menu(umkm_id, keyword=keyword, category=category)

@router.post("/", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def add_product(
    name: str = Form(...),
    price: Decimal = Form(...),
    stock: int = Form(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    seller_payload: dict = Depends(require_seller), 
    service: CatalogService = Depends(get_catalog_service)
):
    """Menambah produk baru dengan upload foto."""
    owner_id = int(seller_payload.get("sub"))
    item = await service.add_product_v2(
        owner_id=owner_id, 
        name=name, 
        price=price, 
        stock=stock, 
        category=category, 
        description=description, 
        photo=photo
    )
    return MenuItemResponse.from_domain(item)

@router.put("/{item_id}", response_model=MenuItemResponse)
async def update_product(
    item_id: int,
    name: str = Form(...),
    price: Decimal = Form(...),
    stock: int = Form(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    seller_payload: dict = Depends(require_seller),
    service: CatalogService = Depends(get_catalog_service)
):
    """Memperbarui detail produk dan foto."""
    owner_id = int(seller_payload.get("sub"))
    item = await service.update_product_v2(
        owner_id=owner_id,
        item_id=item_id,
        name=name,
        price=price,
        stock=stock,
        category=category,
        description=description,
        photo=photo
    )
    return MenuItemResponse.from_domain(item)


@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_product_detail(
    item_id: int,
    service: CatalogService = Depends(get_catalog_service)
):
    """Mendapatkan detail satu produk[cite: 34]."""
    try:
        item = await service.get_product_detail(item_id)
        return MenuItemResponse.from_domain(item)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{item_id}", response_model=MenuItemResponse)
async def delete_product(
    item_id: int,
    seller_payload: dict = Depends(require_seller),
    service: CatalogService = Depends(get_catalog_service)
):
    """Soft delete produk[cite: 34]."""
    owner_id = int(seller_payload.get("sub"))
    item = await service.delete_product(owner_id=owner_id, item_id=item_id)
    return MenuItemResponse.from_domain(item)