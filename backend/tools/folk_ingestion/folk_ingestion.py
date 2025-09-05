"""
Folk.app CRM Data Ingestion Service

Main orchestration service for ingesting Folk.app CRM data into Neo4j,
implementing the hybrid model for business development integration.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from .folk_client import FolkClient, FolkAPIError, FolkUser
from .folk_models import FolkPerson, FolkCompany, FolkGroup, FolkCustomObject
from .config import FolkConfig
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database.neo4j_client import Neo4jClient, ConnectionConfig

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    """Statistics for ingestion process"""
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # API stats
    api_keys_processed: int = 0
    api_requests_made: int = 0
    api_errors: int = 0
    
    # Data stats
    people_fetched: int = 0
    people_processed: int = 0
    companies_fetched: int = 0
    companies_processed: int = 0
    groups_fetched: int = 0
    groups_processed: int = 0
    custom_objects_fetched: int = 0
    custom_objects_processed: int = 0
    entity_types_discovered: int = 0
    
    # Neo4j stats
    nodes_created: int = 0
    nodes_updated: int = 0
    relationships_created: int = 0
    transactions_executed: int = 0
    neo4j_errors: int = 0
    
    # Errors
    validation_errors: List[str] = field(default_factory=list)
    processing_errors: List[str] = field(default_factory=list)
    
    def finalize(self):
        """Finalize stats when ingestion completes"""
        self.end_time = datetime.utcnow()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            "timing": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": self.duration_seconds
            },
            "api": {
                "keys_processed": self.api_keys_processed,
                "requests_made": self.api_requests_made,
                "errors": self.api_errors
            },
            "data": {
                "people": {"fetched": self.people_fetched, "processed": self.people_processed},
                "companies": {"fetched": self.companies_fetched, "processed": self.companies_processed},
                "groups": {"fetched": self.groups_fetched, "processed": self.groups_processed},
                "custom_objects": {"fetched": self.custom_objects_fetched, "processed": self.custom_objects_processed},
                "entity_types_discovered": self.entity_types_discovered
            },
            "neo4j": {
                "nodes_created": self.nodes_created,
                "nodes_updated": self.nodes_updated,
                "relationships_created": self.relationships_created,
                "transactions_executed": self.transactions_executed,
                "errors": self.neo4j_errors
            },
            "errors": {
                "validation_errors": self.validation_errors,
                "processing_errors": self.processing_errors,
                "total_errors": len(self.validation_errors) + len(self.processing_errors)
            }
        }


class FolkIngestionService:
    """
    Main service for ingesting Folk.app CRM data into Neo4j
    
    Implements the hybrid model:
    1. Ingest core entities (Person, Organization, Group, Deal)
    2. Store Folk IDs for live API lookups
    3. Create relationships between entities
    4. Track data provenance
    """
    
    def __init__(self, config: FolkConfig):
        self.config = config
        self.neo4j_client: Optional[Neo4jClient] = None
        self.stats = IngestionStats()
        self.processed_folk_ids: Set[str] = set()
        
        logger.info(f"Folk ingestion service initialized with {len(config.api_keys)} API keys")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize Neo4j connection"""
        try:
            # Initialize Neo4j client
            neo4j_config = ConnectionConfig(
                uri=self.config.neo4j_uri,
                username=self.config.neo4j_username,
                password=self.config.neo4j_password,
                database=self.config.neo4j_database
            )
            
            self.neo4j_client = Neo4jClient(neo4j_config)
            await self.neo4j_client.connect()
            
            logger.info("Neo4j connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {e}")
            raise
    
    async def cleanup(self):
        """Clean up connections"""
        if self.neo4j_client:
            await self.neo4j_client.disconnect()
            logger.info("Neo4j connection closed")
    
    async def run_full_ingestion(self) -> IngestionStats:
        """
        Run complete Folk data ingestion process
        
        Returns:
            IngestionStats: Comprehensive ingestion statistics
        """
        
        logger.info("Starting Folk CRM data ingestion")
        self.stats = IngestionStats()
        
        try:
            # Process each API key
            for i, api_key in enumerate(self.config.api_keys):
                logger.info(f"Processing API key {i+1}/{len(self.config.api_keys)}")
                
                try:
                    await self._process_api_key(api_key)
                    self.stats.api_keys_processed += 1
                    
                except Exception as e:
                    error_msg = f"Failed to process API key {i+1}: {str(e)}"
                    logger.error(error_msg)
                    self.stats.processing_errors.append(error_msg)
                    self.stats.api_errors += 1
                    
                    # Continue with next API key
                    continue
            
            # Finalize stats
            self.stats.finalize()
            
            logger.info(f"Folk ingestion completed in {self.stats.duration_seconds:.2f}s")
            logger.info(f"Processed {self.stats.people_processed} people, "
                       f"{self.stats.companies_processed} companies, "
                       f"{self.stats.groups_processed} groups, "
                       f"{self.stats.custom_objects_processed} custom objects across "
                       f"{self.stats.entity_types_discovered} entity types")
            
            return self.stats
            
        except Exception as e:
            self.stats.finalize()
            logger.error(f"Folk ingestion failed: {e}")
            raise
    
    async def _process_api_key(self, api_key: str):
        """Process data for a single API key"""
        
        async with FolkClient(
            api_key=api_key,
            base_url=self.config.base_url,
            rate_limit=self.config.rate_limit,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        ) as folk_client:
            
            # Get user profile to identify data owner
            user_profile = await folk_client.get_user_profile()
            data_owner_id = user_profile.id
            
            logger.info(f"Processing data for user: {user_profile.name} ({user_profile.email})")
            
            # Ensure internal user exists in Neo4j
            await self._ensure_internal_user(user_profile)
            
            # Folk API has max limit of 100 per request
            page_limit = min(100, self.config.page_size if not self.config.dry_run else 100)
            
            # Fetch all data concurrently
            people_task = asyncio.create_task(folk_client.get_people(limit=page_limit))
            companies_task = asyncio.create_task(folk_client.get_companies(limit=page_limit))  
            groups_task = asyncio.create_task(folk_client.get_all_groups_paginated(self.config.page_size))
            
            # Wait for core data
            people_data, companies_data, groups_data = await asyncio.gather(
                people_task, companies_task, groups_task, return_exceptions=True
            )
            
            # Handle fetch errors
            if isinstance(people_data, Exception):
                logger.error(f"Failed to fetch people: {people_data}")
                people_data = []
            
            if isinstance(companies_data, Exception):
                logger.error(f"Failed to fetch companies: {companies_data}")
                companies_data = []
            
            if isinstance(groups_data, Exception):
                logger.error(f"Failed to fetch groups: {groups_data}")
                groups_data = []
            
            self.stats.people_fetched += len(people_data) if people_data else 0
            self.stats.companies_fetched += len(companies_data) if companies_data else 0
            self.stats.groups_fetched += len(groups_data) if groups_data else 0
            
            # Process groups first (needed for relationships)
            if groups_data:
                await self._process_groups(groups_data, data_owner_id)
            
            # Process people and companies concurrently
            await asyncio.gather(
                self._process_people(people_data, data_owner_id),
                self._process_companies(companies_data, data_owner_id),
                return_exceptions=True
            )
            
            # Discover entity types and process custom objects for each group
            if groups_data:
                await self._process_custom_objects_for_groups(
                    folk_client, groups_data, people_data, companies_data, data_owner_id
                )
            
            # Update API request stats
            client_stats = folk_client.get_stats()
            self.stats.api_requests_made += client_stats["requests_made"]
            self.stats.api_errors += client_stats["errors_count"]
    
    async def _ensure_internal_user(self, user_profile: FolkUser):
        """Ensure internal user exists in Neo4j"""
        
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would create/update internal user: {user_profile.name}")
            return
        
        # Create internal user as Person node
        internal_person = FolkPerson(
            folk_id=f"internal_{user_profile.id}",
            email=user_profile.email,
            name=user_profile.name,
            company=user_profile.company,
            is_internal=True,
            folk_user_id=user_profile.id
        )
        
        query = """
        MERGE (p:Person {folkUserId: $folk_user_id})
        SET p += $properties
        RETURN p.personId as person_id
        """
        
        try:
            result = await self.neo4j_client.execute_query(
                query,
                {
                    "folk_user_id": user_profile.id,
                    "properties": internal_person.to_neo4j_node()
                }
            )
            
            if result.success:
                self.stats.transactions_executed += 1
                logger.info(f"Internal user ensured: {user_profile.name}")
            else:
                self.stats.neo4j_errors += 1
                logger.error(f"Failed to ensure internal user: {result.error}")
                
        except Exception as e:
            self.stats.neo4j_errors += 1
            logger.error(f"Error ensuring internal user: {e}")
    
    async def _process_people(self, people_data: List[Dict[str, Any]], data_owner_id: str):
        """Process people data in batches"""
        
        if not people_data:
            return
        
        logger.info(f"Processing {len(people_data)} people")
        
        # Process in batches
        for i in range(0, len(people_data), self.config.batch_size):
            batch = people_data[i:i + self.config.batch_size]
            await self._process_people_batch(batch, data_owner_id)
    
    async def _process_people_batch(self, batch: List[Dict[str, Any]], data_owner_id: str):
        """Process a batch of people"""
        
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would process {len(batch)} people")
            self.stats.people_processed += len(batch)
            return
        
        queries = []
        
        for person_data in batch:
            try:
                # Validate and transform data
                folk_person = FolkPerson.from_folk_api(person_data, data_owner_id)
                
                # Skip if already processed
                if folk_person.folk_id in self.processed_folk_ids:
                    continue
                
                self.processed_folk_ids.add(folk_person.folk_id)
                
                # Create merge query
                person_props = folk_person.to_neo4j_node(data_owner_id)
                
                query = {
                    "query": """
                    MERGE (p:Person {folkId: $folk_id})
                    SET p += $properties
                    WITH p
                    OPTIONAL MATCH (owner:Person {folkUserId: $data_owner_id})
                    WHERE owner IS NOT NULL
                    MERGE (owner)-[:OWNS_CONTACT]->(p)
                    RETURN p.personId as person_id
                    """,
                    "parameters": {
                        "folk_id": folk_person.folk_id,
                        "properties": person_props,
                        "data_owner_id": data_owner_id
                    }
                }
                
                queries.append(query)
                
            except Exception as e:
                error_msg = f"Failed to process person {person_data.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                self.stats.validation_errors.append(error_msg)
        
        # Execute batch transaction
        if queries:
            try:
                results = await self.neo4j_client.execute_queries_in_transaction(queries)
                
                successful_queries = sum(1 for r in results if r.success)
                failed_queries = len(results) - successful_queries
                
                self.stats.people_processed += successful_queries
                self.stats.nodes_created += successful_queries
                self.stats.relationships_created += successful_queries  # OWNS_CONTACT relationships
                self.stats.transactions_executed += 1
                self.stats.neo4j_errors += failed_queries
                
                logger.info(f"Processed {successful_queries}/{len(queries)} people in batch")
                
            except Exception as e:
                self.stats.neo4j_errors += 1
                logger.error(f"Failed to execute people batch transaction: {e}")
    
    async def _process_companies(self, companies_data: List[Dict[str, Any]], data_owner_id: str):
        """Process companies data in batches"""
        
        if not companies_data:
            return
        
        logger.info(f"Processing {len(companies_data)} companies")
        
        # Process in batches
        for i in range(0, len(companies_data), self.config.batch_size):
            batch = companies_data[i:i + self.config.batch_size]
            await self._process_companies_batch(batch, data_owner_id)
    
    async def _process_companies_batch(self, batch: List[Dict[str, Any]], data_owner_id: str):
        """Process a batch of companies"""
        
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would process {len(batch)} companies")
            self.stats.companies_processed += len(batch)
            return
        
        queries = []
        
        for company_data in batch:
            try:
                # Validate and transform data
                folk_company = FolkCompany.from_folk_api(company_data)
                
                # Skip if already processed
                if folk_company.folk_id in self.processed_folk_ids:
                    continue
                
                self.processed_folk_ids.add(folk_company.folk_id)
                
                # Create merge query
                company_props = folk_company.to_neo4j_node(data_owner_id)
                
                query = {
                    "query": """
                    MERGE (o:Organization {folkId: $folk_id})
                    SET o += $properties
                    WITH o
                    OPTIONAL MATCH (owner:Person {folkUserId: $data_owner_id})
                    WHERE owner IS NOT NULL
                    MERGE (owner)-[:OWNS_CONTACT]->(o)
                    RETURN o.organizationId as org_id
                    """,
                    "parameters": {
                        "folk_id": folk_company.folk_id,
                        "properties": company_props,
                        "data_owner_id": data_owner_id
                    }
                }
                
                queries.append(query)
                
            except Exception as e:
                error_msg = f"Failed to process company {company_data.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                self.stats.validation_errors.append(error_msg)
        
        # Execute batch transaction
        if queries:
            try:
                results = await self.neo4j_client.execute_queries_in_transaction(queries)
                
                successful_queries = sum(1 for r in results if r.success)
                failed_queries = len(results) - successful_queries
                
                self.stats.companies_processed += successful_queries
                self.stats.nodes_created += successful_queries
                self.stats.relationships_created += successful_queries  # OWNS_CONTACT relationships
                self.stats.transactions_executed += 1
                self.stats.neo4j_errors += failed_queries
                
                logger.info(f"Processed {successful_queries}/{len(queries)} companies in batch")
                
            except Exception as e:
                self.stats.neo4j_errors += 1
                logger.error(f"Failed to execute companies batch transaction: {e}")
    
    async def _process_groups(self, groups_data: List[Dict[str, Any]], data_owner_id: str):
        """Process groups data"""
        
        if not groups_data:
            return
        
        logger.info(f"Processing {len(groups_data)} groups")
        
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would process {len(groups_data)} groups")
            self.stats.groups_processed += len(groups_data)
            return
        
        queries = []
        
        for group_data in groups_data:
            try:
                # Validate and transform data
                folk_group = FolkGroup.from_folk_api(group_data)
                
                # Create merge query
                group_props = folk_group.to_neo4j_node(data_owner_id)
                
                query = {
                    "query": """
                    MERGE (g:Group {folkId: $folk_id})
                    SET g += $properties
                    RETURN g.name as group_name
                    """,
                    "parameters": {
                        "folk_id": folk_group.folk_id,
                        "properties": group_props
                    }
                }
                
                queries.append(query)
                
            except Exception as e:
                error_msg = f"Failed to process group {group_data.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                self.stats.validation_errors.append(error_msg)
        
        # Execute batch transaction
        if queries:
            try:
                results = await self.neo4j_client.execute_queries_in_transaction(queries)
                
                successful_queries = sum(1 for r in results if r.success)
                failed_queries = len(results) - successful_queries
                
                self.stats.groups_processed += successful_queries
                self.stats.nodes_created += successful_queries
                self.stats.transactions_executed += 1
                self.stats.neo4j_errors += failed_queries
                
                logger.info(f"Processed {successful_queries}/{len(queries)} groups")
                
            except Exception as e:
                self.stats.neo4j_errors += 1
                logger.error(f"Failed to execute groups transaction: {e}")
    
    async def _process_custom_objects_for_groups(
        self, 
        folk_client: FolkClient, 
        groups_data: List[Dict[str, Any]],
        people_data: List[Dict[str, Any]],
        companies_data: List[Dict[str, Any]],
        data_owner_id: str
    ):
        """Process custom objects (deals, projects, etc.) for all groups using dynamic entity discovery"""
        
        logger.info(f"Discovering entity types and processing custom objects for {len(groups_data)} groups")
        
        # Discover entity types from people and companies data
        entity_types_by_group = folk_client.discover_entity_types_from_data(people_data, companies_data)
        
        if entity_types_by_group:
            self.stats.entity_types_discovered = sum(len(types) for types in entity_types_by_group.values())
            logger.info(f"Discovered {self.stats.entity_types_discovered} entity types across groups")
        
        for group_data in groups_data:
            group_id = group_data.get("id")
            group_name = group_data.get("name", "Unknown")
            
            if not group_id:
                continue
            
            # Get discovered entity types for this group, default to ["Deals"] for backward compatibility
            entity_types = entity_types_by_group.get(group_id, ["Deals"])
            
            logger.info(f"Processing entity types {entity_types} for group '{group_name}'")
            
            # Process each entity type for this group
            for entity_type in entity_types:
                try:
                    # Fetch custom objects for this group and entity type using pagination
                    custom_objects_data = await folk_client.get_all_custom_objects_paginated(
                        group_id, entity_type, page_size=100
                    )
                    
                    if custom_objects_data:
                        self.stats.custom_objects_fetched += len(custom_objects_data)
                        logger.info(f"Processing {len(custom_objects_data)} {entity_type} for group '{group_name}'")
                        
                        # Process custom objects in batches
                        for i in range(0, len(custom_objects_data), self.config.batch_size):
                            batch = custom_objects_data[i:i + self.config.batch_size]
                            await self._process_custom_objects_batch(batch, entity_type, data_owner_id)
                    
                except Exception as e:
                    error_msg = f"Failed to process {entity_type} for group {group_name}: {str(e)}"
                    
                    # Don't treat 404 as failures - they're expected for groups without that entity type
                    if "404" in str(e):
                        logger.debug(f"Group '{group_name}' has no {entity_type} (expected)")
                    else:
                        logger.error(error_msg)
                        self.stats.processing_errors.append(error_msg)
    
    async def _process_custom_objects_batch(
        self, batch: List[Dict[str, Any]], entity_type: str, data_owner_id: str
    ):
        """Process a batch of custom objects (deals, projects, opportunities, etc.)"""
        
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would process {len(batch)} {entity_type}")
            self.stats.custom_objects_processed += len(batch)
            return
        
        queries = []
        
        for custom_object_data in batch:
            try:
                # Validate and transform data using generic custom object model
                folk_custom_object = FolkCustomObject.from_folk_api(custom_object_data, entity_type)
                
                # Create merge query with relationships
                custom_object_props = folk_custom_object.to_neo4j_node(data_owner_id)
                
                # Build relationship creation queries
                relationship_queries = []
                
                # Link to contacts
                for contact_id in folk_custom_object.contact_ids:
                    if contact_id:
                        relationship_queries.append("""
                        OPTIONAL MATCH (contact:Person {folkId: $contact_id})
                        WHERE contact IS NOT NULL
                        MERGE (co)-[:WITH_CONTACT]->(contact)
                        """)
                
                # Link to companies
                for company_id in folk_custom_object.company_ids:
                    if company_id:
                        relationship_queries.append("""
                        OPTIONAL MATCH (org:Organization {folkId: $company_id})
                        WHERE org IS NOT NULL
                        MERGE (co)-[:FOR_ORGANIZATION]->(org)
                        """)
                
                # Link to data owner
                relationship_queries.append("""
                OPTIONAL MATCH (owner:Person {folkUserId: $data_owner_id})
                WHERE owner IS NOT NULL
                MERGE (owner)-[:SOURCED]->(co)
                """)
                
                relationship_cypher = "\n".join(relationship_queries)
                
                # Use dynamic label based on entity type (Deal, Project, Opportunity, etc.)
                node_label = entity_type.rstrip('s')  # Convert "Deals" -> "Deal", "Projects" -> "Project"
                
                query = {
                    "query": f"""
                    MERGE (co:{node_label} {{folkId: $folk_id}})
                    SET co += $properties
                    WITH co
                    {relationship_cypher}
                    RETURN co.name as object_name
                    """,
                    "parameters": {
                        "folk_id": folk_custom_object.folk_id,
                        "properties": custom_object_props,
                        "data_owner_id": data_owner_id
                    }
                }
                
                # Add contact and company IDs for relationship queries
                if folk_custom_object.contact_ids:
                    query["parameters"]["contact_id"] = folk_custom_object.contact_ids[0]
                if folk_custom_object.company_ids:
                    query["parameters"]["company_id"] = folk_custom_object.company_ids[0]
                
                queries.append(query)
                
            except Exception as e:
                error_msg = f"Failed to process {entity_type} {custom_object_data.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                self.stats.validation_errors.append(error_msg)
        
        # Execute batch transaction
        if queries:
            try:
                results = await self.neo4j_client.execute_queries_in_transaction(queries)
                
                successful_queries = sum(1 for r in results if r.success)
                failed_queries = len(results) - successful_queries
                
                self.stats.custom_objects_processed += successful_queries
                self.stats.nodes_created += successful_queries
                self.stats.relationships_created += successful_queries * 3  # Approximate relationship count
                self.stats.transactions_executed += 1
                self.stats.neo4j_errors += failed_queries
                
                logger.info(f"Processed {successful_queries}/{len(queries)} {entity_type} in batch")
                
            except Exception as e:
                self.stats.neo4j_errors += 1
                logger.error(f"Failed to execute {entity_type} batch transaction: {e}")


