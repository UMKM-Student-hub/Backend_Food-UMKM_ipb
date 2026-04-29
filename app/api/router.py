from fastapi import APIRouter
from app.controllers.auth_controller import router as auth_router
from app.controllers.umkm_controller import router as umkm_router
from app.controllers.user_controller import router as user_router
from app.controllers.catalog_controller import router as catalog_router
from app.controllers.order_controller import router as order_router
from app.controllers.promo_controller import router as promo_router
from app.controllers.review_controller import router as review_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(umkm_router)
api_router.include_router(catalog_router)
api_router.include_router(order_router)
api_router.include_router(promo_router)
api_router.include_router(review_router)