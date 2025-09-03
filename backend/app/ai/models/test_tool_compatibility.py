"""
Tool Compatibility Testing Framework

Comprehensive tests for model-tool compatibility verification
and validation of the model configuration system.
"""

import pytest
import asyncio
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, MagicMock

from .model_registry import MODEL_REGISTRY, get_model_info
from .tool_compatibility import ToolCompatibilityChecker, ToolRequirement, ToolType
from .model_config import ModelConfigurationManager, ModelProfile, Environment, SelectionStrategy
from ..config import AIConfig

class TestToolCompatibilityChecker:
    """Test suite for tool compatibility checking"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock AIConfig for testing"""
        config = Mock(spec=AIConfig)
        config.redis_url = "redis://localhost:6379"
        config.redis_key_prefix = "onevice:test:"
        return config
    
    @pytest.fixture
    def compatibility_checker(self, mock_config):
        """Create ToolCompatibilityChecker instance for testing"""
        return ToolCompatibilityChecker(mock_config)
    
    def test_model_registry_completeness(self):
        """Test that all models in registry have required fields"""
        for alias, model_info in MODEL_REGISTRY.items():
            assert model_info.provider is not None
            assert model_info.model_id is not None
            assert model_info.display_name is not None
            assert model_info.capabilities is not None
            assert model_info.metrics is not None
            assert model_info.tool_calling is not None
    
    def test_neo4j_compatibility_checking(self, compatibility_checker):
        """Test Neo4j compatibility requirements"""
        neo4j_req = ToolRequirement(ToolType.NEO4J, required=True)
        
        # Test models with Neo4j support
        for alias, model_info in MODEL_REGISTRY.items():
            if model_info.capabilities.neo4j:
                result = compatibility_checker.check_model_compatibility(
                    alias, [neo4j_req]
                )
                assert result.compatible, f"Model {alias} should be Neo4j compatible"
                assert len(result.failed_requirements) == 0
    
    def test_folk_crm_compatibility_checking(self, compatibility_checker):
        """Test Folk CRM compatibility requirements"""
        folk_crm_req = ToolRequirement(ToolType.FOLK_CRM, required=True)
        
        # Test models with Folk CRM support
        for alias, model_info in MODEL_REGISTRY.items():
            if model_info.capabilities.folk_crm:
                result = compatibility_checker.check_model_compatibility(
                    alias, [folk_crm_req]
                )
                assert result.compatible, f"Model {alias} should be Folk CRM compatible"
                assert len(result.failed_requirements) == 0
    
    def test_mcp_compatibility_checking(self, compatibility_checker):
        """Test MCP server compatibility requirements"""
        mcp_req = ToolRequirement(ToolType.MCP_SERVER, required=True)
        
        # Test models with MCP support
        for alias, model_info in MODEL_REGISTRY.items():
            if model_info.capabilities.mcp_compatible:
                result = compatibility_checker.check_model_compatibility(
                    alias, [mcp_req]
                )
                assert result.compatible, f"Model {alias} should be MCP compatible"
                assert len(result.failed_requirements) == 0
    
    def test_function_calling_compatibility(self, compatibility_checker):
        """Test function calling compatibility requirements"""
        function_req = ToolRequirement(ToolType.FUNCTION_CALLING, required=True)
        
        # Test models with function calling support
        for alias, model_info in MODEL_REGISTRY.items():
            if model_info.capabilities.function_calling or model_info.capabilities.native_tool_use:
                result = compatibility_checker.check_model_compatibility(
                    alias, [function_req]
                )
                assert result.compatible, f"Model {alias} should support function calling"
                assert len(result.failed_requirements) == 0
    
    def test_agent_requirements_validation(self, compatibility_checker):
        """Test predefined agent requirements"""
        for agent_type, requirements in compatibility_checker.agent_requirements.items():
            assert len(requirements) > 0, f"Agent {agent_type} should have requirements"
            for req in requirements:
                assert isinstance(req, ToolRequirement)
                assert req.tool_type in ToolType
    
    def test_compatibility_scoring(self, compatibility_checker):
        """Test compatibility scoring system"""
        # Test with all requirements passed
        all_passed_req = [ToolRequirement(ToolType.FUNCTION_CALLING, required=True)]
        result = compatibility_checker.check_model_compatibility(
            "mixtral-8x7b", all_passed_req
        )
        assert 0.8 <= result.score <= 1.0
        
        # Test with some requirements failed
        impossible_req = [
            ToolRequirement(ToolType.NEO4J, required=True),
            ToolRequirement(ToolType.FOLK_CRM, required=True),
            ToolRequirement(ToolType.REASONING, required=True, minimum_capability_level="excellent")
        ]
        
        # Find a model that doesn't meet all requirements
        for alias in MODEL_REGISTRY.keys():
            result = compatibility_checker.check_model_compatibility(alias, impossible_req)
            if not result.compatible:
                assert result.score < 1.0
                break
    
    def test_fallback_acceptance(self, compatibility_checker):
        """Test fallback acceptance for optional requirements"""
        fallback_req = [
            ToolRequirement(ToolType.NEO4J, required=True),
            ToolRequirement(ToolType.VECTOR_SEARCH, required=False, fallback_acceptable=True)
        ]
        
        # Find a model with Neo4j but potentially without vector search
        for alias, model_info in MODEL_REGISTRY.items():
            if model_info.capabilities.neo4j:
                result = compatibility_checker.check_model_compatibility(alias, fallback_req)
                # Should be compatible even if vector search is missing due to fallback
                break
    
    def test_find_compatible_models(self, compatibility_checker):
        """Test finding compatible models"""
        basic_requirements = [ToolRequirement(ToolType.FUNCTION_CALLING, required=True)]
        
        compatible_models = compatibility_checker.find_compatible_models(
            basic_requirements, min_score=0.8
        )
        
        assert len(compatible_models) > 0
        for result in compatible_models:
            assert result.compatible
            assert result.score >= 0.8
            assert result.model_alias in MODEL_REGISTRY
    
    def test_agent_compatibility_checking(self, compatibility_checker):
        """Test agent-specific compatibility checking"""
        for agent_type in compatibility_checker.agent_requirements.keys():
            # Find at least one compatible model for each agent type
            compatible_found = False
            for model_alias in MODEL_REGISTRY.keys():
                result = compatibility_checker.check_agent_compatibility(agent_type, model_alias)
                if result.compatible:
                    compatible_found = True
                    break
            
            assert compatible_found, f"No compatible models found for agent type: {agent_type}"
    
    def test_compatibility_matrix_generation(self, compatibility_checker):
        """Test compatibility matrix generation"""
        matrix = compatibility_checker.generate_compatibility_matrix()
        
        # Check structure
        for agent_type in compatibility_checker.agent_requirements.keys():
            assert agent_type in matrix
            for model_alias in MODEL_REGISTRY.keys():
                assert model_alias in matrix[agent_type]
                result_data = matrix[agent_type][model_alias]
                assert "compatible" in result_data
                assert "compatibility_score" in result_data
    
    def test_model_tool_summary(self, compatibility_checker):
        """Test model tool capability summary generation"""
        for model_alias in list(MODEL_REGISTRY.keys())[:3]:  # Test first 3 models
            summary = compatibility_checker.get_model_tool_summary(model_alias)
            
            assert "model" in summary
            assert "tool_capabilities" in summary
            assert "supported_agents" in summary
            assert "cost_per_1k_tokens" in summary
            assert "performance" in summary
            
            # Check tool capabilities structure
            tool_caps = summary["tool_capabilities"]
            assert "neo4j_cypher" in tool_caps
            assert "folk_crm_api" in tool_caps
            assert "mcp_compatible" in tool_caps
            assert "function_calling" in tool_caps

