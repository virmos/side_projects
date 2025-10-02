from __future__ import annotations

from typing import Optional, Tuple

from models.db.price_trie import TriePriceDB
from models.schemas.pricing import PriceEntry
from typing import Mapping, List
from typing import Iterable, Optional, Protocol

from repository.crud.types import IPriceRepository


class PricingRepository(IPriceRepository):
    def __init__(self, db: TriePriceDB):
        self.db = db

    async def find_cheapest(self, phone_number: str) -> Optional[Tuple[str, float]]:
        return await self.db.find_cheapest_price(phone_number)
