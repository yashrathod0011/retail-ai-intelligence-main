# tests/conftest.py
import pytest
import os
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "mongodb_uri": os.getenv("MONGODB_URI"),
        "groq_api_key": os.getenv("GROQ_API_KEY"),
    }


@pytest.fixture
def sample_product():
    """Sample product data for testing"""
    return {
        "platform": "amazon",
        "product_id": "TEST123",
        "title": "Test Product",
        "price": 999.0,
        "rating": 4.5,
        "category": "electronics",
    }


@pytest.fixture
def sample_products():
    """Multiple sample products"""
    return [
        {
            "platform": "amazon",
            "product_id": "TEST001",
            "title": "Product 1",
            "price": 1000.0,
            "rating": 4.5,
        },
        {
            "platform": "amazon",
            "product_id": "TEST002",
            "title": "Product 2",
            "price": 2000.0,
            "rating": 4.0,
        },
    ]  # tests/conftest.py


import pytest
import os
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "mongodb_uri": os.getenv("MONGODB_URI"),
        "groq_api_key": os.getenv("GROQ_API_KEY"),
    }


@pytest.fixture
def sample_product():
    """Sample product data for testing"""
    return {
        "platform": "amazon",
        "product_id": "TEST123",
        "title": "Test Product",
        "price": 999.0,
        "rating": 4.5,
        "category": "electronics",
    }


@pytest.fixture
def sample_products():
    """Multiple sample products"""
    return [
        {
            "platform": "amazon",
            "product_id": "TEST001",
            "title": "Product 1",
            "price": 1000.0,
            "rating": 4.5,
        },
        {
            "platform": "amazon",
            "product_id": "TEST002",
            "title": "Product 2",
            "price": 2000.0,
            "rating": 4.0,
        },
    ]