# CLI interface for direct execution
async def run_ingestion_cli():
    """Command line interface for Folk ingestion"""
    
    from .config import get_config, validate_environment
    
    print("Folk.app CRM Data Ingestion Tool")
    print("=" * 40)
    
    # Validate environment
    validation = validate_environment()
    if not validation["valid"]:
        print("❌ Environment validation failed!")
        print("Missing required variables:", validation["missing_required"])
        print("\nAdd the following to your .env file:")
        from .config import get_sample_env_file
        print(get_sample_env_file())
        return
    
    print("✅ Environment validation passed")
    
    try:
        # Load configuration
        config = get_config()
        print(f"📝 Configuration loaded ({len(config.api_keys)} API keys)")
        
        # Run ingestion
        async with FolkIngestionService(config) as service:
            print("🚀 Starting Folk data ingestion...")
            
            stats = await service.run_full_ingestion()
            
            print("\n" + "=" * 40)
            print("📊 INGESTION COMPLETED")
            print("=" * 40)
            print(f"⏱️  Duration: {stats.duration_seconds:.2f}s")
            print(f"👥 People: {stats.people_processed} processed")
            print(f"🏢 Companies: {stats.companies_processed} processed") 
            print(f"📋 Groups: {stats.groups_processed} processed")
            print(f"💼 Custom Objects: {stats.custom_objects_processed} processed ({stats.entity_types_discovered} types)")
            print(f"🔗 Relationships: {stats.relationships_created} created")
            print(f"❌ Errors: {len(stats.validation_errors) + len(stats.processing_errors)}")
            
            if stats.processing_errors:
                print("\n⚠️  Processing Errors:")
                for error in stats.processing_errors[:5]:  # Show first 5
                    print(f"   • {error}")
                if len(stats.processing_errors) > 5:
                    print(f"   ... and {len(stats.processing_errors) - 5} more")
            
            print("✅ Ingestion complete!")
            
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        logger.error(f"CLI ingestion failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_ingestion_cli())