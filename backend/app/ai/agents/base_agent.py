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
from langgraph.prebuilt import ToolNode, tools_condition

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
    """Agent conversation state with tool support"""
    messages: Annotated[List[Dict[str, str]], add_messages]
    user_context: Dict[str, Any]
    conversation_id: str
    agent_type: str
    memory: Dict[str, Any]
    task_context: Optional[Dict[str, Any]]
    last_updated: str
    # Tool execution state
    tool_results: Optional[Dict[str, Any]]
    tool_errors: Optional[List[str]]

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
        
        # Tool setup (to be initialized by subclasses)
        self._tools = []
        self._tool_node = None
        self._llm_with_tools = None
        
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
        """Create LangGraph state graph for agent workflow with tool support"""
        
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_conversation)
        workflow.add_node("process_query", self._process_query)
        workflow.add_node("llm_with_tools", self._llm_with_tools_node)
        
        # Add tool node if tools are available
        if self._tools:
            self._tool_node = ToolNode(self._tools)
            
            # Debug wrapper for tool node
            async def debug_tool_node(state: AgentState):
                logger.info("🔧 DEBUG: Entering ToolNode execution")
                logger.info(f"🔧 DEBUG: Tool node has {len(self._tools)} tools available")
                logger.info(f"🔧 DEBUG: Tool names: {[tool.name for tool in self._tools]}")
                
                # Get tool calls from the latest message
                latest_message = state["messages"][-1] if state["messages"] else None
                if hasattr(latest_message, 'tool_calls') and latest_message.tool_calls:
                    logger.info(f"🔧 DEBUG: Executing {len(latest_message.tool_calls)} tool calls")
                    for i, tool_call in enumerate(latest_message.tool_calls):
                        logger.info(f"🔧 DEBUG: Tool call {i+1}: {tool_call}")
                else:
                    logger.info("🔧 DEBUG: No tool calls found in latest message!")
                
                try:
                    # Execute the actual ToolNode
                    result = await self._tool_node.ainvoke(state)
                    logger.info("🔧 DEBUG: ToolNode execution completed successfully")
                    logger.info(f"🔧 DEBUG: ToolNode result keys: {result.keys() if isinstance(result, dict) else type(result)}")
                    
                    # CRITICAL FIX: Extract tool results from ToolNode messages
                    if isinstance(result, dict) and "messages" in result:
                        tool_results = {}
                        for message in result["messages"]:
                            # Look for ToolMessage objects that contain tool results
                            if hasattr(message, 'type') and message.type == 'tool':
                                tool_name = getattr(message, 'name', 'unknown_tool')
                                tool_content = getattr(message, 'content', {})
                                tool_results[tool_name] = tool_content
                                logger.info(f"🔧 DEBUG: Extracted tool result for {tool_name}: {str(tool_content)[:200]}...")
                        
                        # Add tool_results to the state  
                        if tool_results:
                            result["tool_results"] = tool_results
                            logger.info(f"🔧 DEBUG: Added tool_results to state: {list(tool_results.keys())}")
                        else:
                            logger.warning("🔧 DEBUG: No tool results found in ToolNode messages")
                    
                    return result
                except Exception as e:
                    logger.error(f"🔧 DEBUG: ToolNode execution failed: {e}")
                    logger.error(f"🔧 DEBUG: Exception type: {type(e)}")
                    raise
            
            workflow.add_node("tools", debug_tool_node)
        
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("update_memory", self._update_memory)
        
        # Add edges with conditional tool routing
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "process_query")
        workflow.add_edge("process_query", "llm_with_tools")
        
        # Conditional routing: if LLM calls tools, go to tools node, otherwise generate response
        if self._tools:
            # Debug wrapper for tools_condition
            def debug_tools_condition(state: AgentState):
                logger.info("🔀 DEBUG: Entering tools_condition check")
                
                # Get the latest message to check for tool calls
                latest_message = state["messages"][-1] if state["messages"] else None
                logger.info(f"🔀 DEBUG: Latest message type: {type(latest_message)}")
                
                if hasattr(latest_message, 'tool_calls'):
                    tool_calls = latest_message.tool_calls
                    logger.info(f"🔀 DEBUG: Found tool_calls attribute: {tool_calls}")
                    if tool_calls:
                        logger.info(f"🔀 DEBUG: Tool calls present, routing to 'tools' node")
                        return "tools"
                    else:
                        logger.info(f"🔀 DEBUG: No tool calls, routing to '__end__' (generate_response)")
                        return "__end__"
                else:
                    logger.info(f"🔀 DEBUG: No tool_calls attribute, routing to '__end__' (generate_response)")
                    return "__end__"
            
            workflow.add_conditional_edges(
                "llm_with_tools",
                debug_tools_condition,
                {
                    "tools": "tools",
                    "__end__": "generate_response"
                }
            )
            workflow.add_edge("tools", "generate_response")
        else:
            workflow.add_edge("llm_with_tools", "generate_response")
        
        workflow.add_edge("generate_response", "update_memory")
        workflow.add_edge("update_memory", END)
        
        return workflow

    async def _initialize_conversation(self, state: AgentState) -> AgentState:
        """Initialize conversation state with tool support"""
        
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
        
        # Initialize tool state
        state["tool_results"] = None
        state["tool_errors"] = None
        
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

    async def _llm_with_tools_node(self, state: AgentState) -> AgentState:
        """LLM node with tool binding for intelligent tool selection"""
        
        if not self._llm_with_tools:
            # If no tools bound, fallback to regular generation
            logger.warning(f"🚫 No tools bound for {self.agent_type.value}, falling back to regular generation")
            return await self._generate_response_fallback(state)
        
        # Get the latest message content
        latest_message = state["messages"][-1]
        if hasattr(latest_message, 'content'):
            user_query = latest_message.content
        else:
            user_query = latest_message["content"]
        
        logger.info(f"🔧 LLM with tools node - Processing query: {user_query[:100]}...")
        logger.info(f"📊 Available tools: {len(self._tools) if self._tools else 0}")
        
        try:
            # The LLM with tools will decide whether to call tools or respond directly
            logger.info(f"🤖 Invoking LLM with {len(state['messages'])} messages")
            result = await self._llm_with_tools.ainvoke(state["messages"])
            
            logger.info(f"📤 LLM Response type: {type(result)}")
            logger.info(f"📝 LLM Response content: {result.content if hasattr(result, 'content') else 'No content attr'}")
            
            # Check if the response contains tool calls
            if hasattr(result, 'tool_calls') and result.tool_calls:
                logger.info(f"🛠️ Tool calls found: {len(result.tool_calls)}")
                for i, tool_call in enumerate(result.tool_calls):
                    logger.info(f"   Tool {i+1}: {tool_call.get('name', 'unknown')} with args: {tool_call.get('args', {})}")
            else:
                logger.warning(f"⚠️ No tool calls in LLM response for {self.agent_type.value} - this might be why tools aren't executing")
                if hasattr(result, 'additional_kwargs'):
                    logger.info(f"📋 Additional kwargs: {result.additional_kwargs}")
            
            # Add the result to messages
            if hasattr(result, 'content'):
                # If result has tool calls, they will be handled by tools_condition
                state["messages"].append(result)
                logger.info("✅ Added LLM result to messages")
            else:
                # Fallback format
                state["messages"].append({
                    "role": "assistant",
                    "content": str(result)
                })
                logger.info("✅ Added LLM result to messages (fallback format)")
            
        except Exception as e:
            logger.error(f"LLM with tools failed: {e}")
            state["tool_errors"] = state.get("tool_errors", []) + [str(e)]
            # Add error response
            state["messages"].append({
                "role": "assistant",
                "content": "I encountered an error while processing your request. Please try again."
            })
        
        return state
    
    async def _generate_response_fallback(self, state: AgentState) -> AgentState:
        """Fallback response generation without tools (original method)"""
        
        # Get prompt type for this agent
        prompt_type = self._get_prompt_type()
        
        # Get the latest message content
        latest_message = state["messages"][-1]
        if hasattr(latest_message, 'content'):
            user_query = latest_message.content
        else:
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
            history = state["messages"][:-1]
            formatted_messages = [formatted_messages[0]] + history + [formatted_messages[-1]]
        
        try:
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
            state["messages"].append({
                "role": "assistant", 
                "content": "I apologize, but I encountered an error. Please try again."
            })
        
        return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response, potentially incorporating tool results"""
        
        logger.info("🎬 DEBUG: Entering _generate_response node")
        logger.info(f"🎬 DEBUG: State keys: {list(state.keys())}")
        logger.info(f"🎬 DEBUG: Messages count: {len(state.get('messages', []))}")
        
        # Check if we have tool results to incorporate
        tool_results = state.get("tool_results")
        tool_errors = state.get("tool_errors")
        
        if tool_results:
            # Log tool results for debugging
            logger.info(f"🎬 DEBUG: Found tool_results: {list(tool_results.keys())}")
            logger.info(f"🎬 DEBUG: Tool results preview: {str(tool_results)[:500]}...")
            
            # Update memory with tool usage
            state["memory"]["last_tool_usage"] = {
                "tools_used": list(tool_results.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": not tool_errors
            }
        else:
            logger.info("🎬 DEBUG: No tool_results found in state")
        
        if tool_errors:
            logger.warning(f"Tool errors encountered: {tool_errors}")
            state["memory"]["last_tool_errors"] = tool_errors
        
        # Check if we already have a proper assistant response
        latest_message = state["messages"][-1] if state["messages"] else None
        logger.info(f"🎬 DEBUG: Latest message type: {type(latest_message)}")
        logger.info(f"🎬 DEBUG: Latest message content preview: {str(latest_message)[:300]}...")
        
        # If the latest message is from the assistant and has content, we're done
        if (latest_message and 
            ((hasattr(latest_message, 'type') and latest_message.type == "ai") or
             (isinstance(latest_message, dict) and latest_message.get("role") == "assistant")) and
            self._get_message_content(latest_message)):
            logger.info("🎬 DEBUG: Found existing assistant response, using it")
            logger.info(f"🎬 DEBUG: Assistant response content: '{self._get_message_content(latest_message)}'")
            return state
        else:
            logger.info("🎬 DEBUG: No existing assistant response, need to generate one")
        
        # If we have tool results but no final response, generate one
        if tool_results:
            logger.info("🎬 DEBUG: Generating final response based on tool results")
            logger.info(f"🎬 DEBUG: Available tool results keys: {list(tool_results.keys())}")
            
            # Create a prompt to synthesize the tool results
            synthesis_prompt = self._create_synthesis_prompt(state, tool_results)
            
            try:
                logger.info("🎬 DEBUG: Calling base LLM for synthesis")
                logger.info(f"🎬 DEBUG: Synthesis prompt preview: {str(synthesis_prompt)[:500]}...")
                
                # Generate synthesis using LLM without tools
                base_llm = self.llm_router.get_langchain_model(
                    provider=self._get_preferred_provider(),
                    model=self._get_agent_model()
                )
                
                synthesis_result = await base_llm.ainvoke(synthesis_prompt)
                
                logger.info(f"🎬 DEBUG: Synthesis result type: {type(synthesis_result)}")
                logger.info(f"🎬 DEBUG: Synthesis result content: {synthesis_result.content[:300] if hasattr(synthesis_result, 'content') else str(synthesis_result)[:300]}...")
                
                # Add the synthesized response
                state["messages"].append(synthesis_result)
                
                logger.info("🎬 DEBUG: Successfully generated synthesis response and added to messages")
                
            except Exception as e:
                logger.error(f"Failed to generate synthesis response: {e}")
                # Fallback to basic summary
                summary = self._create_tool_summary(tool_results)
                state["messages"].append({
                    "role": "assistant",
                    "content": summary
                })
        
        elif not latest_message or not self._get_message_content(latest_message):
            # No response at all - this shouldn't happen but let's handle it
            logger.warning("No response generated, creating fallback")
            state["messages"].append({
                "role": "assistant",
                "content": "I apologize, but I wasn't able to generate a response to your query. Please try again."
            })
        
        return state
    
    def _get_message_content(self, message) -> str:
        """Extract content from a message (handles both dict and LangGraph formats)"""
        if hasattr(message, 'content'):
            return message.content
        elif isinstance(message, dict):
            return message.get("content", "")
        return ""
    
    def _create_synthesis_prompt(self, state: AgentState, tool_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create a prompt to synthesize tool results into a final response"""
        
        # Extract user query from the first message (handles both dict and LangChain message objects)
        if state["messages"]:
            first_message = state["messages"][0]
            if hasattr(first_message, 'content'):
                user_query = first_message.content
            else:
                user_query = first_message.get("content", "")
        else:
            user_query = ""
        
        # Build context from tool results
        tool_context = []
        for tool_name, result in tool_results.items():
            if result:
                tool_context.append(f"**{tool_name}**: {result}")
        
        synthesis_prompt = f"""Based on the user's question: "{user_query}"

I have gathered the following information:

{chr(10).join(tool_context)}

Please provide a comprehensive and helpful response to the user's question using this information. Be conversational and directly address their query."""

        return [{"role": "user", "content": synthesis_prompt}]
    
    def _create_tool_summary(self, tool_results: Dict[str, Any]) -> str:
        """Create a basic summary of tool results as fallback"""
        
        if not tool_results:
            return "I wasn't able to find any relevant information for your query."
        
        summary_parts = []
        for tool_name, result in tool_results.items():
            if result:
                summary_parts.append(f"From {tool_name}: {str(result)[:200]}...")
        
        if summary_parts:
            return "Here's what I found:\n\n" + "\n\n".join(summary_parts)
        else:
            return "I searched for information but didn't find any relevant results."

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
    
    def bind_tools(self, tools: List[Any]) -> None:
        """
        Bind tools to this agent for LLM-driven tool selection.
        
        This method enables the agent to intelligently select and call tools
        based on user queries, replacing manual regex-based routing.
        
        Args:
            tools: List of @tool decorated functions
        """
        if not tools:
            logger.warning(f"No tools provided to bind for {self.agent_type.value}")
            return
        
        self._tools = tools
        logger.info(f"Bound {len(tools)} tools to {self.agent_type.value} agent")
        
        # Get base LLM from router
        try:
            # Get the LangChain-compatible model for tool binding
            base_llm = self.llm_router.get_langchain_model(
                provider=self._get_preferred_provider(),
                model=self._get_agent_model()
            )
            
            # Bind tools to the model
            self._llm_with_tools = base_llm.bind_tools(tools)
            logger.info(f"Successfully bound tools to LLM for {self.agent_type.value}")
            
            # Create tool node for execution
            self._tool_node = ToolNode(tools)
            
            # Rebuild graph with tools
            self.graph = self._create_graph()
            self.app = self.graph.compile(checkpointer=MemorySaver())
            
        except Exception as e:
            logger.error(f"Failed to bind tools to {self.agent_type.value}: {e}")
            raise AIProcessingError(f"Tool binding failed: {e}")
    
    def get_bound_tools(self) -> List[str]:
        """Get list of bound tool names"""
        if not self._tools:
            return []
        return [getattr(tool, 'name', str(tool)) for tool in self._tools]
    
    def has_tools(self) -> bool:
        """Check if agent has tools bound"""
        return bool(self._tools)
    
    def get_tool_count(self) -> int:
        """Get number of bound tools"""
        return len(self._tools) if self._tools else 0

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
            "tool_configuration": {
                "has_tools": self.has_tools(),
                "tool_count": self.get_tool_count(),
                "bound_tools": self.get_bound_tools(),
                "tool_node_ready": self._tool_node is not None,
                "llm_with_tools_ready": self._llm_with_tools is not None
            },
            "llm_provider_stats": self.llm_router.get_provider_stats(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()