# Model-Tool Compatibility Matrix

This document provides a comprehensive overview of the OneVice AI model configuration system, including tool compatibility requirements, model assignments, and testing strategies.

## Overview

OneVice uses a sophisticated model configuration system that:

- ✅ **Validates tool compatibility** for Neo4j, Folk CRM, MCP servers, and other integrations
- 🔄 **Enables dynamic model switching** during testing and development
- 💰 **Optimizes costs** across different environments (development, testing, production)
- 🛡️ **Ensures reliability** through fallback model configuration
- 📊 **Provides detailed analytics** on model performance and compatibility

## System Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Model         │    │  Tool Compatibility  │    │  Model Configuration│
│   Registry      │◄──►│  Checker             │◄──►│  Manager            │
│                 │    │                      │    │                     │
│ • 8 Models      │    │ • Validates Neo4j    │    │ • Environment       │
│ • Capabilities  │    │ • Validates Folk CRM │    │   Profiles          │
│ • Metrics       │    │ • Validates MCP      │    │ • Agent Assignments │
│ • Cost Info     │    │ • Agent Requirements │    │ • Cost Optimization │
└─────────────────┘    └──────────────────────┘    └─────────────────────┘
```

## Model Registry

### Available Models

| Model Alias | Display Name | Provider | Size | Cost/1k Output | Tool Support |
|-------------|--------------|----------|------|----------------|--------------|
| `llama-3.1-405b` | Llama 3.1 405B Instruct Turbo | Together | XLarge | $0.015 | Neo4j + Folk + MCP + Reasoning |
| `qwen2.5-72b` | Qwen 2.5 72B Instruct Turbo | Together | Medium | $0.0009 | Neo4j + Folk + MCP + Native Tools |
| `mixtral-8x7b` | Mixtral 8x7B Instruct | Together | Medium | $0.0006 | Neo4j + Folk + MCP |
| `mixtral-8x22b` | Mixtral 8x22B Instruct | Together | Large | $0.0012 | Neo4j + Folk + MCP |
| `dbrx-instruct` | DBRX Instruct | Together | Large | $0.0012 | Neo4j + Folk + MCP + Enterprise |
| `deepseek-coder-v2` | DeepSeek Coder V2 Lite | Together | Small | $0.00015 | Neo4j + Folk + MCP + Structured |
| `llama-3.1-70b` | Llama 3.1 70B Instruct Turbo | Together | Medium | $0.0009 | Neo4j + Folk + MCP |
| `gpt-4o-mini` | GPT-4o Mini | OpenAI | Medium | $0.0006 | Neo4j + Folk + MCP + Fast |

### Model Capabilities

Each model in the registry includes detailed capability flags:

```python
@dataclass
class ModelCapabilities:
    neo4j: bool = False              # Can generate Cypher queries
    folk_crm: bool = False           # Can integrate with Folk CRM API
    function_calling: bool = False   # Supports function/tool calling
    mcp_compatible: bool = False     # Compatible with MCP servers
    json_mode: bool = False          # Supports JSON output mode
    native_tool_use: bool = False    # Has native tool use training
    cypher_generation: bool = False  # Specifically good at Cypher
    structured_output: bool = False  # Good at structured responses
    reasoning: bool = False          # Enhanced reasoning capabilities
