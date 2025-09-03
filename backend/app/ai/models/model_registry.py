"""
Model Registry

Comprehensive catalog of AI models with tool calling capabilities,
performance metrics, and compatibility information.
"""

from typing import Dict, List, Any, Optional, Literal
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class ModelProvider(str, Enum):
    """Supported model providers"""
    TOGETHER = "together"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class ModelSize(str, Enum):
    """Model size categories"""
    SMALL = "small"      # < 10B parameters
    MEDIUM = "medium"    # 10B - 100B parameters  
    LARGE = "large"      # 100B - 500B parameters
    XLARGE = "xlarge"    # > 500B parameters

class ToolFormat(str, Enum):
    """Supported tool calling formats"""
    OPENAI = "openai"           # OpenAI function calling format
    NATIVE = "native"           # Model's native tool format
    JSON = "json"               # JSON mode output
    STRUCTURED = "structured"   # Structured output

@dataclass
class ModelCapabilities:
    """Model capability flags"""
    neo4j: bool = False              # Can generate Cypher queries
    folk_crm: bool = False           # Can integrate with Folk CRM API
    function_calling: bool = False   # Supports function/tool calling
    mcp_compatible: bool = False     # Compatible with MCP servers
    json_mode: bool = False          # Supports JSON output mode
    native_tool_use: bool = False    # Has native tool use training
    cypher_generation: bool = False  # Specifically good at Cypher
    structured_output: bool = False  # Good at structured responses
    reasoning: bool = False          # Enhanced reasoning capabilities

@dataclass
class ModelMetrics:
    """Performance and cost metrics"""
    cost_per_1k_input: float
    cost_per_1k_output: float
    avg_response_time: float        # seconds
    context_length: int
    max_tokens: int
    speed_tier: Literal["slow", "medium", "fast", "ultrafast"]
    accuracy_tier: Literal["basic", "good", "excellent", "best"]

@dataclass
class ModelInfo:
    """Complete model information"""
    provider: ModelProvider
    model_id: str
    display_name: str
    parameters: str                    # e.g., "8B", "70B", "405B"
    size_category: ModelSize
    tool_calling: bool
    tool_formats: List[ToolFormat]
    capabilities: ModelCapabilities
    metrics: ModelMetrics
    best_for: List[str]               # Agent types or use cases
    description: str
    strengths: List[str]
    limitations: List[str]
    verified_date: str                # When compatibility was last verified
    status: Literal["verified", "testing", "deprecated"] = "verified"

