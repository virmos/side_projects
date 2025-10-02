"""
Unit tests for schemas and models validation.
"""
import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from models.schemas.pricing import PhoneNumberIn, CheapestOut, PriceEntry
from models.schemas.orders import OrderCreateIn, OrderOut, OrderLineIn, OrderLineOut


class TestPricingSchemas:
    """Test cases for pricing schema models."""
    
    def test_price_entry_creation(self):
        """Test PriceEntry dataclass creation."""
        entry = PriceEntry(prefix="123", operator="OperatorA", price=0.05)
        
        assert entry.prefix == "123"
        assert entry.operator == "OperatorA"
        assert entry.price == 0.05
    
    def test_price_entry_default_values(self):
        """Test PriceEntry with default values."""
        entry = PriceEntry()
        
        assert entry.prefix == ""
        assert entry.operator == ""
        assert entry.price == 0
    
    def test_price_entry_frozen(self):
        """Test that PriceEntry is frozen (immutable)."""
        entry = PriceEntry(prefix="123", operator="OperatorA", price=0.05)
        
        with pytest.raises(AttributeError):
            entry.prefix = "456"
        
        with pytest.raises(AttributeError):
            entry.operator = "OperatorB"
        
        with pytest.raises(AttributeError):
            entry.price = 0.10
    
    def test_phone_number_in_normalization(self):
        """Test phone number normalization."""
        # Test with + prefix
        phone_in = PhoneNumberIn(phone_number="+1234567890")
        assert phone_in.phone_number == "1234567890"
        
        # Test with - separators
        phone_in = PhoneNumberIn(phone_number="123-456-7890")
        assert phone_in.phone_number == "1234567890"
        
        # Test with both + and -
        phone_in = PhoneNumberIn(phone_number="+1-234-567-890")
        assert phone_in.phone_number == "1234567890"
        
        # Test with spaces (should not be removed by current implementation)
        phone_in = PhoneNumberIn(phone_number="123 456 7890")
        assert phone_in.phone_number == "123 456 7890"
    
    def test_phone_number_in_validation(self):
        """Test PhoneNumberIn validation."""
        # Valid phone number
        phone_in = PhoneNumberIn(phone_number="1234567890")
        assert phone_in.phone_number == "1234567890"
        
        # Empty phone number should be allowed (validation happens at business logic level)
        phone_in = PhoneNumberIn(phone_number="")
        assert phone_in.phone_number == ""
    
    def test_cheapest_out_creation(self):
        """Test CheapestOut model creation."""
        cheapest = CheapestOut(operator="OperatorA", price=0.05, prefix="123")
        
        assert cheapest.operator == "OperatorA"
        assert cheapest.price == 0.05
        assert cheapest.prefix == "123"
    
    def test_cheapest_out_validation(self):
        """Test CheapestOut validation."""
        # Valid cheapest out
        cheapest = CheapestOut(operator="OperatorA", price=0.05, prefix="123")
        assert cheapest.operator == "OperatorA"
        assert cheapest.price == 0.05
        assert cheapest.prefix == "123"
        
        # Test with zero price
        cheapest = CheapestOut(operator="OperatorA", price=0.0, prefix="123")
        assert cheapest.price == 0.0
        
        # Test with negative price (should be allowed, business logic handles validation)
        cheapest = CheapestOut(operator="OperatorA", price=-0.01, prefix="123")
        assert cheapest.price == -0.01