```

## Tool Compatibility Requirements

### Agent Requirements

Each agent type has specific tool requirements that must be met:

#### Supervisor Agent
- ✅ **Function Calling** (required)
- ✅ **Reasoning** (required, excellent level)
- ✅ **Structured Output** (required)
- ✅ **MCP Server** (required)

**Compatible Models:** `llama-3.1-405b` only

#### Analytics Agent
- ✅ **Neo4j** (required)
- ✅ **Function Calling** (required)
- ✅ **Structured Output** (required)
- 🔄 **Vector Search** (optional, fallback acceptable)

**Compatible Models:** All 8 models

#### Sales Agent
- ✅ **Folk CRM** (required)
- ✅ **Function Calling** (required)
- ✅ **Neo4j** (required)
- 🔄 **Structured Output** (optional, fallback acceptable)

**Compatible Models:** All 8 models

#### Talent Agent
- ✅ **Neo4j** (required)
- ✅ **Function Calling** (required)
- ✅ **Vector Search** (required)
- ✅ **Structured Output** (required)

**Compatible Models:** All 8 models

### Tool Type Definitions

| Tool Type | Description | Validation Method |
|-----------|-------------|-------------------|
| `NEO4J` | Cypher query generation and graph traversal | Checks `neo4j` and `cypher_generation` flags |
| `FOLK_CRM` | Folk CRM API integration | Requires both `folk_crm` and `function_calling` |
| `MCP_SERVER` | Model Context Protocol compatibility | Requires both `mcp_compatible` and `function_calling` |
| `FUNCTION_CALLING` | OpenAI-format function calling | Checks `function_calling` or `native_tool_use` |
| `STRUCTURED_OUTPUT` | Structured data generation | Checks `structured_output` or `json_mode` |
| `VECTOR_SEARCH` | Vector similarity operations | Currently assumed available for all models |
| `REASONING` | Enhanced reasoning capabilities | Checks `reasoning` flag plus size/accuracy requirements |

## Environment Configurations

### Development Environment
- **Strategy:** Cost Optimized
- **Max Cost:** $0.02/1k tokens
- **Fallbacks:** Enabled
- **Goal:** Minimize costs while maintaining functionality

**Typical Assignments:**
- Supervisor: `llama-3.1-405b` (only compatible option)
- Analytics: `deepseek-coder-v2` (cheapest option)
- Sales: `deepseek-coder-v2` (cheapest option)
- Talent: `deepseek-coder-v2` (cheapest option)

**Estimated Monthly Cost (1M tokens):** ~$20.90

### Testing Environment
- **Strategy:** Balanced
- **Max Cost:** $0.01/1k tokens (but flexible for required capabilities)
- **Fallbacks:** Enabled
- **Goal:** Balance of cost and performance for thorough testing

### Staging Environment
- **Strategy:** Performance Optimized
- **Provider Preference:** Together.ai
- **Fallbacks:** Disabled
- **Goal:** Production-like performance testing

### Production Environment
- **Strategy:** Performance Optimized
- **Provider Preference:** Together.ai
- **Min Accuracy:** Excellent
- **Fallbacks:** Disabled
- **Goal:** Maximum performance and reliability

**Typical Assignments:**
- Supervisor: `llama-3.1-405b` (best reasoning)
- Analytics: `llama-3.1-405b` (best performance)
- Sales: `llama-3.1-405b` (best performance)
- Talent: `llama-3.1-405b` (best performance)

**Estimated Monthly Cost (1M tokens):** ~$80.00

## Usage Examples

### Basic Configuration

```python
from app.ai.models import ModelConfigurationManager, Environment

# Initialize manager
config_manager = ModelConfigurationManager(config)

# Create optimal configuration for development
mapping = config_manager.create_optimal_configuration(
    environment=Environment.DEVELOPMENT,
    agent_types=["supervisor", "analytics", "sales", "talent"]
)

# The system will automatically select the best models based on:
# - Tool compatibility requirements
# - Cost constraints
# - Performance requirements
```

### Model Switching

```python
# Switch analytics agent to a different model
success = config_manager.switch_model(
    agent_type="analytics",
    new_model_alias="mixtral-8x22b",
    validate=True  # Ensure compatibility before switching
)

if success:
    print("Model switched successfully")
else:
    print("Model switch failed - compatibility issues")
```

### Compatibility Checking

```python
from app.ai.models import ToolCompatibilityChecker, ToolRequirement, ToolType

checker = ToolCompatibilityChecker(config)

# Check if a model supports specific tools
result = checker.check_model_compatibility(
    model_alias="mixtral-8x7b",
    requirements=[
        ToolRequirement(ToolType.NEO4J, required=True),
        ToolRequirement(ToolType.FOLK_CRM, required=True)
    ]
)

print(f"Compatible: {result.compatible}")
print(f"Score: {result.score}")
print(f"Warnings: {result.warnings}")
```

### Finding Compatible Models

```python
# Find all models compatible with analytics agent
analytics_requirements = checker.agent_requirements["analytics"]
compatible_models = checker.find_compatible_models(
    requirements=analytics_requirements,
    min_score=0.8
)

for result in compatible_models:
    model_info = MODEL_REGISTRY[result.model_alias]
    cost = model_info.metrics.cost_per_1k_output
    print(f"{result.model_alias}: {cost:.4f}/1k tokens (score: {result.score})")
```

## Cost Analysis

### Cost Comparison by Environment

| Environment | Total Cost/1k | Light Usage (100k) | Moderate (1M) | Heavy (10M) |
|-------------|---------------|-------------------|---------------|-------------|
| Development | $0.0155 | $2.09 | $20.90 | $209.00 |
| Production | $0.0600 | $8.00 | $80.00 | $800.00 |

### Model Cost Analysis

| Model | Input Cost/1k | Output Cost/1k | Speed Tier | Accuracy Tier |
|-------|---------------|----------------|------------|---------------|
| `deepseek-coder-v2` | $0.00015 | $0.00015 | Fast | Good |
| `mixtral-8x7b` | $0.0006 | $0.0006 | Fast | Good |
| `qwen2.5-72b` | $0.0009 | $0.0009 | Medium | Excellent |
| `llama-3.1-70b` | $0.0009 | $0.0009 | Medium | Excellent |
| `dbrx-instruct` | $0.0012 | $0.0012 | Medium | Excellent |
| `mixtral-8x22b` | $0.0012 | $0.0012 | Medium | Excellent |
| `gpt-4o-mini` | $0.00015 | $0.0006 | Ultrafast | Excellent |
| `llama-3.1-405b` | $0.005 | $0.015 | Slow | Best |

## Testing Framework

### Automated Tests

The system includes comprehensive automated tests:

```bash
# Run full test suite
source venv/bin/activate
python3 test_model_system.py

