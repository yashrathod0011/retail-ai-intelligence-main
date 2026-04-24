# tests/test_database.py
import pytest
from src.database.mongo_manager import MongoDBManager


class TestDatabase:
    """Test database operations"""

    @pytest.fixture
    def db_manager(self):
        """Create database manager instance"""
        return MongoDBManager()

    def test_database_connection(self, db_manager):
        """Test database connection"""
        assert db_manager.client is not None
        assert db_manager.db is not None

    def test_get_database_stats(self, db_manager):
        """Test getting database stats"""
        stats = db_manager.get_database_stats()
        assert "total_products" in stats
        assert "platforms" in stats
        assert "categories" in stats

    def test_upsert_product_insert(self, db_manager, sample_product):
        """Test inserting a new product"""
        result = db_manager.upsert_product(sample_product)
        assert "action" in result
        assert (
            result["unique_id"]
            == f"{sample_product['platform']}_{sample_product['product_id']}"
        )