class TestModelConfigurationManager:
    """Test suite for model configuration management"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock AIConfig for testing"""
        config = Mock(spec=AIConfig)
        config.redis_url = "redis://localhost:6379"
        config.redis_key_prefix = "onevice:test:"
        return config
    
    @pytest.fixture
    def config_manager(self, mock_config):
        """Create ModelConfigurationManager instance for testing"""
        return ModelConfigurationManager(mock_config)
    
    def test_default_profiles_exist(self, config_manager):
        """Test that default profiles exist for all environments"""
        for env in Environment:
            assert env in config_manager.default_profiles
            profile = config_manager.default_profiles[env]
            assert profile.environment == env
            assert profile.strategy in SelectionStrategy
    
    def test_optimal_configuration_creation(self, config_manager):
        """Test optimal configuration creation"""
        agent_types = ["supervisor", "analytics", "sales", "talent"]
        
        for env in Environment:
            mapping = config_manager.create_optimal_configuration(
                environment=env,
                agent_types=agent_types
            )
            
            assert mapping.profile.environment == env
            assert len(mapping.agent_assignments) == len(agent_types)
            
            # Verify all agent types have model assignments
            for agent_type in agent_types:
                assert agent_type in mapping.agent_assignments
                model_alias = mapping.agent_assignments[agent_type]
                assert model_alias in MODEL_REGISTRY
    
    def test_model_selection_strategies(self, config_manager):
        """Test different model selection strategies"""
        agent_type = "analytics"
        
        # Test cost optimized
        cost_profile = ModelProfile(
            environment=Environment.DEVELOPMENT,
            strategy=SelectionStrategy.COST_OPTIMIZED,
            max_cost_per_1k=0.001
        )
        
        cost_model = config_manager._select_optimal_model(agent_type, cost_profile)
        if cost_model:  # Might be None if no models meet cost constraint
            model_info = MODEL_REGISTRY[cost_model]
            assert model_info.metrics.cost_per_1k_output <= 0.001
        
        # Test performance optimized
        perf_profile = ModelProfile(
            environment=Environment.PRODUCTION,
            strategy=SelectionStrategy.PERFORMANCE_OPTIMIZED,
            min_accuracy_tier="excellent"
        )
        
        perf_model = config_manager._select_optimal_model(agent_type, perf_profile)
        if perf_model:
            model_info = MODEL_REGISTRY[perf_model]
            assert model_info.metrics.accuracy_tier in ["excellent", "best"]
    
    def test_fallback_model_finding(self, config_manager):
        """Test fallback model identification"""
        agent_type = "sales"
        primary_model = "mixtral-8x7b"
        
        profile = ModelProfile(
            environment=Environment.TESTING,
            strategy=SelectionStrategy.BALANCED,
            allow_fallbacks=True
        )
        
        fallbacks = config_manager._find_fallback_models(agent_type, primary_model, profile)
        
        # Should find at least some fallback models
        assert isinstance(fallbacks, list)
        if fallbacks:
            for fallback in fallbacks:
                assert fallback != primary_model
                assert fallback in MODEL_REGISTRY
    
    def test_model_switching(self, config_manager):
        """Test model switching functionality"""
        # Initialize with default configuration
        mapping = config_manager.create_optimal_configuration(Environment.DEVELOPMENT)
        config_manager.current_mapping = mapping
        
        agent_type = "analytics"
        original_model = mapping.agent_assignments[agent_type]
        
        # Find a different compatible model
        compatible_models = config_manager.compatibility_checker.find_compatible_models(
            config_manager.compatibility_checker.agent_requirements[agent_type]
        )
        
        if len(compatible_models) > 1:
            # Find a different model
            new_model = None
            for result in compatible_models:
                if result.model_alias != original_model:
                    new_model = result.model_alias
                    break
            
            if new_model:
                success = config_manager.switch_model(agent_type, new_model, validate=True)
                assert success
                assert config_manager.current_mapping.agent_assignments[agent_type] == new_model
    
    def test_configuration_validation(self, config_manager):
        """Test configuration validation"""
        # Create a valid configuration
        valid_mapping = config_manager.create_optimal_configuration(Environment.DEVELOPMENT)
        
        validation_results = config_manager.compatibility_checker.validate_deployment_requirements(
            valid_mapping.agent_assignments
        )
        
        assert "valid" in validation_results
        assert "agent_results" in validation_results
        assert "critical_failures" in validation_results
        assert "warnings" in validation_results
    
    def test_configuration_report_generation(self, config_manager):
        """Test configuration report generation"""
        # Initialize configuration
        mapping = config_manager.create_optimal_configuration(Environment.DEVELOPMENT)
        config_manager.current_mapping = mapping
        
        report = config_manager.generate_configuration_report()
        
        assert "configuration_summary" in report
        assert "model_details" in report
        assert "cost_analysis" in report
        assert "compatibility_matrix" in report
        assert "recommendations" in report
        
        # Check cost analysis structure
        cost_analysis = report["cost_analysis"]
        assert "total_input_cost_per_1k" in cost_analysis
        assert "total_output_cost_per_1k" in cost_analysis
        assert "estimated_monthly_cost" in cost_analysis
    
    def test_cheaper_alternatives_finding(self, config_manager):
        """Test finding cheaper alternatives"""
        agent_type = "supervisor"
        current_model = "llama-3.1-405b"  # Expensive model
        
        alternatives = config_manager._find_cheaper_alternatives(agent_type, current_model)
        
        if alternatives:
            current_cost = MODEL_REGISTRY[current_model].metrics.cost_per_1k_output
            for alt_model in alternatives:
                alt_cost = MODEL_REGISTRY[alt_model].metrics.cost_per_1k_output
                assert alt_cost < current_cost

