"""
Tests for base agent class.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langgraph.graph import StateGraph

from app.ai.agents.base_agent import BaseAgent, AgentState
from app.ai.config import AIConfig


class TestConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def __init__(self, config: AIConfig):
        super().__init__(config)
        self.agent_type = "test"
    
    async def _process_message(self, state: AgentState) -> AgentState:
        """Test implementation of message processing."""
        state["messages"].append({
            "role": "assistant",
            "content": "Test response from concrete agent"
        })
        return state
    
    def _get_system_prompt(self) -> str:
        """Test system prompt."""
        return "You are a test agent."


class TestBaseAgent:
    """Test base agent functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock AI configuration."""
        config = MagicMock(spec=AIConfig)
        config.agent_configs = {
            "test": {
                "name": "Test Agent",
                "max_memory_items": 10,
                "capabilities": ["testing"]
            }
        }
        config.redis_host = "localhost"
        config.redis_port = 6379
        return config
    
    @pytest.fixture
    def test_agent(self, mock_config):
        """Create test agent instance."""
        with patch('app.ai.agents.base_agent.redis.Redis'):
            agent = TestConcreteAgent(mock_config)
            return agent
    
    def test_agent_initialization(self, test_agent, mock_config):
        """Test agent initialization."""
        assert test_agent.config == mock_config
        assert test_agent.agent_type == "test"
        assert isinstance(test_agent.graph, StateGraph)
    
    @pytest.mark.asyncio
    async def test_process_simple_query(self, test_agent):
        """Test processing a simple query."""
        query = "What can you help me with?"
        user_context = {"user_id": "test-user", "role": "producer"}
        
        with patch.object(test_agent, '_load_conversation_memory', return_value=[]), \
             patch.object(test_agent, '_save_conversation_memory'):
            
            response = await test_agent.process(query, user_context)
            
            assert "content" in response
            assert response["content"] == "Test response from concrete agent"
    
    @pytest.mark.asyncio
    async def test_conversation_memory_management(self, test_agent):
        """Test conversation memory loading and saving."""
        conversation_id = "test-conv-123"
        memory_data = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
        
        # Mock Redis operations
        test_agent.memory_store = AsyncMock()
        test_agent.memory_store.get.return_value = str(memory_data).encode()
        
        loaded_memory = await test_agent._load_conversation_memory(conversation_id)
        assert loaded_memory == memory_data
        
        # Test saving memory
        await test_agent._save_conversation_memory(conversation_id, memory_data)
        test_agent.memory_store.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_trimming(self, test_agent):
        """Test memory trimming when exceeding max items."""
        conversation_id = "test-conv-456"
        
        # Create memory that exceeds max_memory_items (10)
        long_memory = []
        for i in range(15):
            long_memory.extend([
                {"role": "user", "content": f"Message {i}"},
                {"role": "assistant", "content": f"Response {i}"}
            ])
        
        test_agent.memory_store = AsyncMock()
        
        await test_agent._save_conversation_memory(conversation_id, long_memory)
        
        # Verify that memory was trimmed to max_memory_items * 2 (user + assistant pairs)
        saved_args = test_agent.memory_store.set.call_args[0]
        saved_memory = eval(saved_args[1])  # Convert back from string
        assert len(saved_memory) <= 20  # 10 pairs max
    
    def test_system_prompt_generation(self, test_agent):
        """Test system prompt generation."""
        system_prompt = test_agent._get_system_prompt()
        assert system_prompt == "You are a test agent."
    
    @pytest.mark.asyncio
    async def test_initialize_conversation(self, test_agent):
        """Test conversation initialization."""
        initial_state = {
            "messages": [{"role": "user", "content": "Hello"}],
            "conversation_id": "test-conv",
            "user_context": {"user_id": "test-user"}
        }
        
        result_state = await test_agent._initialize_conversation(initial_state)
        
        assert "messages" in result_state
        assert len(result_state["messages"]) >= 1
        # Should have system message added
        system_messages = [msg for msg in result_state["messages"] if msg["role"] == "system"]
        assert len(system_messages) == 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_agent):
        """Test error handling in agent processing."""
        query = "Test error handling"
        user_context = {"user_id": "test-user"}
        
        # Mock an error in message processing
        with patch.object(test_agent, '_process_message', side_effect=Exception("Test error")), \
             patch.object(test_agent, '_load_conversation_memory', return_value=[]), \
             patch.object(test_agent, '_save_conversation_memory'):
            
            response = await test_agent.process(query, user_context)
            
            assert "error" in response
            assert "Test error" in response["error"]
    
    def test_graph_structure(self, test_agent):
        """Test that the graph is properly structured."""
        # Verify that required nodes exist
        nodes = test_agent.graph.nodes
        assert "initialize" in nodes
        assert "process" in nodes
        assert "finalize" in nodes
        
        # Verify entry and finish points
        assert test_agent.graph.entry_point == "initialize"
        assert "finalize" in test_agent.graph.finish_point
    
    @pytest.mark.asyncio
    async def test_concurrent_conversations(self, test_agent):
        """Test handling multiple concurrent conversations."""
        import asyncio
        
        async def process_conversation(conv_id, message):
            user_context = {"user_id": f"user-{conv_id}", "conversation_id": conv_id}
            return await test_agent.process(message, user_context)
        
        with patch.object(test_agent, '_load_conversation_memory', return_value=[]), \
             patch.object(test_agent, '_save_conversation_memory'):
            
            # Process multiple conversations concurrently
            tasks = [
                process_conversation("conv1", "Message 1"),
                process_conversation("conv2", "Message 2"),
                process_conversation("conv3", "Message 3")
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert len(results) == 3
            for result in results:
                assert "content" in result
                assert result["content"] == "Test response from concrete agent"