class TestOrderSchemas:
    """Test cases for order schema models."""
    
    def test_order_line_in_creation(self):
        """Test OrderLineIn model creation."""
        line = OrderLineIn(
            product_id=1,
            quantity=2,
            unit_price=Decimal("10.50")
        )
        
        assert line.product_id == 1
        assert line.quantity == 2
        assert line.unit_price == Decimal("10.50")
    
    def test_order_line_in_validation_positive_values(self):
        """Test OrderLineIn validation for positive values."""
        # Valid values
        line = OrderLineIn(
            product_id=1,
            quantity=1,
            unit_price=Decimal("0.01")
        )
        assert line.product_id == 1
        assert line.quantity == 1
        assert line.unit_price == Decimal("0.01")
        
        # Test with large values
        line = OrderLineIn(
            product_id=999999,
            quantity=1000,
            unit_price=Decimal("999.99")
        )
        assert line.product_id == 999999
        assert line.quantity == 1000
        assert line.unit_price == Decimal("999.99")
    
    def test_order_line_in_validation_errors(self):
        """Test OrderLineIn validation errors."""
        # Zero product_id
        with pytest.raises(ValidationError) as exc_info:
            OrderLineIn(product_id=0, quantity=1, unit_price=Decimal("10.50"))
        assert "greater than 0" in str(exc_info.value)
        
        # Negative product_id
        with pytest.raises(ValidationError) as exc_info:
            OrderLineIn(product_id=-1, quantity=1, unit_price=Decimal("10.50"))
        assert "greater than 0" in str(exc_info.value)
        
        # Zero quantity
        with pytest.raises(ValidationError) as exc_info:
            OrderLineIn(product_id=1, quantity=0, unit_price=Decimal("10.50"))
        assert "greater than 0" in str(exc_info.value)
        
        # Negative quantity
        with pytest.raises(ValidationError) as exc_info:
            OrderLineIn(product_id=1, quantity=-1, unit_price=Decimal("10.50"))
        assert "greater than 0" in str(exc_info.value)
        
        # Zero unit_price
        with pytest.raises(ValidationError) as exc_info:
            OrderLineIn(product_id=1, quantity=1, unit_price=Decimal("0"))
        assert "greater than 0" in str(exc_info.value)
        
        # Negative unit_price
        with pytest.raises(ValidationError) as exc_info:
            OrderLineIn(product_id=1, quantity=1, unit_price=Decimal("-1.00"))
        assert "greater than 0" in str(exc_info.value)
    
    def test_order_line_in_string_price_conversion(self):
        """Test OrderLineIn with string price conversion."""
        line = OrderLineIn(
            product_id=1,
            quantity=2,
            unit_price="10.50"  # String should be converted to Decimal
        )
        
        assert isinstance(line.unit_price, Decimal)
        assert line.unit_price == Decimal("10.50")
    
    def test_order_create_in_creation(self):
        """Test OrderCreateIn model creation."""
        lines = [
            OrderLineIn(product_id=1, quantity=2, unit_price=Decimal("10.50")),
            OrderLineIn(product_id=2, quantity=1, unit_price=Decimal("25.00"))
        ]
        
        order = OrderCreateIn(
            customer_id="test_customer_123",
            order_date=date(2024, 1, 15),
            status="pending",
            lines=lines
        )
        
        assert order.customer_id == "test_customer_123"
        assert order.order_date == date(2024, 1, 15)
        assert order.status == "pending"
        assert len(order.lines) == 2
        assert order.lines[0].product_id == 1
        assert order.lines[1].product_id == 2
    
    def test_order_create_in_string_date_conversion(self):
        """Test OrderCreateIn with string date conversion."""
        lines = [OrderLineIn(product_id=1, quantity=1, unit_price=Decimal("10.50"))]
        
        order = OrderCreateIn(
            customer_id="test_customer_123",
            order_date="2024-01-15",  # String should be converted to date
            status="pending",
            lines=lines
        )
        
        assert isinstance(order.order_date, date)
        assert order.order_date == date(2024, 1, 15)
    
    def test_order_create_in_empty_lines(self):
        """Test OrderCreateIn with empty lines list."""
        order = OrderCreateIn(
            customer_id="test_customer_123",
            order_date=date(2024, 1, 15),
            status="pending",
            lines=[]
        )
        
        assert order.customer_id == "test_customer_123"
        assert len(order.lines) == 0
    
    def test_order_line_out_inheritance(self):
        """Test OrderLineOut inherits from OrderLineIn."""
        line_out = OrderLineOut(
            id=1,
            product_id=1,
            quantity=2,
            unit_price=Decimal("10.50")
        )
        
        assert line_out.id == 1
        assert line_out.product_id == 1
        assert line_out.quantity == 2
        assert line_out.unit_price == Decimal("10.50")
    
    def test_order_line_out_validation(self):
        """Test OrderLineOut validation."""
        # Valid order line out
        line_out = OrderLineOut(
            id=1,
            product_id=1,
            quantity=2,
            unit_price=Decimal("10.50")
        )
        assert line_out.id == 1
        
        # Test with zero id (should be allowed for new records)
        line_out = OrderLineOut(
            id=0,
            product_id=1,
            quantity=2,
            unit_price=Decimal("10.50")
        )
        assert line_out.id == 0
        
        # Test with negative id (should be allowed, database handles validation)
        line_out = OrderLineOut(
            id=-1,
            product_id=1,
            quantity=2,
            unit_price=Decimal("10.50")
        )
        assert line_out.id == -1
    
    def test_order_out_creation(self):
        """Test OrderOut model creation."""
        lines = [
            OrderLineOut(
                id=1,
                product_id=1,
                quantity=2,
                unit_price=Decimal("10.50")
            )
        ]
        
        order = OrderOut(
            id=1,
            customer_id="test_customer_123",
            order_date=date(2024, 1, 15),
            status="pending",
            lines=lines
        )
        
        assert order.id == 1
        assert order.customer_id == "test_customer_123"
        assert order.order_date == date(2024, 1, 15)
        assert order.status == "pending"
        assert len(order.lines) == 1
        assert order.lines[0].id == 1
    
    def test_order_out_string_date_conversion(self):
        """Test OrderOut with string date conversion."""
        lines = [
            OrderLineOut(
                id=1,
                product_id=1,
                quantity=1,
                unit_price=Decimal("10.50")
            )
        ]
        
        order = OrderOut(
            id=1,
            customer_id="test_customer_123",
            order_date="2024-01-15",  # String should be converted to date
            status="pending",
            lines=lines
        )
        
        assert isinstance(order.order_date, date)
        assert order.order_date == date(2024, 1, 15)
    
    def test_order_out_empty_lines(self):
        """Test OrderOut with empty lines list."""
        order = OrderOut(
            id=1,
            customer_id="test_customer_123",
            order_date=date(2024, 1, 15),
            status="pending",
            lines=[]
        )
        
        assert order.id == 1
        assert len(order.lines) == 0
    
    def test_order_status_values(self):
        """Test various order status values."""
        valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        
        for status in valid_statuses:
            order = OrderCreateIn(
                customer_id="test_customer",
                order_date=date(2024, 1, 15),
                status=status,
                lines=[]
            )
            assert order.status == status
    
    def test_customer_id_formats(self):
        """Test various customer ID formats."""
        valid_customer_ids = [
            "customer_123",
            "user-456",
            "CUST789",
            "1234567890",
            "test@example.com"
        ]
        
        for customer_id in valid_customer_ids:
            order = OrderCreateIn(
                customer_id=customer_id,
                order_date=date(2024, 1, 15),
                status="pending",
                lines=[]
            )
            assert order.customer_id == customer_id
    
    def test_decimal_precision_handling(self):
        """Test Decimal precision handling."""
        # Test with high precision decimal
        line = OrderLineIn(
            product_id=1,
            quantity=1,
            unit_price=Decimal("10.123456789")
        )
        
        assert line.unit_price == Decimal("10.123456789")
        
        # Test with very small decimal
        line = OrderLineIn(
            product_id=1,
            quantity=1,
            unit_price=Decimal("0.000001")
        )
        
        assert line.unit_price == Decimal("0.000001")