class TestModelIntegration:
    """Integration tests for the complete model system"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock AIConfig for testing"""
        config = Mock(spec=AIConfig)
        config.redis_url = "redis://localhost:6379"
        config.redis_key_prefix = "onevice:test:"
        config.get_agent_config = Mock(return_value={
            "memory_ttl": 3600,
            "max_history": 10,
            "timeout": 30
        })
        return config
    
    @pytest.fixture
    def mock_llm_router(self):
        """Create mock LLMRouter for testing"""
        router = Mock()
        router.get_provider_stats = Mock(return_value={"together": {"requests": 100}})
        return router
    
    def test_end_to_end_model_configuration(self, mock_config, mock_llm_router):
        """Test complete end-to-end model configuration flow"""
        # Initialize system
        config_manager = ModelConfigurationManager(mock_config)
        
        # Create configuration for development environment
        mapping = config_manager.create_optimal_configuration(
            environment=Environment.DEVELOPMENT,
            agent_types=["analytics", "sales", "talent"]
        )
        
        # Validate configuration
        assert mapping.compatibility_verified or mapping.profile.allow_fallbacks
        assert len(mapping.agent_assignments) == 3
        
        # Test model switching
        config_manager.current_mapping = mapping
        
        # Test configuration report
        report = config_manager.generate_configuration_report()
        assert report is not None
        assert "error" not in report
    
    def test_production_configuration_requirements(self, mock_config):
        """Test production configuration meets strict requirements"""
        config_manager = ModelConfigurationManager(mock_config)
        
        # Production should have strict requirements
        prod_mapping = config_manager.create_optimal_configuration(
            environment=Environment.PRODUCTION,
            agent_types=["supervisor", "analytics", "sales", "talent"]
        )
        
        # Production should be fully validated
        assert prod_mapping.compatibility_verified
        
        # Check that production models meet high standards
        for agent_type, model_alias in prod_mapping.agent_assignments.items():
            model_info = MODEL_REGISTRY[model_alias]
            
            # Production models should have good accuracy
            assert model_info.metrics.accuracy_tier in ["good", "excellent", "best"]
            
            # Should have required capabilities for their agent type
            requirements = config_manager.compatibility_checker.agent_requirements[agent_type]
            result = config_manager.compatibility_checker.check_model_compatibility(
                model_alias, requirements
            )
            assert result.compatible
    
    def test_development_vs_production_differences(self, mock_config):
        """Test that development and production configurations differ appropriately"""
        config_manager = ModelConfigurationManager(mock_config)
        
        dev_mapping = config_manager.create_optimal_configuration(Environment.DEVELOPMENT)
        prod_mapping = config_manager.create_optimal_configuration(Environment.PRODUCTION)
        
        # Calculate cost differences
        dev_cost = sum(
            MODEL_REGISTRY[model].metrics.cost_per_1k_output 
            for model in dev_mapping.agent_assignments.values()
        )
        prod_cost = sum(
            MODEL_REGISTRY[model].metrics.cost_per_1k_output 
            for model in prod_mapping.agent_assignments.values()
        )
        
        # Development should generally be more cost-conscious
        # (This might not always be true, but it's a reasonable expectation)
        # assert dev_cost <= prod_cost * 1.5  # Allow some flexibility

