"""
Tests for AI API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

from app.api.ai.chat import ai_chat_router
from app.api.ai.agents import ai_agents_router


# Create test app
app = FastAPI()
app.include_router(ai_chat_router, prefix="/ai")
app.include_router(ai_agents_router, prefix="/ai")

client = TestClient(app)


class TestAIChatEndpoints:
    """Test AI chat endpoints."""
    
    @pytest.fixture
    def mock_auth(self):
        """Mock authentication dependency."""
        with patch('app.api.ai.chat.get_current_user') as mock:
            mock.return_value = {
                "user_id": "test-user-123",
                "email": "test@example.com",
                "role": "producer"
            }
            yield mock
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock agent orchestrator."""
        with patch('app.api.ai.chat.agent_orchestrator') as mock:
            orchestrator = AsyncMock()
            mock.return_value = orchestrator
            yield orchestrator
    
    def test_chat_endpoint_success(self, mock_auth, mock_orchestrator):
        """Test successful chat request."""
        mock_orchestrator.route_query.return_value = {
            "agent_type": "sales",
            "response": {
                "content": "Hello! I'm your sales intelligence agent.",
                "confidence": 0.9
            }
        }
        
        response = client.post("/ai/chat", json={
            "message": "Hello, I need help with lead qualification",
            "agent_type": "sales",
            "conversation_id": "conv-123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "sales"
        assert "content" in data["response"]
        assert data["response"]["confidence"] == 0.9
    
    def test_chat_endpoint_missing_message(self, mock_auth):
        """Test chat endpoint with missing message."""
        response = client.post("/ai/chat", json={
            "agent_type": "sales"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_invalid_agent_type(self, mock_auth):
        """Test chat endpoint with invalid agent type."""
        response = client.post("/ai/chat", json={
            "message": "Hello",
            "agent_type": "invalid_agent"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_unauthorized(self):
        """Test chat endpoint without authentication."""
        with patch('app.api.ai.chat.get_current_user', side_effect=Exception("Unauthorized")):
            response = client.post("/ai/chat", json={
                "message": "Hello",
                "agent_type": "sales"
            })
            
            assert response.status_code == 500  # Should handle auth error


class TestAIAgentsEndpoints:
    """Test AI agents management endpoints."""
    
    @pytest.fixture
    def mock_auth(self):
        """Mock authentication dependency."""
        with patch('app.api.ai.agents.get_current_user') as mock:
            mock.return_value = {
                "user_id": "test-user-123",
                "email": "test@example.com",
                "role": "producer"
            }
            yield mock
    
    @pytest.fixture
    def mock_agents(self):
        """Mock agent instances."""
        with patch('app.api.ai.agents.sales_agent') as mock_sales, \
             patch('app.api.ai.agents.talent_agent') as mock_talent, \
             patch('app.api.ai.agents.analytics_agent') as mock_analytics, \
             patch('app.api.ai.agents.knowledge_service') as mock_knowledge:
            
            mock_sales.qualify_lead = AsyncMock(return_value={
                "qualification_score": 0.85,
                "strengths": ["Experienced", "Available"],
                "concerns": ["High rate"],
                "recommendations": ["Negotiate rate"]
            })
            
            mock_talent.search_talent = AsyncMock(return_value={
                "matches": [{"name": "John Director", "score": 0.9}],
                "total_found": 1
            })
            
            mock_analytics.analyze_performance = AsyncMock(return_value={
                "performance_score": 0.78,
                "key_metrics": {"efficiency": 0.8, "quality": 0.85},
                "insights": ["Strong performance in Q3"]
            })
            
            mock_knowledge.search = AsyncMock(return_value={
                "results": [{"type": "Person", "name": "Test Person"}],
                "total": 1
            })
            
            yield {
                "sales": mock_sales,
                "talent": mock_talent, 
                "analytics": mock_analytics,
                "knowledge": mock_knowledge
            }
    
    def test_list_agents_endpoint(self, mock_auth):
        """Test listing available agents."""
        response = client.get("/ai/agents/")
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) >= 3  # sales, talent, analytics
        
        # Check agent structure
        sales_agent = next(a for a in data["agents"] if a["type"] == "sales")
        assert "name" in sales_agent
        assert "capabilities" in sales_agent
        assert "description" in sales_agent
    
    def test_qualify_lead_endpoint(self, mock_auth, mock_agents, sample_person_data):
        """Test lead qualification endpoint."""
        response = client.post("/ai/agents/sales/qualify-lead", json={
            "lead_info": sample_person_data
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["qualification_score"] == 0.85
        assert "strengths" in data
        assert "concerns" in data
        assert "recommendations" in data
    
    def test_search_talent_endpoint(self, mock_auth, mock_agents):
        """Test talent search endpoint."""
        response = client.post("/ai/agents/talent/search", json={
            "requirements": {
                "skills": ["Directing"],
                "experience_level": "Senior",
                "location": "Los Angeles"
            },
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert "total_found" in data
        assert len(data["matches"]) == 1
    
    def test_performance_analysis_endpoint(self, mock_auth, mock_agents):
        """Test performance analysis endpoint."""
        response = client.post("/ai/agents/analytics/performance", json={
            "entity_type": "person",
            "entity_id": "person-123",
            "metrics": ["efficiency", "quality", "collaboration"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "performance_score" in data
        assert "key_metrics" in data
        assert "insights" in data
    
    def test_direct_chat_endpoint(self, mock_auth):
        """Test direct agent chat endpoint."""
        with patch('app.api.ai.agents.sales_agent.process') as mock_process:
            mock_process.return_value = {
                "content": "I can help you with lead qualification.",
                "confidence": 0.9
            }
            
            response = client.post("/ai/agents/sales/direct-chat", json={
                "message": "What can you help me with?",
                "conversation_id": "conv-456"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert data["confidence"] == 0.9
    
    def test_knowledge_search_endpoint(self, mock_auth, mock_agents):
        """Test knowledge graph search endpoint."""
        response = client.post("/ai/agents/knowledge/search", json={
            "query": "Find directors in Los Angeles",
            "entity_types": ["Person"],
            "limit": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert data["total"] == 1
    
    def test_invalid_agent_type_in_direct_chat(self, mock_auth):
        """Test direct chat with invalid agent type."""
        response = client.post("/ai/agents/invalid/direct-chat", json={
            "message": "Hello"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid agent type" in data["detail"]
    
    def test_missing_required_fields(self, mock_auth):
        """Test endpoints with missing required fields."""
        # Missing lead_info in qualify-lead
        response = client.post("/ai/agents/sales/qualify-lead", json={})
        assert response.status_code == 422
        
        # Missing requirements in talent search
        response = client.post("/ai/agents/talent/search", json={})
        assert response.status_code == 422
        
        # Missing message in direct chat
        response = client.post("/ai/agents/sales/direct-chat", json={})
        assert response.status_code == 422


class TestWebSocketEndpoints:
    """Test WebSocket endpoints."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        with patch('app.api.ai.websocket.agent_orchestrator') as mock_orchestrator:
            mock_orchestrator.route_query = AsyncMock(return_value={
                "agent_type": "sales",
                "response": {"content": "WebSocket response"}
            })
            
            with client.websocket_connect("/ws/ai/chat/test-user") as websocket:
                # Send a message
                websocket.send_json({
                    "message": "Hello via WebSocket",
                    "agent_type": "sales"
                })
                
                # Receive response
                data = websocket.receive_json()
                assert "agent_type" in data
                assert "response" in data
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling."""
        with patch('app.api.ai.websocket.agent_orchestrator') as mock_orchestrator:
            mock_orchestrator.route_query = AsyncMock(side_effect=Exception("Test error"))
            
            with client.websocket_connect("/ws/ai/chat/test-user") as websocket:
                websocket.send_json({
                    "message": "This should cause an error",
                    "agent_type": "sales"
                })
                
                data = websocket.receive_json()
                assert "error" in data
                assert "Test error" in data["error"]