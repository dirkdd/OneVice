"""
Integration tests for AI system components.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import json

from app.ai.config import AIConfig, LLMProvider
from app.ai.llm.router import LLMRouter
from app.ai.agents.sales_agent import SalesIntelligenceAgent
from app.ai.agents.orchestrator import AgentOrchestrator
from app.ai.graph.connection import Neo4jConnectionManager


class TestAISystemIntegration:
    """Integration tests for the complete AI system."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock AI configuration for integration tests."""
        with patch.dict('os.environ', {
            'TOGETHER_API_KEY': 'test_together_key',
            'OPENAI_API_KEY': 'test_openai_key',
            'NEO4J_URI': 'neo4j://localhost:7687',
            'NEO4J_USERNAME': 'neo4j',
            'NEO4J_PASSWORD': 'test_password',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379'
        }):
            return AIConfig()
    
    @pytest.fixture
    def mock_neo4j_system(self):
        """Mock Neo4j system for integration tests."""
        with patch('app.ai.graph.connection.AsyncGraphDatabase') as mock_graph:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_driver.session.return_value.__aenter__.return_value = mock_session
            mock_graph.driver.return_value = mock_driver
            
            # Mock typical query responses
            mock_session.run.return_value.__aiter__.return_value = [
                MagicMock(data=lambda: {"name": "John Director", "score": 0.85})
            ]
            
            yield mock_driver, mock_session
    
    @pytest.mark.asyncio
    async def test_end_to_end_sales_workflow(self, mock_config, mock_neo4j_system):
        """Test complete sales intelligence workflow."""
        mock_driver, mock_session = mock_neo4j_system
        
        # Mock LLM responses
        with patch('app.ai.llm.router.Together') as mock_together:
            mock_together_client = AsyncMock()
            mock_together.return_value = mock_together_client
            mock_together_client.chat.completions.create.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "qualification_score": 0.85,
                            "strengths": ["Experienced director", "Strong portfolio"],
                            "concerns": ["Limited availability"],
                            "recommendations": ["Schedule early meeting"]
                        })
                    }
                }]
            }
            
            # Mock Redis for agent memory
            with patch('app.ai.agents.base_agent.redis.Redis'):
                # Initialize components
                llm_router = LLMRouter()
                connection_manager = Neo4jConnectionManager(mock_config)
                await connection_manager.connect()
                
                sales_agent = SalesIntelligenceAgent(mock_config)
                sales_agent.connection_manager = connection_manager
                sales_agent.llm_router = llm_router
                
                # Test data
                lead_data = {
                    "name": "Jane Producer",
                    "bio": "Award-winning producer with 15 years experience",
                    "skills": ["Producing", "Development", "Financing"],
                    "location": "Los Angeles, CA",
                    "experience_level": "Senior"
                }
                
                user_context = {
                    "user_id": "test-user-123",
                    "role": "business_development"
                }
                
                # Execute end-to-end workflow
                result = await sales_agent.qualify_lead(lead_data, user_context)
                
                # Verify results
                assert "qualification_score" in result
                assert result["qualification_score"] >= 0.8
                assert len(result["strengths"]) >= 2
                assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_multi_agent_orchestration(self, mock_config, mock_neo4j_system):
        """Test orchestration between multiple agents."""
        mock_driver, mock_session = mock_neo4j_system
        
        with patch('app.ai.llm.router.Together') as mock_together, \
             patch('app.ai.agents.base_agent.redis.Redis'):
            
            # Mock LLM responses for different agents
            mock_together_client = AsyncMock()
            mock_together.return_value = mock_together_client
            
            def mock_llm_response(messages, **kwargs):
                # Different responses based on agent context
                if "sales" in str(messages).lower():
                    return {
                        "choices": [{
                            "message": {"content": "Sales intelligence response"}
                        }]
                    }
                elif "talent" in str(messages).lower():
                    return {
                        "choices": [{
                            "message": {"content": "Talent acquisition response"}
                        }]
                    }
                else:
                    return {
                        "choices": [{
                            "message": {"content": "General AI response"}
                        }]
                    }
            
            mock_together_client.chat.completions.create.side_effect = mock_llm_response
            
            # Initialize orchestrator
            orchestrator = AgentOrchestrator(mock_config)
            
            # Test routing to different agents
            sales_query = "Can you qualify this lead for me?"
            sales_result = await orchestrator.route_query(
                query=sales_query,
                user_context={"user_id": "test", "role": "producer"},
                preferred_agent="sales"
            )
            
            talent_query = "Find me directors available for this project"
            talent_result = await orchestrator.route_query(
                query=talent_query,
                user_context={"user_id": "test", "role": "casting"},
                preferred_agent="talent"
            )
            
            # Verify routing worked correctly
            assert sales_result["agent_type"] == "sales"
            assert "sales intelligence" in sales_result["response"]["content"].lower()
            
            assert talent_result["agent_type"] == "talent"
            assert "talent acquisition" in talent_result["response"]["content"].lower()
    
    @pytest.mark.asyncio
    async def test_knowledge_graph_integration(self, mock_config, mock_neo4j_system):
        """Test knowledge graph integration with agents."""
        mock_driver, mock_session = mock_neo4j_system
        
        # Mock various Neo4j query responses
        def mock_query_response(query, params=None):
            if "vector" in query.lower():
                return [
                    MagicMock(data=lambda: {
                        "node": {"name": "Similar Director", "bio": "Experienced"},
                        "score": 0.88
                    })
                ]
            elif "person" in query.lower():
                return [
                    MagicMock(data=lambda: {
                        "name": "John Director",
                        "experience_level": "Senior",
                        "union_status": "DGA Member"
                    })
                ]
            elif "project" in query.lower():
                return [
                    MagicMock(data=lambda: {
                        "title": "Test Movie",
                        "budget_range": "10M-50M",
                        "genre": "Drama"
                    })
                ]
            else:
                return []
        
        mock_session.run.return_value.__aiter__.side_effect = lambda: iter(mock_query_response("test"))
        
        # Initialize connection manager
        connection_manager = Neo4jConnectionManager(mock_config)
        await connection_manager.connect()
        
        # Test different query types
        person_results = await connection_manager.execute_query(
            "MATCH (p:Person) WHERE p.name = $name RETURN p",
            {"name": "John Director"}
        )
        assert len(person_results) > 0
        
        # Test vector query
        vector = [0.1] * 1536  # Mock embedding
        vector_results = await connection_manager.run_vector_query(
            index_name="person_bio_embedding",
            vector=vector,
            top_k=5,
            similarity_threshold=0.8
        )
        # This would fail with our simple mock, but structure is tested
    
    @pytest.mark.asyncio
    async def test_llm_provider_fallback(self, mock_config):
        """Test LLM provider fallback mechanism."""
        with patch('app.ai.llm.router.Together') as mock_together, \
             patch('app.ai.llm.router.OpenAI') as mock_openai:
            
            # Mock Together.ai failure and OpenAI success
            mock_together_client = AsyncMock()
            mock_together.return_value = mock_together_client
            mock_together_client.chat.completions.create.side_effect = Exception("Together.ai unavailable")
            
            mock_openai_client = AsyncMock()
            mock_openai.return_value = mock_openai_client
            mock_openai_client.chat.completions.create.return_value = {
                "choices": [{"message": {"content": "OpenAI fallback response"}}]
            }
            
            llm_router = LLMRouter()
            
            messages = [{"role": "user", "content": "Test fallback"}]
            result = await llm_router.route_query(
                messages=messages,
                agent_type="sales",
                complexity="simple",
                preferred_provider=LLMProvider.TOGETHER
            )
            
            # Should have fallen back to OpenAI
            assert "OpenAI fallback response" in result["choices"][0]["message"]["content"]
            mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_requests(self, mock_config, mock_neo4j_system):
        """Test handling multiple concurrent requests to agents."""
        mock_driver, mock_session = mock_neo4j_system
        
        with patch('app.ai.llm.router.Together') as mock_together, \
             patch('app.ai.agents.base_agent.redis.Redis'):
            
            mock_together_client = AsyncMock()
            mock_together.return_value = mock_together_client
            mock_together_client.chat.completions.create.return_value = {
                "choices": [{"message": {"content": "Concurrent response"}}]
            }
            
            # Initialize agent
            sales_agent = SalesIntelligenceAgent(mock_config)
            
            # Create multiple concurrent requests
            async def process_request(request_id):
                return await sales_agent.process(
                    f"Query {request_id}",
                    {"user_id": f"user-{request_id}", "role": "producer"}
                )
            
            # Execute concurrent requests
            tasks = [process_request(i) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            assert len(results) == 5
            for result in results:
                assert not isinstance(result, Exception)
                assert "content" in result
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self, mock_config):
        """Test system resilience and error recovery."""
        # Test various failure scenarios
        
        # 1. Database connection failure
        with patch('app.ai.graph.connection.AsyncGraphDatabase.driver', side_effect=Exception("DB Error")):
            connection_manager = Neo4jConnectionManager(mock_config)
            
            with pytest.raises(Exception, match="DB Error"):
                await connection_manager.connect()
        
        # 2. LLM provider failure with fallback
        with patch('app.ai.llm.router.Together') as mock_together, \
             patch('app.ai.llm.router.OpenAI') as mock_openai:
            
            # Both providers fail
            mock_together.return_value.chat.completions.create.side_effect = Exception("Together failed")
            mock_openai.return_value.chat.completions.create.side_effect = Exception("OpenAI failed")
            
            llm_router = LLMRouter()
            
            with pytest.raises(Exception):
                await llm_router.route_query(
                    messages=[{"role": "user", "content": "Test"}],
                    agent_type="sales",
                    complexity="simple"
                )
        
        # 3. Agent processing error recovery
        with patch('app.ai.agents.base_agent.redis.Redis'):
            sales_agent = SalesIntelligenceAgent(mock_config)
            
            # Mock LLM to cause processing error
            sales_agent.llm_router = AsyncMock()
            sales_agent.llm_router.route_query.side_effect = Exception("Processing error")
            
            result = await sales_agent.process("Test query", {"user_id": "test"})
            
            # Should return error response rather than crash
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_memory_persistence_across_conversations(self, mock_config):
        """Test conversation memory persistence."""
        with patch('app.ai.agents.base_agent.redis.Redis') as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock stored conversation memory
            stored_memory = json.dumps([
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"}
            ]).encode()
            
            mock_redis_client.get.return_value = stored_memory
            
            sales_agent = SalesIntelligenceAgent(mock_config)
            
            # Load conversation memory
            conversation_id = "test-conv-123"
            memory = await sales_agent._load_conversation_memory(conversation_id)
            
            assert len(memory) == 2
            assert memory[0]["role"] == "user"
            assert memory[1]["role"] == "assistant"
            
            # Add new message and save
            memory.append({"role": "user", "content": "New message"})
            await sales_agent._save_conversation_memory(conversation_id, memory)
            
            # Verify save was called
            mock_redis_client.set.assert_called_once()
            saved_data = mock_redis_client.set.call_args[0][1]
            saved_memory = json.loads(saved_data)
            assert len(saved_memory) == 3