#!/usr/bin/env python3
"""
LLM Router for OneVice - Security-First Model Selection
Prioritizes Together.ai for data sovereignty while maintaining fallback capabilities
"""

import os
import asyncio
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel
import logging

from .providers.together_provider import TogetherProvider
from .providers.anthropic_provider import AnthropicProvider
from auth.models import UserRole, DataSensitivity

logger = logging.getLogger(__name__)

class ModelProvider(str, Enum):
    TOGETHER = "together"
    ANTHROPIC = "anthropic" 
    GEMINI = "gemini"

class QueryComplexity(str, Enum):
    SIMPLE = "simple"          # Basic queries, data retrieval
    MODERATE = "moderate"      # Analysis, summarization
    COMPLEX = "complex"        # Strategic reasoning, complex analysis
    CRITICAL = "critical"      # Mission-critical decisions

@dataclass
class ModelConfiguration:
    """Configuration for specific models"""
    provider: ModelProvider
    model_name: str
    max_tokens: int
    cost_per_1k_tokens: float
    supports_function_calling: bool
    max_context_length: int
    specialties: List[str]

class LLMRouter:
    """
    Security-first LLM router that prioritizes data sovereignty
    Routes queries based on RBAC, data sensitivity, and model capabilities
    """
    
    def __init__(self):
        # self.rbac_manager = RBACManager()  # TODO: Integrate with auth system
        self.providers = self._initialize_providers()
        self.model_configs = self._initialize_model_configs()
        
    def _initialize_providers(self) -> Dict[ModelProvider, Any]:
        """Initialize LLM providers with API keys"""
        providers = {}
        
        # Together.ai - Primary for sensitive data
        if os.getenv("TOGETHER_API_KEY"):
            providers[ModelProvider.TOGETHER] = TogetherProvider(
                api_key=os.getenv("TOGETHER_API_KEY")
            )
            logger.info("Together.ai provider initialized")
        
        # Anthropic - Fallback for complex reasoning
        if os.getenv("ANTHROPIC_API_KEY"):
            providers[ModelProvider.ANTHROPIC] = AnthropicProvider(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            logger.info("Anthropic provider initialized")
            
        return providers
    
    def _initialize_model_configs(self) -> Dict[str, ModelConfiguration]:
        """Initialize model configurations with capabilities and costs"""
        return {
            # Together.ai Models - Primary for sensitive data
            "together:mixtral-8x7b-instruct": ModelConfiguration(
                provider=ModelProvider.TOGETHER,
                model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
                max_tokens=4096,
                cost_per_1k_tokens=0.0006,  # Very cost-effective
                supports_function_calling=True,
                max_context_length=32768,
                specialties=["general", "analysis", "function_calling", "sensitive_data"]
            ),
            "together:llama-3-70b-chat": ModelConfiguration(
                provider=ModelProvider.TOGETHER,
                model_name="meta-llama/Llama-3-70b-chat-hf",
                max_tokens=4096,
                cost_per_1k_tokens=0.0009,
                supports_function_calling=True,
                max_context_length=8192,
                specialties=["complex_reasoning", "strategic_analysis", "sensitive_data"]
            ),
            
            # Anthropic - Fallback for complex reasoning (non-sensitive)
            "anthropic:claude-3-5-sonnet-latest": ModelConfiguration(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                cost_per_1k_tokens=0.015,  # Higher cost
                supports_function_calling=True,
                max_context_length=200000,
                specialties=["complex_reasoning", "code_analysis", "strategic_planning"]
            )
        }
    
    async def get_optimal_model(
        self,
        query: str,
        user_role: UserRole,
        data_sensitivity: int,
        query_complexity: QueryComplexity = QueryComplexity.MODERATE,
        context_length_needed: int = 0
    ) -> str:
        """
        Get optimal model based on security requirements and capabilities
        Prioritizes Together.ai for any sensitive data
        """
        
        # Security-first routing: Always use Together.ai for sensitive data
        if data_sensitivity <= DataSensitivity.INTERNAL.value:
            logger.info(f"Sensitive data detected (level {data_sensitivity}), routing to Together.ai")
            
            if query_complexity == QueryComplexity.COMPLEX:
                return "together:llama-3-70b-chat"
            else:
                return "together:mixtral-8x7b-instruct"
        
        # For non-sensitive data, consider other factors
        if query_complexity == QueryComplexity.CRITICAL:
            # Critical queries need the most capable model
            if self._can_use_anthropic(user_role, data_sensitivity):
                return "anthropic:claude-3-5-sonnet-latest"
            else:
                return "together:llama-3-70b-chat"
        
        elif query_complexity == QueryComplexity.COMPLEX:
            # Complex reasoning - prefer powerful models
            if context_length_needed > 32000:
                # Long context needs
                if self._can_use_anthropic(user_role, data_sensitivity):
                    return "anthropic:claude-3-5-sonnet-latest"
                else:
                    return "together:llama-3-70b-chat"
            else:
                return "together:llama-3-70b-chat"
        
        else:
            # Simple/moderate queries - cost-optimize with Together.ai
            return "together:mixtral-8x7b-instruct"
    
    def _can_use_anthropic(self, user_role: UserRole, data_sensitivity: int) -> bool:
        """
        Determine if Anthropic can be used based on data sensitivity
        Only allow for non-sensitive data (level 4-6)
        """
        return data_sensitivity >= DataSensitivity.CONFIDENTIAL.value
    
    async def route_query(
        self,
        query: str,
        user_context: Dict[str, Any],
        system_prompt: Optional[str] = None,
        functions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Route query to optimal model with security validation
        """
        
        # Extract user context
        role_str = user_context.get("role", "SALESPERSON").upper()
        try:
            user_role = UserRole[role_str]
        except KeyError:
            user_role = UserRole.SALESPERSON
        data_sensitivity = user_context.get("data_sensitivity", 6)  # Default to least sensitive
        
        # Assess query complexity
        query_complexity = self._assess_complexity(query)
        context_length_needed = len(query) + len(system_prompt or "")
        
        # Get optimal model
        selected_model = await self.get_optimal_model(
            query, user_role, data_sensitivity, query_complexity, context_length_needed
        )
        
        model_config = self.model_configs[selected_model]
        provider = self.providers[model_config.provider]
        
        logger.info(f"Routing query to {selected_model} (sensitivity: {data_sensitivity}, complexity: {query_complexity})")
        
        # Execute query with selected provider
        try:
            response = await provider.complete(
                model=model_config.model_name,
                messages=[
                    {"role": "system", "content": system_prompt or "You are a helpful AI assistant."},
                    {"role": "user", "content": query}
                ],
                max_tokens=model_config.max_tokens,
                functions=functions if model_config.supports_function_calling else None
            )
            
            # Add routing metadata
            response["routing_info"] = {
                "selected_model": selected_model,
                "provider": model_config.provider.value,
                "data_sensitivity": data_sensitivity,
                "query_complexity": query_complexity.value,
                "cost_estimate": self._estimate_cost(response.get("usage", {}), model_config)
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error with {selected_model}: {e}")
            
            # Fallback to Together.ai Mixtral for reliability
            if selected_model != "together:mixtral-8x7b-instruct":
                logger.info("Falling back to Together.ai Mixtral")
                fallback_config = self.model_configs["together:mixtral-8x7b-instruct"]
                fallback_provider = self.providers[ModelProvider.TOGETHER]
                
                return await fallback_provider.complete(
                    model=fallback_config.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt or "You are a helpful AI assistant."},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=fallback_config.max_tokens
                )
            else:
                raise e
    
    def _assess_complexity(self, query: str) -> QueryComplexity:
        """Assess query complexity based on content and length"""
        
        query_lower = query.lower()
        
        # Critical indicators
        critical_terms = ["strategic", "decision", "recommendation", "budget approval", "investment"]
        if any(term in query_lower for term in critical_terms):
            return QueryComplexity.CRITICAL
        
        # Complex indicators  
        complex_terms = ["analyze", "compare", "evaluate", "summarize", "explain why"]
        if any(term in query_lower for term in complex_terms) or len(query) > 500:
            return QueryComplexity.COMPLEX
        
        # Moderate indicators
        moderate_terms = ["what", "how", "when", "where", "list", "show"]
        if any(term in query_lower for term in moderate_terms) or len(query) > 100:
            return QueryComplexity.MODERATE
        
        return QueryComplexity.SIMPLE
    
    def _estimate_cost(self, usage: Dict, model_config: ModelConfiguration) -> float:
        """Estimate cost based on token usage"""
        total_tokens = usage.get("total_tokens", 0)
        return (total_tokens / 1000) * model_config.cost_per_1k_tokens
    
    async def get_available_models(self, user_role: UserRole, data_sensitivity: int) -> List[str]:
        """Get list of available models for user's security level"""
        available = []
        
        # Together.ai always available (data sovereignty)
        available.extend([
            "together:mixtral-8x7b-instruct",
            "together:llama-3-70b-chat"
        ])
        
        # Anthropic only for non-sensitive data
        if self._can_use_anthropic(user_role, data_sensitivity):
            available.append("anthropic:claude-3-5-sonnet-latest")
        
        return available
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers"""
        return {
            provider.value: provider in self.providers
            for provider in ModelProvider
        }