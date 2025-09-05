"""
Connection Manager for OneVice Database Operations

Provides centralized connection management, health monitoring,
and initialization coordination for all database components.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from .neo4j_client import Neo4jClient, ConnectionConfig
from .schema_manager import SchemaManager, SchemaValidationResult

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Centralized database connection and schema management
    
    Coordinates Neo4j connections, schema validation, and provides
    health monitoring for the OneVice platform database layer.
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        """Initialize connection manager"""
        
        self.config = config
        self.neo4j_client: Optional[Neo4jClient] = None
        self.schema_manager: Optional[SchemaManager] = None
        self._initialized = False
        
        logger.info("Connection manager initialized")
    
    async def initialize(self, validate_schema: bool = True) -> Dict[str, Any]:
        """
        Initialize all database connections and validate schema
        
        Args:
            validate_schema: Whether to validate schema on startup
            
        Returns:
            Dict with initialization results and status
        """
        
        logger.info("Initializing database connections...")
        
        results = {
            "success": False,
            "neo4j_connected": False,
            "schema_valid": False,
            "initialization_time": 0,
            "errors": []
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Initialize Neo4j client
            self.neo4j_client = Neo4jClient(self.config)
            neo4j_connected = await self.neo4j_client.connect()
            
            if not neo4j_connected:
                results["errors"].append("Failed to connect to Neo4j database")
                return results
            
            results["neo4j_connected"] = True
            logger.info("Neo4j connection established")
            
            # Initialize schema manager
            self.schema_manager = SchemaManager(self.neo4j_client)
            
            # Validate schema if requested
            if validate_schema:
                schema_validation = await self.schema_manager.validate_schema()
                results["schema_valid"] = schema_validation.valid
                
                if not schema_validation.valid:
                    logger.warning("Schema validation issues found")
                    results["schema_validation"] = {
                        "missing_constraints": schema_validation.missing_constraints,
                        "missing_indexes": schema_validation.missing_indexes,
                        "missing_vector_indexes": schema_validation.missing_vector_indexes,
                        "warnings": schema_validation.warnings,
                        "errors": schema_validation.errors
                    }
                else:
                    logger.info("Schema validation passed")
            else:
                results["schema_valid"] = True  # Assume valid if not checking
            
            results["initialization_time"] = asyncio.get_event_loop().time() - start_time
            results["success"] = neo4j_connected  # Only require connection, not schema validity
            self._initialized = neo4j_connected    # Mark as initialized if connected
            
            if self._initialized:
                logger.info(f"Database initialization completed successfully in {results['initialization_time']:.2f}s")
            else:
                logger.error("Database initialization completed with errors")
            
            return results
            
        except Exception as e:
            error_msg = f"Database initialization failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["initialization_time"] = asyncio.get_event_loop().time() - start_time
            return results
    
    async def ensure_schema(self) -> Dict[str, Any]:
        """
        Ensure database schema is complete and valid
        
        Creates missing schema elements and validates the complete schema.
        
        Returns:
            Dict with schema creation/validation results
        """
        
        if not self.neo4j_client or not self.schema_manager:
            raise RuntimeError("Database connection not available. Call initialize() first.")
        
        logger.info("Ensuring database schema is complete...")
        
        # First validate current schema
        validation_result = await self.schema_manager.validate_schema()
        
        if validation_result.valid:
            logger.info("Database schema is already complete and valid")
            return {
                "schema_complete": True,
                "creation_required": False,
                "validation_result": validation_result
            }
        
        # Schema is incomplete, create missing elements
        logger.info("Creating missing schema elements...")
        creation_result = await self.schema_manager.create_core_schema()
        
        # Re-validate after creation
        final_validation = await self.schema_manager.validate_schema()
        
        return {
            "schema_complete": final_validation.valid,
            "creation_required": True,
            "creation_result": creation_result,
            "validation_result": final_validation
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check of all database components
        
        Returns:
            Dict with detailed health status
        """
        
        health_status = {
            "overall_status": "unhealthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {}
        }
        
        try:
            if not self._initialized:
                health_status["components"]["initialization"] = {
                    "status": "failed",
                    "message": "Connection manager not initialized"
                }
                return health_status
            
            # Neo4j health check
            if self.neo4j_client:
                neo4j_health = await self.neo4j_client.health_check()
                health_status["components"]["neo4j"] = neo4j_health
            else:
                health_status["components"]["neo4j"] = {
                    "status": "unhealthy",
                    "message": "Neo4j client not available"
                }
            
            # Schema validation check
            if self.schema_manager:
                try:
                    schema_validation = await self.schema_manager.validate_schema()
                    health_status["components"]["schema"] = {
                        "status": "healthy" if schema_validation.valid else "degraded",
                        "valid": schema_validation.valid,
                        "missing_constraints": len(schema_validation.missing_constraints),
                        "missing_indexes": len(schema_validation.missing_indexes),
                        "missing_vector_indexes": len(schema_validation.missing_vector_indexes),
                        "warnings": len(schema_validation.warnings),
                        "errors": len(schema_validation.errors)
                    }
                except Exception as e:
                    health_status["components"]["schema"] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
            
            # Determine overall status
            component_statuses = [
                comp.get("status", "unhealthy") 
                for comp in health_status["components"].values()
            ]
            
            if all(status == "healthy" for status in component_statuses):
                health_status["overall_status"] = "healthy"
            elif any(status in ["healthy", "degraded"] for status in component_statuses):
                health_status["overall_status"] = "degraded"
            else:
                health_status["overall_status"] = "unhealthy"
            
            return health_status
            
        except Exception as e:
            health_status["components"]["health_check"] = {
                "status": "failed",
                "error": str(e)
            }
            return health_status
    
    async def close(self):
        """Close all database connections"""
        
        logger.info("Closing database connections...")
        
        if self.neo4j_client:
            await self.neo4j_client.disconnect()
            self.neo4j_client = None
        
        self.schema_manager = None
        self._initialized = False
        
        logger.info("Database connections closed")
    
    @property
    def is_initialized(self) -> bool:
        """Check if connection manager is initialized"""
        return self._initialized
    
    @property
    def neo4j(self) -> Neo4jClient:
        """Get Neo4j client instance"""
        if not self._initialized or not self.neo4j_client:
            raise RuntimeError("Neo4j client not available. Initialize connection manager first.")
        return self.neo4j_client
    
    @property
    def schema(self) -> SchemaManager:
        """Get schema manager instance"""
        if not self._initialized or not self.schema_manager:
            raise RuntimeError("Schema manager not available. Initialize connection manager first.")
        return self.schema_manager
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for database operations"""
        
        if not self._initialized:
            # Auto-initialize if not already done
            init_result = await self.initialize()
            if not init_result["success"]:
                raise RuntimeError(f"Failed to initialize database: {init_result['errors']}")
        
        try:
            yield self
        finally:
            # Connection cleanup if needed
            pass


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


async def get_connection_manager(config: Optional[ConnectionConfig] = None) -> ConnectionManager:
    """
    Get singleton connection manager instance
    
    Args:
        config: Optional connection configuration
        
    Returns:
        ConnectionManager instance
    """
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = ConnectionManager(config)
        await _connection_manager.initialize()
    
    return _connection_manager


async def initialize_database(
    config: Optional[ConnectionConfig] = None,
    ensure_schema: bool = True
) -> Dict[str, Any]:
    """
    Initialize database with full schema setup
    
    Args:
        config: Optional connection configuration
        ensure_schema: Whether to create schema if missing
        
    Returns:
        Dict with initialization results
    """
    
    logger.info("Initializing OneVice database...")
    
    try:
        # Get connection manager
        connection_manager = await get_connection_manager(config)
        
        # Ensure schema is complete if requested
        if ensure_schema:
            schema_result = await connection_manager.ensure_schema()
            
            return {
                "success": True,
                "connection_manager": connection_manager,
                "schema_result": schema_result
            }
        else:
            return {
                "success": True,
                "connection_manager": connection_manager,
                "schema_result": {"schema_complete": True, "creation_required": False}
            }
    
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }