"""
LLM Router

Intelligent routing between LLM providers with fallback handling,
cost optimization, and provider-specific configuration.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from enum import Enum
import httpx
import openai
from openai import AsyncOpenAI

from ..config import AIConfig, LLMProvider
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

class QueryComplexity(str, Enum):
    """Query complexity levels for model routing"""
    SIMPLE = "simple"      # Basic queries, factual lookups
    MODERATE = "moderate"  # Analysis, reasoning
    COMPLEX = "complex"    # Multi-step reasoning, planning

class LLMRouter:
    """
    Intelligent LLM router that selects optimal providers based on
    query complexity, cost, and availability.
    """
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.providers = {}
        self._initialize_providers()
        
        # Cost tracking
        self.cost_per_token = {
            LLMProvider.TOGETHER: 0.0001,  # Approximate cost per token
            LLMProvider.OPENAI: 0.0005,
        }
        
        # Performance tracking
        self.provider_stats = {
            provider: {"requests": 0, "failures": 0, "avg_response_time": 0}
            for provider in LLMProvider
        }

    def _initialize_providers(self):
        """Initialize LLM provider clients"""
        
        # Together.ai client (using OpenAI-compatible interface)
        if self.config.together_api_key:
            self.providers[LLMProvider.TOGETHER] = AsyncOpenAI(
                api_key=self.config.together_api_key,
                base_url=self.config.together_base_url
            )
            logger.info("Initialized Together.ai provider")
        
        # OpenAI client
        if self.config.openai_api_key:
            self.providers[LLMProvider.OPENAI] = AsyncOpenAI(
                api_key=self.config.openai_api_key
            )
            logger.info("Initialized OpenAI provider")

    async def route_query(
        self,
        messages: List[Dict[str, str]],
        agent_type: str = "general",
        complexity: Optional[QueryComplexity] = None,
        preferred_provider: Optional[LLMProvider] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Route query to optimal LLM provider
        
        Args:
            messages: Conversation messages
            agent_type: Type of agent making request
            complexity: Query complexity level
            preferred_provider: Preferred provider (optional)
            stream: Whether to stream response
            **kwargs: Additional parameters
            
        Returns:
            Response from LLM provider
        """
        
        # Determine query complexity if not provided
        if complexity is None:
            complexity = self._assess_complexity(messages)
        
        # Select optimal provider
        provider = self._select_provider(
            complexity=complexity,
            agent_type=agent_type,
            preferred=preferred_provider
        )
        
        # Execute query with fallback
        try:
            if stream:
                return self._stream_completion(provider, messages, **kwargs)
            else:
                return await self._complete(provider, messages, **kwargs)
                
        except Exception as e:
            logger.error(f"Primary provider {provider} failed: {e}")
            
            # Try fallback provider
            fallback = self._get_fallback_provider(provider)
            if fallback and fallback != provider:
                logger.info(f"Falling back to {fallback}")
                try:
                    if stream:
                        return self._stream_completion(fallback, messages, **kwargs)
                    else:
                        return await self._complete(fallback, messages, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback provider {fallback} also failed: {fallback_error}")
            
            raise AIProcessingError(f"All LLM providers failed: {e}")

    def _assess_complexity(self, messages: List[Dict[str, str]]) -> QueryComplexity:
        """Assess query complexity based on message content"""
        
        # Get the latest user message
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            return QueryComplexity.SIMPLE
            
        latest_message = user_messages[-1].get("content", "")
        
        # Simple heuristics for complexity assessment
        complexity_indicators = {
            "complex_keywords": ["analyze", "compare", "strategy", "plan", "optimize", "evaluate"],
            "multi_step_keywords": ["first", "then", "after", "step", "process"],
            "reasoning_keywords": ["because", "therefore", "explain why", "reasoning"],
        }
        
        content_lower = latest_message.lower()
        
        # Count indicators
        complex_count = sum(1 for keyword in complexity_indicators["complex_keywords"] 
                          if keyword in content_lower)
        multi_step_count = sum(1 for keyword in complexity_indicators["multi_step_keywords"]
                             if keyword in content_lower)
        reasoning_count = sum(1 for keyword in complexity_indicators["reasoning_keywords"]
                            if keyword in content_lower)
        
        # Determine complexity
        if (complex_count >= 2 or multi_step_count >= 2 or 
            reasoning_count >= 1 or len(latest_message) > 500):
            return QueryComplexity.COMPLEX
        elif complex_count >= 1 or multi_step_count >= 1 or len(latest_message) > 200:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE

    def _select_provider(
        self,
        complexity: QueryComplexity,
        agent_type: str,
        preferred: Optional[LLMProvider] = None
    ) -> LLMProvider:
        """Select optimal provider based on criteria"""
        
        # Use preferred provider if specified and available
        if preferred and preferred in self.providers:
            return preferred
        
        # Provider selection logic based on complexity and cost
        if complexity == QueryComplexity.COMPLEX:
            # Use OpenAI for complex reasoning (better quality)
            if LLMProvider.OPENAI in self.providers:
                return LLMProvider.OPENAI
        
        # Default to Together.ai for cost efficiency
        if LLMProvider.TOGETHER in self.providers:
            return LLMProvider.TOGETHER
        
        # Fallback to any available provider
        available_providers = list(self.providers.keys())
        if available_providers:
            return available_providers[0]
        
        raise AIProcessingError("No LLM providers available")

    def _get_fallback_provider(self, failed_provider: LLMProvider) -> Optional[LLMProvider]:
        """Get fallback provider when primary fails"""
        
        fallback_order = {
            LLMProvider.TOGETHER: LLMProvider.OPENAI,
            LLMProvider.OPENAI: LLMProvider.TOGETHER,
        }
        
        fallback = fallback_order.get(failed_provider)
        return fallback if fallback in self.providers else None

    async def _complete(
        self,
        provider: LLMProvider,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute non-streaming completion"""
        
        client = self.providers[provider]
        model_config = self.config.get_model_config(provider)
        
        # Prepare parameters
        params = {
            "model": model_config["model"],
            "messages": messages,
            "max_tokens": model_config.get("max_tokens", 2048),
            "temperature": model_config.get("temperature", 0.7),
            **kwargs
        }
        
        # Execute completion
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await client.chat.completions.create(**params)
            
            # Update statistics
            response_time = asyncio.get_event_loop().time() - start_time
            self._update_stats(provider, success=True, response_time=response_time)
            
            # Format response
            return {
                "content": response.choices[0].message.content,
                "provider": provider,
                "model": params["model"],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "response_time": response_time,
                "cost_estimate": self._estimate_cost(provider, response.usage.total_tokens)
            }
            
        except Exception as e:
            self._update_stats(provider, success=False)
            raise e

    async def _stream_completion(
        self,
        provider: LLMProvider,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming completion"""
        
        client = self.providers[provider]
        model_config = self.config.get_model_config(provider)
        
        # Prepare parameters
        params = {
            "model": model_config["model"],
            "messages": messages,
            "max_tokens": model_config.get("max_tokens", 2048),
            "temperature": model_config.get("temperature", 0.7),
            "stream": True,
            **kwargs
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            stream = await client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "provider": provider,
                        "model": params["model"],
                        "type": "content"
                    }
            
            # Final chunk with metadata
            response_time = asyncio.get_event_loop().time() - start_time
            self._update_stats(provider, success=True, response_time=response_time)
            
            yield {
                "type": "metadata",
                "provider": provider,
                "model": params["model"],
                "response_time": response_time
            }
            
        except Exception as e:
            self._update_stats(provider, success=False)
            raise e

    def _update_stats(
        self,
        provider: LLMProvider,
        success: bool = True,
        response_time: Optional[float] = None
    ):
        """Update provider performance statistics"""
        
        stats = self.provider_stats[provider]
        stats["requests"] += 1
        
        if not success:
            stats["failures"] += 1
        
        if response_time:
            # Update rolling average
            current_avg = stats["avg_response_time"]
            total_requests = stats["requests"]
            stats["avg_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )

    def _estimate_cost(self, provider: LLMProvider, total_tokens: int) -> float:
        """Estimate cost for request"""
        cost_per_token = self.cost_per_token.get(provider, 0)
        return total_tokens * cost_per_token

    async def get_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate text embeddings using OpenAI"""
        
        if LLMProvider.OPENAI not in self.providers:
            raise AIProcessingError("OpenAI provider required for embeddings")
        
        client = self.providers[LLMProvider.OPENAI]
        embedding_model = model or self.config.openai_embedding_model
        
        try:
            response = await client.embeddings.create(
                input=text,
                model=embedding_model
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise AIProcessingError(f"Embedding generation failed: {e}")

    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for all providers"""
        return {
            provider.value: {
                **stats,
                "success_rate": (
                    (stats["requests"] - stats["failures"]) / stats["requests"]
                    if stats["requests"] > 0 else 0
                ),
                "available": provider in self.providers
            }
            for provider, stats in self.provider_stats.items()
        }