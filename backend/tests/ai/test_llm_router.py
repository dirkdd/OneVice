"""
Tests for LLM router module.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from app.ai.llm.router import LLMRouter, QueryComplexity
from app.ai.config import LLMProvider


class TestLLMRouter:
    """Test LLM router functionality."""
    
    @pytest.fixture
    def llm_router(self):
        """Create LLM router instance for testing."""
        with patch('app.ai.llm.router.Together') as mock_together, \
             patch('app.ai.llm.router.OpenAI') as mock_openai:
            
            mock_together_client = AsyncMock()
            mock_openai_client = AsyncMock()
            mock_together.return_value = mock_together_client
            mock_openai.return_value = mock_openai_client
            
            router = LLMRouter()
            return router, mock_together_client, mock_openai_client
    
    @pytest.mark.asyncio
    async def test_route_query_together_provider(self, llm_router):
        """Test routing query to Together.ai provider."""
        router, mock_together, mock_openai = llm_router
        
        mock_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100}
        }
        mock_together.chat.completions.create = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "Test query"}]
        result = await router.route_query(
            messages=messages,
            agent_type="sales",
            complexity=QueryComplexity.SIMPLE,
            preferred_provider=LLMProvider.TOGETHER
        )
        
        assert result == mock_response
        mock_together.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_query_openai_fallback(self, llm_router):
        """Test fallback to OpenAI when Together.ai fails."""
        router, mock_together, mock_openai = llm_router
        
        # Mock Together.ai failure
        mock_together.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        mock_response = {
            "choices": [{"message": {"content": "Fallback response"}}],
            "usage": {"total_tokens": 120}
        }
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "Test query"}]
        result = await router.route_query(
            messages=messages,
            agent_type="sales",
            complexity=QueryComplexity.SIMPLE,
            preferred_provider=LLMProvider.TOGETHER
        )
        
        assert result == mock_response
        mock_openai.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, llm_router):
        """Test streaming response functionality."""
        router, mock_together, mock_openai = llm_router
        
        async def mock_stream():
            for chunk in ["Hello", " world", "!"]:
                yield {"choices": [{"delta": {"content": chunk}}]}
        
        mock_together.chat.completions.create = AsyncMock(return_value=mock_stream())
        
        messages = [{"role": "user", "content": "Test streaming"}]
        stream = await router.route_query(
            messages=messages,
            agent_type="sales",
            complexity=QueryComplexity.SIMPLE,
            stream=True
        )
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert len(chunks) == 3
        assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
    
    def test_select_provider_simple_query(self, llm_router):
        """Test provider selection for simple queries."""
        router, _, _ = llm_router
        
        provider = router._select_provider(
            complexity=QueryComplexity.SIMPLE,
            agent_type="sales",
            preferred=None
        )
        
        assert provider == LLMProvider.TOGETHER
    
    def test_select_provider_complex_query(self, llm_router):
        """Test provider selection for complex queries."""
        router, _, _ = llm_router
        
        provider = router._select_provider(
            complexity=QueryComplexity.COMPLEX,
            agent_type="analytics",
            preferred=None
        )
        
        # Complex analytics queries should prefer OpenAI
        assert provider == LLMProvider.OPENAI
    
    def test_select_provider_preferred_override(self, llm_router):
        """Test preferred provider override."""
        router, _, _ = llm_router
        
        provider = router._select_provider(
            complexity=QueryComplexity.SIMPLE,
            agent_type="sales",
            preferred=LLMProvider.OPENAI
        )
        
        assert provider == LLMProvider.OPENAI
    
    @pytest.mark.asyncio
    async def test_get_model_for_provider_together(self, llm_router):
        """Test model selection for Together.ai provider."""
        router, _, _ = llm_router
        
        model = await router._get_model_for_provider(
            provider=LLMProvider.TOGETHER,
            complexity=QueryComplexity.SIMPLE,
            agent_type="sales"
        )
        
        assert "mixtral" in model.lower() or "llama" in model.lower()
    
    @pytest.mark.asyncio
    async def test_get_model_for_provider_openai(self, llm_router):
        """Test model selection for OpenAI provider."""
        router, _, _ = llm_router
        
        model = await router._get_model_for_provider(
            provider=LLMProvider.OPENAI,
            complexity=QueryComplexity.COMPLEX,
            agent_type="analytics"
        )
        
        assert "gpt-4" in model.lower()
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, llm_router):
        """Test cost tracking functionality."""
        router, mock_together, mock_openai = llm_router
        
        mock_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
        }
        mock_together.chat.completions.create = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "Test cost tracking"}]
        await router.route_query(
            messages=messages,
            agent_type="sales",
            complexity=QueryComplexity.SIMPLE
        )
        
        # Verify cost tracking (implementation would track actual costs)
        assert router._usage_stats["total_requests"] > 0
        assert router._usage_stats["total_tokens"] > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, llm_router):
        """Test rate limiting functionality."""
        router, mock_together, mock_openai = llm_router
        
        # Mock rate limit exceeded response
        rate_limit_error = Exception("Rate limit exceeded")
        mock_together.chat.completions.create = AsyncMock(side_effect=rate_limit_error)
        
        # Should fallback to OpenAI when rate limited
        mock_response = {"choices": [{"message": {"content": "Fallback response"}}]}
        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "Test rate limiting"}]
        result = await router.route_query(
            messages=messages,
            agent_type="sales",
            complexity=QueryComplexity.SIMPLE
        )
        
        assert result == mock_response
        mock_openai.chat.completions.create.assert_called_once()


class TestQueryComplexity:
    """Test query complexity enumeration."""
    
    def test_complexity_values(self):
        """Test complexity enumeration values."""
        assert QueryComplexity.SIMPLE == "simple"
        assert QueryComplexity.MODERATE == "moderate"
        assert QueryComplexity.COMPLEX == "complex"