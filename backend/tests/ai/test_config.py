"""
Tests for AI configuration module.
"""
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.ai.config import AIConfig, LLMProvider


class TestAIConfig:
    """Test AI configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        with patch.dict('os.environ', {
            'TOGETHER_API_KEY': 'test_together_key',
            'OPENAI_API_KEY': 'test_openai_key',
            'NEO4J_URI': 'neo4j://localhost:7687',
            'NEO4J_USERNAME': 'neo4j',
            'NEO4J_PASSWORD': 'test_password',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379'
        }):
            config = AIConfig()
            
            assert config.default_provider == LLMProvider.TOGETHER
            assert config.together_api_key == 'test_together_key'
            assert config.openai_api_key == 'test_openai_key'
            assert config.neo4j_uri == 'neo4j://localhost:7687'
            assert config.neo4j_username == 'neo4j'
            assert config.neo4j_password == 'test_password'
    
    def test_missing_required_env_vars(self):
        """Test validation error when required environment variables are missing."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValidationError):
                AIConfig()
    
    def test_llm_provider_enum(self):
        """Test LLM provider enumeration."""
        assert LLMProvider.TOGETHER == "together"
        assert LLMProvider.OPENAI == "openai"
    
    def test_agent_config(self):
        """Test agent configuration settings."""
        with patch.dict('os.environ', {
            'TOGETHER_API_KEY': 'test_together_key',
            'OPENAI_API_KEY': 'test_openai_key',
            'NEO4J_URI': 'neo4j://localhost:7687',
            'NEO4J_USERNAME': 'neo4j',
            'NEO4J_PASSWORD': 'test_password',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379'
        }):
            config = AIConfig()
            
            assert "sales" in config.agent_configs
            assert "talent" in config.agent_configs
            assert "analytics" in config.agent_configs
            
            sales_config = config.agent_configs["sales"]
            assert sales_config["name"] == "Sales Intelligence Agent"
            assert sales_config["max_memory_items"] == 50
            assert "lead_qualification" in sales_config["capabilities"]
    
    def test_vector_search_config(self):
        """Test vector search configuration."""
        with patch.dict('os.environ', {
            'TOGETHER_API_KEY': 'test_together_key',
            'OPENAI_API_KEY': 'test_openai_key',
            'NEO4J_URI': 'neo4j://localhost:7687',
            'NEO4J_USERNAME': 'neo4j',
            'NEO4J_PASSWORD': 'test_password',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379'
        }):
            config = AIConfig()
            
            assert config.vector_dimensions == 1536
            assert config.vector_similarity_threshold == 0.8
            assert config.max_vector_results == 10