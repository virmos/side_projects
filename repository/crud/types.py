from typing import Iterable, Optional, Protocol, Tuple


class IPriceRepository(Protocol):
    """Interface to find the cheapest operator for a given phone number."""

    def find_cheapest(self, phone_number: str) -> Optional[Tuple[str, float]]:
        """Return (operator, price) for the cheapest available match.

        If no operator matches the number, return None.
        """

