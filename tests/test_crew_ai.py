# tests/test_crew_ai.py
import pytest
from src.database.mongo_manager import db_manager
from src.agents.crew_manager import crew_manager


class TestCrewAI:
    """Test CrewAI multi-agent system"""
    
    @pytest.mark.slow
    def test_crew_manager_initialization(self):
        """Test that crew manager initializes correctly"""
        assert crew_manager is not None
        assert crew_manager.task_delay_seconds > 0
    
    @pytest.mark.slow
    def test_create_agents(self):
        """Test agent creation"""
        agents = crew_manager.create_agents()
        
        assert 'scout' in agents
        assert 'pricing' in agents
        assert 'risk' in agents
        assert 'forecast' in agents
        assert 'writer' in agents
    
    @pytest.mark.slow
    @pytest.mark.skipif(
        db_manager.products.count_documents({}) == 0,
        reason="No products in database to analyze"
    )
    def test_analyze_products(self):
        """Test full crew analysis (slow test - skipped in CI)"""
        # Get some products from database
        products = list(db_manager.products.find().limit(5))
        
        if len(products) > 0:
            # This will take several minutes
            result = crew_manager.analyze_products(products)
            
            assert result is not None
            assert 'error' not in result or result.get('tasks_completed', 0) > 0