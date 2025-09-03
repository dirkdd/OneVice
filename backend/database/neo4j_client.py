"""
Neo4j Database Client for OneVice

Provides production-ready Neo4j connectivity with connection pooling,
transaction management, and comprehensive error handling.
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import (
    ServiceUnavailable,
    AuthError,
    ClientError,
    TransientError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Neo4j connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ConnectionConfig:
    """Neo4j connection configuration"""
    uri: str
    username: str
    password: str
    database: str = "neo4j"
    max_connection_lifetime: int = 3600  # 1 hour
    max_connection_pool_size: int = 100
    connection_timeout: int = 30  # 30 seconds
    resolver: Optional[callable] = None
    encrypted: bool = True


@dataclass 
class QueryResult:
    """Query execution result with metadata"""
    records: List[Dict[str, Any]]
    summary: Dict[str, Any]
    execution_time: float
    query: str
    parameters: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class Neo4jClient:
    """
    Production-ready Neo4j client for OneVice
    
    Features:
    - Async connection management with automatic retry
    - Transaction support with rollback capabilities
    - Connection health monitoring and automatic reconnection
    - Comprehensive error handling and logging
    - Query performance monitoring
    - Connection pooling optimization
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        """Initialize Neo4j client with configuration"""
        
        self.config = config or self._load_config_from_env()
        self.driver = None
        self.state = ConnectionState.DISCONNECTED
        self._connection_attempts = 0
        self._last_health_check = 0
        self._performance_metrics = {
            "queries_executed": 0,
            "total_execution_time": 0,
            "errors": 0,
            "reconnections": 0
        }
        
        logger.info(f"Neo4j client initialized for database: {self.config.database}")
    
    def _load_config_from_env(self) -> ConnectionConfig:
        """Load configuration from environment variables"""
        
        return ConnectionConfig(
            uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
            max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
            max_connection_pool_size=int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "100")),
            connection_timeout=int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30")),
            encrypted=os.getenv("NEO4J_ENCRYPTED", "true").lower() == "true"
        )
    
    async def connect(self) -> bool:
        """
        Establish connection to Neo4j database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        
        if self.state == ConnectionState.CONNECTED and self.driver:
            if await self._verify_connectivity():
                return True
        
        self.state = ConnectionState.CONNECTING
        self._connection_attempts += 1
        
        try:
            logger.info(f"Connecting to Neo4j at {self.config.uri}")
            
            # Create async driver with optimized configuration
            # Note: For neo4j+s:// and bolt+s:// schemes, encryption is handled by URI
            driver_config = {
                "max_connection_lifetime": self.config.max_connection_lifetime,
                "max_connection_pool_size": self.config.max_connection_pool_size,
                "connection_timeout": self.config.connection_timeout,
                "resolver": self.config.resolver
            }
            
            # Only set encrypted parameter for non-secure URI schemes
            if not (self.config.uri.startswith("neo4j+s://") or self.config.uri.startswith("bolt+s://")):
                driver_config["encrypted"] = self.config.encrypted
            
            self.driver = AsyncGraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                **driver_config
            )
            
            # Verify connection with simple query
            await self._verify_connectivity()
            
            self.state = ConnectionState.CONNECTED
            self._connection_attempts = 0
            
            logger.info("Neo4j connection established successfully")
            return True
            
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            self.state = ConnectionState.FAILED
            return False
            
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            self.state = ConnectionState.FAILED
            return False
            
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            self.state = ConnectionState.FAILED
            return False
    
    async def disconnect(self):
        """Gracefully close Neo4j connection"""
        
        if self.driver:
            try:
                await self.driver.close()
                logger.info("Neo4j connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
            finally:
                self.driver = None
                self.state = ConnectionState.DISCONNECTED
    
    async def _verify_connectivity(self) -> bool:
        """Verify Neo4j database connectivity"""
        
        try:
            async with self.driver.session(database=self.config.database) as session:
                result = await session.run("RETURN 1 as test")
                await result.consume()
                self._last_health_check = time.time()
                return True
                
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed: {e}")
            return False
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> QueryResult:
        """
        Execute Cypher query with comprehensive error handling
        
        Args:
            query: Cypher query string
            parameters: Query parameters dictionary
            timeout: Query timeout in seconds
            
        Returns:
            QueryResult: Query execution result with metadata
        """
        
        if not await self._ensure_connected():
            raise DatabaseError("Failed to establish Neo4j connection")
        
        parameters = parameters or {}
        start_time = time.time()
        
        try:
            async with self.driver.session(database=self.config.database) as session:
                
                # Set query timeout if specified
                if timeout:
                    session._config.update({"timeout": timeout})
                
                result = await session.run(query, parameters)
                
                # Collect all records first
                record_list = []
                async for record in result:
                    record_list.append(record.data())
                
                # Then consume for summary
                summary = await result.consume()
                
                execution_time = time.time() - start_time
                
                # Update performance metrics
                self._performance_metrics["queries_executed"] += 1
                self._performance_metrics["total_execution_time"] += execution_time
                
                query_result = QueryResult(
                    records=record_list,
                    summary={
                        "query_type": summary.query_type,
                        "counters": summary.counters._raw_data if hasattr(summary.counters, '_raw_data') else {},
                        "result_available_after": summary.result_available_after,
                        "result_consumed_after": summary.result_consumed_after
                    },
                    execution_time=execution_time,
                    query=query,
                    parameters=parameters,
                    success=True
                )
                
                logger.debug(f"Query executed in {execution_time:.3f}s: {query[:100]}...")
                return query_result
                
        except (ClientError, TransientError, DatabaseError) as e:
            execution_time = time.time() - start_time
            self._performance_metrics["errors"] += 1
            
            error_msg = f"Neo4j query failed: {str(e)}"
            logger.error(error_msg)
            
            return QueryResult(
                records=[],
                summary={},
                execution_time=execution_time,
                query=query,
                parameters=parameters,
                success=False,
                error=error_msg
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            self._performance_metrics["errors"] += 1
            
            error_msg = f"Unexpected error during query execution: {str(e)}"
            logger.error(error_msg)
            
            return QueryResult(
                records=[],
                summary={},
                execution_time=execution_time,
                query=query,
                parameters=parameters,
                success=False,
                error=error_msg
            )
    
    @asynccontextmanager
    async def transaction(self, timeout: Optional[int] = None):
        """
        Async context manager for Neo4j transactions
        
        Usage:
            async with neo4j_client.transaction() as tx:
                result1 = await tx.run("CREATE (n:Node) RETURN n")
                result2 = await tx.run("MATCH (n:Node) RETURN count(n)")
                # Transaction automatically committed on success
                # or rolled back on exception
        """
        
        if not await self._ensure_connected():
            raise DatabaseError("Failed to establish Neo4j connection")
        
        session = self.driver.session(database=self.config.database)
        transaction = None
        
        try:
            if timeout:
                session._config.update({"timeout": timeout})
            
            transaction = await session.begin_transaction()
            yield transaction
            await transaction.commit()
            
        except Exception as e:
            if transaction:
                await transaction.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
            
        finally:
            await session.close()
    
    async def execute_queries_in_transaction(
        self,
        queries: List[Dict[str, Any]],
        timeout: Optional[int] = None
    ) -> List[QueryResult]:
        """
        Execute multiple queries in a single transaction
        
        Args:
            queries: List of query dictionaries with 'query' and optional 'parameters'
            timeout: Transaction timeout in seconds
            
        Returns:
            List[QueryResult]: Results from all executed queries
        """
        
        results = []
        start_time = time.time()
        
        try:
            async with self.transaction(timeout=timeout) as tx:
                for query_dict in queries:
                    query = query_dict.get("query", "")
                    parameters = query_dict.get("parameters", {})
                    
                    result = await tx.run(query, parameters)
                    
                    # Collect all records first
                    record_list = []
                    async for record in result:
                        record_list.append(record.data())
                    
                    # Then consume for summary
                    summary = await result.consume()
                    
                    query_result = QueryResult(
                        records=record_list,
                        summary={
                            "query_type": summary.query_type,
                            "counters": summary.counters._raw_data if hasattr(summary.counters, '_raw_data') else {}
                        },
                        execution_time=time.time() - start_time,
                        query=query,
                        parameters=parameters,
                        success=True
                    )
                    
                    results.append(query_result)
            
            logger.info(f"Transaction with {len(queries)} queries completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            
            # Return failed results for all queries
            failed_results = []
            for query_dict in queries:
                failed_results.append(QueryResult(
                    records=[],
                    summary={},
                    execution_time=time.time() - start_time,
                    query=query_dict.get("query", ""),
                    parameters=query_dict.get("parameters", {}),
                    success=False,
                    error=str(e)
                ))
            
            return failed_results
    
    async def _ensure_connected(self) -> bool:
        """Ensure connection is active, reconnect if necessary"""
        
        if self.state == ConnectionState.CONNECTED:
            # Check if health check is recent
            if time.time() - self._last_health_check < 60:  # 1 minute
                return True
            
            # Perform health check
            if await self._verify_connectivity():
                return True
        
        # Connection lost, attempt reconnection
        logger.info("Connection lost, attempting reconnection...")
        self.state = ConnectionState.RECONNECTING
        self._performance_metrics["reconnections"] += 1
        
        return await self.connect()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and metrics"""
        
        return {
            "state": self.state.value,
            "database": self.config.database,
            "connection_attempts": self._connection_attempts,
            "last_health_check": self._last_health_check,
            "performance_metrics": self._performance_metrics.copy(),
            "connected": self.state == ConnectionState.CONNECTED
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        
        health_status = {
            "status": "unhealthy",
            "timestamp": time.time(),
            "connection_state": self.state.value,
            "database": self.config.database,
            "performance": self._performance_metrics.copy()
        }
        
        try:
            if await self._verify_connectivity():
                health_status["status"] = "healthy"
                health_status["response_time"] = time.time() - health_status["timestamp"]
        
        except Exception as e:
            health_status["error"] = str(e)
        
        return health_status


# Global client instance
_neo4j_client = None


def get_neo4j_client() -> Neo4jClient:
    """Get singleton Neo4j client instance"""
    global _neo4j_client
    
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    
    return _neo4j_client


async def initialize_neo4j_client(config: Optional[ConnectionConfig] = None) -> Neo4jClient:
    """Initialize and connect Neo4j client"""
    global _neo4j_client
    
    _neo4j_client = Neo4jClient(config)
    await _neo4j_client.connect()
    
    return _neo4j_client