# Comprehensive model registry with tool compatibility information
MODEL_REGISTRY: Dict[str, ModelInfo] = {
    
    # === SUPERVISOR MODELS (Large, high-capability) ===
    "llama-3.1-405b": ModelInfo(
        provider=ModelProvider.TOGETHER,
        model_id="meta-llama/Llama-3.1-405B-Instruct-Turbo",
        display_name="Llama 3.1 405B Instruct Turbo",
        parameters="405B",
        size_category=ModelSize.XLARGE,
        tool_calling=True,
        tool_formats=[ToolFormat.OPENAI, ToolFormat.JSON],
        capabilities=ModelCapabilities(
            neo4j=True,
            folk_crm=True,
            function_calling=True,
            mcp_compatible=True,
            json_mode=True,
            cypher_generation=True,
            structured_output=True,
            reasoning=True
        ),
        metrics=ModelMetrics(
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.015,
            avg_response_time=8.0,
            context_length=130000,
            max_tokens=4000,
            speed_tier="slow",
            accuracy_tier="best"
        ),
        best_for=["supervisor", "orchestration", "complex_reasoning"],
        description="Most capable model for complex orchestration and reasoning tasks",
        strengths=[
            "Exceptional reasoning capabilities",
            "Superior tool calling accuracy",
            "Excellent Cypher generation",
            "Complex multi-step workflows",
            "High-quality structured output"
        ],
        limitations=[
            "Highest cost per request",
            "Slowest response time",
            "May be overkill for simple tasks"
        ],
        verified_date="2025-01-15"
    ),
    
    "qwen2.5-72b": ModelInfo(
        provider=ModelProvider.TOGETHER,
        model_id="Qwen/Qwen2.5-72B-Instruct-Turbo",
        display_name="Qwen 2.5 72B Instruct Turbo",
        parameters="72B",
        size_category=ModelSize.MEDIUM,
        tool_calling=True,
        tool_formats=[ToolFormat.OPENAI, ToolFormat.NATIVE],
        capabilities=ModelCapabilities(
            neo4j=True,
            folk_crm=True,
            function_calling=True,
            mcp_compatible=True,
            json_mode=True,
            native_tool_use=True,
            cypher_generation=True,
            structured_output=True
        ),
        metrics=ModelMetrics(
            cost_per_1k_input=0.0009,
            cost_per_1k_output=0.0009,
            avg_response_time=4.5,
            context_length=262144,  # 262K context
            max_tokens=2048,
            speed_tier="medium",
            accuracy_tier="excellent"
        ),
        best_for=["analytics", "data_processing", "supervisor"],
        description="Excellent balance of capability and efficiency with native tool use",
        strengths=[
            "Native tool use training",
            "Large context window (262K)",
            "Strong multilingual support",
            "Good cost-performance ratio",
            "Reliable function calling"
        ],
        limitations=[
            "Not as strong for creative tasks",
            "Medium speed tier"
        ],
        verified_date="2025-01-15"
    ),
    
    # === SALES & GENERAL MODELS (Medium, balanced) ===
    "mixtral-8x7b": ModelInfo(
        provider=ModelProvider.TOGETHER,
        model_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
        display_name="Mixtral 8x7B Instruct",
        parameters="46.7B",
        size_category=ModelSize.MEDIUM,
        tool_calling=True,
        tool_formats=[ToolFormat.OPENAI],
        capabilities=ModelCapabilities(
            neo4j=True,
            folk_crm=True,
            function_calling=True,
            mcp_compatible=True,
            cypher_generation=True,
            structured_output=True
        ),
        metrics=ModelMetrics(
            cost_per_1k_input=0.0006,
            cost_per_1k_output=0.0006,
            avg_response_time=3.2,
            context_length=32768,
            max_tokens=2048,
            speed_tier="fast",
            accuracy_tier="good"
        ),
        best_for=["sales", "general", "talent"],
        description="Fast and reliable workhorse for most agent tasks",
        strengths=[
            "Excellent speed-cost ratio",
            "Reliable tool calling",
            "Good general capabilities",
            "Stable and well-tested",
            "Good Cypher generation"
        ],
        limitations=[
            "Not the most accurate for complex reasoning",
            "Limited context compared to newer models"
        ],
        verified_date="2025-01-15",
        status="verified"
    ),
    
    "mixtral-8x22b": ModelInfo(
        provider=ModelProvider.TOGETHER,
        model_id="mistralai/Mixtral-8x22B-Instruct-v0.1",
        display_name="Mixtral 8x22B Instruct",
        parameters="141B",
        size_category=ModelSize.LARGE,
        tool_calling=True,
        tool_formats=[ToolFormat.OPENAI],
        capabilities=ModelCapabilities(
            neo4j=True,
            folk_crm=True,
            function_calling=True,
            mcp_compatible=True,
            cypher_generation=True,
            structured_output=True
        ),
        metrics=ModelMetrics(
            cost_per_1k_input=0.0012,
            cost_per_1k_output=0.0012,
            avg_response_time=5.5,
            context_length=65536,
            max_tokens=2048,
            speed_tier="medium",
            accuracy_tier="excellent"
        ),
        best_for=["talent", "analytics", "complex_sales"],
        description="Higher capability Mixtral for complex agent tasks",
        strengths=[
            "Excellent tool calling accuracy",
            "Strong reasoning capabilities",
            "Good for complex queries",
            "Reliable performance",
            "Better context handling"
        ],
        limitations=[
            "Higher cost than 8x7B",
            "Slower response time"
        ],
        verified_date="2025-01-15"
    ),
    
    # === SPECIALIZED MODELS ===
    "dbrx-instruct": ModelInfo(
        provider=ModelProvider.TOGETHER,
        model_id="databricks/dbrx-instruct",
        display_name="DBRX Instruct",
        parameters="132B",
        size_category=ModelSize.LARGE,
        tool_calling=True,
        tool_formats=[ToolFormat.OPENAI, ToolFormat.STRUCTURED],
        capabilities=ModelCapabilities(
            neo4j=True,
            folk_crm=True,
            function_calling=True,
            mcp_compatible=True,
            structured_output=True,
            cypher_generation=True
        ),
        metrics=ModelMetrics(
            cost_per_1k_input=0.0012,
            cost_per_1k_output=0.0012,
            avg_response_time=4.8,
            context_length=32768,
            max_tokens=2048,
            speed_tier="medium",
            accuracy_tier="excellent"
        ),
        best_for=["sales", "data_analysis", "enterprise"],
        description="Enterprise-focused model excellent for structured data tasks",
        strengths=[
            "Excellent for enterprise data",
            "Strong structured output",
            "Good CRM integration",
            "Reliable tool calling",
            "Business-oriented training"
        ],
        limitations=[
            "Less general purpose",
            "Higher cost"
        ],
        verified_date="2025-01-15"
    ),
    
    "deepseek-coder-v2": ModelInfo(
        provider=ModelProvider.TOGETHER,
        model_id="deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        display_name="DeepSeek Coder V2 Lite",
        parameters="16B",
        size_category=ModelSize.SMALL,
        tool_calling=True,
        tool_formats=[ToolFormat.OPENAI, ToolFormat.STRUCTURED],
        capabilities=ModelCapabilities(
            neo4j=True,
            folk_crm=True,
            function_calling=True,
            mcp_compatible=True,
            structured_output=True,
            cypher_generation=True
        ),
        metrics=ModelMetrics(
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.00015,
            avg_response_time=2.0,
            context_length=32768,
            max_tokens=2048,
            speed_tier="fast",
            accuracy_tier="good"
        ),
        best_for=["analytics", "structured_output", "budget"],
        description="Fast, cost-effective model excellent for structured tasks",
        strengths=[
            "Very cost-effective",
            "Fast response time",
            "Excellent structured output",
            "Good for analytical tasks",
            "Strong logical reasoning"
        ],
        limitations=[
            "Not as good for creative tasks",
            "Smaller context window",
            "Less general knowledge"
        ],
        verified_date="2025-01-15"
    ),
    
    # === FALLBACK MODELS ===
    "llama-3.1-70b": ModelInfo(
        provider=ModelProvider.TOGETHER,
        model_id="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        display_name="Llama 3.1 70B Instruct Turbo",
        parameters="70B",
        size_category=ModelSize.MEDIUM,
        tool_calling=True,
        tool_formats=[ToolFormat.OPENAI],
        capabilities=ModelCapabilities(
            neo4j=True,
            folk_crm=True,
            function_calling=True,
            mcp_compatible=True,
            cypher_generation=True,
            structured_output=True
        ),
        metrics=ModelMetrics(
            cost_per_1k_input=0.0009,
            cost_per_1k_output=0.0009,
            avg_response_time=3.8,
            context_length=131072,
            max_tokens=2048,
            speed_tier="medium",
            accuracy_tier="excellent"
        ),
        best_for=["fallback", "general", "talent"],
        description="Reliable fallback model with good general capabilities",
        strengths=[
            "Reliable fallback option",
            "Good general capabilities",
            "Large context window",
            "Strong tool calling",
            "Well-tested"
        ],
        limitations=[
            "Not specialized for any particular task"
        ],
        verified_date="2025-01-15"
    ),
    
    # === OPENAI MODELS (for fallback) ===
    "gpt-4o-mini": ModelInfo(
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        parameters="Unknown",
        size_category=ModelSize.MEDIUM,
        tool_calling=True,
        tool_formats=[ToolFormat.OPENAI],
        capabilities=ModelCapabilities(
            neo4j=True,
            folk_crm=True,
            function_calling=True,
            mcp_compatible=True,
            json_mode=True,
            cypher_generation=True,
            structured_output=True
        ),
        metrics=ModelMetrics(
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.0006,
            avg_response_time=1.5,
            context_length=128000,
            max_tokens=16384,
            speed_tier="ultrafast",
            accuracy_tier="excellent"
        ),
        best_for=["fallback", "fast_responses"],
        description="Fast OpenAI fallback model for high availability",
        strengths=[
            "Extremely fast",
            "Very reliable",
            "Excellent tool calling",
            "Good for fallback",
            "High availability"
        ],
        limitations=[
            "External dependency",
            "Requires separate API key"
        ],
        verified_date="2025-01-15"
    )
}

