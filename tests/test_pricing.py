"""
Unit tests for the pricing router and TriePriceDB functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from api.routers.pricing import router
from models.db.price_trie import TriePriceDB, TriePrice, TrieNode
from models.schemas.pricing import PhoneNumberIn, CheapestOut, PriceEntry
from repository.crud.pricing import PricingRepository


class TestTrieNode:
    """Test cases for TrieNode class."""
    
    def test_trie_node_initialization(self):
        """Test TrieNode initialization."""
        node = TrieNode()
        assert len(node.childrens) == 10
        assert node.childrens == [None] * 10
        assert node.supported_operators == []
        assert node.operator_to_price == {}
        assert node.next is None
    
    def test_get_child(self):
        """Test getting child node by digit."""
        node = TrieNode()
        child = TrieNode()
        node.set_child("5", child)
        
        assert node.get_child("5") == child
        assert node.get_child("0") is None
        assert node.get_child("9") is None
    
    def test_set_child(self):
        """Test setting child node by digit."""
        node = TrieNode()
        child = TrieNode()
        
        node.set_child("3", child)
        assert node.childrens[3] == child
        
        # Test invalid digit
        with pytest.raises(ValueError):
            node.set_child("a", child)


class TestTriePrice:
    """Test cases for TriePrice class."""
    
    @pytest.fixture
    def trie_price(self):
        """Create a TriePrice instance for testing."""
        return TriePrice()
    
    @pytest.mark.asyncio
    async def test_insert_single_entry(self, trie_price):
        """Test inserting a single price entry."""
        await trie_price.insert("123", 0.05, "OperatorA")
        
        # Check root -> 1 -> 2 -> 3 path
        node1 = trie_price._root.get_child("1")
        assert node1 is not None
        assert "OperatorA" in node1.operator_to_price
        assert node1.operator_to_price["OperatorA"] == 0.05
        
        node2 = node1.get_child("2")
        assert node2 is not None
        assert "OperatorA" in node2.operator_to_price
        assert node2.operator_to_price["OperatorA"] == 0.05
        
        node3 = node2.get_child("3")
        assert node3 is not None
        assert "OperatorA" in node3.operator_to_price
        assert node3.operator_to_price["OperatorA"] == 0.05
    
    @pytest.mark.asyncio
    async def test_insert_multiple_operators(self, trie_price):
        """Test inserting entries for multiple operators."""
        await trie_price.insert("123", 0.05, "OperatorA")
        await trie_price.insert("123", 0.03, "OperatorB")
        
        node3 = trie_price._root.get_child("1").get_child("2").get_child("3")
        assert "OperatorA" in node3.operator_to_price
        assert "OperatorB" in node3.operator_to_price
        assert node3.operator_to_price["OperatorA"] == 0.05
        assert node3.operator_to_price["OperatorB"] == 0.03
    
    @pytest.mark.asyncio
    async def test_find_longest_match_and_smallest_price(self, trie_price):
        """Test finding longest match with smallest price."""
        await trie_price.insert("123", 0.05, "OperatorA")
        await trie_price.insert("1234", 0.03, "OperatorA")
        await trie_price.insert("123", 0.04, "OperatorB")
        
        # Test exact match
        result = await trie_price.find_longest_match_and_smallest_price("1234567890")
        assert result is not None
        operator, price, prefix = result
        assert operator == "OperatorB"  # Cheapest for prefix "123"
        assert price == 0.04
        assert prefix == "123"
        
        # Test longer match
        result = await trie_price.find_longest_match_and_smallest_price("1234567890")
        assert result is not None
        operator, price, prefix = result
        assert operator == "OperatorA"  # Only operator for prefix "1234"
        assert price == 0.03
        assert prefix == "1234"
    
    @pytest.mark.asyncio
    async def test_find_no_match(self, trie_price):
        """Test finding when no match exists."""
        await trie_price.insert("123", 0.05, "OperatorA")
        
        result = await trie_price.find_longest_match_and_smallest_price("9999999999")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_partial_match(self, trie_price):
        """Test finding partial match."""
        await trie_price.insert("123", 0.05, "OperatorA")
        
        result = await trie_price.find_longest_match_and_smallest_price("12")
        assert result is None  # No complete prefix match


class TestTriePriceDB:
    """Test cases for TriePriceDB class."""
    
    @pytest.fixture
    def trie_price_db(self):
        """Create a TriePriceDB instance for testing."""
        # Reset singleton for testing
        TriePriceDB._instance = None
        return TriePriceDB()
    
    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test that TriePriceDB follows singleton pattern."""
        TriePriceDB._instance = None
        db1 = TriePriceDB()
        db2 = TriePriceDB()
        assert db1 is db2
    
    @pytest.mark.asyncio
    async def test_build_data_structure(self, trie_price_db):
        """Test building data structure from operator entries."""
        operator_to_entries = {
            "OperatorA": [
                PriceEntry(prefix="123", operator="OperatorA", price=0.05),
                PriceEntry(prefix="456", operator="OperatorA", price=0.03)
            ],
            "OperatorB": [
                PriceEntry(prefix="123", operator="OperatorB", price=0.04)
            ]
        }
        
        await trie_price_db.build_data_structure(operator_to_entries)
        
        # Verify data was inserted
        result = await trie_price_db.find_cheapest_price("1234567890")
        assert result is not None
        operator, price, prefix = result
        assert operator == "OperatorB"  # Cheapest for prefix "123"
        assert price == 0.04
        assert prefix == "123"
    
    @pytest.mark.asyncio
    async def test_find_cheapest_price(self, trie_price_db):
        """Test finding cheapest price for a phone number."""
        await trie_price_db.trie.insert("123", 0.05, "OperatorA")
        await trie_price_db.trie.insert("123", 0.03, "OperatorB")
        
        result = await trie_price_db.find_cheapest_price("1234567890")
        assert result is not None
        operator, price, prefix = result
        assert operator == "OperatorB"
        assert price == 0.03
        assert prefix == "123"


