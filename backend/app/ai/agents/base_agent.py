"""
Base Agent

LangGraph-based base agent class providing conversation state management,
memory persistence, and common agent functionality.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime, timezone
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

import redis.asyncio as redis
from redis.asyncio import Redis

from ..config import AIConfig, AgentType
from ..llm.router import LLMRouter
from ..llm.prompt_templates import PromptTemplateManager, PromptType
from ..models import ModelConfigurationManager, ToolCompatibilityChecker
from ...core.exceptions import AIProcessingError
from ...core.redis import get_redis

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """Agent conversation state"""
    messages: Annotated[List[Dict[str, str]], add_messages]
    user_context: Dict[str, Any]
    conversation_id: str
    agent_type: str
    memory: Dict[str, Any]
    task_context: Optional[Dict[str, Any]]
    last_updated: str

class BaseAgent(ABC):
    """
    Base agent class using LangGraph for stateful conversations.
    
    Provides:
    - Conversation state management
    - Memory persistence with Redis
    - LLM routing and provider management  
    - Common agent utilities
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        config: AIConfig,
        llm_router: LLMRouter,
        redis_client: Optional[Redis] = None,
        model_config_manager: Optional[ModelConfigurationManager] = None
    ):
        self.agent_type = agent_type
        self.config = config
        self.llm_router = llm_router
        self.prompt_manager = PromptTemplateManager()
        
        # Redis for memory persistence - will be initialized in setup()
        self.redis_client = redis_client
        
        # Agent configuration
        self.agent_config = config.get_agent_config(agent_type)
        
        # Model configuration management
        self.model_config_manager = model_config_manager or ModelConfigurationManager(config)
        self.compatibility_checker = ToolCompatibilityChecker(config)
        
        # Initialize LangGraph workflow
        self.graph = self._create_graph()
        self.app = self.graph.compile(checkpointer=MemorySaver())
        
        logger.info(f"Initialized {agent_type.value} agent")

    async def setup(self):
        """Initialize async resources including Redis connection"""
        if not self.redis_client:
            self.redis_client = await get_redis()
            logger.info(f"Redis client initialized for {self.agent_type.value} agent")

    def _create_graph(self) -> StateGraph:
        """Create LangGraph state graph for agent workflow"""
        
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_conversation)
        workflow.add_node("process_query", self._process_query)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("update_memory", self._update_memory)
        
        # Add edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "process_query")
        workflow.add_edge("process_query", "generate_response")
        workflow.add_edge("generate_response", "update_memory")
        workflow.add_edge("update_memory", END)
        
        return workflow

    async def _initialize_conversation(self, state: AgentState) -> AgentState:
        """Initialize conversation state"""
        
        # Load existing memory if conversation exists
        if state.get("conversation_id"):
            memory = await self._load_memory(state["conversation_id"])
            state["memory"] = memory
        else:
            # Create new conversation
            state["conversation_id"] = str(uuid.uuid4())
            state["memory"] = {}
        
        # Set defaults
        state["agent_type"] = self.agent_type.value
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        return state

    async def _process_query(self, state: AgentState) -> AgentState:
        """Process user query and update context"""
        
        # Get the latest user message (handle both dict and LangGraph message objects)
        user_messages = []
        for msg in state["messages"]:
            if hasattr(msg, 'type') and msg.type == "human":  # LangGraph HumanMessage
                user_messages.append(msg)
            elif isinstance(msg, dict) and msg.get("role") == "user":  # Dict format
                user_messages.append(msg)
        
        if not user_messages:
            raise AIProcessingError("No user query found")
        
        # Get content from the message (handle both formats)
        latest_message = user_messages[-1]
        if hasattr(latest_message, 'content'):  # LangGraph message object
            latest_query = latest_message.content
        else:  # Dict format
            latest_query = latest_message["content"]
        
        # Extract entities and context
        query_context = await self._analyze_query(latest_query, state["user_context"])
        state["task_context"] = query_context
        
        # Update memory with new context
        state["memory"]["last_query"] = latest_query
        state["memory"]["query_count"] = state["memory"].get("query_count", 0) + 1
        
        return state

    @abstractmethod
    async def _analyze_query(
        self,
        query: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze query for agent-specific context (to be implemented by subclasses)"""
        pass

    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate response using LLM"""
        
        # Get prompt type for this agent
        prompt_type = self._get_prompt_type()
        
        # Get the latest message content (handle both dict and LangGraph formats)
        latest_message = state["messages"][-1]
        if hasattr(latest_message, 'content'):  # LangGraph message object
            user_query = latest_message.content
        else:  # Dict format
            user_query = latest_message["content"]
        
        # Format messages with system prompt
        formatted_messages = self.prompt_manager.format_conversation_prompt(
            agent_type=prompt_type,
            user_query=user_query,
            context=state["user_context"],
            task_type=state.get("task_context", {}).get("task_type"),
            task_params=state.get("task_context", {}).get("task_params")
        )
        
        # Add conversation history
        if len(state["messages"]) > 1:
            # Insert history before the latest user message
            history = state["messages"][:-1]
            formatted_messages = [formatted_messages[0]] + history + [formatted_messages[-1]]
        
        try:
            # Get configured model for this agent
            preferred_model = self._get_agent_model()
            
            # Generate response with model preference
            response = await self.llm_router.route_query(
                messages=formatted_messages,
                agent_type=self.agent_type.value,
                preferred_provider=self._get_preferred_provider()
            )
            
            # Add assistant response to messages
            state["messages"].append({
                "role": "assistant",
                "content": response["content"]
            })
            
            # Store response metadata
            state["memory"]["last_response_metadata"] = {
                "provider": response["provider"],
                "model": response["model"],
                "tokens": response.get("usage", {}).get("total_tokens", 0),
                "cost": response.get("cost_estimate", 0),
                "response_time": response.get("response_time", 0)
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Add error response
            state["messages"].append({
                "role": "assistant", 
                "content": f"I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists."
            })
        
        return state

    async def _update_memory(self, state: AgentState) -> AgentState:
        """Update persistent memory"""
        
        conversation_id = state["conversation_id"]
        memory_key = f"{self.config.redis_key_prefix}memory:{conversation_id}"
        
        # Update memory
        state["memory"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        state["memory"]["message_count"] = len(state["messages"])
        
        # Store in Redis with TTL
        try:
            await self.setup()  # Ensure Redis client is initialized
            await self.redis_client.setex(
                memory_key,
                self.agent_config["memory_ttl"],
                json.dumps(state["memory"])
            )
        except Exception as e:
            logger.error(f"Memory persistence failed: {e}")
        
        return state

    async def _load_memory(self, conversation_id: str) -> Dict[str, Any]:
        """Load memory from Redis"""
        
        memory_key = f"{self.config.redis_key_prefix}memory:{conversation_id}"
        
        try:
            await self.setup()  # Ensure Redis client is initialized
            memory_data = await self.redis_client.get(memory_key)
            if memory_data:
                return json.loads(memory_data)
        except Exception as e:
            logger.error(f"Memory loading failed: {e}")
        
        return {}

    @abstractmethod
    def _get_prompt_type(self) -> PromptType:
        """Get prompt type for this agent"""
        pass

    def _get_preferred_provider(self) -> Optional[str]:
        """Get preferred LLM provider for this agent"""
        return None  # Use router default
    
    def _get_agent_model(self) -> Optional[str]:
        """Get the configured model for this agent type"""
        return self.model_config_manager.get_model_for_agent(self.agent_type.value)
    
    def _get_fallback_models(self) -> List[str]:
        """Get fallback models for this agent type"""
        return self.model_config_manager.get_fallback_models(self.agent_type.value)
    
    def _validate_tool_compatibility(self) -> Dict[str, Any]:
        """Validate this agent's tool compatibility requirements"""
        current_model = self._get_agent_model()
        if not current_model:
            return {"compatible": False, "error": "No model assigned"}
        
        return self.compatibility_checker.check_agent_compatibility(
            self.agent_type.value, current_model
        ).to_dict()
    
    def switch_model(self, new_model_alias: str, validate: bool = True) -> bool:
        """Switch this agent's model"""
        return self.model_config_manager.switch_model(
            self.agent_type.value, new_model_alias, validate
        )

    async def chat(
        self,
        message: str,
        user_context: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main chat interface for the agent
        
        Args:
            message: User message
            user_context: User context information
            conversation_id: Optional conversation ID for continuity
            
        Returns:
            Response with content and metadata
        """
        
        # Create initial state
        initial_state = AgentState(
            messages=[{"role": "user", "content": message}],
            user_context=user_context,
            conversation_id=conversation_id or str(uuid.uuid4()),
            agent_type=self.agent_type.value,
            memory={},
            task_context=None,
            last_updated=datetime.now(timezone.utc).isoformat()
        )
        
        # Configure for conversation continuity
        config = {"thread_id": initial_state["conversation_id"]}
        
        try:
            # Run the workflow
            result = await self.app.ainvoke(initial_state, config)
            
            # Extract response (handle both dict and LangGraph message formats)
            assistant_messages = []
            for msg in result["messages"]:
                if hasattr(msg, 'type') and msg.type == "ai":  # LangGraph AIMessage
                    assistant_messages.append(msg)
                elif isinstance(msg, dict) and msg.get("role") == "assistant":  # Dict format
                    assistant_messages.append(msg)
            
            if not assistant_messages:
                raise AIProcessingError("No response generated")
            
            # Get content from the latest response
            latest_message = assistant_messages[-1]
            if hasattr(latest_message, 'content'):  # LangGraph message object
                latest_response = latest_message.content
            else:  # Dict format
                latest_response = latest_message["content"]
            
            return {
                "content": latest_response,
                "conversation_id": result["conversation_id"],
                "agent_type": self.agent_type.value,
                "metadata": result["memory"].get("last_response_metadata", {}),
                "timestamp": result["last_updated"]
            }
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            raise AIProcessingError(f"Chat processing failed: {e}")

    async def stream_chat(
        self,
        message: str,
        user_context: Dict[str, Any],
        conversation_id: Optional[str] = None
    ):
        """
        Streaming chat interface (simplified for this implementation)
        """
        
        # For now, delegate to regular chat
        # In a full implementation, this would use LangGraph streaming capabilities
        response = await self.chat(message, user_context, conversation_id)
        
        # Yield response in chunks to simulate streaming
        content = response["content"]
        chunk_size = 50
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield {
                "type": "content",
                "content": chunk,
                "conversation_id": response["conversation_id"]
            }
            await asyncio.sleep(0.1)  # Small delay for streaming effect
        
        # Final metadata chunk
        yield {
            "type": "metadata", 
            "metadata": response["metadata"],
            "conversation_id": response["conversation_id"]
        }

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get conversation history"""
        
        config = {"thread_id": conversation_id}
        
        try:
            # Get current state
            state = await self.app.aget_state(config)
            if state and state.values:
                messages = state.values.get("messages", [])
                return messages[-limit:] if limit else messages
        except Exception as e:
            logger.error(f"History retrieval failed: {e}")
        
        return []

    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history and memory"""
        
        try:
            await self.setup()  # Ensure Redis client is initialized
            # Clear Redis memory
            memory_key = f"{self.config.redis_key_prefix}memory:{conversation_id}"
            await self.redis_client.delete(memory_key)
            
            # Clear LangGraph state (if using persistent checkpointer)
            # For MemorySaver, this is automatically handled
            
            return True
            
        except Exception as e:
            logger.error(f"Conversation clearing failed: {e}")
            return False

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and health information"""
        
        # Get current model configuration
        current_model = self._get_agent_model()
        fallback_models = self._get_fallback_models()
        compatibility_status = self._validate_tool_compatibility()
        
        return {
            "agent_type": self.agent_type.value,
            "status": "healthy" if compatibility_status.get("compatible", False) else "degraded",
            "configuration": {
                "memory_ttl": self.agent_config["memory_ttl"],
                "max_history": self.agent_config["max_history"],
                "timeout": self.agent_config["timeout"]
            },
            "model_configuration": {
                "current_model": current_model,
                "fallback_models": fallback_models,
                "compatibility_status": compatibility_status
            },
            "llm_provider_stats": self.llm_router.get_provider_stats(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()