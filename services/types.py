from __future__ import annotations

from typing import Mapping, Protocol, List
from typing import List, Mapping
from typing import Protocol
from models.schemas.pricing import PriceEntry


class IPriceListLoader(Protocol):
    def load_from_file(
        self, path: str, encoding: str = "utf-8"
    ) -> Mapping[str, List[PriceEntry]]:
        """Parse operators and their price lists from a file path."""
