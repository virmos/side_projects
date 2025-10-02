import pytest
from models.db.price_trie import TriePriceDB, TriePrice, TrieNode
from tests.test_utils import TestDataFactory


class TestTrieNode:
    def test_trie_node_initialization(self):
        node = TrieNode()
        assert len(node.childrens) == 10
        assert node.childrens == [None] * 10
        assert node.supported_operators == []
        assert node.operator_to_price == {}
        assert node.next is None

    def test_get_child(self):
        node = TrieNode()
        child = TrieNode()
        node.set_child("5", child)

        assert node.get_child("5") == child
        assert node.get_child("0") is None
        assert node.get_child("9") is None

    def test_set_child(self):
        node = TrieNode()
        child = TrieNode()

        node.set_child("3", child)
        assert node.childrens[3] == child

        with pytest.raises(ValueError):
            node.set_child("a", child)


class TestTriePrice:
    @pytest.fixture
    def trie_price(self):
        return TriePrice()

    @pytest.mark.asyncio
    async def test_insert_single_entry(self, trie_price):
        await trie_price.insert("123", 0.05, "OperatorA")

        node1 = trie_price._root.get_child("1")
        assert node1 is not None
        assert "OperatorA" not in node1.operator_to_price

        node2 = node1.get_child("2")
        assert node2 is not None
        assert "OperatorA" not in node2.operator_to_price

        node3 = node2.get_child("3")
        assert node3 is not None
        assert "OperatorA" in node3.operator_to_price
        assert node3.operator_to_price["OperatorA"] == 0.05

    @pytest.mark.asyncio
    async def test_insert_multiple_operators(self, trie_price):
        await trie_price.insert("123", 0.05, "OperatorA")
        await trie_price.insert("123", 0.03, "OperatorB")

        node3 = trie_price._root.get_child("1").get_child("2").get_child("3")
        assert "OperatorA" in node3.operator_to_price
        assert "OperatorB" in node3.operator_to_price
        assert node3.operator_to_price["OperatorA"] == 0.05
        assert node3.operator_to_price["OperatorB"] == 0.03

    @pytest.mark.asyncio
    async def test_find_longest_match_and_smallest_price(self, trie_price):
        await trie_price.insert("123", 0.05, "OperatorA")
        await trie_price.insert("1234", 0.03, "OperatorA")
        await trie_price.insert("123", 0.04, "OperatorB")

        # Test exact match
        result = await trie_price.find_longest_match_and_smallest_price("123567890")
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
        await trie_price.insert("123", 0.05, "OperatorA")

        result = await trie_price.find_longest_match_and_smallest_price("9999999999")
        assert result is None


class TestTriePriceDB:
    @pytest.fixture
    def trie_price_db(self):
        TriePriceDB._instance = None
        return TriePriceDB()

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        TriePriceDB._instance = None
        db1 = TriePriceDB()
        db2 = TriePriceDB()
        assert db1 is db2

    @pytest.mark.asyncio
    async def test_find_cheapest_price(self, trie_price_db):
        operator_to_entries = TestDataFactory.create_price_data()

        await trie_price_db.build_data_structure(operator_to_entries)

        result = await trie_price_db.find_cheapest_price("1234567890")
        assert result is not None
        operator, price, prefix = result
        assert operator == "OperatorA"
        assert price == 0.03
        assert prefix == "1234"
