# tests/test_helpers.py
import pytest
from src.utils.helpers import clean_price, clean_rating


class TestHelpers:
    """Test utility helper functions"""

    def test_clean_price_with_rupee_symbol(self):
        """Test price cleaning with rupee symbol"""
        assert clean_price("₹1,234") == 1234.0
        assert clean_price("₹10,999") == 10999.0

    def test_clean_price_with_comma(self):
        """Test price cleaning with commas"""
        assert clean_price("1,234") == 1234.0
        assert clean_price("10,00,000") == 1000000.0

    def test_clean_price_plain_number(self):
        """Test price cleaning with plain numbers"""
        assert clean_price("1234") == 1234.0
        assert clean_price("999.99") == 999.99
        assert clean_price("1234.50") == 1234.50

    def test_clean_price_invalid(self):
        """Test price cleaning with invalid input"""
        assert clean_price("") is None
        assert clean_price("invalid") is None
        assert clean_price(None) is None

    def test_clean_rating_with_text(self):
        """Test rating extraction from text"""
        assert clean_rating("4.5 out of 5 stars") == 4.5
        assert clean_rating("3.8 out of 5") == 3.8

    def test_clean_rating_plain_number(self):
        """Test rating with plain number"""
        assert clean_rating("4.5") == 4.5
        assert clean_rating("3") == 3.0

    def test_clean_rating_invalid(self):
        """Test rating with invalid input"""
        assert clean_rating("") is None
        assert clean_rating("invalid") is None
        assert clean_rating(None) is None
