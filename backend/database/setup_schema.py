#!/usr/bin/env python3
"""
OneVice Database Schema Setup Script

Production-ready script to initialize the Neo4j database schema
for the OneVice entertainment industry intelligence platform.

Usage:
    python setup_schema.py [--drop-existing] [--validate-only] [--config-file CONFIG]

Options:
    --drop-existing    Drop all existing schema elements before creating new ones (DANGEROUS)
    --validate-only    Only validate existing schema without making changes
    --config-file      Path to configuration file (default: uses environment variables)
    --force           Skip confirmation prompts (for automated deployment)
    --verbose         Enable verbose logging output
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.connection_manager import ConnectionManager, initialize_database
from database.neo4j_client import ConnectionConfig
from database.create_indexes import IndexManager


def setup_logging(verbose: bool = False):
    """Configure logging for schema setup"""
    
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Setup file handler
    log_file = Path(__file__).parent / "setup_schema.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    logging.getLogger("database").setLevel(log_level)
    logging.getLogger("neo4j").setLevel(logging.WARNING)  # Reduce neo4j driver noise
    
    return logging.getLogger(__name__)


def load_config_from_file(config_file: str) -> ConnectionConfig:
    """Load database configuration from JSON file"""
    
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        return ConnectionConfig(
            uri=config_data.get("uri", "neo4j://localhost:7687"),
            username=config_data.get("username", "neo4j"),
            password=config_data.get("password", "password"),
            database=config_data.get("database", "neo4j"),
            max_connection_lifetime=config_data.get("max_connection_lifetime", 3600),
            max_connection_pool_size=config_data.get("max_connection_pool_size", 100),
            connection_timeout=config_data.get("connection_timeout", 30),
            encrypted=config_data.get("encrypted", True)
        )
    
    except FileNotFoundError:
        raise ValueError(f"Configuration file not found: {config_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading configuration: {e}")


def load_config_from_env() -> ConnectionConfig:
    """Load database configuration from environment variables"""
    
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


def confirm_dangerous_operation(operation: str) -> bool:
    """Get user confirmation for dangerous operations"""
    
    print(f"\n⚠️  WARNING: You are about to perform a dangerous operation: {operation}")
    print("This action cannot be undone and may result in data loss.")
    print("Are you sure you want to continue? (type 'yes' to confirm)")
    
    response = input("\nConfirmation: ").strip().lower()
    return response == "yes"


async def validate_schema_only(connection_manager: ConnectionManager, logger: logging.Logger) -> Dict[str, Any]:
    """Validate schema without making any changes"""
    
    logger.info("🔍 Validating database schema...")
    
    try:
        validation_result = await connection_manager.schema.validate_schema()
        
        if validation_result.valid:
            logger.info("✅ Database schema is valid and complete")
            return {"success": True, "valid": True, "validation": validation_result}
        else:
            logger.warning("❌ Database schema validation failed")
            
            if validation_result.missing_constraints:
                logger.warning(f"Missing constraints: {validation_result.missing_constraints}")
            if validation_result.missing_indexes:
                logger.warning(f"Missing indexes: {validation_result.missing_indexes}")
            if validation_result.missing_vector_indexes:
                logger.warning(f"Missing vector indexes: {validation_result.missing_vector_indexes}")
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Warning: {warning}")
            if validation_result.errors:
                for error in validation_result.errors:
                    logger.error(f"Error: {error}")
            
            return {"success": True, "valid": False, "validation": validation_result}
    
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return {"success": False, "error": str(e)}


async def create_schema(
    connection_manager: ConnectionManager,
    logger: logging.Logger,
    drop_existing: bool = False
) -> Dict[str, Any]:
    """Create or recreate database schema"""
    
    try:
        # Drop existing schema if requested
        if drop_existing:
            logger.warning("🗑️  Dropping existing database schema...")
            drop_result = await connection_manager.schema.drop_schema()
            
            if drop_result["errors"]:
                logger.warning("Some errors occurred during schema drop:")
                for error in drop_result["errors"]:
                    logger.warning(f"  - {error}")
            
            logger.info(f"Dropped {drop_result['constraints_dropped']} constraints, "
                       f"{drop_result['indexes_dropped']} indexes, "
                       f"{drop_result['vector_indexes_dropped']} vector indexes")
        
        # Create core schema
        logger.info("🏗️  Creating database schema...")
        creation_result = await connection_manager.schema.create_core_schema()
        
        if creation_result["success"]:
            logger.info("✅ Database schema created successfully")
            logger.info(f"Created {creation_result['constraints']['created']} constraints, "
                       f"{creation_result['indexes']['created']} indexes, "
                       f"{creation_result['vector_indexes']['created']} vector indexes "
                       f"in {creation_result['execution_time']:.2f} seconds")
        else:
            logger.error("❌ Database schema creation completed with errors")
            
            # Log constraint errors
            if creation_result["constraints"]["errors"]:
                logger.error("Constraint creation errors:")
                for error in creation_result["constraints"]["errors"]:
                    logger.error(f"  - {error}")
            
            # Log index errors
            if creation_result["indexes"]["errors"]:
                logger.error("Index creation errors:")
                for error in creation_result["indexes"]["errors"]:
                    logger.error(f"  - {error}")
            
            # Log vector index errors
            if creation_result["vector_indexes"]["errors"]:
                logger.error("Vector index creation errors:")
                for error in creation_result["vector_indexes"]["errors"]:
                    logger.error(f"  - {error}")
        
        # Create performance indexes for graph tools
        logger.info("🚀 Creating performance indexes for graph tools...")
        
        try:
            # Initialize index manager
            index_manager = IndexManager(connection_manager.neo4j_client, logger)
            
            # Create performance indexes
            performance_created, performance_failed = await index_manager.create_all_indexes(
                drop_existing=False  # Don't drop existing since we just created core schema
            )
            
            logger.info(f"✅ Performance indexes created: {performance_created} created, {performance_failed} failed")
            
            # Add performance index results to creation result
            creation_result["performance_indexes"] = {
                "created": performance_created,
                "failed": performance_failed,
                "success": performance_failed == 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create performance indexes: {e}")
            creation_result["performance_indexes"] = {
                "created": 0,
                "failed": 0,
                "success": False,
                "error": str(e)
            }
        
        # Final validation
        logger.info("🔍 Validating created schema...")
        final_validation = await connection_manager.schema.validate_schema()
        
        if final_validation.valid:
            logger.info("✅ Schema validation passed - database is ready for use")
        else:
            logger.warning("⚠️  Schema validation found issues after creation")
        
        return {
            "success": creation_result["success"] and final_validation.valid,
            "creation_result": creation_result,
            "final_validation": final_validation
        }
    
    except Exception as e:
        logger.error(f"Schema creation failed: {e}")
        return {"success": False, "error": str(e)}


async def create_performance_indexes_only(
    connection_manager: ConnectionManager,
    logger: logging.Logger,
    drop_existing: bool = False
) -> Dict[str, Any]:
    """Create only performance indexes for graph tools (skip schema creation)"""
    
    try:
        logger.info("🚀 Creating performance indexes for graph tools...")
        
        # Initialize index manager
        index_manager = IndexManager(connection_manager.neo4j_client, logger)
        
        # Create performance indexes
        created_count, failed_count = await index_manager.create_all_indexes(drop_existing)
        
        success = failed_count == 0
        
        if success:
            logger.info(f"✅ Performance index creation completed successfully")
            logger.info(f"Created {created_count} indexes")
        else:
            logger.error(f"❌ Performance index creation completed with {failed_count} failures")
            logger.info(f"Created {created_count} indexes successfully")
        
        return {
            "success": success,
            "performance_indexes": {
                "created": created_count,
                "failed": failed_count,
                "success": success
            }
        }
    
    except Exception as e:
        logger.error(f"Performance index creation failed: {e}")
        return {"success": False, "error": str(e)}


async def generate_schema_report(connection_manager: ConnectionManager, logger: logging.Logger) -> Dict[str, Any]:
    """Generate comprehensive schema documentation report"""
    
    try:
        logger.info("📊 Generating schema documentation...")
        
        # Get schema documentation
        schema_docs = connection_manager.schema.get_schema_documentation()
        
        # Get current database state
        validation_result = await connection_manager.schema.validate_schema()
        
        # Get health status
        health_status = await connection_manager.health_check()
        
        report = {
            "generated_at": asyncio.get_event_loop().time(),
            "schema_documentation": schema_docs,
            "current_validation": validation_result,
            "health_status": health_status,
            "summary": {
                "schema_valid": validation_result.valid,
                "total_constraints": len(schema_docs["constraints"]),
                "total_indexes": len(schema_docs["indexes"]),
                "total_vector_indexes": len(schema_docs["vector_indexes"]),
                "total_relationships": len(schema_docs["relationships"]),
                "database_healthy": health_status["overall_status"] == "healthy"
            }
        }
        
        # Write report to file
        report_file = Path(__file__).parent / "schema_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Schema report written to: {report_file}")
        
        return report
    
    except Exception as e:
        logger.error(f"Failed to generate schema report: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """Main schema setup function"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="OneVice Database Schema Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--drop-existing", action="store_true",
                       help="Drop existing schema before creating new (DANGEROUS)")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate existing schema")
    parser.add_argument("--indexes-only", action="store_true",
                       help="Only create performance indexes (skip schema creation)")
    parser.add_argument("--config-file", type=str,
                       help="Path to JSON configuration file")
    parser.add_argument("--force", action="store_true",
                       help="Skip confirmation prompts")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--generate-report", action="store_true",
                       help="Generate schema documentation report")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    logger.info("🚀 OneVice Database Schema Setup Starting...")
    
    try:
        # Load configuration
        if args.config_file:
            logger.info(f"Loading configuration from: {args.config_file}")
            config = load_config_from_file(args.config_file)
        else:
            logger.info("Loading configuration from environment variables")
            config = load_config_from_env()
        
        # Log configuration (excluding sensitive info)
        logger.info(f"Database URI: {config.uri}")
        logger.info(f"Database: {config.database}")
        logger.info(f"Username: {config.username}")
        logger.info(f"Encrypted: {config.encrypted}")
        
        # Confirm dangerous operations
        if args.drop_existing and not args.force:
            if not confirm_dangerous_operation("DROP ALL EXISTING SCHEMA ELEMENTS"):
                logger.info("Operation cancelled by user")
                sys.exit(0)
        
        # Initialize connection manager
        logger.info("📡 Connecting to database...")
        connection_manager = ConnectionManager(config)
        init_result = await connection_manager.initialize(validate_schema=False)
        
        if not init_result["success"]:
            logger.error("❌ Failed to initialize database connection")
            for error in init_result["errors"]:
                logger.error(f"  - {error}")
            sys.exit(1)
        
        logger.info("✅ Database connection established")
        
        # Execute requested operation
        if args.validate_only:
            result = await validate_schema_only(connection_manager, logger)
            exit_code = 0 if result["success"] and result.get("valid", False) else 1
        
        elif args.indexes_only:
            result = await create_performance_indexes_only(connection_manager, logger, args.drop_existing)
            exit_code = 0 if result["success"] else 1
        
        else:
            result = await create_schema(connection_manager, logger, args.drop_existing)
            exit_code = 0 if result["success"] else 1
        
        # Generate report if requested
        if args.generate_report:
            await generate_schema_report(connection_manager, logger)
        
        # Cleanup
        await connection_manager.close()
        
        if exit_code == 0:
            logger.info("🎉 Schema setup completed successfully")
        else:
            logger.error("❌ Schema setup completed with errors")
        
        sys.exit(exit_code)
    
    except KeyboardInterrupt:
        logger.info("Schema setup cancelled by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"❌ Schema setup failed with unexpected error: {e}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())