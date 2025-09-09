"""
AI System Configuration

Centralized configuration for the OneVice AI system including
model settings, provider configurations, and system parameters.
"""

import os
from typing import Dict, Any, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from enum import Enum

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    TOGETHER = "together"
    OPENAI = "openai" 
    ANTHROPIC = "anthropic"

class AgentType(str, Enum):
    """Available AI agent types"""
    SALES = "sales"
    TALENT = "talent"
    ANALYTICS = "analytics"
    GENERAL = "general"

class AIConfig(BaseSettings):
    """AI system configuration settings"""
    
    # Model Configuration
    default_provider: LLMProvider = LLMProvider.TOGETHER
    fallback_provider: LLMProvider = LLMProvider.TOGETHER
    
    # Together.ai Configuration
    together_api_key: Optional[str] = Field(default=None, env="TOGETHER_API_KEY")
    together_base_url: str = "https://api.together.xyz/v1"
    together_default_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    together_max_tokens: int = 2048
    together_temperature: float = 0.7
    
    # OpenAI Configuration  
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_default_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_max_tokens: int = 2048
    openai_temperature: float = 0.7
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Folk CRM Configuration
    folk_api_keys: Optional[str] = Field(default=None, env="FOLK_API_KEYS")
    folk_api_url: str = Field(default="https://api.folk.app/v1", env="FOLK_API_BASE_URL")
    folk_api_rate_limit: int = Field(default=100, env="FOLK_API_RATE_LIMIT")
    folk_api_timeout: int = Field(default=30, env="FOLK_API_TIMEOUT")
    
    @property
    def folk_api_key(self) -> Optional[str]:
        """Get the first Folk API key from comma-separated list"""
        if self.folk_api_keys:
            return self.folk_api_keys.split(',')[0].strip()
        return None
    
    # Neo4j Configuration
    neo4j_uri: Optional[str] = Field(default=None, env="NEO4J_URI") 
    neo4j_username: Optional[str] = Field(default=None, env="NEO4J_USERNAME")
    neo4j_password: Optional[str] = Field(default=None, env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    # Vector Search Configuration
    embedding_dimension: int = 1536
    vector_similarity_threshold: float = 0.7
    max_search_results: int = 10
    
    # Agent Configuration
    agent_memory_ttl: int = 3600  # 1 hour in seconds
    max_conversation_history: int = 20
    agent_timeout: int = 30  # seconds
    
    # Redis Configuration (for agent state)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_key_prefix: str = "onevice:ai:"
    
    # System Configuration
    max_concurrent_requests: int = 100
    request_timeout: int = 30
    enable_caching: bool = True
    cache_ttl: int = 900  # 15 minutes
    
    # Logging Configuration
    log_level: str = "INFO"
    enable_tracing: bool = True
    trace_sample_rate: float = 0.1
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables not defined in the model

    def get_model_config(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get model configuration for specific provider"""
        configs = {
            LLMProvider.TOGETHER: {
                "api_key": self.together_api_key,
                "base_url": self.together_base_url,
                "model": self.together_default_model,
                "max_tokens": self.together_max_tokens,
                "temperature": self.together_temperature,
            },
            LLMProvider.OPENAI: {
                "api_key": self.openai_api_key,
                "model": self.openai_default_model,
                "max_tokens": self.openai_max_tokens,
                "temperature": self.openai_temperature,
            }
        }
        return configs.get(provider, {})
    
    def get_agent_config(self, agent_type: AgentType) -> Dict[str, Any]:
        """Get configuration specific to agent type"""
        base_config = {
            "memory_ttl": self.agent_memory_ttl,
            "max_history": self.max_conversation_history,
            "timeout": self.agent_timeout,
        }
        
        # Agent-specific configurations
        agent_configs = {
            AgentType.SALES: {
                **base_config,
                "preferred_model": self.together_default_model,
                "temperature": 0.6,  # Slightly more focused
                "system_prompt_key": "sales_intelligence",
            },
            AgentType.TALENT: {
                **base_config,
                "preferred_model": self.together_default_model,
                "temperature": 0.5,  # More deterministic
                "system_prompt_key": "talent_acquisition",
            },
            AgentType.ANALYTICS: {
                **base_config,
                "preferred_model": self.together_default_model,  # Use Together.ai for analytics
                "temperature": 0.3,  # Very focused
                "system_prompt_key": "leadership_analytics",
            },
            AgentType.GENERAL: {
                **base_config,
                "preferred_model": self.together_default_model,
                "temperature": self.together_temperature,
                "system_prompt_key": "general_assistant",
            }
        }
        
        return agent_configs.get(agent_type, base_config)
    
    def is_agent_orchestrator_available(self) -> bool:
        """Check if all required services are available for agent orchestrator"""
        required_fields = [
            self.together_api_key or self.openai_api_key,  # At least one LLM provider
            self.redis_url,  # Required for agent memory
        ]
        return all(required_fields)
    
    def get_missing_config_items(self) -> List[str]:
        """Get list of missing configuration items for agent orchestrator"""
        missing = []
        
        if not (self.together_api_key or self.openai_api_key):
            missing.append("LLM API key (TOGETHER_API_KEY or OPENAI_API_KEY)")
        
        if not self.redis_url:
            missing.append("REDIS_URL")
            
        # Neo4j is optional for basic operation
        if not (self.neo4j_uri and self.neo4j_username and self.neo4j_password):
            missing.append("Neo4j configuration (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD) - optional for basic operation")
            
        return missing

# Global configuration instance
ai_config = AIConfig()