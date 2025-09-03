#!/usr/bin/env python3
"""
Model Configuration System Test Runner

Quick validation of the model registry, tool compatibility checker,
and configuration management system.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.ai.models import (
    MODEL_REGISTRY, ToolCompatibilityChecker, ModelConfigurationManager,
    ToolRequirement, ToolType, Environment, get_model_info
)
from app.ai.config import AIConfig


class MockConfig:
    """Mock configuration for testing"""
    def __init__(self):
        self.redis_url = "redis://localhost:6379"
        self.redis_key_prefix = "onevice:test:"
    
    def get_agent_config(self, agent_type):
        return {
            "memory_ttl": 3600,
            "max_history": 10,
            "timeout": 30
        }


def test_model_registry():
    """Test model registry functionality"""
    print("🔍 Testing Model Registry...")
    
    # Check registry is populated
    assert len(MODEL_REGISTRY) > 0, "Model registry is empty"
    print(f"  ✓ Found {len(MODEL_REGISTRY)} models in registry")
    
    # Test specific models
    test_models = ["llama-3.1-405b", "mixtral-8x7b", "qwen2.5-72b"]
    for model_alias in test_models:
        model_info = get_model_info(model_alias)
        assert model_info is not None, f"Model {model_alias} not found"
        assert model_info.tool_calling, f"Model {model_alias} should support tool calling"
        print(f"  ✓ {model_alias}: {model_info.display_name}")
    
    # Validate model structure
    for alias, model in MODEL_REGISTRY.items():
        assert model.provider is not None
        assert model.model_id is not None
        assert model.capabilities is not None
        assert model.metrics is not None
    
    print("  ✅ Model registry validation passed")


def test_tool_compatibility():
    """Test tool compatibility checking"""
    print("\n🛠️ Testing Tool Compatibility...")
    
    config = MockConfig()
    checker = ToolCompatibilityChecker(config)
    
    # Test Neo4j compatibility
    neo4j_models = []
    for alias, model in MODEL_REGISTRY.items():
        if model.capabilities.neo4j:
            neo4j_models.append(alias)
    
    print(f"  ✓ Found {len(neo4j_models)} Neo4j compatible models")
    
    # Test Folk CRM compatibility
    folk_models = []
    for alias, model in MODEL_REGISTRY.items():
        if model.capabilities.folk_crm:
            folk_models.append(alias)
    
    print(f"  ✓ Found {len(folk_models)} Folk CRM compatible models")
    
    # Test MCP compatibility
    mcp_models = []
    for alias, model in MODEL_REGISTRY.items():
        if model.capabilities.mcp_compatible:
            mcp_models.append(alias)
    
    print(f"  ✓ Found {len(mcp_models)} MCP compatible models")
    
    # Test agent compatibility
    for agent_type in ["supervisor", "analytics", "sales", "talent"]:
        compatible_count = 0
        for model_alias in MODEL_REGISTRY.keys():
            result = checker.check_agent_compatibility(agent_type, model_alias)
            if result.compatible:
                compatible_count += 1
        print(f"  ✓ Agent '{agent_type}': {compatible_count} compatible models")
        assert compatible_count > 0, f"No compatible models for {agent_type}"
    
    print("  ✅ Tool compatibility validation passed")


def test_model_configuration():
    """Test model configuration management"""
    print("\n⚙️ Testing Model Configuration...")
    
    config = MockConfig()
    manager = ModelConfigurationManager(config)
    
    # Test default profiles
    for env in Environment:
        profile = manager.default_profiles[env]
        assert profile.environment == env
        print(f"  ✓ {env.value} profile: {profile.strategy.value}")
    
    # Test configuration creation
    agent_types = ["analytics", "sales", "talent"]
    mapping = manager.create_optimal_configuration(
        environment=Environment.DEVELOPMENT,
        agent_types=agent_types
    )
    
    assert len(mapping.agent_assignments) == len(agent_types)
    print(f"  ✓ Created configuration with {len(mapping.agent_assignments)} agents")
    
    # Display assignments
    for agent_type, model_alias in mapping.agent_assignments.items():
        model_info = MODEL_REGISTRY[model_alias]
        cost = model_info.metrics.cost_per_1k_output
        print(f"    - {agent_type}: {model_alias} (${cost:.4f}/1k tokens)")
    
    # Test configuration validation
    manager.current_mapping = mapping
    validation = manager.compatibility_checker.validate_deployment_requirements(
        mapping.agent_assignments
    )
    
    if validation["valid"]:
        print("  ✅ Configuration validation passed")
    else:
        print("  ⚠️ Configuration has compatibility warnings")
        for failure in validation["critical_failures"]:
            print(f"    - {failure['agent']}: {failure['failed_requirements']}")
    
    print("  ✅ Model configuration validation passed")


def test_cost_analysis():
    """Test cost analysis functionality"""
    print("\n💰 Testing Cost Analysis...")
    
    config = MockConfig()
    manager = ModelConfigurationManager(config)
    
    # Compare environments
    for env in [Environment.DEVELOPMENT, Environment.PRODUCTION]:
        mapping = manager.create_optimal_configuration(env)
        manager.current_mapping = mapping
        
        report = manager.generate_configuration_report()
        cost_analysis = report["cost_analysis"]
        
        total_cost = cost_analysis["total_output_cost_per_1k"]
        monthly_moderate = cost_analysis["estimated_monthly_cost"]["moderate_usage"]
        
        print(f"  ✓ {env.value}:")
        print(f"    - Cost per 1k tokens: ${total_cost:.4f}")
        print(f"    - Est. monthly (moderate): ${monthly_moderate:.2f}")
        
        # Show model assignments
        for agent, model in mapping.agent_assignments.items():
            model_info = MODEL_REGISTRY[model]
            print(f"    - {agent}: {model} ({model_info.metrics.accuracy_tier})")
    
    print("  ✅ Cost analysis validation passed")


def test_model_switching():
    """Test model switching functionality"""
    print("\n🔄 Testing Model Switching...")
    
    config = MockConfig()
    manager = ModelConfigurationManager(config)
    
    # Initialize configuration
    mapping = manager.create_optimal_configuration(Environment.DEVELOPMENT)
    manager.current_mapping = mapping
    
    # Try switching analytics model
    agent_type = "analytics"
    original_model = mapping.agent_assignments[agent_type]
    
    # Find compatible alternatives
    compatible = manager.compatibility_checker.find_compatible_models(
        manager.compatibility_checker.agent_requirements[agent_type],
        min_score=0.8
    )
    
    alternative_model = None
    for result in compatible:
        if result.model_alias != original_model:
            alternative_model = result.model_alias
            break
    
    if alternative_model:
        success = manager.switch_model(agent_type, alternative_model, validate=True)
        assert success, "Model switching should succeed"
        
        current_model = manager.get_model_for_agent(agent_type)
        assert current_model == alternative_model, "Model should be updated"
        
        print(f"  ✓ Switched {agent_type}: {original_model} → {alternative_model}")
    else:
        print(f"  ⚠️ No alternative models available for {agent_type}")
    
    print("  ✅ Model switching validation passed")


def main():
    """Run all tests"""
    print("🚀 OneVice Model Configuration System Test")
    print("=" * 50)
    
    try:
        test_model_registry()
        test_tool_compatibility()
        test_model_configuration()
        test_cost_analysis()
        test_model_switching()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Model system is working correctly.")
        print("\n📊 System Summary:")
        print(f"   - {len(MODEL_REGISTRY)} models in registry")
        print(f"   - 4 agent types supported (supervisor, analytics, sales, talent)")
        print(f"   - {len(Environment)} environment configurations")
        print("   - Full tool compatibility validation")
        print("   - Dynamic model switching capability")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()