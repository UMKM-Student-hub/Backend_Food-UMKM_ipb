from typing import List
from app.repositories.interfaces.i_review_repository import IReviewRepository
from app.repositories.interfaces.i_order_repository import IOrderRepository
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.domain.review import Review
from app.domain.order import OrderStatus
from app.schemas.review_schema import ReviewCreateRequest
from app.core.exceptions import BusinessRuleViolationError, NotFoundError, PermissionDeniedError

class ReviewService:
    def __init__(self, review_repo: IReviewRepository, order_repo: IOrderRepository, umkm_repo: IUMKMRepository):
        self._review_repo = review_repo
        self._order_repo = order_repo
        self._umkm_repo = umkm_repo

    async def submit_review(self, buyer_id: int, request: ReviewCreateRequest) -> Review:
        """US-R01: Pembeli memberikan ulasan pada pesanan selesai."""
        
        order = await self._order_repo.find_by_id(request.order_id)
        if not order:
            raise NotFoundError("Pesanan tidak ditemukan.")

        if order.buyer_id != buyer_id:
            raise PermissionDeniedError("Anda tidak berhak mengulas pesanan ini.")

        if order.status != OrderStatus.DONE:
            raise BusinessRuleViolationError("Ulasan hanya dapat diberikan untuk pesanan yang sudah selesai diambil.")

        is_reviewed = await self._review_repo.exists_by_order_id(order.id)
        if is_reviewed:
            raise BusinessRuleViolationError("Anda sudah memberikan ulasan untuk pesanan ini.")

        valid_menu_ids = [item.menu_item_id for item in order.items]
        if request.menu_item_id not in valid_menu_ids:
            raise BusinessRuleViolationError("Menu yang Anda ulas tidak terdapat dalam pesanan ini.")

        review = Review(
            order_id=order.id,
            buyer_id=buyer_id,
            menu_item_id=request.menu_item_id,
            rating=request.rating,
            comment=request.comment
        )
        review.validate()

        return await self._review_repo.save(review)

    async def get_product_reviews(self, menu_item_id: int) -> List[Review]:
        """US-R02: Mengambil ulasan produk untuk ditampilkan di Katalog."""
        return await self._review_repo.find_by_menu_item(menu_item_id)

    async def get_umkm_reviews(self, owner_id: int) -> List[Review]:
        """US-R03: Pemilik UMKM melihat semua ulasan produknya di Dashboard."""
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise NotFoundError("UMKM tidak ditemukan untuk akun ini.")
        
        return await self._review_repo.find_by_umkm(umkm.id)

    async def get_product_average_rating(self, menu_item_id: int) -> float:
        """Menghitung rata-rata rating untuk satu produk (US-R03)."""
        return await self._review_repo.calculate_average_rating(menu_item_id)