"""
Tool Compatibility Checker

Verifies model capabilities against specific tool requirements
for Neo4j, Folk CRM, MCP servers, and other integrations.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from .model_registry import MODEL_REGISTRY, ModelInfo, get_model_info
from ..config import AIConfig
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

class ToolType(str, Enum):
    """Categories of tools that require compatibility checking"""
    NEO4J = "neo4j"
    FOLK_CRM = "folk_crm"
    MCP_SERVER = "mcp_server"
    FUNCTION_CALLING = "function_calling"
    VECTOR_SEARCH = "vector_search"
    STRUCTURED_OUTPUT = "structured_output"
    JSON_MODE = "json_mode"
    REASONING = "reasoning"

@dataclass
class ToolRequirement:
    """Specific tool requirement specification"""
    tool_type: ToolType
    required: bool = True
    minimum_capability_level: str = "basic"  # basic, good, excellent
    fallback_acceptable: bool = False
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.tool_type.value} capability required"

@dataclass
class CompatibilityResult:
    """Result of compatibility checking"""
    model_alias: str
    compatible: bool
    passed_requirements: List[ToolRequirement]
    failed_requirements: List[ToolRequirement]
    warnings: List[str]
    score: float  # 0.0 to 1.0 compatibility score
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_alias": self.model_alias,
            "compatible": self.compatible,
            "passed_requirements": len(self.passed_requirements),
            "failed_requirements": len(self.failed_requirements),
            "warnings": self.warnings,
            "compatibility_score": self.score,
            "timestamp": self.timestamp
        }

class ToolCompatibilityChecker:
    """
    Comprehensive tool compatibility checker for AI models
    """
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.compatibility_cache: Dict[str, Dict[str, CompatibilityResult]] = {}
        
        # Predefined requirement sets for common agent types
        self.agent_requirements = {
            "supervisor": [
                ToolRequirement(ToolType.FUNCTION_CALLING, required=True),
                ToolRequirement(ToolType.REASONING, required=True, minimum_capability_level="excellent"),
                ToolRequirement(ToolType.STRUCTURED_OUTPUT, required=True),
                ToolRequirement(ToolType.MCP_SERVER, required=True)
            ],
            "analytics": [
                ToolRequirement(ToolType.NEO4J, required=True),
                ToolRequirement(ToolType.FUNCTION_CALLING, required=True),
                ToolRequirement(ToolType.STRUCTURED_OUTPUT, required=True),
                ToolRequirement(ToolType.VECTOR_SEARCH, required=False, fallback_acceptable=True)
            ],
            "sales": [
                ToolRequirement(ToolType.FOLK_CRM, required=True),
                ToolRequirement(ToolType.FUNCTION_CALLING, required=True),
                ToolRequirement(ToolType.NEO4J, required=True),
                ToolRequirement(ToolType.STRUCTURED_OUTPUT, required=False, fallback_acceptable=True)
            ],
            "talent": [
                ToolRequirement(ToolType.NEO4J, required=True),
                ToolRequirement(ToolType.FUNCTION_CALLING, required=True),
                ToolRequirement(ToolType.VECTOR_SEARCH, required=True),
                ToolRequirement(ToolType.STRUCTURED_OUTPUT, required=True)
            ],
            "general": [
                ToolRequirement(ToolType.FUNCTION_CALLING, required=True),
                ToolRequirement(ToolType.JSON_MODE, required=False, fallback_acceptable=True),
                ToolRequirement(ToolType.MCP_SERVER, required=False, fallback_acceptable=True)
            ]
        }

    def check_model_compatibility(
        self,
        model_alias: str,
        requirements: List[ToolRequirement]
    ) -> CompatibilityResult:
        """
        Check if a model meets specific tool requirements
        """
        model_info = get_model_info(model_alias)
        if not model_info:
            return CompatibilityResult(
                model_alias=model_alias,
                compatible=False,
                passed_requirements=[],
                failed_requirements=requirements,
                warnings=[f"Model {model_alias} not found in registry"],
                score=0.0,
                timestamp=datetime.utcnow().isoformat()
            )
        
        passed_requirements = []
        failed_requirements = []
        warnings = []
        
        for requirement in requirements:
            compatibility_check = self._check_single_requirement(
                model_info, requirement
            )
            
            if compatibility_check["passed"]:
                passed_requirements.append(requirement)
                if compatibility_check.get("warning"):
                    warnings.append(compatibility_check["warning"])
            else:
                if requirement.fallback_acceptable:
                    passed_requirements.append(requirement)
                    warnings.append(
                        f"{requirement.tool_type.value} not natively supported but fallback acceptable"
                    )
                else:
                    failed_requirements.append(requirement)
        
        # Calculate compatibility score
        total_requirements = len(requirements)
        passed_count = len(passed_requirements)
        score = passed_count / total_requirements if total_requirements > 0 else 1.0
        
        # Apply penalty for warnings
        warning_penalty = len(warnings) * 0.1
        score = max(0.0, score - warning_penalty)
        
        compatible = len(failed_requirements) == 0
        
        return CompatibilityResult(
            model_alias=model_alias,
            compatible=compatible,
            passed_requirements=passed_requirements,
            failed_requirements=failed_requirements,
            warnings=warnings,
            score=score,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _check_single_requirement(
        self, 
        model_info: ModelInfo, 
        requirement: ToolRequirement
    ) -> Dict[str, Any]:
        """Check a single requirement against model capabilities"""
        
        caps = model_info.capabilities
        
        if requirement.tool_type == ToolType.NEO4J:
            return {
                "passed": caps.neo4j and caps.cypher_generation,
                "warning": "Neo4j support available but Cypher generation quality not verified" 
                          if caps.neo4j and not caps.cypher_generation else None
            }
        
        elif requirement.tool_type == ToolType.FOLK_CRM:
            return {
                "passed": caps.folk_crm and caps.function_calling,
                "warning": "Folk CRM requires function calling - both must be supported" 
                          if not (caps.folk_crm and caps.function_calling) else None
            }
        
        elif requirement.tool_type == ToolType.MCP_SERVER:
            return {
                "passed": caps.mcp_compatible and caps.function_calling,
                "warning": "MCP compatibility requires function calling support" 
                          if not (caps.mcp_compatible and caps.function_calling) else None
            }
        
        elif requirement.tool_type == ToolType.FUNCTION_CALLING:
            return {
                "passed": caps.function_calling or caps.native_tool_use,
                "warning": "Native tool use available but OpenAI format compatibility not verified" 
                          if caps.native_tool_use and not caps.function_calling else None
            }
        
        elif requirement.tool_type == ToolType.STRUCTURED_OUTPUT:
            return {
                "passed": caps.structured_output or caps.json_mode,
                "warning": "JSON mode available but structured output quality not verified" 
                          if caps.json_mode and not caps.structured_output else None
            }
        
        elif requirement.tool_type == ToolType.JSON_MODE:
            return {"passed": caps.json_mode}
        
        elif requirement.tool_type == ToolType.VECTOR_SEARCH:
            # For now, consider all models capable of vector search through embedding models
            # This could be enhanced to check specific vector database integrations
            return {"passed": True, "warning": "Vector search assumed available through embeddings"}
        
        elif requirement.tool_type == ToolType.REASONING:
            # Check reasoning capability against minimum level
            has_reasoning = caps.reasoning
            if requirement.minimum_capability_level == "excellent":
                # Only large models with explicit reasoning flags
                has_sufficient_reasoning = (
                    has_reasoning and 
                    model_info.size_category.value in ["large", "xlarge"] and
                    model_info.metrics.accuracy_tier in ["excellent", "best"]
                )
            else:
                has_sufficient_reasoning = has_reasoning
                
            return {
                "passed": has_sufficient_reasoning,
                "warning": f"Reasoning capability may not meet {requirement.minimum_capability_level} level"
                          if has_reasoning and not has_sufficient_reasoning else None
            }
        
        else:
            return {"passed": False, "warning": f"Unknown requirement type: {requirement.tool_type}"}

    def check_agent_compatibility(
        self,
        agent_type: str,
        model_alias: str
    ) -> CompatibilityResult:
        """Check if a model is compatible with a specific agent type"""
        
        if agent_type not in self.agent_requirements:
            raise AIProcessingError(f"Unknown agent type: {agent_type}")
        
        requirements = self.agent_requirements[agent_type]
        return self.check_model_compatibility(model_alias, requirements)
    
    def find_compatible_models(
        self,
        requirements: List[ToolRequirement],
        min_score: float = 0.8,
        max_models: int = 10
    ) -> List[CompatibilityResult]:
        """Find all models that meet the requirements"""
        
        results = []
        
        for model_alias in MODEL_REGISTRY.keys():
            result = self.check_model_compatibility(model_alias, requirements)
            if result.score >= min_score:
                results.append(result)
        
        # Sort by compatibility score (highest first), then by cost (lowest first)
        results.sort(
            key=lambda x: (
                -x.score,  # Higher score first
                MODEL_REGISTRY[x.model_alias].metrics.cost_per_1k_output  # Lower cost first
            )
        )
        
        return results[:max_models]
    
    def find_best_model_for_agent(
        self,
        agent_type: str,
        exclude_models: List[str] = None,
        prefer_provider: str = None
    ) -> Optional[str]:
        """Find the best model for a specific agent type"""
        
        if agent_type not in self.agent_requirements:
            return None
        
        exclude_models = exclude_models or []
        compatible_models = []
        
        for model_alias in MODEL_REGISTRY.keys():
            if model_alias in exclude_models:
                continue
                
            result = self.check_agent_compatibility(agent_type, model_alias)
            if result.compatible:
                compatible_models.append((model_alias, result))
        
        if not compatible_models:
            return None
        
        # Sort by preference: provider match, score, cost
        def sort_key(item):
            model_alias, result = item
            model_info = MODEL_REGISTRY[model_alias]
            
            provider_match = 1 if (prefer_provider and 
                                 model_info.provider.value == prefer_provider) else 0
            
            return (
                -provider_match,  # Preferred provider first
                -result.score,    # Higher score first
                model_info.metrics.cost_per_1k_output  # Lower cost first
            )
        
        compatible_models.sort(key=sort_key)
        return compatible_models[0][0]
    
    def generate_compatibility_matrix(self) -> Dict[str, Dict[str, Any]]:
        """Generate a complete compatibility matrix for all models and agent types"""
        
        matrix = {}
        
        for agent_type in self.agent_requirements.keys():
            matrix[agent_type] = {}
            
            for model_alias in MODEL_REGISTRY.keys():
                result = self.check_agent_compatibility(agent_type, model_alias)
                matrix[agent_type][model_alias] = result.to_dict()
        
        return matrix
    
    def get_model_tool_summary(self, model_alias: str) -> Dict[str, Any]:
        """Get a comprehensive tool capability summary for a model"""
        
        model_info = get_model_info(model_alias)
        if not model_info:
            return {"error": f"Model {model_alias} not found"}
        
        caps = model_info.capabilities
        
        return {
            "model": model_alias,
            "display_name": model_info.display_name,
            "provider": model_info.provider.value,
            "tool_capabilities": {
                "neo4j_cypher": caps.neo4j and caps.cypher_generation,
                "folk_crm_api": caps.folk_crm and caps.function_calling,
                "mcp_compatible": caps.mcp_compatible and caps.function_calling,
                "function_calling": caps.function_calling or caps.native_tool_use,
                "structured_output": caps.structured_output or caps.json_mode,
                "reasoning": caps.reasoning
            },
            "supported_agents": [
                agent_type for agent_type in self.agent_requirements.keys()
                if self.check_agent_compatibility(agent_type, model_alias).compatible
            ],
            "cost_per_1k_tokens": {
                "input": model_info.metrics.cost_per_1k_input,
                "output": model_info.metrics.cost_per_1k_output
            },
            "performance": {
                "speed_tier": model_info.metrics.speed_tier,
                "accuracy_tier": model_info.metrics.accuracy_tier
            }
        }

    def validate_deployment_requirements(
        self, 
        agent_assignments: Dict[str, str]
    ) -> Dict[str, Any]:
        """Validate that all agent assignments meet tool requirements"""
        
        validation_results = {
            "valid": True,
            "agent_results": {},
            "critical_failures": [],
            "warnings": []
        }
        
        for agent_type, model_alias in agent_assignments.items():
            result = self.check_agent_compatibility(agent_type, model_alias)
            validation_results["agent_results"][agent_type] = result.to_dict()
            
            if not result.compatible:
                validation_results["valid"] = False
                validation_results["critical_failures"].append({
                    "agent": agent_type,
                    "model": model_alias,
                    "failed_requirements": [req.tool_type.value for req in result.failed_requirements]
                })
            
            validation_results["warnings"].extend(result.warnings)
        
        return validation_results