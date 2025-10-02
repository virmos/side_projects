
from typing import Iterable, Optional, Protocol


class IDatabase(Protocol):
    def build_data_structure(data: any):
        """ Build data structure from data
        """


class IPriceDB(IDatabase):
    def find_cheapest_price(self, operator: str, phone_number: str) -> Optional[float]:
        """Return the price for the longest matching prefix in the operator's list.
        Returns None if the operator has no price for the given number.
        """
