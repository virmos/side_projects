from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from typing import Dict, Iterable, List, Mapping, Optional, Protocol
from math import inf

import loguru
from models.db.types import IPriceDB
from models.schemas.pricing import PriceEntry


@dataclass
class TrieNode:
    childrens: List[Optional["TrieNode"]] = field(default_factory=lambda: [None] * 10)
    supported_operators: List[Optional[str]] = field(default_factory=list)
    operator_to_price: Dict[str, float] = field(default_factory=dict)
    next: Optional[TrieNode] = None

    def get_child(self, digit: str) -> Optional["TrieNode"]:
        index = int(digit)
        return self.childrens[index]

    def set_child(self, digit: str, node: "TrieNode") -> None:
        index = int(digit)
        self.childrens[index] = node


class TriePrice:
    def __init__(self) -> None:
        self._root = TrieNode()

    """Runtime: O(n*l*m)
    n is the largest number of prices belong to one operator in the input file
    l is prefix length
    m is num operators
    """
    async def insert(self, prefix: str, price: float, operator: str) -> None:
        node = self._root
        for num in prefix:
            if not node.get_child(num):
                node.set_child(num, TrieNode())
            node = node.get_child(num)
        node.operator_to_price[operator] = price
        node.supported_operators.append(operator)

    """Runtime: O(m*11)
    m is num operators
    10 is phone length
    With m <= 1.000.000 => runtime 
    """
    async def find_longest_match_and_smallest_price(self, number: str) -> Optional[Tuple[float, str]]:
        node = self._root
        
        operator_to_price: Dict[str, float] = {}
        prefix = ""
        for num in number:
            if not node.get_child(num):
                break
            node = node.get_child(num)
            prefix += num
            for operator in node.supported_operators:
                operator_to_price[operator] = (node.operator_to_price[operator], prefix)

        if not operator_to_price:
            return None
        
        min_operator = None
        min_price = inf
        min_prefix = None
        for operator, (price, prefix) in operator_to_price.items():
            if price < min_price:
                min_price = price
                min_operator = operator
                min_prefix = prefix
        return (min_operator, min_price, min_prefix)


class TriePriceDB(IPriceDB):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TriePriceDB, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.trie = TriePrice()
        self._initialized = True

    async def build_data_structure(
        self, operator_to_entries: Mapping[str, List[PriceEntry]]
    ) -> None:
        for operator, entries in operator_to_entries.items():
            for entry in entries:
                await self.trie.insert(entry.prefix, float(entry.price), operator)

    async def find_cheapest_price(self, phone_number: str) -> Optional[float]:
        return await self.trie.find_longest_match_and_smallest_price(phone_number)
