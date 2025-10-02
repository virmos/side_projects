import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path

from services.price_loader import TextPriceListLoader
from models.schemas.pricing import PriceEntry
from models.db.price_trie import TriePriceDB


class TestTextPriceListLoader:
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=TriePriceDB)

    @pytest.fixture
    def price_loader(self, mock_db):
        return TextPriceListLoader(batch_size=100, db=mock_db)

    def test_initialization(self, mock_db):
        loader = TextPriceListLoader(batch_size=50, db=mock_db)

        assert loader.db == mock_db
        assert loader.batch_size == 50
        assert loader.current_operator is None
        assert loader.line_counter == 0

    @pytest.mark.asyncio
    async def test_load_from_file_fast_success(self, price_loader, mock_db):
        file_content = """OperatorA:
123 0.05
456 0.03
OperatorB:
123 0.04
789 0.06
"""

        with patch("pathlib.Path.cwd", return_value=Path("/test")):
            with patch("pathlib.Path.open", mock_open(read_data=file_content)):
                await price_loader.load_from_file_fast("test_file.txt")
                assert mock_db.build_data_structure.called

    @pytest.mark.asyncio
    async def test_load_from_file_success(self, price_loader, mock_db):
        file_content = """OperatorA:
123 0.05
456 0.03
OperatorB:
123 0.04
"""
        async def async_gen(lines):
            for line in lines:
                yield line
        fake_lines = ["OperatorA:", "123 0.05", "1234 0.03"]

        with patch("pathlib.Path.cwd", return_value=Path("/test")):
            with patch("pathlib.Path.open", mock_open(read_data=file_content)):
                with patch.object(price_loader, "_aiter_file") as mock_aiter:
                    mock_aiter.return_value = async_gen(fake_lines)
                    await price_loader.load_from_file("test_file.txt")
                    assert mock_db.build_data_structure.called

    @pytest.mark.asyncio
    async def test_load_batch_success(self, price_loader, mock_db):
        batch_lines = ["OperatorA:", "123 0.05", "456 0.03", "OperatorB:", "123 0.04"]

        with patch.object(
            price_loader,
            "_load_batch",
            return_value={
                "OperatorA": [
                    PriceEntry(prefix="123", operator="OperatorA", price=0.05)
                ],
                "OperatorB": [
                    PriceEntry(prefix="123", operator="OperatorB", price=0.04)
                ],
            },
        ) as mock_load_batch:
            with patch("loguru.logger.info") as mock_logger:
                await price_loader.load_batch(batch_lines, 1)

                mock_load_batch.assert_called_once_with(batch_lines)
                mock_db.build_data_structure.assert_called_once()
                mock_logger.assert_called_once()