class TestPricingRepository:
    """Test cases for PricingRepository class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock TriePriceDB."""
        return MagicMock(spec=TriePriceDB)
    
    @pytest.fixture
    def pricing_repo(self, mock_db):
        """Create a PricingRepository with mock DB."""
        return PricingRepository(mock_db)
    
    @pytest.mark.asyncio
    async def test_find_cheapest_success(self, pricing_repo, mock_db):
        """Test successful cheapest price finding."""
        mock_db.find_cheapest_price.return_value = ("OperatorA", 0.05, "123")
        
        result = await pricing_repo.find_cheapest("1234567890")
        
        assert result == ("OperatorA", 0.05, "123")
        mock_db.find_cheapest_price.assert_called_once_with("1234567890")
    
    @pytest.mark.asyncio
    async def test_find_cheapest_no_result(self, pricing_repo, mock_db):
        """Test when no cheapest price is found."""
        mock_db.find_cheapest_price.return_value = None
        
        result = await pricing_repo.find_cheapest("9999999999")
        
        assert result is None
        mock_db.find_cheapest_price.assert_called_once_with("9999999999")


class TestPricingRouter:
    """Test cases for pricing router endpoints."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create a mock PricingRepository."""
        return MagicMock(spec=PricingRepository)
    
    @pytest.mark.asyncio
    async def test_find_cheapest_success(self, mock_repo):
        """Test successful cheapest price endpoint."""
        mock_repo.find_cheapest.return_value = ("OperatorA", 0.05, "123")
        
        from api.routers.pricing import find_cheapest
        payload = PhoneNumberIn(phone_number="1234567890")
        
        result = await find_cheapest(payload, mock_repo)
        
        assert isinstance(result, CheapestOut)
        assert result.operator == "OperatorA"
        assert result.price == 0.05
        assert result.prefix == "123"
        mock_repo.find_cheapest.assert_called_once_with("1234567890")
    
    @pytest.mark.asyncio
    async def test_find_cheapest_no_match(self, mock_repo):
        """Test cheapest price endpoint when no match found."""
        mock_repo.find_cheapest.return_value = None
        
        from api.routers.pricing import find_cheapest
        payload = PhoneNumberIn(phone_number="9999999999")
        
        with pytest.raises(HTTPException) as exc_info:
            await find_cheapest(payload, mock_repo)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "No operator match"
    
    def test_phone_number_normalization(self):
        """Test phone number normalization in PhoneNumberIn."""
        # Test with + prefix
        payload1 = PhoneNumberIn(phone_number="+1234567890")
        assert payload1.phone_number == "1234567890"
        
        # Test with - separators
        payload2 = PhoneNumberIn(phone_number="123-456-7890")
        assert payload2.phone_number == "1234567890"
        
        # Test with both + and -
        payload3 = PhoneNumberIn(phone_number="+1-234-567-890")
        assert payload3.phone_number == "1234567890"
    
    def test_cheapest_out_model(self):
        """Test CheapestOut model validation."""
        result = CheapestOut(operator="OperatorA", price=0.05, prefix="123")
        assert result.operator == "OperatorA"
        assert result.price == 0.05
        assert result.prefix == "123"
