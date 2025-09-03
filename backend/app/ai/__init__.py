"""
OneVice AI System

Multi-agent AI orchestration system for entertainment industry intelligence.
Provides specialized agents for sales, talent acquisition, and leadership analytics.
"""

from .config import AIConfig
from .workflows.orchestrator import AgentOrchestrator
from .agents.base_agent import BaseAgent
from .llm.router import LLMRouter

__version__ = "1.0.0"
__all__ = [
    "AIConfig",
    "AgentOrchestrator", 
    "BaseAgent",
    "LLMRouter"
]