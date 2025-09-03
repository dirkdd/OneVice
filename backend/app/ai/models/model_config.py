"""
Model Configuration Management

Dynamic model assignment system with tool compatibility validation
and easy switching for testing environments.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json

from .model_registry import MODEL_REGISTRY, ModelInfo, get_model_info
from .tool_compatibility import ToolCompatibilityChecker, ToolRequirement, ToolType
from ..config import AIConfig, AgentType
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Deployment environments with different model selection strategies"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class SelectionStrategy(str, Enum):
    """Model selection strategies"""
    COST_OPTIMIZED = "cost_optimized"      # Cheapest compatible model
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Best performance
    BALANCED = "balanced"                  # Balance of cost and performance
    PROVIDER_PREFERENCE = "provider_preference"  # Prefer specific provider

@dataclass
class ModelProfile:
    """Model configuration profile for different environments"""
    environment: Environment
    strategy: SelectionStrategy
    preferred_provider: Optional[str] = None
    max_cost_per_1k: Optional[float] = None
    min_accuracy_tier: Optional[str] = None
    require_tool_compatibility: bool = True
    allow_fallbacks: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment.value,
            "strategy": self.strategy.value,
            "preferred_provider": self.preferred_provider,
            "max_cost_per_1k": self.max_cost_per_1k,
            "min_accuracy_tier": self.min_accuracy_tier,
            "require_tool_compatibility": self.require_tool_compatibility,
            "allow_fallbacks": self.allow_fallbacks,
            "created_at": self.created_at
        }

@dataclass
class AgentModelMapping:
    """Complete agent-to-model mapping configuration"""
    agent_assignments: Dict[str, str]  # agent_type -> model_alias
    profile: ModelProfile
    compatibility_verified: bool = False
    fallback_models: Dict[str, List[str]] = field(default_factory=dict)
    validation_results: Optional[Dict[str, Any]] = None
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_assignments": self.agent_assignments,
            "profile": self.profile.to_dict(),
            "compatibility_verified": self.compatibility_verified,
            "fallback_models": self.fallback_models,
            "validation_results": self.validation_results,
            "last_updated": self.last_updated
        }

class ModelConfigurationManager:
    """
    Central manager for model configuration with tool compatibility validation
    """
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.compatibility_checker = ToolCompatibilityChecker(config)
        self.current_mapping: Optional[AgentModelMapping] = None
        self.saved_configurations: Dict[str, AgentModelMapping] = {}
        
        # Default configurations for each environment
        self.default_profiles = {
            Environment.DEVELOPMENT: ModelProfile(
                environment=Environment.DEVELOPMENT,
                strategy=SelectionStrategy.COST_OPTIMIZED,
                max_cost_per_1k=0.02,  # Increased to allow supervisor models
                allow_fallbacks=True,
                require_tool_compatibility=True
            ),
            Environment.TESTING: ModelProfile(
                environment=Environment.TESTING,
                strategy=SelectionStrategy.BALANCED,
                max_cost_per_1k=0.01,
                allow_fallbacks=True,
                require_tool_compatibility=True
            ),
            Environment.STAGING: ModelProfile(
                environment=Environment.STAGING,
                strategy=SelectionStrategy.PERFORMANCE_OPTIMIZED,
                preferred_provider="together",
                require_tool_compatibility=True,
                allow_fallbacks=False
            ),
            Environment.PRODUCTION: ModelProfile(
                environment=Environment.PRODUCTION,
                strategy=SelectionStrategy.PERFORMANCE_OPTIMIZED,
                preferred_provider="together",
                min_accuracy_tier="excellent",
                require_tool_compatibility=True,
                allow_fallbacks=False
            )
        }

    def create_optimal_configuration(
        self,
        environment: Environment,
        agent_types: List[str] = None,
        custom_profile: Optional[ModelProfile] = None
    ) -> AgentModelMapping:
        """
        Create an optimal model configuration for the specified environment
        """
        
        if agent_types is None:
            agent_types = ["supervisor", "analytics", "sales", "talent"]
        
        profile = custom_profile or self.default_profiles[environment]
        agent_assignments = {}
        fallback_models = {}
        
        for agent_type in agent_types:
            # Find the best model for this agent type
            best_model = self._select_optimal_model(agent_type, profile)
            if not best_model:
                raise AIProcessingError(f"No compatible model found for agent type: {agent_type}")
            
            agent_assignments[agent_type] = best_model
            
            # Find fallback models if allowed
            if profile.allow_fallbacks:
                fallbacks = self._find_fallback_models(agent_type, best_model, profile)
                fallback_models[agent_type] = fallbacks[:3]  # Top 3 fallbacks
        
        mapping = AgentModelMapping(
            agent_assignments=agent_assignments,
            profile=profile,
            fallback_models=fallback_models
        )
        
        # Validate the configuration
        validation_results = self.compatibility_checker.validate_deployment_requirements(
            agent_assignments
        )
        mapping.validation_results = validation_results
        mapping.compatibility_verified = validation_results["valid"]
        
        if not mapping.compatibility_verified:
            logger.warning(f"Configuration validation failed: {validation_results['critical_failures']}")
            if not profile.allow_fallbacks:
                raise AIProcessingError("Configuration validation failed and fallbacks not allowed")
        
        return mapping
    
    def _select_optimal_model(
        self, 
        agent_type: str, 
        profile: ModelProfile
    ) -> Optional[str]:
        """Select the optimal model for an agent type based on the profile strategy"""
        
        if agent_type not in self.compatibility_checker.agent_requirements:
            logger.error(f"Unknown agent type: {agent_type}")
            return None
        
        requirements = self.compatibility_checker.agent_requirements[agent_type]
        compatible_results = self.compatibility_checker.find_compatible_models(
            requirements=requirements,
            min_score=0.8 if profile.require_tool_compatibility else 0.0
        )
        
        if not compatible_results:
            return None
        
        # Filter by profile constraints
        filtered_models = []
        for result in compatible_results:
            model_info = MODEL_REGISTRY[result.model_alias]
            
            # Cost constraint
            if (profile.max_cost_per_1k and 
                model_info.metrics.cost_per_1k_output > profile.max_cost_per_1k):
                continue
            
            # Accuracy constraint
            if profile.min_accuracy_tier:
                accuracy_order = {"basic": 0, "good": 1, "excellent": 2, "best": 3}
                required_level = accuracy_order.get(profile.min_accuracy_tier, 0)
                model_level = accuracy_order.get(model_info.metrics.accuracy_tier, 0)
                if model_level < required_level:
                    continue
            
            # Provider preference
            if (profile.preferred_provider and 
                model_info.provider.value != profile.preferred_provider):
                # Don't skip, but add penalty in sorting
                pass
            
            filtered_models.append((result, model_info))
        
        if not filtered_models:
            return None
        
        # Sort based on strategy
        if profile.strategy == SelectionStrategy.COST_OPTIMIZED:
            filtered_models.sort(key=lambda x: x[1].metrics.cost_per_1k_output)
        
        elif profile.strategy == SelectionStrategy.PERFORMANCE_OPTIMIZED:
            # Sort by accuracy tier, then speed tier, then compatibility score
            def perf_key(item):
                result, model_info = item
                accuracy_score = {"basic": 0, "good": 1, "excellent": 2, "best": 3}.get(
                    model_info.metrics.accuracy_tier, 0
                )
                speed_score = {"slow": 0, "medium": 1, "fast": 2, "ultrafast": 3}.get(
                    model_info.metrics.speed_tier, 0
                )
                return (-accuracy_score, -speed_score, -result.score)
            
            filtered_models.sort(key=perf_key)
        
        elif profile.strategy == SelectionStrategy.PROVIDER_PREFERENCE:
            def provider_key(item):
                result, model_info = item
                provider_match = 1 if (profile.preferred_provider and 
                                     model_info.provider.value == profile.preferred_provider) else 0
                return (-provider_match, -result.score, model_info.metrics.cost_per_1k_output)
            
            filtered_models.sort(key=provider_key)
        
        else:  # BALANCED
            def balanced_key(item):
                result, model_info = item
                # Balance score: compatibility * 0.4 + cost_efficiency * 0.3 + performance * 0.3
                max_cost = max(m.metrics.cost_per_1k_output for m in MODEL_REGISTRY.values())
                cost_efficiency = 1.0 - (model_info.metrics.cost_per_1k_output / max_cost)
                
                accuracy_score = {"basic": 0.25, "good": 0.5, "excellent": 0.75, "best": 1.0}.get(
                    model_info.metrics.accuracy_tier, 0.25
                )
                
                balanced_score = (result.score * 0.4 + cost_efficiency * 0.3 + accuracy_score * 0.3)
                return -balanced_score
            
            filtered_models.sort(key=balanced_key)
        
        return filtered_models[0][0].model_alias
    
    def _find_fallback_models(
        self,
        agent_type: str,
        primary_model: str,
        profile: ModelProfile,
        max_fallbacks: int = 3
    ) -> List[str]:
        """Find suitable fallback models for an agent type"""
        
        requirements = self.compatibility_checker.agent_requirements[agent_type]
        compatible_results = self.compatibility_checker.find_compatible_models(
            requirements=requirements,
            min_score=0.6  # Lower threshold for fallbacks
        )
        
        fallbacks = []
        for result in compatible_results:
            if result.model_alias == primary_model:
                continue
                
            model_info = MODEL_REGISTRY[result.model_alias]
            
            # Relax constraints for fallbacks
            max_cost = profile.max_cost_per_1k * 1.5 if profile.max_cost_per_1k else None
            if max_cost and model_info.metrics.cost_per_1k_output > max_cost:
                continue
                
            fallbacks.append(result.model_alias)
            
            if len(fallbacks) >= max_fallbacks:
                break
        
        return fallbacks

    def switch_model(
        self,
        agent_type: str,
        new_model_alias: str,
        validate: bool = True
    ) -> bool:
        """
        Switch the model for a specific agent type
        """
        if not self.current_mapping:
            raise AIProcessingError("No current configuration loaded")
        
        if validate:
            # Check compatibility
            result = self.compatibility_checker.check_agent_compatibility(
                agent_type, new_model_alias
            )
            if not result.compatible:
                logger.error(f"Model {new_model_alias} not compatible with agent {agent_type}")
                return False
        
        # Update the mapping
        old_model = self.current_mapping.agent_assignments.get(agent_type)
        self.current_mapping.agent_assignments[agent_type] = new_model_alias
        self.current_mapping.last_updated = datetime.utcnow().isoformat()
        
        logger.info(f"Switched {agent_type} model from {old_model} to {new_model_alias}")
        return True
    
    def load_configuration(self, config_name: str) -> AgentModelMapping:
        """Load a saved configuration"""
        if config_name not in self.saved_configurations:
            raise AIProcessingError(f"Configuration '{config_name}' not found")
        
        self.current_mapping = self.saved_configurations[config_name]
        return self.current_mapping
    
    def save_configuration(self, config_name: str, mapping: AgentModelMapping = None) -> None:
        """Save the current or specified configuration"""
        if mapping is None:
            if not self.current_mapping:
                raise AIProcessingError("No configuration to save")
            mapping = self.current_mapping
        
        self.saved_configurations[config_name] = mapping
        logger.info(f"Saved configuration '{config_name}'")
    
    def get_current_assignments(self) -> Dict[str, str]:
        """Get current agent-to-model assignments"""
        if not self.current_mapping:
            return {}
        return self.current_mapping.agent_assignments.copy()
    
    def get_model_for_agent(self, agent_type: str) -> Optional[str]:
        """Get the current model assignment for an agent type"""
        if not self.current_mapping:
            return None
        return self.current_mapping.agent_assignments.get(agent_type)
    
    def get_fallback_models(self, agent_type: str) -> List[str]:
        """Get fallback models for an agent type"""
        if not self.current_mapping:
            return []
        return self.current_mapping.fallback_models.get(agent_type, [])
    
    def generate_configuration_report(self) -> Dict[str, Any]:
        """Generate a comprehensive configuration report"""
        if not self.current_mapping:
            return {"error": "No configuration loaded"}
        
        report = {
            "configuration_summary": self.current_mapping.to_dict(),
            "model_details": {},
            "cost_analysis": {},
            "compatibility_matrix": {},
            "recommendations": []
        }
        
        # Model details for each assigned model
        total_cost_input = 0
        total_cost_output = 0
        
        for agent_type, model_alias in self.current_mapping.agent_assignments.items():
            model_summary = self.compatibility_checker.get_model_tool_summary(model_alias)
            report["model_details"][agent_type] = model_summary
            
            # Cost analysis
            model_info = MODEL_REGISTRY[model_alias]
            total_cost_input += model_info.metrics.cost_per_1k_input
            total_cost_output += model_info.metrics.cost_per_1k_output
        
        report["cost_analysis"] = {
            "total_input_cost_per_1k": total_cost_input,
            "total_output_cost_per_1k": total_cost_output,
            "estimated_monthly_cost": {
                "light_usage": (total_cost_input + total_cost_output) * 100,  # 100K tokens
                "moderate_usage": (total_cost_input + total_cost_output) * 1000,  # 1M tokens
                "heavy_usage": (total_cost_input + total_cost_output) * 10000   # 10M tokens
            }
        }
        
        # Compatibility matrix
        report["compatibility_matrix"] = self.compatibility_checker.generate_compatibility_matrix()
        
        # Recommendations
        if self.current_mapping.validation_results and not self.current_mapping.compatibility_verified:
            report["recommendations"].append("Critical: Some models do not meet tool requirements")
        
        # Cost optimization recommendations
        for agent_type, model_alias in self.current_mapping.agent_assignments.items():
            cheaper_alternatives = self._find_cheaper_alternatives(agent_type, model_alias)
            if cheaper_alternatives:
                report["recommendations"].append(
                    f"Consider {cheaper_alternatives[0]} for {agent_type} to reduce costs"
                )
        
        return report
    
    def _find_cheaper_alternatives(
        self, 
        agent_type: str, 
        current_model: str
    ) -> List[str]:
        """Find cheaper compatible alternatives"""
        current_cost = MODEL_REGISTRY[current_model].metrics.cost_per_1k_output
        
        requirements = self.compatibility_checker.agent_requirements[agent_type]
        compatible_results = self.compatibility_checker.find_compatible_models(requirements)
        
        cheaper_models = []
        for result in compatible_results:
            if result.model_alias == current_model:
                continue
            
            model_cost = MODEL_REGISTRY[result.model_alias].metrics.cost_per_1k_output
            if model_cost < current_cost:
                cheaper_models.append(result.model_alias)
        
        # Sort by cost (cheapest first)
        cheaper_models.sort(key=lambda x: MODEL_REGISTRY[x].metrics.cost_per_1k_output)
        return cheaper_models

    def initialize_default_configuration(
        self, 
        environment: Environment = Environment.DEVELOPMENT
    ) -> AgentModelMapping:
        """Initialize with default configuration for environment"""
        
        mapping = self.create_optimal_configuration(environment)
        self.current_mapping = mapping
        
        logger.info(f"Initialized default configuration for {environment.value}")
        logger.info(f"Agent assignments: {mapping.agent_assignments}")
        
        return mapping