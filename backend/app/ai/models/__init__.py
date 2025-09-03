"""
AI Models Package

Model registry, configuration, and compatibility checking for OneVice AI agents.
"""

from .model_registry import (
    MODEL_REGISTRY, ModelInfo, ModelProvider, ModelSize, ToolFormat,
    ModelCapabilities, ModelMetrics, get_model_info, list_compatible_models,
    get_models_by_provider, get_fallback_models
)
from .tool_compatibility import (
    ToolCompatibilityChecker, ToolRequirement, ToolType, 
    CompatibilityResult
)
from .model_config import (
    ModelConfigurationManager, ModelProfile, AgentModelMapping,
    Environment, SelectionStrategy
)

__all__ = [
    # Model Registry
    'MODEL_REGISTRY',
    'ModelInfo',
    'ModelProvider', 
    'ModelSize',
    'ToolFormat',
    'ModelCapabilities',
    'ModelMetrics',
    'get_model_info',
    'list_compatible_models',
    'get_models_by_provider',
    'get_fallback_models',
    
    # Tool Compatibility
    'ToolCompatibilityChecker',
    'ToolRequirement',
    'ToolType',
    'CompatibilityResult',
    
    # Model Configuration
    'ModelConfigurationManager',
    'ModelProfile',
    'AgentModelMapping',
    'Environment',
    'SelectionStrategy'
]