"""
Vector Search Service

Handles embeddings generation, vector storage, and semantic search
operations for the entertainment industry knowledge graph.
"""

import asyncio
import logging
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

import redis.asyncio as redis
from redis.asyncio import Redis
import numpy as np

from ..config import AIConfig
from ..llm.router import LLMRouter
from ..graph.connection import Neo4jClient
from ..graph.queries import EntertainmentQueries
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

class VectorType(str, Enum):
    """Types of vectors we generate"""
    PERSON_BIO = "person_bio"
    PROJECT_DESCRIPTION = "project_description" 
    COMPANY_DESCRIPTION = "company_description"
    QUERY = "query"

class VectorSearchService:
    """
    Vector search service with embeddings generation and caching
    """
    
    def __init__(
        self,
        config: AIConfig,
        llm_router: LLMRouter,
        neo4j_client: Neo4jClient,
        redis_client: Optional[Redis] = None
    ):
        self.config = config
        self.llm_router = llm_router
        self.neo4j = neo4j_client
        self.queries = EntertainmentQueries(neo4j_client)
        
        # Redis for vector caching
        self.redis_client = redis_client or self._create_redis_client()
        
        # Vector configuration
        self.embedding_dimension = config.embedding_dimension
        self.cache_ttl = 86400  # 24 hours
        self.batch_size = 100
        
        # Performance tracking
        self.embedding_stats = {
            "total_generated": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_generation_time": 0
        }

    def _create_redis_client(self) -> Redis:
        """Create Redis client for vector caching"""
        return redis.from_url(
            self.config.redis_url,
            encoding="utf-8",
            decode_responses=False  # Keep binary data for vectors
        )

    async def generate_embedding(
        self,
        text: str,
        vector_type: VectorType = VectorType.QUERY,
        use_cache: bool = True
    ) -> List[float]:
        """
        Generate embedding for text with caching
        
        Args:
            text: Text to embed
            vector_type: Type of vector for cache organization
            use_cache: Whether to use/store cache
            
        Returns:
            Embedding vector
        """
        
        if not text or not text.strip():
            raise AIProcessingError("Empty text provided for embedding")
        
        # Create cache key
        cache_key = None
        if use_cache:
            text_hash = hashlib.md5(text.encode()).hexdigest()
            cache_key = f"{self.config.redis_key_prefix}vector:{vector_type.value}:{text_hash}"
            
            # Check cache first
            try:
                cached_vector = await self.redis_client.get(cache_key)
                if cached_vector:
                    self.embedding_stats["cache_hits"] += 1
                    vector_data = json.loads(cached_vector)
                    return vector_data["embedding"]
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
        
        # Generate embedding
        start_time = asyncio.get_event_loop().time()
        
        try:
            embedding = await self.llm_router.get_embedding(text)
            
            # Validate embedding
            if not embedding or len(embedding) != self.embedding_dimension:
                raise AIProcessingError(f"Invalid embedding dimension: {len(embedding) if embedding else 0}")
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            # Update stats
            self.embedding_stats["total_generated"] += 1
            self.embedding_stats["cache_misses"] += 1
            
            # Update rolling average
            current_avg = self.embedding_stats["avg_generation_time"]
            total_generated = self.embedding_stats["total_generated"]
            self.embedding_stats["avg_generation_time"] = (
                (current_avg * (total_generated - 1) + generation_time) / total_generated
            )
            
            # Cache the result
            if use_cache and cache_key:
                try:
                    vector_data = {
                        "embedding": embedding,
                        "text_length": len(text),
                        "generated_at": datetime.utcnow().isoformat(),
                        "vector_type": vector_type.value
                    }
                    await self.redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(vector_data)
                    )
                except Exception as e:
                    logger.warning(f"Cache storage failed: {e}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise AIProcessingError(f"Embedding generation failed: {e}")

    async def batch_generate_embeddings(
        self,
        texts: List[str],
        vector_type: VectorType,
        use_cache: bool = True
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts efficiently"""
        
        if not texts:
            return []
        
        # Split into batches to avoid overwhelming the API
        results = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.generate_embedding(text, vector_type, use_cache)
                for text in batch
            ]
            
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Handle exceptions in batch
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Batch embedding failed for text {i+j}: {result}")
                        results.append(None)
                    else:
                        results.append(result)
                
                # Rate limiting - small delay between batches
                if i + self.batch_size < len(texts):
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                # Fill with None for this batch
                results.extend([None] * len(batch))
        
        return results

    async def semantic_search(
        self,
        query: str,
        search_types: List[VectorType] = None,
        similarity_threshold: float = 0.7,
        limit: int = 10,
        hybrid_search: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform semantic search across knowledge graph
        
        Args:
            query: Search query
            search_types: Types of entities to search
            similarity_threshold: Minimum similarity score
            limit: Maximum results per type
            hybrid_search: Whether to combine with graph traversal
            
        Returns:
            Dictionary of results by entity type
        """
        
        # Generate query embedding
        query_embedding = await self.generate_embedding(query, VectorType.QUERY)
        
        # Default search types
        if search_types is None:
            search_types = [
                VectorType.PERSON_BIO,
                VectorType.PROJECT_DESCRIPTION,
                VectorType.COMPANY_DESCRIPTION
            ]
        
        results = {}
        
        # Execute vector searches in parallel
        search_tasks = []
        
        for vector_type in search_types:
            index_name = self._get_vector_index_name(vector_type)
            if index_name:
                task = self._vector_search_by_type(
                    vector_type,
                    index_name,
                    query_embedding,
                    similarity_threshold,
                    limit
                )
                search_tasks.append((vector_type, task))
        
        # Execute all searches
        search_results = await asyncio.gather(
            *[task for _, task in search_tasks],
            return_exceptions=True
        )
        
        # Process results
        for i, (vector_type, result) in enumerate(zip([t[0] for t in search_tasks], search_results)):
            if isinstance(result, Exception):
                logger.error(f"Vector search failed for {vector_type}: {result}")
                results[vector_type.value] = []
            else:
                results[vector_type.value] = result
        
        # Apply hybrid search if requested
        if hybrid_search:
            results = await self._enhance_with_graph_search(query, results)
        
        return results

    async def _vector_search_by_type(
        self,
        vector_type: VectorType,
        index_name: str,
        query_vector: List[float],
        similarity_threshold: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Execute vector search for specific type"""
        
        try:
            vector_results = await self.neo4j.run_vector_query(
                index_name=index_name,
                vector=query_vector,
                top_k=limit,
                similarity_threshold=similarity_threshold
            )
            
            # Enhance results with additional context
            enhanced_results = []
            for result in vector_results:
                enhanced_result = {
                    "entity": result["node_properties"],
                    "similarity_score": result["similarity_score"],
                    "vector_type": vector_type.value,
                    "match_type": "semantic"
                }
                
                # Add type-specific context
                if vector_type == VectorType.PERSON_BIO:
                    enhanced_result["entity_type"] = "person"
                elif vector_type == VectorType.PROJECT_DESCRIPTION:
                    enhanced_result["entity_type"] = "project"
                elif vector_type == VectorType.COMPANY_DESCRIPTION:
                    enhanced_result["entity_type"] = "company"
                
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Vector search failed for {vector_type}: {e}")
            return []

    def _get_vector_index_name(self, vector_type: VectorType) -> Optional[str]:
        """Get Neo4j vector index name for vector type"""
        
        index_mapping = {
            VectorType.PERSON_BIO: "person_bio_vector",
            VectorType.PROJECT_DESCRIPTION: "project_description_vector",
            VectorType.COMPANY_DESCRIPTION: "company_description_vector"
        }
        
        return index_mapping.get(vector_type)

    async def _enhance_with_graph_search(
        self,
        query: str,
        vector_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Enhance vector search results with graph traversal"""
        
        # Extract keywords from query for graph search
        query_keywords = await self._extract_query_keywords(query)
        
        # Perform graph-based search
        try:
            graph_results = await self.queries.search_entities(
                search_term=query,
                limit=20
            )
            
            # Add graph results to appropriate categories
            for graph_result in graph_results:
                entity_type = graph_result["entity_type"].lower()
                
                # Map to vector types
                if entity_type == "person":
                    key = VectorType.PERSON_BIO.value
                elif entity_type == "project":
                    key = VectorType.PROJECT_DESCRIPTION.value
                elif entity_type == "company":
                    key = VectorType.COMPANY_DESCRIPTION.value
                else:
                    continue
                
                # Add as graph match
                enhanced_result = {
                    "entity": dict(graph_result["n"]),
                    "similarity_score": 0.8,  # Default graph match score
                    "vector_type": key,
                    "match_type": "graph",
                    "entity_type": entity_type
                }
                
                # Avoid duplicates
                existing_ids = {r["entity"].get("id") for r in vector_results.get(key, [])}
                if enhanced_result["entity"].get("id") not in existing_ids:
                    if key not in vector_results:
                        vector_results[key] = []
                    vector_results[key].append(enhanced_result)
        
        except Exception as e:
            logger.warning(f"Graph search enhancement failed: {e}")
        
        return vector_results

    async def _extract_query_keywords(self, query: str) -> List[str]:
        """Extract keywords from query for graph search"""
        
        # Simple keyword extraction (could be enhanced with NLP)
        keywords = []
        
        # Remove common stop words and extract meaningful terms
        stop_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        
        words = query.lower().split()
        for word in words:
            word = word.strip(".,!?;:")
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)
        
        return keywords[:10]  # Limit keywords

    async def index_entities(
        self,
        entity_type: str,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """Index entities with vector embeddings"""
        
        indexing_results = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Get entities to index
            if entity_type == "person":
                entities = await self._get_people_for_indexing()
                vector_type = VectorType.PERSON_BIO
                text_field = "bio"
                embedding_field = "bio_embedding"
            elif entity_type == "project":
                entities = await self._get_projects_for_indexing()
                vector_type = VectorType.PROJECT_DESCRIPTION
                text_field = "description"
                embedding_field = "description_embedding"
            elif entity_type == "company":
                entities = await self._get_companies_for_indexing()
                vector_type = VectorType.COMPANY_DESCRIPTION
                text_field = "description"
                embedding_field = "description_embedding"
            else:
                raise AIProcessingError(f"Unsupported entity type: {entity_type}")
            
            # Process in batches
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                
                # Extract texts for embedding
                texts = [entity.get(text_field, "") for entity in batch]
                
                # Generate embeddings
                embeddings = await self.batch_generate_embeddings(
                    texts, 
                    vector_type,
                    use_cache=True
                )
                
                # Update entities with embeddings
                for entity, embedding in zip(batch, embeddings):
                    indexing_results["total_processed"] += 1
                    
                    if embedding:
                        try:
                            await self._update_entity_embedding(
                                entity_type,
                                entity["id"],
                                embedding_field,
                                embedding
                            )
                            indexing_results["successful"] += 1
                        except Exception as e:
                            indexing_results["failed"] += 1
                            indexing_results["errors"].append(f"Entity {entity['id']}: {e}")
                    else:
                        indexing_results["failed"] += 1
                        indexing_results["errors"].append(f"Entity {entity['id']}: embedding generation failed")
            
            logger.info(f"Indexing completed for {entity_type}: {indexing_results}")
            return indexing_results
            
        except Exception as e:
            logger.error(f"Entity indexing failed for {entity_type}: {e}")
            indexing_results["errors"].append(str(e))
            return indexing_results

    async def _get_people_for_indexing(self) -> List[Dict[str, Any]]:
        """Get people that need bio embedding indexing"""
        
        query = """
        MATCH (p:Person)
        WHERE p.bio IS NOT NULL 
          AND (p.bio_embedding IS NULL OR p.bio_updated > p.embedding_updated)
        RETURN p.id as id, p.bio as bio
        LIMIT 1000
        """
        
        results = await self.neo4j.run_query(query)
        return [{"id": r["id"], "bio": r["bio"]} for r in results]

    async def _get_projects_for_indexing(self) -> List[Dict[str, Any]]:
        """Get projects that need description embedding indexing"""
        
        query = """
        MATCH (p:Project)
        WHERE p.description IS NOT NULL
          AND (p.description_embedding IS NULL OR p.description_updated > p.embedding_updated)
        RETURN p.id as id, p.description as description
        LIMIT 1000
        """
        
        results = await self.neo4j.run_query(query)
        return [{"id": r["id"], "description": r["description"]} for r in results]

    async def _get_companies_for_indexing(self) -> List[Dict[str, Any]]:
        """Get companies that need description embedding indexing"""
        
        query = """
        MATCH (c:Company)
        WHERE c.description IS NOT NULL
          AND (c.description_embedding IS NULL OR c.description_updated > c.embedding_updated)
        RETURN c.id as id, c.description as description
        LIMIT 1000
        """
        
        results = await self.neo4j.run_query(query)
        return [{"id": r["id"], "description": r["description"]} for r in results]

    async def _update_entity_embedding(
        self,
        entity_type: str,
        entity_id: str,
        embedding_field: str,
        embedding: List[float]
    ) -> None:
        """Update entity with generated embedding"""
        
        label_map = {
            "person": "Person",
            "project": "Project",
            "company": "Company"
        }
        
        label = label_map.get(entity_type)
        if not label:
            raise AIProcessingError(f"Unknown entity type: {entity_type}")
        
        query = f"""
        MATCH (n:{label} {{id: $entity_id}})
        SET n.{embedding_field} = $embedding,
            n.embedding_updated = datetime()
        """
        
        await self.neo4j.run_write_query(query, {
            "entity_id": entity_id,
            "embedding": embedding
        })

    async def get_similar_entities(
        self,
        entity_id: str,
        entity_type: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find entities similar to given entity"""
        
        # Get entity's embedding
        embedding_field_map = {
            "person": "bio_embedding",
            "project": "description_embedding",
            "company": "description_embedding"
        }
        
        label_map = {
            "person": "Person",
            "project": "Project", 
            "company": "Company"
        }
        
        embedding_field = embedding_field_map.get(entity_type)
        label = label_map.get(entity_type)
        
        if not embedding_field or not label:
            raise AIProcessingError(f"Unsupported entity type: {entity_type}")
        
        # Get source entity's embedding
        query = f"""
        MATCH (n:{label} {{id: $entity_id}})
        RETURN n.{embedding_field} as embedding
        """
        
        result = await self.neo4j.run_query(query, {"entity_id": entity_id})
        
        if not result or not result[0]["embedding"]:
            raise AIProcessingError(f"No embedding found for entity {entity_id}")
        
        source_embedding = result[0]["embedding"]
        
        # Find similar entities using vector search
        index_name = self._get_vector_index_name(
            getattr(VectorType, f"{entity_type.upper()}_BIO" if entity_type == "person" else f"{entity_type.upper()}_DESCRIPTION")
        )
        
        if not index_name:
            raise AIProcessingError(f"No vector index for {entity_type}")
        
        similar_entities = await self.neo4j.run_vector_query(
            index_name=index_name,
            vector=source_embedding,
            top_k=limit + 1,  # +1 to exclude self
            similarity_threshold=0.5
        )
        
        # Filter out the source entity
        filtered_results = [
            entity for entity in similar_entities
            if entity["node_properties"].get("id") != entity_id
        ]
        
        return filtered_results[:limit]

    async def get_service_stats(self) -> Dict[str, Any]:
        """Get vector service statistics"""
        
        return {
            "embedding_stats": self.embedding_stats,
            "cache_hit_rate": (
                self.embedding_stats["cache_hits"] /
                max(1, self.embedding_stats["cache_hits"] + self.embedding_stats["cache_misses"])
            ),
            "configuration": {
                "embedding_dimension": self.embedding_dimension,
                "cache_ttl": self.cache_ttl,
                "batch_size": self.batch_size
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()