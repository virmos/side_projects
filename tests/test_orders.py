"""
Unit tests for the orders router and CRUD operations.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from api.routers.orders import router
from models.schemas.orders import OrderCreateIn, OrderOut, OrderLineIn, OrderLineOut
from repository.crud.orders import OrdersCRUDRepository
from models.db.orders import OrderHeader, OrderLine


class TestOrderSchemas:
    """Test cases for order schema models."""
    
    def test_order_line_in_validation(self):
        """Test OrderLineIn validation."""
        # Valid order line
        line = OrderLineIn(product_id=1, quantity=2, unit_price=Decimal("10.50"))
        assert line.product_id == 1
        assert line.quantity == 2
        assert line.unit_price == Decimal("10.50")
        
        # Test validation errors
        with pytest.raises(ValueError):
            OrderLineIn(product_id=0, quantity=2, unit_price=Decimal("10.50"))
        
        with pytest.raises(ValueError):
            OrderLineIn(product_id=1, quantity=0, unit_price=Decimal("10.50"))
        
        with pytest.raises(ValueError):
            OrderLineIn(product_id=1, quantity=2, unit_price=Decimal("0"))
    
    def test_order_create_in_validation(self):
        """Test OrderCreateIn validation."""
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
    
    def test_order_out_model(self):
        """Test OrderOut model."""
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


class TestOrdersCRUDRepository:
    """Test cases for OrdersCRUDRepository."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_order_header(self):
        """Create a mock OrderHeader."""
        mock_order = MagicMock(spec=OrderHeader)
        mock_order.id = 1
        mock_order.customer_id = "test_customer_123"
        mock_order.order_date = date(2024, 1, 15)
        mock_order.status = "pending"
        mock_order.lines = []
        return mock_order
    
    @pytest.fixture
    def orders_repo(self, mock_session):
        """Create OrdersCRUDRepository with mock session."""
        repo = OrdersCRUDRepository()
        repo.async_session = mock_session
        return repo
    
    @pytest.mark.asyncio
    async def test_create_order_success(self, orders_repo, mock_session, mock_order_header):
        """Test successful order creation."""
        # Setup
        order_in = OrderCreateIn(
            customer_id="test_customer_123",
            order_date=date(2024, 1, 15),
            status="pending",
            lines=[
                OrderLineIn(product_id=1, quantity=2, unit_price=Decimal("10.50"))
            ]
        )
        
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Mock the OrderHeader creation
        with patch('repository.crud.orders.OrderHeader') as mock_order_class:
            mock_order_class.return_value = mock_order_header
            
            result = await orders_repo.create_order(order_in)
            
            # Verify
            assert result == mock_order_header
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_order_success(self, orders_repo, mock_session, mock_order_header):
        """Test successful order retrieval."""
        # Setup mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_order_header
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await orders_repo.get_order(1)
        
        assert result == mock_order_header
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_order_not_found(self, orders_repo, mock_session):
        """Test order retrieval when order doesn't exist."""
        # Setup mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await orders_repo.get_order(999)
        
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_orders_by_customer(self, orders_repo, mock_session):
        """Test listing orders by customer."""
        # Setup mock orders
        mock_orders = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_orders
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await orders_repo.list_orders_by_customer("test_customer_123", skip=0, limit=10)
        
        assert result == mock_orders
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_order_success(self, orders_repo, mock_session, mock_order_header):
        """Test successful order update."""
        # Setup
        order_in = OrderCreateIn(
            customer_id="updated_customer",
            order_date=date(2024, 2, 1),
            status="completed",
            lines=[]
        )
        
        # Mock get_order to return existing order
        orders_repo.get_order = AsyncMock(return_value=mock_order_header)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await orders_repo.update_order(1, order_in)
        
        assert result == mock_order_header
        assert mock_order_header.customer_id == "updated_customer"
        assert mock_order_header.order_date == date(2024, 2, 1)
        assert mock_order_header.status == "completed"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_order_not_found(self, orders_repo, mock_session):
        """Test order update when order doesn't exist."""
        order_in = OrderCreateIn(
            customer_id="test_customer",
            order_date=date(2024, 1, 15),
            status="pending",
            lines=[]
        )
        
        # Mock get_order to return None
        orders_repo.get_order = AsyncMock(return_value=None)
        
        result = await orders_repo.update_order(999, order_in)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_order_success(self, orders_repo, mock_session, mock_order_header):
        """Test successful order deletion."""
        # Mock get_order to return existing order
        orders_repo.get_order = AsyncMock(return_value=mock_order_header)
        mock_session.delete = MagicMock()
        mock_session.commit = AsyncMock()
        
        result = await orders_repo.delete_order(1)
        
        assert result is True
        mock_session.delete.assert_called_once_with(mock_order_header)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_order_not_found(self, orders_repo, mock_session):
        """Test order deletion when order doesn't exist."""
        # Mock get_order to return None
        orders_repo.get_order = AsyncMock(return_value=None)
        
        result = await orders_repo.delete_order(999)
        
        assert result is False


