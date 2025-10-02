"""
Additional test utilities and helpers.
"""
import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import date

from models.schemas.pricing import PriceEntry
from models.schemas.orders import OrderCreateIn, OrderLineIn


class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_price_entry(
        prefix: str = "123",
        operator: str = "OperatorA",
        price: float = 0.05
    ) -> PriceEntry:
        """Create a PriceEntry for testing."""
        return PriceEntry(prefix=prefix, operator=operator, price=price)
    
    @staticmethod
    def create_order_line(
        product_id: int = 1,
        quantity: int = 2,
        unit_price: str = "10.50"
    ) -> OrderLineIn:
        """Create an OrderLineIn for testing."""
        return OrderLineIn(
            product_id=product_id,
            quantity=quantity,
            unit_price=Decimal(unit_price)
        )
    
    @staticmethod
    def create_order(
        customer_id: str = "test_customer_123",
        order_date: str = "2024-01-15",
        status: str = "pending",
        lines: Optional[List[OrderLineIn]] = None
    ) -> OrderCreateIn:
        """Create an OrderCreateIn for testing."""
        if lines is None:
            lines = [TestDataFactory.create_order_line()]
        
        return OrderCreateIn(
            customer_id=customer_id,
            order_date=date.fromisoformat(order_date),
            status=status,
            lines=lines
        )
    
    @staticmethod
    def create_phone_number_variations() -> List[str]:
        """Create various phone number formats for testing."""
        return [
            "1234567890",
            "+1234567890",
            "123-456-7890",
            "+1-234-567-890",
            "123 456 7890",
            "+1 234 567 890"
        ]
    
    @staticmethod
    def create_price_data() -> Dict[str, List[PriceEntry]]:
        """Create sample price data for testing."""
        return {
            "OperatorA": [
                PriceEntry(prefix="123", operator="OperatorA", price=0.05),
                PriceEntry(prefix="1234", operator="OperatorA", price=0.03),
                PriceEntry(prefix="456", operator="OperatorA", price=0.04)
            ],
            "OperatorB": [
                PriceEntry(prefix="123", operator="OperatorB", price=0.04),
                PriceEntry(prefix="567", operator="OperatorB", price=0.06),
                PriceEntry(prefix="789", operator="OperatorB", price=0.07)
            ],
            "OperatorC": [
                PriceEntry(prefix="999", operator="OperatorC", price=0.08),
                PriceEntry(prefix="111", operator="OperatorC", price=0.02)
            ]
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
    def create_mock_orders_repository():
        mock_repo = MagicMock()
        mock_repo.async_session = AsyncMock()
        mock_repo.create_order = AsyncMock()
        mock_repo.get_order = AsyncMock()
        mock_repo.list_orders_by_customer = AsyncMock()
        mock_repo.update_order = AsyncMock()
        mock_repo.delete_order = AsyncMock()
        return mock_repo
    
    @staticmethod
    def create_mock_price_loader():
        mock_loader = MagicMock()
        mock_loader.load_from_file = AsyncMock()
        mock_loader.load_from_file_fast = AsyncMock()
        mock_loader._load_batch = AsyncMock()
        return mock_loader


class AssertionHelpers:
    """Helper class for common test assertions."""
    
    @staticmethod
    def assert_price_entry_equal(actual: PriceEntry, expected: PriceEntry):
        """Assert that two PriceEntry objects are equal."""
        assert actual.prefix == expected.prefix
        assert actual.operator == expected.operator
        assert actual.price == expected.price
    
    @staticmethod
    def assert_order_line_equal(actual: OrderLineIn, expected: OrderLineIn):
        """Assert that two OrderLineIn objects are equal."""
        assert actual.product_id == expected.product_id
        assert actual.quantity == expected.quantity
        assert actual.unit_price == expected.unit_price
    
    @staticmethod
    def assert_http_exception(
        exception: Exception,
        expected_status_code: int,
        expected_detail: str
    ):
        """Assert HTTP exception properties."""
        assert isinstance(exception, Exception)
        assert hasattr(exception, 'status_code')
        assert hasattr(exception, 'detail')
        assert exception.status_code == expected_status_code
        assert exception.detail == expected_detail


class TestMarkers:
    """Test markers for categorizing tests."""
    
    UNIT = pytest.mark.unit
    INTEGRATION = pytest.mark.integration
    SLOW = pytest.mark.slow
    
    @staticmethod
    def parametrize_phone_numbers():
        """Parametrize decorator for phone number tests."""
        phone_numbers = TestDataFactory.create_phone_number_variations()
        return pytest.mark.parametrize("phone_number", phone_numbers)
    
    @staticmethod
    def parametrize_price_entries():
        """Parametrize decorator for price entry tests."""
        price_data = TestDataFactory.create_price_data()
        entries = []
        for operator, price_list in price_data.items():
            for entry in price_list:
                entries.append((entry, operator))
        
        return pytest.mark.parametrize("price_entry,operator", entries)


class DatabaseTestHelpers:
    """Helpers for database-related tests."""
    
    @staticmethod
    async def setup_test_data(mock_db, price_data: Dict[str, List[PriceEntry]]):
        """Setup test data in mock database."""
        mock_db.build_data_structure.return_value = None
        await mock_db.build_data_structure(price_data)
    
    @staticmethod
    def assert_database_called(mock_db, expected_calls: int = 1):
        """Assert database methods were called expected number of times."""
        assert mock_db.build_data_structure.call_count == expected_calls


class FileTestHelpers:
    """Helpers for file-related tests."""
    
    @staticmethod
    def create_mock_file_content(operators_data: Dict[str, List[tuple]]) -> str:
        """Create mock file content for testing."""
        content_lines = []
        
        for operator, entries in operators_data.items():
            content_lines.append(f"{operator}:")
            for prefix, price in entries:
                content_lines.append(f"{prefix} {price}")
            content_lines.append("")  # Empty line between operators
        
        return "\n".join(content_lines)
    
    @staticmethod
    def assert_file_operations_called(mock_loader, expected_calls: int = 1):
        """Assert file operations were called expected number of times."""
        assert mock_loader.load_from_file.call_count == expected_calls


# Common test data constants
class TestConstants:
    """Constants for test data."""
    
    # Phone numbers
    VALID_PHONE_NUMBERS = [
        "1234567890",
        "12345678901",
        "5678901234"
    ]
    
    INVALID_PHONE_NUMBERS = [
        "9999999999",  # No match
        "0000000000",  # No match
        "1111111111"   # No match
    ]
    
    # Operators
    OPERATORS = ["OperatorA", "OperatorB", "OperatorC"]
    
    # Prices
    PRICES = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    
    # Order statuses
    ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]
    
    # Customer IDs
    CUSTOMER_IDS = [
        "customer_123",
        "user-456",
        "CUST789",
        "1234567890",
        "test@example.com"
    ]
    
    # Product IDs
    PRODUCT_IDS = list(range(1, 101))  # 1 to 100
    
    # Quantities
    QUANTITIES = list(range(1, 11))  # 1 to 10
