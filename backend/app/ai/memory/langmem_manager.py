"""
LangMem Manager

Integrates LangMem SDK with Neo4j backend for sophisticated memory management
in OneVice AI agents. Provides semantic, episodic, and procedural memory
capabilities with vector-based retrieval.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Note: LangMem imports updated for actual available interface  
from langmem import create_memory_manager, create_memory_store_manager
from langgraph.store.base import BaseStore
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.documents import Document

from ..config import AIConfig
from ..graph.connection import Neo4jClient
from ..services.vector_service import VectorSearchService
from .neo4j_memory_schema import MemorySchema
from .memory_types import (
    MemoryType, MemoryImportance, UserMemory, SemanticFact, 
    EpisodicMemory as EpisodicMemoryType, ProceduralMemory as ProceduralMemoryType,
    ConversationMemory, MemoryQuery, MemorySearchResult
)
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)


class Neo4jMemoryStore(BaseStore):
    """LangMem-compatible store implementation using Neo4j"""
    
    def __init__(self, memory_schema: MemorySchema):
        self.schema = memory_schema
        
    async def search(
        self,
        namespace: Tuple[str, ...],
        query: str,
        limit: int = 10,
        **kwargs
    ) -> List[Document]:
        """Search memories and return as LangChain documents"""
        
        user_id = namespace[0] if namespace else "default"
        
        memory_query = MemoryQuery(
            user_id=user_id,
            query_text=query,
            limit=limit,
            similarity_threshold=kwargs.get("similarity_threshold", 0.7)
        )
        
        results = await self.schema.search_memories(memory_query)
        
        # Convert to Documents
        documents = []
        for result in results:
            doc = Document(
                page_content=result.memory.content,
                metadata={
                    "memory_id": result.memory.id,
                    "memory_type": result.memory.memory_type.value,
                    "importance": result.memory.importance.value,
                    "similarity_score": result.similarity_score,
                    "created_at": result.memory.created_at.isoformat()
                }
            )
            documents.append(doc)
            
        return documents
    
    async def put(
        self,
        namespace: Tuple[str, ...],
        key: str,
        value: Dict[str, Any]
    ) -> None:
        """Store memory in Neo4j"""
        
        user_id = namespace[0] if namespace else "default"
        
        # Convert LangMem format to our memory types
        memory_type = MemoryType(value.get("memory_type", "semantic"))
        
        if memory_type == MemoryType.SEMANTIC:
            memory = SemanticFact(
                id=key,
                user_id=user_id,
                content=value["content"],
                fact_type=value.get("fact_type", "general"),
                confidence=value.get("confidence", 0.8),
                importance=MemoryImportance(value.get("importance", "medium")),
                embedding=value.get("embedding"),
                source_conversation_id=value.get("source_conversation_id")
            )
        elif memory_type == MemoryType.EPISODIC:
            memory = EpisodicMemoryType(
                id=key,
                user_id=user_id,
                content=value["content"],
                conversation_id=value["conversation_id"],
                agent_type=value.get("agent_type", "unknown"),
                interaction_summary=value["content"],
                importance=MemoryImportance(value.get("importance", "medium")),
                embedding=value.get("embedding"),
                topics=value.get("topics", [])
            )
        else:  # PROCEDURAL
            memory = ProceduralMemoryType(
                id=key,
                user_id=user_id,
                content=value["content"],
                pattern_type=value.get("pattern_type", "behavior"),
                trigger_condition=value.get("trigger_condition", ""),
                action_taken=value.get("action_taken", ""),
                importance=MemoryImportance(value.get("importance", "medium")),
                embedding=value.get("embedding")
            )
        
        await self.schema.store_user_memory(user_id, memory)
    
    async def delete(self, namespace: Tuple[str, ...], key: str) -> None:
        """Delete memory from Neo4j"""
        # Implementation would delete from Neo4j
        pass


class LangMemManager:
    """
    Advanced memory management using LangMem SDK with Neo4j backend
    
    Provides three types of memory:
    - Semantic: Facts, preferences, knowledge
    - Episodic: Specific interactions and events  
    - Procedural: Behavioral patterns and optimizations
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
        
        # Initialize memory schema
        self.schema = MemorySchema(neo4j_client, vector_service)
        
        # Initialize LangMem store
        self.store = Neo4jMemoryStore(self.schema)
        
        # Initialize LangMem memory types
        self.semantic_memory = SemanticMemory(store=self.store)
        self.episodic_memory = EpisodicMemory(store=self.store)
        self.procedural_memory = ProceduralMemory(store=self.store)
        
        # Memory processing settings
        self.max_context_memories = 10
        self.memory_consolidation_threshold = 50
        
    async def initialize(self) -> bool:
        """Initialize the memory system"""
        
        try:
            # Initialize Neo4j schema
            await self.schema.initialize_schema()
            
            logger.info("LangMem manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"LangMem manager initialization failed: {e}")
            raise AIProcessingError(f"Memory system initialization failed: {e}")
    
    async def extract_conversation_memories(
        self,
        conversation_id: str,
        user_id: str,
        messages: List[BaseMessage],
        agent_types: List[str]
    ) -> List[str]:
        """
        Extract memories from a conversation using LangMem
        
        Returns list of memory IDs that were created
        """
        
        try:
            namespace = (user_id,)
            extracted_memory_ids = []
            
            # Prepare conversation context
            conversation_text = self._format_conversation(messages)
            
            # Extract semantic facts using LangMem
            semantic_facts = await self.semantic_memory.extract(
                text=conversation_text,
                namespace=namespace
            )
            
            for fact in semantic_facts:
                memory_id = str(uuid.uuid4())
                
                # Generate embedding for the fact
                embedding = await self.vector_service.generate_embedding(fact["content"])
                
                # Store as semantic memory
                semantic_memory = SemanticFact(
                    id=memory_id,
                    user_id=user_id,
                    content=fact["content"],
                    fact_type=fact.get("type", "conversation_fact"),
                    confidence=fact.get("confidence", 0.8),
                    importance=self._determine_importance(fact),
                    embedding=embedding,
                    source_conversation_id=conversation_id
                )
                
                await self.schema.store_user_memory(user_id, semantic_memory)
                extracted_memory_ids.append(memory_id)
            
            # Create episodic memory for the conversation
            episodic_id = str(uuid.uuid4())
            conversation_summary = await self._summarize_conversation(messages)
            summary_embedding = await self.vector_service.generate_embedding(conversation_summary)
            
            episodic_memory = EpisodicMemoryType(
                id=episodic_id,
                user_id=user_id,
                content=conversation_summary,
                conversation_id=conversation_id,
                agent_type=", ".join(agent_types),
                interaction_summary=conversation_summary,
                importance=MemoryImportance.MEDIUM,
                embedding=summary_embedding,
                topics=await self._extract_topics(messages)
            )
            
            await self.schema.store_user_memory(user_id, episodic_memory)
            extracted_memory_ids.append(episodic_id)
            
            # Extract procedural patterns if conversation shows repeated behaviors
            procedural_patterns = await self._extract_procedural_patterns(
                user_id, messages, agent_types
            )
            
            for pattern in procedural_patterns:
                pattern_id = str(uuid.uuid4())
                pattern_embedding = await self.vector_service.generate_embedding(pattern["description"])
                
                procedural_memory = ProceduralMemoryType(
                    id=pattern_id,
                    user_id=user_id,
                    content=pattern["description"],
                    pattern_type=pattern["type"],
                    trigger_condition=pattern["trigger"],
                    action_taken=pattern["action"],
                    importance=MemoryImportance.HIGH,
                    embedding=pattern_embedding
                )
                
                await self.schema.store_user_memory(user_id, procedural_memory)
                extracted_memory_ids.append(pattern_id)
            
            logger.info(f"Extracted {len(extracted_memory_ids)} memories from conversation {conversation_id}")
            return extracted_memory_ids
            
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            raise AIProcessingError(f"Memory extraction failed: {e}")
    
    async def get_relevant_memories(
        self,
        user_id: str,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10
    ) -> List[MemorySearchResult]:
        """Get memories relevant to a query"""
        
        memory_query = MemoryQuery(
            user_id=user_id,
            query_text=query,
            memory_types=memory_types,
            limit=limit,
            similarity_threshold=0.7
        )
        
        return await self.schema.search_memories(memory_query)
    
    async def build_memory_context(
        self,
        user_id: str,
        current_query: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build memory context for agent prompts"""
        
        try:
            # Get relevant memories
            relevant_memories = await self.get_relevant_memories(
                user_id=user_id,
                query=current_query,
                limit=self.max_context_memories
            )
            
            # Organize by memory type
            context = {
                "user_id": user_id,
                "query": current_query,
                "semantic_facts": [],
                "past_interactions": [],
                "behavioral_patterns": [],
                "total_memories": len(relevant_memories)
            }
            
            for result in relevant_memories:
                memory = result.memory
                
                if memory.memory_type == MemoryType.SEMANTIC:
                    context["semantic_facts"].append({
                        "fact": memory.content,
                        "confidence": getattr(memory, 'confidence', 0.8),
                        "importance": memory.importance.value,
                        "relevance": result.similarity_score
                    })
                
                elif memory.memory_type == MemoryType.EPISODIC:
                    context["past_interactions"].append({
                        "summary": memory.content,
                        "agent_type": getattr(memory, 'agent_type', 'unknown'),
                        "outcome": getattr(memory, 'outcome', None),
                        "relevance": result.similarity_score
                    })
                
                elif memory.memory_type == MemoryType.PROCEDURAL:
                    context["behavioral_patterns"].append({
                        "pattern": memory.content,
                        "trigger": getattr(memory, 'trigger_condition', ''),
                        "action": getattr(memory, 'action_taken', ''),
                        "success_rate": getattr(memory, 'success_rate', 0.0),
                        "relevance": result.similarity_score
                    })
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build memory context: {e}")
            return {"user_id": user_id, "query": current_query, "error": str(e)}
    
    async def update_memory_access(self, memory_ids: List[str]) -> None:
        """Update access counts and last accessed timestamps for memories"""
        
        try:
            async with self.neo4j_client.session() as session:
                query = """
                UNWIND $memory_ids as memory_id
                MATCH (m:Memory {id: memory_id})
                SET m.access_count = m.access_count + 1,
                    m.last_accessed = datetime()
                """
                
                await session.run(query, {"memory_ids": memory_ids})
                
        except Exception as e:
            logger.error(f"Failed to update memory access: {e}")
    
    async def consolidate_memories(self, user_id: str) -> int:
        """Consolidate similar memories to reduce redundancy"""
        
        try:
            # Get all user memories
            all_memories = await self.get_relevant_memories(
                user_id=user_id,
                query="",  # Empty query to get all memories
                limit=1000
            )
            
            consolidated_count = 0
            
            # Group similar memories
            memory_groups = await self._group_similar_memories(all_memories)
            
            # Consolidate each group
            for group in memory_groups:
                if len(group) > 1:
                    consolidated_memory = await self._consolidate_memory_group(group)
                    if consolidated_memory:
                        consolidated_count += len(group) - 1
            
            logger.info(f"Consolidated {consolidated_count} memories for user {user_id}")
            return consolidated_count
            
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            return 0
    
    def _format_conversation(self, messages: List[BaseMessage]) -> str:
        """Format conversation messages for memory extraction"""
        
        formatted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted.append(f"Assistant: {msg.content}")
            else:
                formatted.append(f"{type(msg).__name__}: {msg.content}")
        
        return "\n".join(formatted)
    
    def _determine_importance(self, fact: Dict[str, Any]) -> MemoryImportance:
        """Determine the importance level of a memory fact"""
        
        # Simple heuristics - in production, this could use ML models
        content = fact.get("content", "").lower()
        
        critical_keywords = ["preference", "never", "always", "important", "critical"]
        high_keywords = ["like", "dislike", "want", "need", "goal"]
        
        if any(keyword in content for keyword in critical_keywords):
            return MemoryImportance.CRITICAL
        elif any(keyword in content for keyword in high_keywords):
            return MemoryImportance.HIGH
        elif fact.get("confidence", 0) > 0.9:
            return MemoryImportance.HIGH
        else:
            return MemoryImportance.MEDIUM
    
    async def _summarize_conversation(self, messages: List[BaseMessage]) -> str:
        """Generate a summary of the conversation"""
        
        # Simple summary - in production, would use LLM
        if len(messages) <= 2:
            return f"Brief interaction with {len(messages)} messages"
        
        user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
        ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
        
        return f"Conversation with {len(user_messages)} user messages and {len(ai_messages)} AI responses"
    
    async def _extract_topics(self, messages: List[BaseMessage]) -> List[str]:
        """Extract main topics from conversation"""
        
        # Simple keyword extraction - in production, would use NLP
        topics = []
        content = " ".join([msg.content for msg in messages]).lower()
        
        topic_keywords = {
            "entertainment": ["movie", "film", "show", "actor", "director"],
            "business": ["revenue", "profit", "client", "deal", "contract"],
            "talent": ["hire", "skill", "team", "crew", "casting"],
            "analytics": ["data", "report", "metrics", "analysis", "performance"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                topics.append(topic)
        
        return topics or ["general"]
    
    async def _extract_procedural_patterns(
        self,
        user_id: str,
        messages: List[BaseMessage],
        agent_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract behavioral patterns from conversation"""
        
        patterns = []
        
        # Look for repeated user behaviors
        user_messages = [msg.content.lower() for msg in messages if isinstance(msg, HumanMessage)]
        
        # Pattern: User asks for specific type of information
        if len(user_messages) > 1:
            for agent_type in agent_types:
                pattern = {
                    "type": "information_request",
                    "description": f"User frequently asks {agent_type} agent for specific information",
                    "trigger": f"User interaction with {agent_type} agent",
                    "action": "Provide detailed, specific information"
                }
                patterns.append(pattern)
        
        return patterns
    
    async def _group_similar_memories(
        self,
        memories: List[MemorySearchResult]
    ) -> List[List[MemorySearchResult]]:
        """Group similar memories for consolidation"""
        
        # Simple grouping by similarity threshold
        groups = []
        processed = set()
        
        for i, memory1 in enumerate(memories):
            if i in processed:
                continue
            
            group = [memory1]
            processed.add(i)
            
            for j, memory2 in enumerate(memories[i+1:], i+1):
                if j in processed:
                    continue
                
                # Check if memories are similar enough to group
                if await self._memories_similar(memory1.memory, memory2.memory):
                    group.append(memory2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    async def _memories_similar(self, memory1: UserMemory, memory2: UserMemory) -> bool:
        """Check if two memories are similar enough to consolidate"""
        
        # Check if same type and similar content
        if memory1.memory_type != memory2.memory_type:
            return False
        
        if memory1.embedding and memory2.embedding:
            # Calculate cosine similarity
            import numpy as np
            
            embedding1 = np.array(memory1.embedding)
            embedding2 = np.array(memory2.embedding)
            
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            
            return similarity > 0.85
        
        return False
    
    async def _consolidate_memory_group(
        self,
        group: List[MemorySearchResult]
    ) -> Optional[UserMemory]:
        """Consolidate a group of similar memories into one"""
        
        # This is a simplified consolidation - in production would use LLM
        # For now, keep the most important/recent memory and mark others as consolidated
        
        best_memory = max(group, key=lambda x: (
            x.memory.importance.value,
            x.memory.created_at,
            x.memory.access_count
        )).memory
        
        # TODO: Implement actual consolidation logic
        return best_memory