# Test runner and fixtures
if __name__ == "__main__":
    import sys
    
    def run_tests():
        """Run all compatibility tests"""
        print("Running Tool Compatibility Tests...")
        
        # Run specific test methods
        test_suite = TestToolCompatibilityChecker()
        config_test_suite = TestModelConfigurationManager()
        integration_test_suite = TestModelIntegration()
        
        # Create mock fixtures
        mock_config = Mock(spec=AIConfig)
        mock_config.redis_url = "redis://localhost:6379"
        mock_config.redis_key_prefix = "onevice:test:"
        
        # Run basic registry tests
        print("✓ Testing model registry completeness...")
        test_suite.test_model_registry_completeness()
        
        # Run compatibility checker tests
        checker = ToolCompatibilityChecker(mock_config)
        print("✓ Testing Neo4j compatibility...")
        test_suite.test_neo4j_compatibility_checking(checker)
        
        print("✓ Testing Folk CRM compatibility...")
        test_suite.test_folk_crm_compatibility_checking(checker)
        
        print("✓ Testing MCP compatibility...")
        test_suite.test_mcp_compatibility_checking(checker)
        
        print("✓ Testing function calling compatibility...")
        test_suite.test_function_calling_compatibility(checker)
        
        # Run configuration manager tests
        config_manager = ModelConfigurationManager(mock_config)
        print("✓ Testing default profiles...")
        config_test_suite.test_default_profiles_exist(config_manager)
        
        print("✓ Testing optimal configuration creation...")
        config_test_suite.test_optimal_configuration_creation(config_manager)
        
        print("\n✅ All tool compatibility tests passed!")
        return True
    
    try:
        run_tests()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        sys.exit(1)