import json
import os
import uuid
from datetime import datetime
from typing import List
from fastapi import UploadFile

from app.repositories.interfaces.i_order_repository import IOrderRepository
from app.repositories.interfaces.i_menu_item_repository import IMenuItemRepository
from app.repositories.interfaces.i_umkm_repository import IUMKMRepository
from app.repositories.interfaces.i_promotion_repository import IPromotionRepository
from app.domain.order import Order, OrderItem, OrderStatus
from app.core.exceptions import BusinessRuleViolationError, NotFoundError, PermissionDeniedError

class OrderService:
    def __init__(
        self, 
        order_repo: IOrderRepository, 
        menu_repo: IMenuItemRepository, 
        umkm_repo: IUMKMRepository,
        promo_repo: IPromotionRepository
    ):
        self._order_repo = order_repo
        self._menu_repo = menu_repo
        self._umkm_repo = umkm_repo
        self._promo_repo = promo_repo

    async def place_order(
        self, 
        buyer_id: int, 
        umkm_id: int, 
        items_json: str, 
        payment_method: str, 
        notes: str, 
        pickup_schedule: str, 
        payment_proof: UploadFile
    ) -> Order:
        try:
            parsed_items = json.loads(items_json)
        except json.JSONDecodeError:
            raise BusinessRuleViolationError("Format keranjang tidak valid.")

        if not parsed_items:
            raise BusinessRuleViolationError("Keranjang belanja tidak boleh kosong.")

        if payment_method == "Gopay" and not payment_proof:
            raise BusinessRuleViolationError("Bukti pembayaran Gopay wajib diunggah.")

        proof_url = None
        if payment_proof:
            upload_dir = "static/uploads/payments"
            os.makedirs(upload_dir, exist_ok=True)
            
            ext = payment_proof.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as f:
                f.write(await payment_proof.read())
            
            proof_url = f"/{file_path}"

        domain_items = []
        total_price = 0

        for req_item in parsed_items:
            menu_item_id = req_item.get("menu_item_id")
            quantity = req_item.get("quantity")
            item_notes = req_item.get("note", "")

            if not menu_item_id or not quantity or quantity <= 0:
                raise BusinessRuleViolationError("Data item pesanan tidak lengkap atau tidak valid.")

            menu_item = await self._menu_repo.find_by_id(menu_item_id)
            if not menu_item:
                raise NotFoundError(f"Menu item {menu_item_id} tidak ditemukan.")

            menu_item.reduce_stock(quantity)
            await self._menu_repo.update(menu_item)

            final_unit_price = menu_item.price
            
            active_promos = await self._promo_repo.find_active_by_menu_item(menu_item.id)
            if active_promos:
                promo = active_promos[0] 
                final_unit_price = promo.calculate_discounted_price(menu_item.price)

            order_item = OrderItem(
                menu_item_id=menu_item.id,
                menu_name=menu_item.name,
                unit_price=final_unit_price,
                quantity=quantity,
                notes=item_notes
            )
            domain_items.append(order_item)
            total_price += order_item.calculate_subtotal()

        dt_pickup = None
        if pickup_schedule:
            try:
                dt_pickup = datetime.fromisoformat(pickup_schedule.replace("Z", "+00:00"))
            except ValueError:
                pass

        new_order = Order(
            buyer_id=buyer_id,
            umkm_id=umkm_id,
            total_price=total_price,
            items=domain_items,
            notes=notes,
            payment_method=payment_method,
            payment_proof_url=proof_url,
            pickup_schedule=dt_pickup
        )

        return await self._order_repo.save(new_order)
    
    async def get_buyer_orders(self, buyer_id: int) -> List[Order]:
        return await self._order_repo.find_by_buyer(buyer_id)

    async def get_umkm_orders(self, owner_id: int) -> List[Order]:
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm:
            raise NotFoundError("Anda belum memiliki UMKM.")
        return await self._order_repo.find_by_umkm(umkm.id)

    async def confirm_order(self, order_id: int, owner_id: int) -> Order:
        order = await self._order_repo.find_by_id(order_id)
        if not order:
            raise NotFoundError("Pesanan tidak ditemukan.")
        
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm or order.umkm_id != umkm.id:
            raise PermissionDeniedError("Anda tidak memiliki akses ke pesanan ini.")
        
        order.confirm() 
        return await self._order_repo.update_status(order)

    async def reject_order(self, order_id: int, owner_id: int, reason: str) -> Order:
        order = await self._order_repo.find_by_id(order_id)
        if not order:
            raise NotFoundError("Pesanan tidak ditemukan.")
            
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm or order.umkm_id != umkm.id:
            raise PermissionDeniedError("Anda tidak berhak menolak pesanan ini.")
            
        order.reject(reason)
        for item in order.items:
            menu_item = await self._menu_repo.find_by_id(item.menu_item_id)
            if menu_item:
                menu_item.restore_stock(item.quantity)
                await self._menu_repo.update(menu_item)
                
        return await self._order_repo.update_status(order)

    async def mark_order_ready(self, order_id: int, owner_id: int) -> Order:
        order = await self._order_repo.find_by_id(order_id)
        if not order:
            raise NotFoundError("Pesanan tidak ditemukan.")
            
        umkm = await self._umkm_repo.find_by_owner(owner_id)
        if not umkm or order.umkm_id != umkm.id:
            raise PermissionDeniedError("Anda tidak memiliki akses ke pesanan ini.")
            
        order.mark_ready()
        return await self._order_repo.update_status(order)

    async def mark_order_done(self, order_id: int, buyer_id: int) -> Order:
        order = await self._order_repo.find_by_id(order_id)
        if not order:
            raise NotFoundError("Pesanan tidak ditemukan.")
            
        if order.buyer_id != buyer_id:
            raise PermissionDeniedError("Hanya pemesan asli yang dapat menyelesaikan pesanan ini.")
            
        order.mark_done()
        return await self._order_repo.update_status(order)