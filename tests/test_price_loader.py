"""
Unit tests for the price loader service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
import asyncio

from services.price_loader import TextPriceListLoader
from models.schemas.pricing import PriceEntry
from models.db.price_trie import TriePriceDB


class TestTextPriceListLoader:
    """Test cases for TextPriceListLoader class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock TriePriceDB."""
        return MagicMock(spec=TriePriceDB)
    
    @pytest.fixture
    def price_loader(self, mock_db):
        """Create a TextPriceListLoader instance."""
        return TextPriceListLoader(batch_size=100, db=mock_db)
    
    def test_initialization(self, mock_db):
        """Test TextPriceListLoader initialization."""
        loader = TextPriceListLoader(batch_size=50, db=mock_db)
        
        assert loader.db == mock_db
        assert loader.batch_size == 50
        assert loader.current_operator is None
        assert loader.line_counter == 0
    
    @pytest.mark.asyncio
    async def test_load_from_file_fast_success(self, price_loader, mock_db):
        """Test successful fast file loading."""
        # Mock file content
        file_content = """OperatorA:
123 0.05
456 0.03
OperatorB:
123 0.04
789 0.06
"""
        
        with patch('pathlib.Path.cwd', return_value=Path("/test")):
            with patch('builtins.open', mock_open(read_data=file_content)):
                await price_loader.load_from_file_fast("test_file.txt")
                
                # Verify db.build_data_structure was called
                assert mock_db.build_data_structure.called
    
    @pytest.mark.asyncio
    async def test_load_from_file_fast_with_batching(self, mock_db):
        """Test fast file loading with batching."""
        loader = TextPriceListLoader(batch_size=2, db=mock_db)
        
        # Mock file content with more lines than batch size
        file_content = """OperatorA:
123 0.05
456 0.03
789 0.06
OperatorB:
123 0.04
"""
        
        with patch('pathlib.Path.cwd', return_value=Path("/test")):
            with patch('builtins.open', mock_open(read_data=file_content)):
                with patch('loguru.logger.info') as mock_logger:
                    await loader.load_from_file_fast("test_file.txt")
                    
                    # Verify multiple batches were processed
                    assert mock_db.build_data_structure.call_count > 1
                    assert mock_logger.called
    
    @pytest.mark.asyncio
    async def test_load_from_file_success(self, price_loader, mock_db):
        """Test successful regular file loading."""
        # Mock file content
        file_content = """OperatorA:
