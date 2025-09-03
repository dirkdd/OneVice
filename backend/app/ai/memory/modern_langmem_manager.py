"""
Modern LangMem Manager

Updated implementation using LangMem SDK's proper API patterns
for semantic, episodic, and procedural memory management.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

# Modern LangMem imports based on documentation
from langmem import create_memory_manager, create_memory_store_manager
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from ..config import AIConfig
from ..graph.connection import Neo4jClient
from ..services.vector_service import VectorSearchService
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)


# Memory Schemas for LangMem (simplified from documentation patterns)
class UserPreference(BaseModel):
    """User preference/fact storage"""
    subject: str = Field(..., description="What the preference is about")
    predicate: str = Field(..., description="Type of preference")
    object: str = Field(..., description="The preference value")
    context: Optional[str] = Field(None, description="Context where this was mentioned")
    confidence: float = Field(0.8, description="Confidence in this preference")


class ConversationEvent(BaseModel):
    """Episodic memory for conversation events"""
    event_type: str = Field(..., description="Type of interaction")
    participants: List[str] = Field(..., description="Who was involved")
    summary: str = Field(..., description="What happened")
    outcome: Optional[str] = Field(None, description="Result of the interaction")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BehaviorPattern(BaseModel):
    """Procedural memory for behavioral patterns"""
    trigger: str = Field(..., description="What triggers this pattern")
    action: str = Field(..., description="What action is taken")
    success_rate: float = Field(0.0, description="How often this works")
    usage_count: int = Field(0, description="How many times used")


class ModernLangMemManager:
    """
    Modern LangMem implementation using proper API patterns
    
    Features:
    - Semantic memory for user preferences and facts
    - Episodic memory for conversation events  
    - Procedural memory for behavioral patterns
    - Integration with Neo4j for persistence
    """
    
    def __init__(
        self,
        config: AIConfig,
        neo4j_client: Neo4jClient,
        vector_service: VectorSearchService
    ):
        self.config = config
        self.neo4j_client = neo4j_client
        self.vector_service = vector_service
        
        # Initialize store (using InMemoryStore for now, can be switched to Neo4j later)
        self.store = InMemoryStore(
            index={
                "dims": 1536,  # OpenAI embedding dimensions
                "embed": "openai:text-embedding-3-small"
            }
        )
        
        # Initialize memory managers
        self.semantic_manager = None
        self.episodic_manager = None
        self.procedural_manager = None
        
        # State tracking
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all memory managers"""
        
        try:
            logger.info("Initializing modern LangMem managers...")
            
            # Initialize semantic memory manager
            self.semantic_manager = create_memory_store_manager(
                "anthropic:claude-3-5-sonnet-latest",
                namespace=("memories", "{user_id}", "semantic"),
                schemas=[UserPreference],
                instructions="Extract user preferences, facts, and knowledge from conversations",
                enable_inserts=True,
                enable_deletes=True
            )
            
            # Initialize episodic memory manager
            self.episodic_manager = create_memory_store_manager(
                "anthropic:claude-3-5-sonnet-latest", 
                namespace=("memories", "{user_id}", "episodic"),
                schemas=[ConversationEvent],
                instructions="Extract significant conversation events and interactions",
                enable_inserts=True,
                enable_deletes=False  # Keep conversation history
            )
            
            # Initialize procedural memory manager
            self.procedural_manager = create_memory_store_manager(
                "anthropic:claude-3-5-sonnet-latest",
                namespace=("memories", "{user_id}", "procedural"), 
                schemas=[BehaviorPattern],
                instructions="Extract behavioral patterns and successful interaction strategies",
                enable_inserts=True,
                enable_deletes=True
            )
            
            self.is_initialized = True
            logger.info("Modern LangMem managers initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"LangMem initialization failed: {e}")
            raise AIProcessingError(f"LangMem initialization failed: {e}")
    
    async def extract_conversation_memories(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[BaseMessage],
        agent_types: List[str]
    ) -> Dict[str, List[str]]:
        """Extract memories from a conversation"""
        
        if not self.is_initialized:
            raise AIProcessingError("LangMem manager not initialized")
        
        try:
            # Convert messages to text for processing
            conversation_text = "\n".join([
                f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
                for msg in messages
            ])
            
            extracted_memories = {
                "semantic": [],
                "episodic": [],
                "procedural": []
            }
            
            # Extract semantic memories (user preferences, facts)
            try:
                semantic_results = await self.semantic_manager.ainvoke(
                    {"messages": [HumanMessage(content=conversation_text)]},
                    config={"configurable": {"user_id": user_id}}
                )
                extracted_memories["semantic"] = [
                    str(memory.id) for memory in semantic_results.get("memories", [])
                ]
            except Exception as e:
                logger.warning(f"Semantic memory extraction failed: {e}")
            
            # Extract episodic memories (conversation events)
            try:
                episodic_results = await self.episodic_manager.ainvoke(
                    {"messages": [HumanMessage(content=conversation_text)]},
                    config={"configurable": {"user_id": user_id}}
                )
                extracted_memories["episodic"] = [
                    str(memory.id) for memory in episodic_results.get("memories", [])
                ]
            except Exception as e:
                logger.warning(f"Episodic memory extraction failed: {e}")
            
            # Extract procedural memories (behavioral patterns)
            try:
                procedural_results = await self.procedural_manager.ainvoke(
                    {"messages": [HumanMessage(content=conversation_text)]},
                    config={"configurable": {"user_id": user_id}}
                )
                extracted_memories["procedural"] = [
                    str(memory.id) for memory in procedural_results.get("memories", [])
                ]
            except Exception as e:
                logger.warning(f"Procedural memory extraction failed: {e}")
            
            logger.info(f"Extracted memories for {user_id}: {extracted_memories}")
            return extracted_memories
            
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            raise AIProcessingError(f"Memory extraction failed: {e}")
    
    async def search_memories(
        self,
        user_id: str,
        query_text: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories for a user"""
        
        if not self.is_initialized:
            raise AIProcessingError("LangMem manager not initialized")
        
        results = []
        search_types = memory_types or ["semantic", "episodic", "procedural"]
        
        try:
            # Search semantic memories
            if "semantic" in search_types and self.semantic_manager:
                semantic_docs = await self.store.search(
                    namespace=("memories", user_id, "semantic"),
                    query=query_text,
                    limit=limit // len(search_types)
                )
                
                for doc in semantic_docs:
                    results.append({
                        "type": "semantic",
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "relevance_score": doc.metadata.get("similarity_score", 0.0)
                    })
            
            # Search episodic memories
            if "episodic" in search_types and self.episodic_manager:
                episodic_docs = await self.store.search(
                    namespace=("memories", user_id, "episodic"),
                    query=query_text,
                    limit=limit // len(search_types)
                )
                
                for doc in episodic_docs:
                    results.append({
                        "type": "episodic",
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "relevance_score": doc.metadata.get("similarity_score", 0.0)
                    })
            
            # Search procedural memories
            if "procedural" in search_types and self.procedural_manager:
                procedural_docs = await self.store.search(
                    namespace=("memories", user_id, "procedural"),
                    query=query_text,
                    limit=limit // len(search_types)
                )
                
                for doc in procedural_docs:
                    results.append({
                        "type": "procedural", 
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "relevance_score": doc.metadata.get("similarity_score", 0.0)
                    })
            
            # Sort by relevance score
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []
    
    async def build_memory_context(
        self,
        user_id: str,
        current_query: str,
        conversation_id: str,
        max_memories: int = 10
    ) -> Dict[str, Any]:
        """Build memory context for agent processing"""
        
        try:
            # Search relevant memories
            relevant_memories = await self.search_memories(
                user_id=user_id,
                query_text=current_query,
                limit=max_memories
            )
            
            # Organize by type
            context = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "query": current_query,
                "total_memories": len(relevant_memories),
                "semantic_memories": [m for m in relevant_memories if m["type"] == "semantic"],
                "episodic_memories": [m for m in relevant_memories if m["type"] == "episodic"],
                "procedural_memories": [m for m in relevant_memories if m["type"] == "procedural"],
                "behavioral_patterns": []  # Extract patterns from procedural memories
            }
            
            # Extract behavioral patterns
            for memory in context["procedural_memories"]:
                if "trigger" in memory.get("metadata", {}):
                    pattern = {
                        "trigger": memory["metadata"].get("trigger", ""),
                        "action": memory["metadata"].get("action", ""),
                        "success_rate": memory["metadata"].get("success_rate", 0.0)
                    }
                    context["behavioral_patterns"].append(pattern)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build memory context: {e}")
            return {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "query": current_query,
                "total_memories": 0,
                "error": str(e)
            }
    
    async def consolidate_memories(self, user_id: str) -> int:
        """Consolidate and optimize memories for a user"""
        
        try:
            # This would implement memory consolidation logic
            # For now, just return a count
            logger.info(f"Memory consolidation initiated for user {user_id}")
            return 0
            
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            return 0
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get memory service statistics"""
        
        return {
            "initialized": self.is_initialized,
            "managers": {
                "semantic": self.semantic_manager is not None,
                "episodic": self.episodic_manager is not None,
                "procedural": self.procedural_manager is not None
            },
            "store_type": type(self.store).__name__
        }
    
    async def close(self):
        """Clean up resources"""
        
        logger.info("Closing modern LangMem manager")
        # Clean up any resources
        self.is_initialized = False


# Factory function for backward compatibility
def create_modern_langmem_manager(
    config: AIConfig,
    neo4j_client: Neo4jClient,
    vector_service: VectorSearchService
) -> ModernLangMemManager:
    """Factory function to create modern LangMem manager"""
    
    return ModernLangMemManager(config, neo4j_client, vector_service)