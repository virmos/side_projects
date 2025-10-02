import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.app import create_app
from models.db.price_trie import TriePriceDB
from models.schemas.pricing import PriceEntry
from repository.crud.pricing import PricingRepository
from repository.crud.orders import OrdersCRUDRepository
from services.price_loader import TextPriceListLoader


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_trie_price_db():
    mock_db = MagicMock(spec=TriePriceDB)
    mock_db.trie = MagicMock()
    return mock_db


@pytest.fixture
def mock_pricing_repository(mock_trie_price_db):
    return PricingRepository(mock_trie_price_db)


@pytest.fixture
def mock_orders_repository():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_repo = MagicMock(spec=OrdersCRUDRepository)
    mock_repo.async_session = mock_session
    return mock_repo


@pytest.fixture
def sample_price_entries():
    return [
        PriceEntry(prefix="123", operator="OperatorA", price=0.05),
        PriceEntry(prefix="1234", operator="OperatorA", price=0.03),
        PriceEntry(prefix="123", operator="OperatorB", price=0.04),
        PriceEntry(prefix="567", operator="OperatorC", price=0.06),
    ]


@pytest.fixture
def sample_phone_numbers():
    return [
        "1234567890",
        "12345678901",
        "5678901234",
        "9999999999",  # No match
    ]


@pytest.fixture
def mock_price_loader():
    return MagicMock(spec=TextPriceListLoader)


@pytest.fixture
def sample_order_data():
    from datetime import date
    from decimal import Decimal
    
    return {
        "customer_id": "test_customer_123",
        "order_date": date(2024, 1, 15),
        "status": "pending",
        "lines": [
            {
                "product_id": 1,
                "quantity": 2,
                "unit_price": Decimal("10.50")
            },
            {
                "product_id": 2,
                "quantity": 1,
                "unit_price": Decimal("25.00")
            }
        ]
    }


@pytest.fixture
def mock_jwt_token():
    return "mock.jwt.token"


@pytest.fixture
def mock_casdoor_settings():
    return {
        "CASDOOR_URL": "https://casdoor.example.com",
        "CASDOOR_APP_NAME": "test_app",
        "CASDOOR_CLIENT_ID": "test_client_id",
        "CASDOOR_CLIENT_SECRET": "test_client_secret",
        "CASDOOR_CERTIFICATE": "-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----"
    }