123 0.05
456 0.03
OperatorB:
123 0.04
"""
        
        with patch('pathlib.Path.cwd', return_value=Path("/test")):
            with patch('builtins.open', mock_open(read_data=file_content)):
                with patch.object(price_loader, '_aiter_file') as mock_aiter:
                    # Mock async file iteration
                    mock_aiter.return_value = file_content.splitlines()
                    
                    await price_loader.load_from_file("test_file.txt")
                    
                    # Verify db.build_data_structure was called
                    assert mock_db.build_data_structure.called
    
    @pytest.mark.asyncio
    async def test_load_batch_success(self, price_loader, mock_db):
        """Test successful batch loading."""
        batch_lines = [
            "OperatorA:",
            "123 0.05",
            "456 0.03",
            "OperatorB:",
            "123 0.04"
        ]
        
        with patch.object(price_loader, '_load_batch', return_value={
            "OperatorA": [PriceEntry(prefix="123", operator="OperatorA", price=0.05)],
            "OperatorB": [PriceEntry(prefix="123", operator="OperatorB", price=0.04)]
        }) as mock_load_batch:
            with patch('loguru.logger.info') as mock_logger:
                await price_loader.load_batch(batch_lines, 1)
                
                mock_load_batch.assert_called_once_with(batch_lines)
                mock_db.build_data_structure.assert_called_once()
                mock_logger.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_batch_with_empty_lines(self, price_loader):
        """Test batch loading with empty lines."""
        batch_lines = [
            "OperatorA:",
            "123 0.05",
            "",  # Empty line
            "   ",  # Whitespace only
            "456 0.03"
        ]
        
        result = await price_loader._load_batch(batch_lines)
        
        assert "OperatorA" in result
        assert len(result["OperatorA"]) == 2
        assert result["OperatorA"][0].prefix == "123"
        assert result["OperatorA"][1].prefix == "456"
    
    @pytest.mark.asyncio
    async def test_load_batch_with_invalid_lines(self, price_loader):
        """Test batch loading with invalid lines."""
        batch_lines = [
            "OperatorA:",
            "123 0.05",
            "invalid_line",  # Invalid format
            "abc 0.03",  # Non-numeric prefix
            "123 invalid_price",  # Non-numeric price
            "123 0.03"  # Valid line
        ]
        
        with patch('loguru.logger.info') as mock_logger:
            result = await price_loader._load_batch(batch_lines)
            
            # Should only process valid lines
            assert "OperatorA" in result
            assert len(result["OperatorA"]) == 2
            assert result["OperatorA"][0].prefix == "123"
            assert result["OperatorA"][0].price == 0.05
            assert result["OperatorA"][1].prefix == "123"
            assert result["OperatorA"][1].price == 0.03
            
            # Should log invalid lines
            assert mock_logger.called
    
    @pytest.mark.asyncio
    async def test_load_batch_with_tab_separated_values(self, price_loader):
        """Test batch loading with tab-separated values."""
        batch_lines = [
            "OperatorA:",
            "123\t0.05",
            "456\t0.03"
        ]
        
        result = await price_loader._load_batch(batch_lines)
        
        assert "OperatorA" in result
        assert len(result["OperatorA"]) == 2
        assert result["OperatorA"][0].prefix == "123"
        assert result["OperatorA"][0].price == 0.05
        assert result["OperatorA"][1].prefix == "456"
        assert result["OperatorA"][1].price == 0.03
    
    @pytest.mark.asyncio
    async def test_load_batch_with_multiple_spaces(self, price_loader):
        """Test batch loading with multiple spaces between values."""
        batch_lines = [
            "OperatorA:",
            "123    0.05",
            "456   0.03"
        ]
        
        result = await price_loader._load_batch(batch_lines)
        
        assert "OperatorA" in result
        assert len(result["OperatorA"]) == 2
        assert result["OperatorA"][0].prefix == "123"
        assert result["OperatorA"][0].price == 0.05
    
    @pytest.mark.asyncio
    async def test_load_batch_without_operator_header(self, price_loader):
        """Test batch loading without operator header."""
        batch_lines = [
            "123 0.05",
            "456 0.03"
        ]
        
        result = await price_loader._load_batch(batch_lines)
        
        # Should return empty dict since no operator is set
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_load_batch_multiple_operators(self, price_loader):
        """Test batch loading with multiple operators."""
        batch_lines = [
            "OperatorA:",
            "123 0.05",
            "456 0.03",
            "OperatorB:",
            "123 0.04",
            "789 0.06"
        ]
        
        result = await price_loader._load_batch(batch_lines)
        
        assert "OperatorA" in result
        assert "OperatorB" in result
        assert len(result["OperatorA"]) == 2
        assert len(result["OperatorB"]) == 2
        
        assert result["OperatorA"][0].prefix == "123"
        assert result["OperatorA"][0].price == 0.05
        assert result["OperatorA"][1].prefix == "456"
        assert result["OperatorA"][1].price == 0.03
        
        assert result["OperatorB"][0].prefix == "123"
        assert result["OperatorB"][0].price == 0.04
        assert result["OperatorB"][1].prefix == "789"
        assert result["OperatorB"][1].price == 0.06
    
    @pytest.mark.asyncio
    async def test_aiter_file(self, price_loader):
        """Test async file iteration."""
        file_content = ["line1\n", "line2\n", "line3\n"]
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = AsyncMock()
            mock_loop.return_value.run_in_executor = mock_executor
            
            # Mock the executor to return the line
            mock_executor.side_effect = lambda executor, func: func()
            
            lines = []
            async for line in price_loader._aiter_file(file_content):
                lines.append(line)
            
            assert lines == ["line1\n", "line2\n", "line3\n"]
    
    @pytest.mark.asyncio
    async def test_load_from_file_with_remaining_batch(self, mock_db):
        """Test file loading with remaining batch at the end."""
        loader = TextPriceListLoader(batch_size=3, db=mock_db)
        
        file_content = """OperatorA:
123 0.05
456 0.03
789 0.06
999 0.07
"""
        
        with patch('pathlib.Path.cwd', return_value=Path("/test")):
            with patch('builtins.open', mock_open(read_data=file_content)):
                with patch.object(loader, '_aiter_file') as mock_aiter:
                    mock_aiter.return_value = file_content.splitlines()
                    
                    await loader.load_from_file("test_file.txt")
                    
                    # Should process all batches including the remaining one
                    assert mock_db.build_data_structure.called
    
    def test_price_entry_creation(self, price_loader):
        """Test PriceEntry creation from parsed data."""
        batch_lines = [
            "OperatorA:",
            "123 0.05"
        ]
        
        # This is a synchronous method, so we can test it directly
        import asyncio
        result = asyncio.run(price_loader._load_batch(batch_lines))
        
        assert "OperatorA" in result
        assert len(result["OperatorA"]) == 1
        
        entry = result["OperatorA"][0]
        assert isinstance(entry, PriceEntry)
        assert entry.prefix == "123"
        assert entry.price == 0.05
        assert entry.operator == "OperatorA"
