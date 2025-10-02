import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from api.app import create_app
from tests.test_utils import TestDataFactory, MockFactory


@pytest.mark.integration
class TestPricingIntegration:
    @pytest.fixture
    def app(self):
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_pricing_endpoint_integration(self, client):
        mock_repo = MockFactory.create_mock_pricing_repository()
        mock_repo.find_cheapest.return_value = ("OperatorA", 0.05, "123")
        
        with patch('api.dependencies.get_repository_with_provider') as mock_dep:
            mock_dep.return_value.return_value = mock_repo
            
            response = client.post(
                "/pricing/cheapest",
                json={"phone_number": "1234567890"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["operator"] == "OperatorA"
            assert data["price"] == 0.05
            assert data["prefix"] == "123"
    
    @pytest.mark.asyncio
    async def test_pricing_endpoint_no_match(self, client):
        mock_repo = MockFactory.create_mock_pricing_repository()
        mock_repo.find_cheapest.return_value = None
        
        with patch('api.dependencies.get_repository_with_provider') as mock_dep:
            mock_dep.return_value.return_value = mock_repo
            
            response = client.post(
                "/pricing/cheapest",
                json={"phone_number": "9999999999"}
            )
            
            assert response.status_code == 404
            assert response.json()["detail"] == "No operator match"


@pytest.mark.integration
class TestOrdersIntegration:
    """Integration tests for orders functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test app with mocked dependencies."""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_order_creation_integration(self, client):
        """Test order creation with mocked dependencies."""
        # Mock the orders repository
        mock_repo = MockFactory.create_mock_orders_repository()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.customer_id = "test_customer_123"
        mock_order.order_date = "2024-01-15"
        mock_order.status = "pending"
        mock_order.lines = []
        mock_repo.create_order.return_value = mock_order
        
        # Mock authentication
        with patch('securities.permissions.get_current_customer_id', return_value="test_customer_123"):
            with patch('securities.permissions.authorize_order_access'):
                with patch('api.dependencies.get_repository') as mock_dep:
                    mock_dep.return_value.return_value = mock_repo
                    
                    order_data = TestDataFactory.create_order()
                    
                    response = client.post(
                        "/orders/create-new",
                        json=order_data.dict(),
                        headers={"Authorization": "Bearer mock_token"}
                    )
                    
                    assert response.status_code == 201
                    data = response.json()
                    assert data["id"] == 1
                    assert data["customer_id"] == "test_customer_123"
    
    @pytest.mark.asyncio
    async def test_order_retrieval_integration(self, client):
        """Test order retrieval with mocked dependencies."""
        # Mock the orders repository
        mock_repo = MockFactory.create_mock_orders_repository()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.customer_id = "test_customer_123"
        mock_order.order_date = "2024-01-15"
        mock_order.status = "pending"
        mock_order.lines = []
        mock_repo.get_order.return_value = mock_order
        
        # Mock authentication
        with patch('securities.permissions.get_current_customer_id', return_value="test_customer_123"):
            with patch('securities.permissions.authorize_order_access'):
                with patch('api.dependencies.get_repository') as mock_dep:
                    mock_dep.return_value.return_value = mock_repo
                    
                    response = client.get(
                        "/orders/1",
                        headers={"Authorization": "Bearer mock_token"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["id"] == 1
                    assert data["customer_id"] == "test_customer_123"


@pytest.mark.integration
class TestAuthIntegration:
    """Integration tests for authentication functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test app with mocked dependencies."""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_signup_redirect_integration(self, client):
        """Test signup redirect integration."""
        with patch('config.manager.settings') as mock_settings:
            mock_settings.CASDOOR_URL = "https://casdoor.example.com"
            mock_settings.CASDOOR_APP_NAME = "test_app"
            
            response = client.get("/auth/signup")
            
            assert response.status_code == 307
            assert "casdoor.example.com" in response.headers["location"]
            assert "test_app" in response.headers["location"]
    
    def test_signin_redirect_integration(self, client):
        """Test signin redirect integration."""
        with patch('config.manager.settings') as mock_settings:
            mock_settings.CASDOOR_URL = "https://casdoor.example.com"
            mock_settings.CASDOOR_CLIENT_ID = "test_client_id"
            
            response = client.get("/auth/signin?redirect_uri=https://example.com/callback")
            
            assert response.status_code == 307
            assert "casdoor.example.com" in response.headers["location"]
            assert "test_client_id" in response.headers["location"]
            assert "https://example.com/callback" in response.headers["location"]


@pytest.mark.integration
class TestPriceLoaderIntegration:
    """Integration tests for price loader functionality."""
    
    @pytest.mark.asyncio
    async def test_price_loader_with_trie_db_integration(self):
        """Test price loader integration with TriePriceDB."""
        from models.db.price_trie import TriePriceDB
        from services.price_loader import TextPriceListLoader
        
        # Create real instances for integration test
        db = TriePriceDB()
        loader = TextPriceListLoader(batch_size=10, db=db)
        
        # Create test data
        test_data = TestDataFactory.create_price_data()
        
        # Test the integration
        await db.build_data_structure(test_data)
        
        # Verify data was loaded correctly
        result = await db.find_cheapest_price("1234567890")
        assert result is not None
        operator, price, prefix = result
        assert operator in ["OperatorA", "OperatorB"]  # Both have prefix "123"
        assert price <= 0.05  # Should find the cheapest price
        assert prefix == "123"
    
    @pytest.mark.asyncio
    async def test_price_loader_file_parsing_integration(self):
        """Test price loader file parsing integration."""
        from services.price_loader import TextPriceListLoader
        from models.db.price_trie import TriePriceDB
        
        # Create test file content
        file_content = """OperatorA:
123 0.05
456 0.03
OperatorB:
123 0.04
789 0.06
"""
        
        # Mock file operations
        with patch('pathlib.Path.cwd', return_value=Path("/test")):
            with patch('builtins.open', mock_open(read_data=file_content)):
                db = TriePriceDB()
                loader = TextPriceListLoader(batch_size=100, db=db)
                
                await loader.load_from_file_fast("test_file.txt")
                
                # Verify data was loaded
                result = await db.find_cheapest_price("1234567890")
                assert result is not None
                operator, price, prefix = result
                assert operator == "OperatorB"  # Cheapest for prefix "123"
                assert price == 0.04
                assert prefix == "123"


@pytest.mark.integration
class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.fixture
    def app(self):
        """Create test app with mocked dependencies."""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_complete_order_flow(self, client):
        """Test complete order creation and retrieval flow."""
        # Mock all dependencies
        mock_orders_repo = MockFactory.create_mock_orders_repository()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.customer_id = "test_customer_123"
        mock_order.order_date = "2024-01-15"
        mock_order.status = "pending"
        mock_order.lines = []
        mock_orders_repo.create_order.return_value = mock_order
        mock_orders_repo.get_order.return_value = mock_order
        
        # Mock authentication
        with patch('securities.permissions.get_current_customer_id', return_value="test_customer_123"):
            with patch('securities.permissions.authorize_order_access'):
                with patch('api.dependencies.get_repository') as mock_dep:
                    mock_dep.return_value.return_value = mock_orders_repo
                    
                    # Create order
                    order_data = TestDataFactory.create_order()
                    create_response = client.post(
                        "/orders/create-new",
                        json=order_data.dict(),
                        headers={"Authorization": "Bearer mock_token"}
                    )
                    
                    assert create_response.status_code == 201
                    order_id = create_response.json()["id"]
                    
                    # Retrieve order
                    get_response = client.get(
                        f"/orders/{order_id}",
                        headers={"Authorization": "Bearer mock_token"}
                    )
                    
                    assert get_response.status_code == 200
                    assert get_response.json()["id"] == order_id
                    assert get_response.json()["customer_id"] == "test_customer_123"
    
    @pytest.mark.asyncio
    async def test_pricing_and_order_integration(self, client):
        """Test integration between pricing and order systems."""
        # Mock pricing repository
        mock_pricing_repo = MockFactory.create_mock_pricing_repository()
        mock_pricing_repo.find_cheapest.return_value = ("OperatorA", 0.05, "123")
        
        # Mock orders repository
        mock_orders_repo = MockFactory.create_mock_orders_repository()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.customer_id = "test_customer_123"
        mock_order.order_date = "2024-01-15"
        mock_order.status = "pending"
        mock_order.lines = []
        mock_orders_repo.create_order.return_value = mock_order
        
        # Mock authentication
        with patch('securities.permissions.get_current_customer_id', return_value="test_customer_123"):
            with patch('securities.permissions.authorize_order_access'):
                with patch('api.dependencies.get_repository_with_provider') as mock_pricing_dep:
                    with patch('api.dependencies.get_repository') as mock_orders_dep:
                        mock_pricing_dep.return_value.return_value = mock_pricing_repo
                        mock_orders_dep.return_value.return_value = mock_orders_repo
                        
                        # Get pricing information
                        pricing_response = client.post(
                            "/pricing/cheapest",
                            json={"phone_number": "1234567890"}
                        )
                        
                        assert pricing_response.status_code == 200
                        pricing_data = pricing_response.json()
                        assert pricing_data["operator"] == "OperatorA"
                        assert pricing_data["price"] == 0.05
                        
                        # Create order (could use pricing data in real scenario)
                        order_data = TestDataFactory.create_order()
                        order_response = client.post(
                            "/orders/create-new",
                            json=order_data.dict(),
                            headers={"Authorization": "Bearer mock_token"}
                        )
                        
                        assert order_response.status_code == 201
                        assert order_response.json()["id"] == 1
