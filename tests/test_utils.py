import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import date

from models.schemas.pricing import PriceEntry


class TestDataFactory:
    @staticmethod
    def create_price_data() -> Dict[str, List[PriceEntry]]:
        return {
            "OperatorA": [
                PriceEntry(prefix="123", operator="OperatorA", price=0.05),
                PriceEntry(prefix="1234", operator="OperatorA", price=0.03),
                PriceEntry(prefix="456", operator="OperatorA", price=0.04),
            ],
            "OperatorB": [
                PriceEntry(prefix="123", operator="OperatorB", price=0.04),
                PriceEntry(prefix="567", operator="OperatorB", price=0.06),
                PriceEntry(prefix="789", operator="OperatorB", price=0.07),
            ],
            "OperatorC": [
                PriceEntry(prefix="999", operator="OperatorC", price=0.08),
                PriceEntry(prefix="111", operator="OperatorC", price=0.02),
            ],
        }


class MockFactory:
    @staticmethod
    def create_mock_trie_price_db():
        mock_db = MagicMock()
        mock_db.trie = MagicMock()
        mock_db.build_data_structure = AsyncMock()
        mock_db.find_cheapest_price = AsyncMock()
        return mock_db

    @staticmethod
    def create_mock_pricing_repository():
        mock_repo = MagicMock()
        mock_repo.find_cheapest = AsyncMock()
        return mock_repo

    @staticmethod
    def create_mock_price_loader():
        mock_loader = MagicMock()
        mock_loader.load_from_file = AsyncMock()
        mock_loader.load_from_file_fast = AsyncMock()
        mock_loader._load_batch = AsyncMock()
        return mock_loader

