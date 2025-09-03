"""
Test configuration and fixtures for OneVice backend tests.
"""
import asyncio
import pytest
import os
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from neo4j import AsyncDriver
import redis.asyncio as redis

# Test environment variables
os.environ.update({
    "TOGETHER_API_KEY": "test_together_key",
    "OPENAI_API_KEY": "test_openai_key", 
    "NEO4J_URI": "neo4j://localhost:7687",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "test_password",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_PASSWORD": "",
    "JWT_SECRET_KEY": "test_secret_key",
    "ENVIRONMENT": "test"
})

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing."""
    driver = AsyncMock(spec=AsyncDriver)
    session = AsyncMock()
    driver.session.return_value.__aenter__.return_value = session
    return driver, session

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_client = AsyncMock(spec=redis.Redis)
    return redis_client

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "id": "test-response-id",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Test AI response"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }

@pytest.fixture
def sample_person_data():
    """Sample person data for testing."""
    return {
        "name": "John Director",
        "bio": "Acclaimed film director with 20 years of experience",
        "skills": ["Directing", "Cinematography", "Storytelling"],
        "location": "Los Angeles, CA",
        "contact_info": {
            "email": "john@example.com",
            "phone": "+1-555-0123"
        },
        "experience_level": "Senior",
        "union_status": "DGA Member"
    }

@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "title": "Test Movie",
        "type": "Feature Film",
        "status": "In Development",
        "budget_range": "10M-50M",
        "start_date": "2024-06-01",
        "location": "Los Angeles, CA",
        "genre": "Drama",
        "description": "A compelling drama about human relationships"
    }

@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "name": "Test Studios",
        "type": "Production Company",
        "location": "Beverly Hills, CA",
        "size": "Large",
        "founded": 1995,
        "specialties": ["Feature Films", "Television", "Streaming Content"]
    }

@pytest.fixture
def mock_user_context():
    """Mock user context for testing."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "role": "producer",
        "permissions": ["read:projects", "write:projects"],
        "company_id": "test-company-456"
    }

@pytest.fixture
def mock_agent_state():
    """Mock agent state for testing."""
    return {
        "conversation_id": "test-conv-123",
        "messages": [],
        "context": {},
        "user_id": "test-user-123",
        "agent_type": "sales",
        "session_data": {}
    }