from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, mock_open, patch
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import get_repository_with_provider
from models.db.price_trie import TriePriceDB
from repository.crud.pricing import PricingRepository
from services.price_loader import TextPriceListLoader
from tests.test_utils import TestDataFactory, MockFactory


@pytest.mark.integration
class TestPricingIntegration:
    @pytest.mark.asyncio
    async def test_pricing_endpoint_integration(self, client):
        await client.app.router.startup()

        response = client.post(
            "/pricing/cheapest", json={"phone_number": "1234567890"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operator"] == "Operator A"
        assert data["price"] == 0.9

    @pytest.mark.asyncio
    async def test_pricing_endpoint_no_match(self, client):
        mock_repo = MockFactory.create_mock_pricing_repository()
        mock_repo.find_cheapest.return_value = None

        with patch("api.routers.pricing.get_repository_with_provider") as mock_dep:
            mock_dep.return_value.return_value = mock_repo

            response = client.post(
                "/pricing/cheapest", json={"phone_number": "9999999999"}
            )

            assert response.status_code == 404
            assert response.json()["detail"] == "No operator match"


@pytest.mark.integration
class TestPriceLoaderIntegration:
    @pytest.mark.asyncio
    async def test_price_loader_with_trie_db_integration(self):
        db = TriePriceDB()

        test_data = TestDataFactory.create_price_data()
        await db.build_data_structure(test_data)

        result = await db.find_cheapest_price("1234567890")
        assert result is not None
        operator, price, prefix = result
        assert operator == "OperatorA"
        assert price == 0.03
        assert prefix == "1234"

    @pytest.mark.asyncio
    async def test_price_loader_file_parsing_integration(self):
        file_content = """OperatorA:
123 0.05
1234 0.03
OperatorB:
123 0.04
789 0.06
"""
        with patch("pathlib.Path.cwd", return_value=Path("/test")):
            with patch("pathlib.Path.open", mock_open(read_data=file_content)):
                db = TriePriceDB()
                loader = TextPriceListLoader(batch_size=100, db=db)

                await loader.load_from_file_fast("test_file.txt")

                result = await db.find_cheapest_price("1234567890")
                assert result is not None
                operator, price, prefix = result
                assert operator == "OperatorA"
                assert price == 0.03
                assert prefix == "1234"
