from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.db.orders import OrderHeader, OrderLine
from repository.base import BaseCRUDRepository


class OrdersCRUDRepository(BaseCRUDRepository):
    async def create_order(self, order_in) -> OrderHeader:
        order = OrderHeader(
            customer_id=order_in.customer_id,
            order_date=order_in.order_date,
            status=order_in.status,
        )
        for line in order_in.lines:
            order.lines.append(
                OrderLine(
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                )
            )
        self.async_session.add(order)
        await self.async_session.commit()
        await self.async_session.refresh(order)
        return order

    async def get_order(self, order_id: int) -> Optional[OrderHeader]:
        stmt = select(OrderHeader).options(selectinload(OrderHeader.lines)).where(OrderHeader.id == order_id)
        res = await self.async_session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_orders_by_customer(self, customer_id: int, skip: int = 0, limit: int = 50) -> List[OrderHeader]:
        stmt = (
            select(OrderHeader)
            .options(selectinload(OrderHeader.lines))
            .where(OrderHeader.customer_id == customer_id)
            .offset(skip)
            .limit(limit)
        )
        res = await self.async_session.execute(stmt)
        return list(res.scalars().all())

    async def update_order(self, order_id: int, order_in) -> Optional[OrderHeader]:
        order = await self.get_order(order_id)
        if not order:
            return None
        if order_in.customer_id is not None:
            order.customer_id = order_in.customer_id
        if order_in.order_date is not None:
            order.order_date = order_in.order_date
        if order_in.status is not None:
            order.status = order_in.status
        if order_in.lines is not None:
            order.lines.clear()
            for line in order_in.lines:
                order.lines.append(
                    OrderLine(
                        product_id=line.product_id,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                    )
                )
        await self.async_session.commit()
        await self.async_session.refresh(order)
        return order

    async def delete_order(self, order_id: int) -> bool:
        order = await self.get_order(order_id)
        if not order:
            return False
        await self.async_session.delete(order)
        await self.async_session.commit()
        return True


