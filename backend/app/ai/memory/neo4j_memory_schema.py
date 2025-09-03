"""
Neo4j Memory Schema

Defines the graph database schema and operations for the OneVice memory system.
Handles semantic, episodic, and procedural memories with vector embeddings.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import uuid

from ..graph.connection import Neo4jClient
from ..services.vector_service import VectorSearchService
from .memory_types import (
    MemoryType, MemoryImportance, UserMemory, SemanticFact, 
    EpisodicMemory, ProceduralMemory, ConversationMemory,
    MemoryQuery, MemorySearchResult, MemoryStats
)
from ...core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class MemorySchema:
    """
    Neo4j schema management for memory system
    
    Graph Structure:
    - (User)-[:HAS_PROFILE]->(UserProfile)
    - (User)-[:REMEMBERS]->(Memory {embedding, type, importance})
    - (User)-[:PARTICIPATED_IN]->(Conversation)
    - (Conversation)-[:CONTAINS]->(Message)
    - (Message)-[:GENERATED_BY]->(Agent)
    - (Memory)-[:RELATES_TO]->(Memory)
    - (Memory)-[:LEARNED_FROM]->(Conversation)
    - (Memory)-[:ABOUT]->(Entity) # Entertainment industry entities
    """
    
    def __init__(self, neo4j_client: Neo4jClient, vector_service: VectorSearchService):
        self.neo4j = neo4j_client
        self.vector_service = vector_service
        
    async def initialize_schema(self) -> bool:
        """Initialize Neo4j schema with constraints and indexes"""
        
        try:
            async with self.neo4j.session() as session:
                # Create constraints for unique identifiers
                constraints = [
                    "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                    "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
                    "CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS FOR (c:Conversation) REQUIRE c.id IS UNIQUE",
                    "CREATE CONSTRAINT message_id_unique IF NOT EXISTS FOR (msg:Message) REQUIRE msg.id IS UNIQUE"
                ]
                
                for constraint in constraints:
                    await session.run(constraint)
                    
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX memory_type_idx IF NOT EXISTS FOR (m:Memory) ON (m.type)",
                    "CREATE INDEX memory_importance_idx IF NOT EXISTS FOR (m:Memory) ON (m.importance)",
                    "CREATE INDEX memory_created_idx IF NOT EXISTS FOR (m:Memory) ON (m.created_at)",
                    "CREATE INDEX conversation_user_idx IF NOT EXISTS FOR (c:Conversation) ON (c.user_id)",
                    "CREATE INDEX user_created_idx IF NOT EXISTS FOR (u:User) ON (u.created_at)"
                ]
                
                for index in indexes:
                    await session.run(index)
                
                # Create vector indexes for embeddings (1536 dimensions for OpenAI)
                vector_indexes = [
                    """
                    CREATE VECTOR INDEX memory_embedding_idx IF NOT EXISTS
                    FOR (m:Memory) ON (m.embedding)
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 1536,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                    """,
                    """
                    CREATE VECTOR INDEX conversation_embedding_idx IF NOT EXISTS  
                    FOR (c:Conversation) ON (c.summary_embedding)
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 1536,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                    """
                ]
                
                for vector_index in vector_indexes:
                    await session.run(vector_index)
                    
                logger.info("Neo4j memory schema initialized successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j memory schema: {e}")
            raise DatabaseConnectionError(f"Schema initialization failed: {e}")
    
    async def store_user_memory(
        self,
        user_id: str,
        memory: UserMemory,
        related_entities: Optional[List[str]] = None
    ) -> str:
        """Store a user memory in Neo4j with optional entity relationships"""
        
        try:
            async with self.neo4j.session() as session:
                # Ensure user exists
                await self._ensure_user_exists(session, user_id)
                
                # Store memory with embedding
                memory_data = {
                    "id": memory.id,
                    "type": memory.memory_type.value,
                    "content": memory.content,
                    "importance": memory.importance.value,
                    "created_at": memory.created_at.isoformat(),
                    "last_accessed": memory.last_accessed.isoformat(),
                    "access_count": memory.access_count,
                    "metadata": json.dumps(memory.metadata)
                }
                
                # Add embedding if available
                if memory.embedding:
                    memory_data["embedding"] = memory.embedding
                
                # Add type-specific fields
                if isinstance(memory, SemanticFact):
                    memory_data.update({
                        "fact_type": memory.fact_type,
                        "confidence": memory.confidence,
                        "source_conversation_id": memory.source_conversation_id
                    })
                elif isinstance(memory, EpisodicMemory):
                    memory_data.update({
                        "conversation_id": memory.conversation_id,
                        "agent_type": memory.agent_type,
                        "interaction_summary": memory.interaction_summary,
                        "outcome": memory.outcome,
                        "emotion": memory.emotion,
                        "topics": json.dumps(memory.topics)
                    })
                elif isinstance(memory, ProceduralMemory):
                    memory_data.update({
                        "pattern_type": memory.pattern_type,
                        "trigger_condition": memory.trigger_condition,
                        "action_taken": memory.action_taken,
                        "success_rate": memory.success_rate,
                        "usage_count": memory.usage_count
                    })
                
                # Create memory node and relationship
                query = """
                MATCH (u:User {id: $user_id})
                CREATE (m:Memory $memory_data)
                CREATE (u)-[:REMEMBERS {created_at: datetime()}]->(m)
                RETURN m.id as memory_id
                """
                
                result = await session.run(query, {
                    "user_id": user_id,
                    "memory_data": memory_data
                })
                
                record = await result.single()
                memory_id = record["memory_id"]
                
                # Create relationships to entities if provided
                if related_entities:
                    for entity_id in related_entities:
                        await session.run("""
                        MATCH (m:Memory {id: $memory_id})
                        MATCH (e) WHERE e.id = $entity_id
                        CREATE (m)-[:ABOUT]->(e)
                        """, {"memory_id": memory_id, "entity_id": entity_id})
                
                logger.debug(f"Stored memory {memory_id} for user {user_id}")
                return memory_id
                
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise DatabaseConnectionError(f"Memory storage failed: {e}")
    
    async def search_memories(
        self,
        query: MemoryQuery
    ) -> List[MemorySearchResult]:
        """Search user memories using hybrid vector + graph approach"""
        
        try:
            # Generate query embedding
            query_embedding = await self.vector_service.generate_embedding(query.query_text)
            
            async with self.neo4j.session() as session:
                # Build Cypher query with filters
                cypher_query = """
                MATCH (u:User {id: $user_id})-[:REMEMBERS]->(m:Memory)
                WHERE m.embedding IS NOT NULL
                """
                
                params = {
                    "user_id": query.user_id,
                    "query_embedding": query_embedding,
                    "similarity_threshold": query.similarity_threshold,
                    "limit": query.limit
                }
                
                # Add filters
                if query.memory_types:
                    cypher_query += " AND m.type IN $memory_types"
                    params["memory_types"] = [mt.value for mt in query.memory_types]
                
                if query.min_importance:
                    importance_values = {
                        MemoryImportance.LOW: 1,
                        MemoryImportance.MEDIUM: 2,
                        MemoryImportance.HIGH: 3,
                        MemoryImportance.CRITICAL: 4
                    }
                    min_importance_value = importance_values[query.min_importance]
                    cypher_query += " AND m.importance_value >= $min_importance_value"
                    params["min_importance_value"] = min_importance_value
                
                if query.max_age_days:
                    cutoff_date = (datetime.utcnow() - timedelta(days=query.max_age_days)).isoformat()
                    cypher_query += " AND m.created_at >= $cutoff_date"
                    params["cutoff_date"] = cutoff_date
                
                # Add vector similarity calculation and ordering
                cypher_query += """
                WITH m, vector.similarity.cosine(m.embedding, $query_embedding) AS score
                WHERE score >= $similarity_threshold
                OPTIONAL MATCH (m)-[:RELATES_TO]-(related:Memory)
                WITH m, score, collect(related.id) as related_ids
                RETURN m, score, related_ids
                ORDER BY score DESC
                LIMIT $limit
                """
                
                result = await session.run(cypher_query, params)
                records = [record async for record in result]
                
                # Convert to MemorySearchResult objects
                search_results = []
                for record in records:
                    memory_node = record["m"]
                    similarity_score = record["score"]
                    related_ids = record["related_ids"]
                    
                    # Reconstruct memory object
                    memory_data = dict(memory_node)
                    memory_data["metadata"] = json.loads(memory_data.get("metadata", "{}"))
                    
                    # Convert to appropriate memory type
                    memory_type = MemoryType(memory_data["type"])
                    if memory_type == MemoryType.SEMANTIC:
                        memory = SemanticFact(**memory_data)
                    elif memory_type == MemoryType.EPISODIC:
                        memory_data["topics"] = json.loads(memory_data.get("topics", "[]"))
                        memory = EpisodicMemory(**memory_data)
                    elif memory_type == MemoryType.PROCEDURAL:
                        memory = ProceduralMemory(**memory_data)
                    else:
                        memory = UserMemory(**memory_data)
                    
                    search_result = MemorySearchResult(
                        memory=memory,
                        similarity_score=similarity_score,
                        related_memories=related_ids
                    )
                    search_results.append(search_result)
                
                logger.debug(f"Found {len(search_results)} memories for query")
                return search_results
                
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise DatabaseConnectionError(f"Memory search failed: {e}")
    
    async def store_conversation_memory(
        self,
        conversation: ConversationMemory
    ) -> str:
        """Store conversation-level memory"""
        
        try:
            async with self.neo4j.session() as session:
                # Generate summary embedding if summary exists
                summary_embedding = None
                if conversation.summary:
                    summary_embedding = await self.vector_service.generate_embedding(
                        conversation.summary
                    )
                
                conversation_data = {
                    "id": conversation.conversation_id,
                    "user_id": conversation.user_id,
                    "agent_types": json.dumps(conversation.agent_types),
                    "start_time": conversation.start_time.isoformat(),
                    "end_time": conversation.end_time.isoformat() if conversation.end_time else None,
                    "message_count": conversation.message_count,
                    "topics": json.dumps(conversation.topics),
                    "summary": conversation.summary,
                    "outcome": conversation.outcome,
                    "satisfaction": conversation.satisfaction,
                    "extracted_facts": json.dumps(conversation.extracted_facts)
                }
                
                if summary_embedding:
                    conversation_data["summary_embedding"] = summary_embedding
                
                # Store conversation and link to user
                query = """
                MATCH (u:User {id: $user_id})
                CREATE (c:Conversation $conversation_data)
                CREATE (u)-[:PARTICIPATED_IN {created_at: datetime()}]->(c)
                
                // Link conversation to extracted memories
                WITH c
                UNWIND $extracted_fact_ids as fact_id
                MATCH (m:Memory {id: fact_id})
                CREATE (m)-[:LEARNED_FROM]->(c)
                
                RETURN c.id as conversation_id
                """
                
                result = await session.run(query, {
                    "user_id": conversation.user_id,
                    "conversation_data": conversation_data,
                    "extracted_fact_ids": conversation.extracted_facts
                })
                
                record = await result.single()
                return record["conversation_id"]
                
        except Exception as e:
            logger.error(f"Failed to store conversation memory: {e}")
            raise DatabaseConnectionError(f"Conversation storage failed: {e}")
    
    async def get_user_memory_stats(self, user_id: str) -> MemoryStats:
        """Get comprehensive memory statistics for a user"""
        
        try:
            async with self.neo4j.session() as session:
                query = """
                MATCH (u:User {id: $user_id})-[:REMEMBERS]->(m:Memory)
                RETURN 
                    count(m) as total_memories,
                    m.type as memory_type,
                    m.importance as importance,
                    m.created_at as created_at,
                    m.access_count as access_count
                ORDER BY m.created_at ASC
                """
                
                result = await session.run(query, {"user_id": user_id})
                records = [record async for record in result]
                
                if not records:
                    return MemoryStats(
                        user_id=user_id,
                        total_memories=0,
                        memory_breakdown={},
                        importance_breakdown={},
                        avg_access_frequency=0.0,
                        top_topics=[]
                    )
                
                # Calculate statistics
                total_memories = len(records)
                memory_breakdown = {}
                importance_breakdown = {}
                access_counts = []
                oldest_date = None
                newest_date = None
                
                for record in records:
                    # Memory type breakdown
                    mem_type = MemoryType(record["memory_type"])
                    memory_breakdown[mem_type] = memory_breakdown.get(mem_type, 0) + 1
                    
                    # Importance breakdown
                    importance = MemoryImportance(record["importance"])
                    importance_breakdown[importance] = importance_breakdown.get(importance, 0) + 1
                    
                    # Access frequency
                    access_counts.append(record["access_count"])
                    
                    # Date tracking
                    created_at = datetime.fromisoformat(record["created_at"].replace('Z', '+00:00'))
                    if oldest_date is None or created_at < oldest_date:
                        oldest_date = created_at
                    if newest_date is None or created_at > newest_date:
                        newest_date = created_at
                
                avg_access_frequency = sum(access_counts) / len(access_counts) if access_counts else 0
                
                return MemoryStats(
                    user_id=user_id,
                    total_memories=total_memories,
                    memory_breakdown=memory_breakdown,
                    importance_breakdown=importance_breakdown,
                    avg_access_frequency=avg_access_frequency,
                    oldest_memory_date=oldest_date,
                    most_recent_date=newest_date,
                    top_topics=[]  # TODO: Implement topic extraction
                )
                
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            raise DatabaseConnectionError(f"Memory stats retrieval failed: {e}")
    
    async def _ensure_user_exists(self, session, user_id: str) -> None:
        """Ensure user node exists in the graph"""
        
        await session.run("""
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.created_at = datetime(), u.updated_at = datetime()
        ON MATCH SET u.updated_at = datetime()
        """, {"user_id": user_id})
    
    async def cleanup_old_memories(
        self,
        user_id: str,
        max_age_days: int = 90,
        importance_threshold: MemoryImportance = MemoryImportance.LOW
    ) -> int:
        """Clean up old, low-importance memories"""
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=max_age_days)).isoformat()
            
            async with self.neo4j.session() as session:
                query = """
                MATCH (u:User {id: $user_id})-[r:REMEMBERS]->(m:Memory)
                WHERE m.created_at < $cutoff_date 
                AND m.importance = $importance_threshold
                AND m.access_count < 3
                DETACH DELETE m
                RETURN count(m) as deleted_count
                """
                
                result = await session.run(query, {
                    "user_id": user_id,
                    "cutoff_date": cutoff_date,
                    "importance_threshold": importance_threshold.value
                })
                
                record = await result.single()
                deleted_count = record["deleted_count"]
                
                logger.info(f"Cleaned up {deleted_count} old memories for user {user_id}")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            return 0