def get_model_info(model_alias: str) -> Optional[ModelInfo]:
    """Get model information by alias"""
    return MODEL_REGISTRY.get(model_alias)

def list_compatible_models(
    tool_requirements: List[str] = None,
    max_cost: float = None,
    min_speed_tier: str = None,
    agent_type: str = None
) -> List[str]:
    """List models that meet specific requirements"""
    
    compatible = []
    
    for alias, model in MODEL_REGISTRY.items():
        # Check tool requirements
        if tool_requirements:
            caps = model.capabilities
            if not all(getattr(caps, req, False) for req in tool_requirements):
                continue
        
        # Check cost requirements
        if max_cost and model.metrics.cost_per_1k_output > max_cost:
            continue
            
        # Check speed requirements
        speed_order = {"slow": 0, "medium": 1, "fast": 2, "ultrafast": 3}
        if (min_speed_tier and 
            speed_order.get(model.metrics.speed_tier, 0) < speed_order.get(min_speed_tier, 0)):
            continue
        
        # Check if good for agent type
        if agent_type and agent_type not in model.best_for:
            continue
            
        compatible.append(alias)
    
    return compatible

def get_models_by_provider(provider: ModelProvider) -> List[str]:
    """Get all models from a specific provider"""
    return [alias for alias, model in MODEL_REGISTRY.items() 
            if model.provider == provider]

def get_fallback_models(primary_model: str) -> List[str]:
    """Get suitable fallback models for a primary model"""
    primary = MODEL_REGISTRY.get(primary_model)
    if not primary:
        return []
    
    # Find models with same capabilities but different providers/sizes
    fallbacks = []
    for alias, model in MODEL_REGISTRY.items():
        if alias == primary_model:
            continue
            
        # Must have same critical capabilities
        if (model.capabilities.function_calling == primary.capabilities.function_calling and
            model.capabilities.neo4j == primary.capabilities.neo4j and
            model.capabilities.folk_crm == primary.capabilities.folk_crm):
            fallbacks.append(alias)
    
    # Sort by cost (cheaper first for fallbacks)
    fallbacks.sort(key=lambda x: MODEL_REGISTRY[x].metrics.cost_per_1k_output)
    return fallbacks