# Run specific compatibility tests
python3 -m pytest app/ai/models/test_tool_compatibility.py
```

### Test Coverage

- ✅ **Model Registry Validation**: Ensures all models have required fields
- ✅ **Tool Compatibility**: Validates Neo4j, Folk CRM, MCP, and function calling support
- ✅ **Agent Requirements**: Tests all predefined agent requirement sets
- ✅ **Configuration Creation**: Tests optimal configuration generation
- ✅ **Model Switching**: Validates dynamic model switching functionality
- ✅ **Cost Analysis**: Verifies cost calculations and optimization
- ✅ **Environment Profiles**: Tests all environment configurations
- ✅ **Integration Tests**: End-to-end system validation

### Manual Testing

```python
# Create a test configuration
from app.ai.models import ModelConfigurationManager, Environment

manager = ModelConfigurationManager(config)
mapping = manager.create_optimal_configuration(Environment.DEVELOPMENT)

# Generate detailed report
report = manager.generate_configuration_report()
print(json.dumps(report, indent=2))

# Test model switching
manager.switch_model("analytics", "mixtral-8x22b")
```

## Troubleshooting

### Common Issues

#### No Compatible Models Found

**Issue:** `AIProcessingError: No compatible model found for agent type: X`

**Solution:** 
1. Check agent requirements vs. available model capabilities
2. Increase cost limits if expensive models are required
3. Enable fallbacks in the profile configuration

#### Model Switch Failed

**Issue:** `switch_model()` returns `False`

**Solution:**
1. Verify the new model exists in the registry
2. Check tool compatibility with `check_agent_compatibility()`
3. Ensure the model meets the agent's requirements

#### High Costs in Development

**Issue:** Development environment using expensive models

**Solution:**
1. Review agent requirements - consider making some optional
2. Increase fallback acceptance for non-critical capabilities
3. Use cost-optimized strategy with appropriate limits

### Performance Optimization

#### Model Selection Strategies

1. **Cost-First**: Start with cheapest compatible models
2. **Performance-First**: Use highest-accuracy models available
3. **Balanced**: Weight cost and performance equally
4. **Provider-Specific**: Prefer specific providers for consistency

#### Fallback Configuration

```python
# Configure fallbacks for resilience
profile = ModelProfile(
    environment=Environment.TESTING,
    strategy=SelectionStrategy.BALANCED,
    allow_fallbacks=True,
    max_cost_per_1k=0.01
)

mapping = manager.create_optimal_configuration(
    environment=Environment.TESTING,
    custom_profile=profile
)

# Check fallback models
for agent_type in mapping.agent_assignments:
    fallbacks = mapping.fallback_models.get(agent_type, [])
    print(f"{agent_type} fallbacks: {fallbacks}")
```

## API Reference

### ModelConfigurationManager

#### Methods

- `create_optimal_configuration(environment, agent_types, custom_profile)`: Create optimal model assignments
- `switch_model(agent_type, new_model_alias, validate)`: Switch model for specific agent
- `get_model_for_agent(agent_type)`: Get current model assignment
- `generate_configuration_report()`: Generate comprehensive analysis report

### ToolCompatibilityChecker

#### Methods

- `check_model_compatibility(model_alias, requirements)`: Check specific requirements
- `check_agent_compatibility(agent_type, model_alias)`: Check agent-specific compatibility
- `find_compatible_models(requirements, min_score)`: Find all compatible models
- `generate_compatibility_matrix()`: Generate full compatibility matrix

### MODEL_REGISTRY

Direct access to all model information:

```python
from app.ai.models import MODEL_REGISTRY, get_model_info

# Get specific model info
model = get_model_info("mixtral-8x7b")
print(f"Cost: ${model.metrics.cost_per_1k_output}")
print(f"Neo4j: {model.capabilities.neo4j}")

# List all models
for alias, model in MODEL_REGISTRY.items():
    print(f"{alias}: {model.display_name}")
```

## Future Enhancements

### Planned Features

1. **Dynamic Cost Monitoring**: Real-time cost tracking and alerts
2. **Performance Benchmarking**: Automated model performance testing
3. **A/B Testing Framework**: Split testing between different models
4. **Usage Analytics**: Detailed usage patterns and optimization recommendations
5. **Custom Model Integration**: Support for custom/fine-tuned models
6. **Multi-Region Support**: Model deployment across multiple regions

### Extension Points

The system is designed for extensibility:

- **Custom Tool Types**: Add new tool compatibility checks
- **Custom Agent Types**: Define new agent profiles with specific requirements
- **Custom Selection Strategies**: Implement domain-specific optimization logic
- **Custom Metrics**: Add performance and cost metrics
- **Custom Providers**: Integrate additional LLM providers

---

*This documentation is automatically maintained and reflects the current state of the OneVice model configuration system. Last updated: September 3, 2025.*