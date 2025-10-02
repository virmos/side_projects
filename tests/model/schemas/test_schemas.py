import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from models.schemas.pricing import PhoneNumberIn, CheapestOut, PriceEntry


class TestPricingSchemas:
    def test_price_entry_creation(self):
        entry = PriceEntry(prefix="123", operator="OperatorA", price=0.05)
        
        assert entry.prefix == "123"
        assert entry.operator == "OperatorA"
        assert entry.price == 0.05
    
    def test_price_entry_default_values(self):
        entry = PriceEntry()
        
        assert entry.prefix == ""
        assert entry.operator == ""
        assert entry.price == 0
    

    def test_phone_number_in_normalization(self):
        phone_in = PhoneNumberIn(phone_number="+1234567890")
        assert phone_in.phone_number == "1234567890"
        
        phone_in = PhoneNumberIn(phone_number="123-456-7890")
        assert phone_in.phone_number == "1234567890"
        
        phone_in = PhoneNumberIn(phone_number="+1-234-567-890")
        assert phone_in.phone_number == "1234567890"
        
        phone_in = PhoneNumberIn(phone_number="123 456 7890")
        assert phone_in.phone_number == "123 456 7890"
    
    def test_phone_number_in_validation(self):
        phone_in = PhoneNumberIn(phone_number="1234567890")
        assert phone_in.phone_number == "1234567890"
        
        phone_in = PhoneNumberIn(phone_number="")
        assert phone_in.phone_number == ""
    
    def test_cheapest_out_creation(self):
        cheapest = CheapestOut(operator="OperatorA", price=0.05, prefix="123")
        
        assert cheapest.operator == "OperatorA"
        assert cheapest.price == 0.05
        assert cheapest.prefix == "123"
    
    def test_cheapest_out_validation(self):
        cheapest = CheapestOut(operator="OperatorA", price=0.05, prefix="123")
        assert cheapest.operator == "OperatorA"
        assert cheapest.price == 0.05
        assert cheapest.prefix == "123"
        
        cheapest = CheapestOut(operator="OperatorA", price=0.0, prefix="123")
        assert cheapest.price == 0.0
        
        cheapest = CheapestOut(operator="OperatorA", price=-0.01, prefix="123")
        assert cheapest.price == -0.01