class TestOrdersRouter:
    """Test cases for orders router endpoints."""
    
    @pytest.fixture
    def mock_order_repo(self):
        """Create a mock OrdersCRUDRepository."""
        return MagicMock(spec=OrdersCRUDRepository)
    
    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing."""
        return {
            "customer_id": "test_customer_123",
            "order_date": "2024-01-15",
            "status": "pending",
            "lines": [
                {
                    "product_id": 1,
                    "quantity": 2,
                    "unit_price": "10.50"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_create_order_success(self, mock_order_repo, sample_order_data):
        """Test successful order creation endpoint."""
        from api.routers.orders import create_order
        
        # Setup
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.customer_id = "test_customer_123"
        mock_order.order_date = date(2024, 1, 15)
        mock_order.status = "pending"
        mock_order.lines = []
        
        mock_order_repo.create_order.return_value = mock_order
        
        order_create = OrderCreateIn(**sample_order_data)
        
        with patch('api.routers.orders.get_current_customer_id', return_value="test_customer_123"):
            with patch('api.routers.orders.authorize_order_access'):
                result = await create_order(order_create, "test_customer_123", mock_order_repo)
                
                assert result == mock_order
                mock_order_repo.create_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_order_integrity_error(self, mock_order_repo, sample_order_data):
        """Test order creation with integrity error."""
        from api.routers.orders import create_order
        
        # Setup
        mock_order_repo.create_order.side_effect = IntegrityError("", "", "")
        order_create = OrderCreateIn(**sample_order_data)
        
        with patch('api.routers.orders.get_current_customer_id', return_value="test_customer_123"):
            with patch('api.routers.orders.authorize_order_access'):
                with pytest.raises(HTTPException) as exc_info:
                    await create_order(order_create, "test_customer_123", mock_order_repo)
                
                assert exc_info.value.status_code == 400
                assert exc_info.value.detail == "Integrity error"
    
    @pytest.mark.asyncio
    async def test_create_order_unauthorized(self, mock_order_repo, sample_order_data):
        """Test order creation with unauthorized access."""
        from api.routers.orders import create_order
        
        order_create = OrderCreateIn(**sample_order_data)
        
        with patch('api.routers.orders.get_current_customer_id', return_value="different_customer"):
            with patch('api.routers.orders.authorize_order_access', side_effect=HTTPException(status_code=403, detail="Not authorized")):
                with pytest.raises(HTTPException) as exc_info:
                    await create_order(order_create, "different_customer", mock_order_repo)
                
                assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_get_order_success(self, mock_order_repo):
        """Test successful order retrieval endpoint."""
        from api.routers.orders import get_order
        
        # Setup
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.customer_id = "test_customer_123"
        mock_order.order_date = date(2024, 1, 15)
        mock_order.status = "pending"
        mock_order.lines = []
        
        mock_order_repo.get_order.return_value = mock_order
        
        with patch('api.routers.orders.get_current_customer_id', return_value="test_customer_123"):
            with patch('api.routers.orders.authorize_order_access'):
                result = await get_order(1, "test_customer_123", mock_order_repo)
                
                assert result == mock_order
                mock_order_repo.get_order.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_order_not_found(self, mock_order_repo):
        """Test order retrieval when order doesn't exist."""
        from api.routers.orders import get_order
        
        # Setup
        mock_order_repo.get_order.return_value = None
        
        with patch('api.routers.orders.get_current_customer_id', return_value="test_customer_123"):
            with pytest.raises(HTTPException) as exc_info:
                await get_order(999, "test_customer_123", mock_order_repo)
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Order not found"
    
    @pytest.mark.asyncio
    async def test_get_order_unauthorized(self, mock_order_repo):
        """Test order retrieval with unauthorized access."""
        from api.routers.orders import get_order
        
        # Setup
        mock_order = MagicMock()
        mock_order.customer_id = "test_customer_123"
        mock_order_repo.get_order.return_value = mock_order
        
        with patch('api.routers.orders.get_current_customer_id', return_value="different_customer"):
            with patch('api.routers.orders.authorize_order_access', side_effect=HTTPException(status_code=403, detail="Not authorized")):
                with pytest.raises(HTTPException) as exc_info:
                    await get_order(1, "different_customer", mock_order_repo)
                
                assert exc_info.value.status_code == 403
