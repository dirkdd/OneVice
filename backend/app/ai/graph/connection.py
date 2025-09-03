"""
Neo4j Connection Manager

Handles Neo4j database connections, query execution, and connection pooling
with proper error handling and retry logic.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager
import json
from datetime import datetime

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, TransientError

from ..config import AIConfig
from ...core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    Async Neo4j client with connection pooling and error handling
    """
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.driver: Optional[AsyncDriver] = None
        self._connection_pool_size = 50
        self._connection_timeout = 15
        self._max_retry_attempts = 3
        
    async def connect(self) -> None:
        """Initialize Neo4j driver connection"""
        
        if self.driver:
            return
            
        try:
            # Configure driver with connection pooling
            self.driver = AsyncGraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_username, self.config.neo4j_password),
                max_connection_pool_size=self._connection_pool_size,
                connection_timeout=self._connection_timeout,
                database=self.config.neo4j_database
            )
            
            # Verify connectivity
            await self._verify_connectivity()
            logger.info("Neo4j connection established successfully")
            
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Neo4j: {e}")

    async def _verify_connectivity(self) -> None:
        """Verify database connectivity"""
        
        async with self.driver.session() as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            if not record or record["test"] != 1:
                raise DatabaseConnectionError("Neo4j connectivity test failed")

    async def close(self) -> None:
        """Close Neo4j driver connection"""
        
        if self.driver:
            await self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")

    @asynccontextmanager
    async def session(self, database: Optional[str] = None):
        """Context manager for Neo4j sessions"""
        
        if not self.driver:
            await self.connect()
        
        session = self.driver.session(database=database or self.config.neo4j_database)
        try:
            yield session
        finally:
            await session.close()

    async def run_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
        retry_attempts: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query with retry logic
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Target database
            retry_attempts: Number of retry attempts
            
        Returns:
            List of result records as dictionaries
        """
        
        if not self.driver:
            await self.connect()
        
        retry_attempts = retry_attempts or self._max_retry_attempts
        
        for attempt in range(retry_attempts):
            try:
                async with self.session(database) as session:
                    result = await session.run(query, parameters or {})
                    
                    # Convert records to dictionaries
                    records = []
                    async for record in result:
                        record_dict = dict(record)
                        # Convert Neo4j types to JSON-serializable types
                        records.append(self._serialize_record(record_dict))
                    
                    # Get query summary
                    summary = await result.consume()
                    
                    logger.debug(f"Query executed successfully: {len(records)} records returned")
                    return records
                    
            except (ServiceUnavailable, TransientError) as e:
                logger.warning(f"Query attempt {attempt + 1} failed: {e}")
                if attempt == retry_attempts - 1:
                    raise DatabaseConnectionError(f"Query failed after {retry_attempts} attempts: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Query execution error: {e}")
                raise DatabaseConnectionError(f"Query execution failed: {e}")

    async def run_write_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute write query (CREATE, UPDATE, DELETE) with transaction handling
        
        Returns:
            Query summary with counters
        """
        
        if not self.driver:
            await self.connect()
        
        try:
            async with self.session(database) as session:
                async with session.begin_transaction() as tx:
                    result = await tx.run(query, parameters or {})
                    summary = await result.consume()
                    
                    # Extract summary counters
                    counters = {
                        "nodes_created": summary.counters.nodes_created,
                        "nodes_deleted": summary.counters.nodes_deleted,
                        "relationships_created": summary.counters.relationships_created,
                        "relationships_deleted": summary.counters.relationships_deleted,
                        "properties_set": summary.counters.properties_set,
                        "labels_added": summary.counters.labels_added,
                        "labels_removed": summary.counters.labels_removed,
                        "indexes_added": summary.counters.indexes_added,
                        "indexes_removed": summary.counters.indexes_removed,
                        "constraints_added": summary.counters.constraints_added,
                        "constraints_removed": summary.counters.constraints_removed,
                    }
                    
                    await tx.commit()
                    
                    logger.info(f"Write query executed: {counters}")
                    return {
                        "counters": counters,
                        "query_type": summary.query_type,
                        "database": summary.database,
                        "server_info": {
                            "address": summary.server_info.address,
                            "protocol_version": summary.server_info.protocol_version
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Write query execution error: {e}")
            raise DatabaseConnectionError(f"Write query execution failed: {e}")

    async def run_vector_query(
        self,
        index_name: str,
        vector: List[float],
        top_k: int = 10,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute vector similarity search query
        
        Args:
            index_name: Vector index name
            vector: Query vector
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar nodes with scores
        """
        
        query = f"""
        CALL db.index.vector.queryNodes('{index_name}', $top_k, $vector)
        YIELD node, score
        WHERE score >= $threshold
        RETURN node, score
        ORDER BY score DESC
        """
        
        parameters = {
            "vector": vector,
            "top_k": top_k,
            "threshold": similarity_threshold or 0.0
        }
        
        try:
            results = await self.run_query(query, parameters)
            
            # Format results
            formatted_results = []
            for record in results:
                formatted_results.append({
                    "node": record["node"],
                    "similarity_score": record["score"],
                    "node_labels": list(record["node"].labels) if hasattr(record["node"], 'labels') else [],
                    "node_properties": dict(record["node"]) if hasattr(record["node"], 'items') else record["node"]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector query failed: {e}")
            raise DatabaseConnectionError(f"Vector search failed: {e}")

    async def create_vector_index(
        self,
        index_name: str,
        label: str,
        property: str,
        dimensions: int,
        similarity_function: str = "cosine"
    ) -> bool:
        """
        Create vector index for similarity search
        
        Args:
            index_name: Name for the index
            label: Node label to index
            property: Property containing vectors
            dimensions: Vector dimensions
            similarity_function: Similarity function (cosine, euclidean)
            
        Returns:
            Success boolean
        """
        
        query = f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (n:{label}) ON (n.{property})
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimensions},
                `vector.similarity_function`: '{similarity_function}'
            }}
        }}
        """
        
        try:
            await self.run_write_query(query)
            logger.info(f"Vector index '{index_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Vector index creation failed: {e}")
            return False

    async def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        
        try:
            # Basic database info
            info_query = "CALL dbms.components() YIELD name, versions, edition"
            db_info = await self.run_query(info_query)
            
            # Node and relationship counts
            count_query = """
            CALL apoc.meta.stats() 
            YIELD nodeCount, relCount, labelCount, relTypeCount
            RETURN nodeCount, relCount, labelCount, relTypeCount
            """
            
            try:
                counts = await self.run_query(count_query)
            except:
                # Fallback if APOC is not available
                counts = [{"nodeCount": 0, "relCount": 0, "labelCount": 0, "relTypeCount": 0}]
            
            # Index information
            index_query = "SHOW INDEXES"
            try:
                indexes = await self.run_query(index_query)
            except:
                indexes = []
            
            return {
                "database_info": db_info,
                "statistics": counts[0] if counts else {},
                "indexes": indexes,
                "connection_status": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database info retrieval failed: {e}")
            return {
                "connection_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _serialize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Neo4j record to JSON-serializable format"""
        
        serialized = {}
        
        for key, value in record.items():
            try:
                # Handle different Neo4j data types
                if hasattr(value, '__dict__'):
                    # Node or Relationship object
                    if hasattr(value, 'labels'):
                        # Node
                        serialized[key] = {
                            "id": value.element_id,
                            "labels": list(value.labels),
                            "properties": dict(value)
                        }
                    elif hasattr(value, 'type'):
                        # Relationship
                        serialized[key] = {
                            "id": value.element_id,
                            "type": value.type,
                            "start_node": value.start_node.element_id,
                            "end_node": value.end_node.element_id,
                            "properties": dict(value)
                        }
                    else:
                        serialized[key] = dict(value)
                elif isinstance(value, (list, tuple)):
                    serialized[key] = [self._serialize_value(item) for item in value]
                else:
                    serialized[key] = self._serialize_value(value)
                    
            except Exception as e:
                logger.warning(f"Failed to serialize record field {key}: {e}")
                serialized[key] = str(value)
        
        return serialized

    def _serialize_value(self, value: Any) -> Any:
        """Serialize individual values"""
        
        if hasattr(value, '__dict__'):
            return dict(value)
        elif isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return str(value)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Neo4j connection"""
        
        try:
            if not self.driver:
                return {"status": "disconnected", "error": "No driver initialized"}
            
            # Simple connectivity test
            start_time = asyncio.get_event_loop().time()
            await self.run_query("RETURN 1 as health_check")
            response_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "database": self.config.neo4j_database,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }