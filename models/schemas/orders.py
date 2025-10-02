from __future__ import annotations

from typing import List
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field
from pydantic import ConfigDict


class OrderLineIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)


class OrderCreateIn(BaseModel):
    customer_id: str
    order_date: date
    status: str
    lines: List[OrderLineIn]


class OrderLineOut(OrderLineIn):
    id: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: str
    order_date: date
    status: str
    lines: List[OrderLineOut]


