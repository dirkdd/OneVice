#!/usr/bin/env python3
"""
Neo4j Performance Index Management Script

Creates comprehensive indexes for optimal query performance across
all graph tools and LangGraph agent operations.

Usage:
    python create_indexes.py [--drop-existing] [--test-performance] [--config-file CONFIG]

Options:
    --drop-existing     Drop all existing indexes before creating new ones (DANGEROUS)
    --test-performance  Run performance tests after index creation
    --config-file       Path to configuration file (default: uses environment variables)
    --force             Skip confirmation prompts (for automated deployment)
    --verbose           Enable verbose logging output
"""

import os
import sys
import json
import asyncio
import argparse
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.connection_manager import ConnectionManager
from database.neo4j_client import Neo4jClient, ConnectionConfig


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for index management"""
    
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
    log_file = Path(__file__).parent / "create_indexes.log"
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


class IndexManager:
    """Manages Neo4j indexes for optimal graph tool performance"""
    
    def __init__(self, neo4j_client: Neo4jClient, logger: logging.Logger):
        self.neo4j_client = neo4j_client
        self.logger = logger
        
    async def get_existing_indexes(self) -> List[Dict[str, Any]]:
        """Get list of existing indexes"""
        
        query = "SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, state"
        
        try:
            result = await self.neo4j_client.execute_query(query)
            indexes = []
            
            for record in result.records:
                indexes.append({
                    "name": record.get("name"),
                    "type": record.get("type"),
                    "entity_type": record.get("entityType"),
                    "labels_or_types": record.get("labelsOrTypes"),
                    "properties": record.get("properties"),
                    "state": record.get("state")
                })
            
            return indexes
            
        except Exception as e:
            self.logger.error(f"Failed to get existing indexes: {e}")
            return []
    
    async def drop_index(self, index_name: str) -> bool:
        """Drop a specific index"""
        
        query = f"DROP INDEX {index_name} IF EXISTS"
        
        try:
            await self.neo4j_client.execute_query(query)
            self.logger.info(f"Dropped index: {index_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to drop index {index_name}: {e}")
            return False
    
    async def create_index(self, index_definition: str) -> bool:
        """Create a single index"""
        
        try:
            await self.neo4j_client.execute_query(index_definition)
            self.logger.info(f"Created index: {index_definition}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create index: {index_definition}, Error: {e}")
            return False
    
    async def get_performance_indexes(self) -> List[str]:
        """Get comprehensive list of performance indexes for graph tools"""
        
        indexes = [
            # ================================================================================
            # CORE ENTITY INDEXES FOR GRAPH TOOLS
            # ================================================================================
            
            # Person entity indexes (critical for talent and CRM tools)
            "CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX person_folk_id_index IF NOT EXISTS FOR (p:Person) ON (p.folkId)",
            "CREATE INDEX person_internal_filter IF NOT EXISTS FOR (p:Person) ON (p.isInternal)",
            "CREATE INDEX person_email_index IF NOT EXISTS FOR (p:Person) ON (p.email)",
            "CREATE INDEX person_title_index IF NOT EXISTS FOR (p:Person) ON (p.title)",
            
            # Organization entity indexes (for client and vendor analysis)
            "CREATE INDEX organization_name_index IF NOT EXISTS FOR (o:Organization) ON (o.name)",
            "CREATE INDEX organization_folk_id_index IF NOT EXISTS FOR (o:Organization) ON (o.folkId)",
            "CREATE INDEX organization_type_index IF NOT EXISTS FOR (o:Organization) ON (o.type)",
            
            # Project entity indexes (for project-based queries)
            "CREATE INDEX project_title_index IF NOT EXISTS FOR (p:Project) ON (p.title)",
            "CREATE INDEX project_id_index IF NOT EXISTS FOR (p:Project) ON (p.projectId)",
            "CREATE INDEX project_type_index IF NOT EXISTS FOR (p:Project) ON (p.type)",
            "CREATE INDEX project_status_index IF NOT EXISTS FOR (p:Project) ON (p.status)",
            "CREATE INDEX project_year_index IF NOT EXISTS FOR (p:Project) ON (p.year)",
            
            # Creative Concept indexes (for style-based matching)
            "CREATE INDEX creative_concept_name_index IF NOT EXISTS FOR (c:CreativeConcept) ON (c.name)",
            "CREATE INDEX creative_concept_category_index IF NOT EXISTS FOR (c:CreativeConcept) ON (c.category)",
            
            # Document indexes (for document analysis tools)
            "CREATE INDEX document_id_index IF NOT EXISTS FOR (d:Document) ON (d.documentId)",
            "CREATE INDEX document_type_index IF NOT EXISTS FOR (d:Document) ON (d.documentType)",
            "CREATE INDEX document_sensitivity_index IF NOT EXISTS FOR (d:Document) ON (d.sensitivityLevel)",
            "CREATE INDEX document_content_index IF NOT EXISTS FOR (d:Document) ON (d.content)",
            
            # Location indexes (for location-based filtering)
            "CREATE INDEX location_name_index IF NOT EXISTS FOR (l:Location) ON (l.name)",
            "CREATE INDEX location_type_index IF NOT EXISTS FOR (l:Location) ON (l.type)",
            
            # ================================================================================
            # FOLK.APP INTEGRATION INDEXES
            # ================================================================================
            
            # Deal indexes (for CRM and sales tools)
            "CREATE INDEX deal_name_index IF NOT EXISTS FOR (d:Deal) ON (d.name)",
            "CREATE INDEX deal_folk_id_index IF NOT EXISTS FOR (d:Deal) ON (d.folkId)",
            "CREATE INDEX deal_status_index IF NOT EXISTS FOR (d:Deal) ON (d.status)",
            "CREATE INDEX deal_value_index IF NOT EXISTS FOR (d:Deal) ON (d.value)",
            "CREATE INDEX deal_stage_index IF NOT EXISTS FOR (d:Deal) ON (d.stage)",
            
            # Group indexes (for segmentation)
            "CREATE INDEX group_name_index IF NOT EXISTS FOR (g:Group) ON (g.name)",
            "CREATE INDEX group_folk_id_index IF NOT EXISTS FOR (g:Group) ON (g.folkId)",
            "CREATE INDEX group_type_index IF NOT EXISTS FOR (g:Group) ON (g.groupType)",
            
            # ================================================================================
            # COMPOSITE INDEXES FOR COMPLEX QUERIES
            # ================================================================================
            
            # Person composite indexes for talent search
            "CREATE INDEX person_name_title_composite IF NOT EXISTS FOR (p:Person) ON (p.name, p.title)",
            "CREATE INDEX person_internal_folk_composite IF NOT EXISTS FOR (p:Person) ON (p.isInternal, p.folkId)",
            
            # Project composite indexes for project analysis
            "CREATE INDEX project_title_year_composite IF NOT EXISTS FOR (p:Project) ON (p.title, p.year)",
            "CREATE INDEX project_type_status_composite IF NOT EXISTS FOR (p:Project) ON (p.type, p.status)",
            
            # Deal composite indexes for sales analysis
            "CREATE INDEX deal_status_value_composite IF NOT EXISTS FOR (d:Deal) ON (d.status, d.value)",
            "CREATE INDEX deal_stage_folk_id_composite IF NOT EXISTS FOR (d:Deal) ON (d.stage, d.folkId)",
            
            # Organization composite indexes for client analysis
            "CREATE INDEX org_name_type_composite IF NOT EXISTS FOR (o:Organization) ON (o.name, o.type)",
            "CREATE INDEX org_folk_id_type_composite IF NOT EXISTS FOR (o:Organization) ON (o.folkId, o.type)",
            
            # ================================================================================
            # RELATIONSHIP INDEXES FOR TRAVERSAL OPTIMIZATION
            # ================================================================================
            
            # Project contribution relationships (for crew analysis)
            "CREATE INDEX contribution_role_index IF NOT EXISTS FOR ()-[r:CONTRIBUTED_TO]-() ON (r.role)",
            "CREATE INDEX contribution_start_date_index IF NOT EXISTS FOR ()-[r:CONTRIBUTED_TO]-() ON (r.startDate)",
            
            # Employment relationships (for organization queries)
            "CREATE INDEX employment_dates_index IF NOT EXISTS FOR ()-[r:WORKS_FOR]-() ON (r.startDate, r.endDate)",
            "CREATE INDEX employment_title_index IF NOT EXISTS FOR ()-[r:WORKS_FOR]-() ON (r.title)",
            
            # Deal relationships (for CRM analysis)
            "CREATE INDEX deal_contact_index IF NOT EXISTS FOR ()-[r:WITH_CONTACT]-() ON (r.contactRole)",
            "CREATE INDEX deal_organization_index IF NOT EXISTS FOR ()-[r:FOR_ORGANIZATION]-() ON (r.contractValue)",
            
            # Project client relationships (for client analysis)
            "CREATE INDEX project_client_dates_index IF NOT EXISTS FOR ()-[r:FOR_CLIENT]-() ON (r.startDate, r.endDate)",
            "CREATE INDEX project_client_value_index IF NOT EXISTS FOR ()-[r:FOR_CLIENT]-() ON (r.contractValue)",
            
            # Group membership relationships (for segmentation)
            "CREATE INDEX group_membership_index IF NOT EXISTS FOR ()-[r:BELONGS_TO]-() ON (r.addedDate)",
            
            # ================================================================================
            # FULL-TEXT SEARCH INDEXES
            # ================================================================================
            
            # Person full-text search (for name variations and fuzzy matching)
            "CREATE FULLTEXT INDEX person_fulltext_index IF NOT EXISTS FOR (p:Person) ON EACH [p.name, p.bio, p.title]",
            
            # Organization full-text search
            "CREATE FULLTEXT INDEX organization_fulltext_index IF NOT EXISTS FOR (o:Organization) ON EACH [o.name, o.description]",
            
            # Project full-text search  
            "CREATE FULLTEXT INDEX project_fulltext_index IF NOT EXISTS FOR (p:Project) ON EACH [p.title, p.description, p.synopsis]",
            
            # Document full-text search (for content analysis)
            "CREATE FULLTEXT INDEX document_fulltext_index IF NOT EXISTS FOR (d:Document) ON EACH [d.title, d.content, d.summary]",
            
            # Deal full-text search
            "CREATE FULLTEXT INDEX deal_fulltext_index IF NOT EXISTS FOR (d:Deal) ON EACH [d.name, d.description]",
            
            # Creative concept full-text search
            "CREATE FULLTEXT INDEX concept_fulltext_index IF NOT EXISTS FOR (c:CreativeConcept) ON EACH [c.name, c.description]",
        ]
        
        return indexes
    
    async def create_all_indexes(self, drop_existing: bool = False) -> Tuple[int, int]:
        """Create all performance indexes"""
        
        self.logger.info("Starting index creation process...")
        
        # Get existing indexes if dropping
        if drop_existing:
            existing_indexes = await self.get_existing_indexes()
            self.logger.info(f"Found {len(existing_indexes)} existing indexes")
            
            # Drop user-created indexes (skip system indexes)
            dropped_count = 0
            for index in existing_indexes:
                if not index["name"].startswith("__"):  # Skip system indexes
                    if await self.drop_index(index["name"]):
                        dropped_count += 1
            
            self.logger.info(f"Dropped {dropped_count} existing indexes")
            
        # Create new indexes
        index_definitions = await self.get_performance_indexes()
        self.logger.info(f"Creating {len(index_definitions)} indexes...")
        
        created_count = 0
        failed_count = 0
        
        for index_def in index_definitions:
            if await self.create_index(index_def):
                created_count += 1
            else:
                failed_count += 1
        
        self.logger.info(f"Index creation complete: {created_count} created, {failed_count} failed")
        return created_count, failed_count
    
    async def test_index_performance(self) -> Dict[str, Any]:
        """Test query performance with created indexes"""
        
        self.logger.info("Running index performance tests...")
        
        test_queries = [
            # Person lookup by name (most common query)
            ("Person name lookup", "MATCH (p:Person {name: 'John Smith'}) RETURN p LIMIT 1"),
            
            # Organization search
            ("Organization search", "MATCH (o:Organization) WHERE o.name CONTAINS 'Media' RETURN o LIMIT 5"),
            
            # Project by title and year
            ("Project lookup", "MATCH (p:Project {title: 'Sample Project', year: 2024}) RETURN p LIMIT 1"),
            
            # Deal status filtering
            ("Deal filtering", "MATCH (d:Deal {status: 'active'}) RETURN d LIMIT 10"),
            
            # Complex relationship query
            ("Relationship traversal", 
             """MATCH (p:Person)-[:CONTRIBUTED_TO]->(proj:Project)-[:FOR_CLIENT]->(o:Organization) 
                WHERE o.name = 'Sample Client' RETURN p.name, proj.title LIMIT 5"""),
            
            # Full-text search test
            ("Full-text search", 
             "CALL db.index.fulltext.queryNodes('person_fulltext_index', 'director') YIELD node RETURN node.name LIMIT 5"),
        ]
        
        performance_results = {}
        
        for test_name, query in test_queries:
            try:
                start_time = time.time()
                result = await self.neo4j_client.execute_query(query)
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                record_count = len(result.records) if result.records else 0
                
                performance_results[test_name] = {
                    "execution_time_ms": round(execution_time, 2),
                    "record_count": record_count,
                    "query": query
                }
                
                self.logger.info(f"{test_name}: {execution_time:.2f}ms ({record_count} records)")
                
            except Exception as e:
                performance_results[test_name] = {
                    "error": str(e),
                    "query": query
                }
                self.logger.warning(f"{test_name} failed: {e}")
        
        return performance_results


async def main():
    """Main execution function"""
    
    parser = argparse.ArgumentParser(description="Neo4j Performance Index Management")
    parser.add_argument("--drop-existing", action="store_true", 
                       help="Drop all existing indexes before creating new ones (DANGEROUS)")
    parser.add_argument("--test-performance", action="store_true",
                       help="Run performance tests after index creation")
    parser.add_argument("--config-file", type=str,
                       help="Path to configuration file")
    parser.add_argument("--force", action="store_true",
                       help="Skip confirmation prompts")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Load configuration
    if args.config_file:
        try:
            with open(args.config_file, 'r') as f:
                config_data = json.load(f)
            config = ConnectionConfig(**config_data)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            sys.exit(1)
    else:
        # Use environment variables
        config = ConnectionConfig(
            uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
        )
    
    # Confirmation prompt for destructive operations
    if args.drop_existing and not args.force:
        response = input("\nWARNING: This will drop all existing indexes! Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Operation cancelled by user")
            sys.exit(0)
    
    try:
        # Initialize Neo4j client
        neo4j_client = Neo4jClient(config)
        await neo4j_client.initialize()
        
        # Create index manager
        index_manager = IndexManager(neo4j_client, logger)
        
        # Create indexes
        created_count, failed_count = await index_manager.create_all_indexes(args.drop_existing)
        
        if failed_count > 0:
            logger.warning(f"Some indexes failed to create: {failed_count} failures")
        
        # Run performance tests if requested
        if args.test_performance:
            performance_results = await index_manager.test_index_performance()
            
            # Save performance results
            results_file = Path(__file__).parent / "index_performance_results.json"
            with open(results_file, 'w') as f:
                json.dump(performance_results, f, indent=2)
            
            logger.info(f"Performance test results saved to: {results_file}")
        
        logger.info("Index management completed successfully")
        
    except Exception as e:
        logger.error(f"Index management failed: {e}")
        sys.exit(1)
        
    finally:
        if 'neo4j_client' in locals():
            await neo4j_client.close()


if __name__ == "__main__":
    asyncio.run(main())