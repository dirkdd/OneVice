"""
Neo4j Schema Manager for OneVice

Manages Neo4j database schema including constraints, indexes, and
entertainment industry-specific node and relationship definitions.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .neo4j_client import Neo4jClient, QueryResult

logger = logging.getLogger(__name__)


class SchemaOperation(Enum):
    """Schema operation types"""
    CREATE_CONSTRAINT = "create_constraint"
    DROP_CONSTRAINT = "drop_constraint"
    CREATE_INDEX = "create_index"
    DROP_INDEX = "drop_index"
    CREATE_VECTOR_INDEX = "create_vector_index"
    DROP_VECTOR_INDEX = "drop_vector_index"


@dataclass
class ConstraintDefinition:
    """Database constraint definition"""
    name: str
    node_label: str
    property: str
    constraint_type: str = "UNIQUE"
    description: str = ""


@dataclass
class IndexDefinition:
    """Database index definition"""
    name: str
    node_label: str
    properties: List[str]
    index_type: str = "BTREE"
    description: str = ""


@dataclass
class VectorIndexDefinition:
    """Vector index definition for embeddings"""
    name: str
    node_label: str
    property: str
    dimensions: int = 1536  # OpenAI embedding dimensions
    similarity_function: str = "cosine"
    description: str = ""


@dataclass 
class SchemaValidationResult:
    """Schema validation result"""
    valid: bool
    missing_constraints: List[str]
    missing_indexes: List[str]
    missing_vector_indexes: List[str]
    extra_constraints: List[str]
    extra_indexes: List[str]
    errors: List[str]
    warnings: List[str]


class SchemaManager:
    """
    OneVice Neo4j Schema Manager
    
    Manages the complete database schema for the entertainment industry
    intelligence platform including:
    
    - Core entity constraints (Person, Project, Organization, Document)
    - Vector indexes for hybrid search capabilities
    - Entertainment industry-specific relationships and properties
    - Schema validation and migration capabilities
    """
    
    def __init__(self, neo4j_client: Neo4jClient):
        """Initialize schema manager with Neo4j client"""
        
        self.client = neo4j_client
        self._define_core_schema()
        
        logger.info("Schema manager initialized")
    
    def _define_core_schema(self):
        """Define core schema components for OneVice"""
        
        # Core entity constraints
        self.core_constraints = [
            ConstraintDefinition(
                name="person_id_unique",
                node_label="Person",
                property="id",
                description="Unique identifier for person entities"
            ),
            ConstraintDefinition(
                name="project_id_unique", 
                node_label="Project",
                property="id",
                description="Unique identifier for project entities"
            ),
            ConstraintDefinition(
                name="organization_id_unique",
                node_label="Organization", 
                property="id",
                description="Unique identifier for organization entities"
            ),
            ConstraintDefinition(
                name="document_id_unique",
                node_label="Document",
                property="id", 
                description="Unique identifier for document entities"
            ),
            # Folk.app CRM constraints  
            ConstraintDefinition(
                name="group_folk_id_unique",
                node_label="Group",
                property="folkId",
                description="Unique Folk ID for group entities"
            ),
            ConstraintDefinition(
                name="deal_folk_id_unique",
                node_label="Deal",
                property="folkId", 
                description="Unique Folk ID for deal entities"
            ),
            ConstraintDefinition(
                name="opportunity_folk_id_unique",
                node_label="Opportunity",
                property="folkId",
                description="Unique Folk ID for opportunity entities" 
            ),
            # Additional constraints for data integrity
            ConstraintDefinition(
                name="person_email_unique",
                node_label="Person",
                property="email",
                description="Unique email addresses for persons"
            ),
            ConstraintDefinition(
                name="person_folk_id_unique",
                node_label="Person",
                property="folkId",
                description="Unique Folk ID for person entities"
            ),
            ConstraintDefinition(
                name="organization_name_unique",
                node_label="Organization",
                property="name",
                description="Unique organization names"
            ),
            ConstraintDefinition(
                name="organization_folk_id_unique",
                node_label="Organization",
                property="folkId",
                description="Unique Folk ID for organization entities"
            )
        ]
        
        # Traditional indexes for performance
        self.core_indexes = [
            IndexDefinition(
                name="person_name_index",
                node_label="Person",
                properties=["name"],
                description="Full-text search on person names"
            ),
            IndexDefinition(
                name="person_role_index", 
                node_label="Person",
                properties=["role"],
                description="Index on person roles (Director, Creative Director, etc.)"
            ),
            IndexDefinition(
                name="project_name_index",
                node_label="Project",
                properties=["name"],
                description="Full-text search on project names"
            ),
            IndexDefinition(
                name="project_type_index",
                node_label="Project", 
                properties=["type"],
                description="Index on project types (Music Video, Commercial, etc.)"
            ),
            IndexDefinition(
                name="project_status_index",
                node_label="Project",
                properties=["status"],
                description="Index on project status"
            ),
            IndexDefinition(
                name="organization_type_index",
                node_label="Organization",
                properties=["type"],
                description="Index on organization types (Agency, Production Company, etc.)"
            ),
            IndexDefinition(
                name="document_type_index",
                node_label="Document",
                properties=["type"],
                description="Index on document types (Script, Treatment, etc.)"
            ),
            IndexDefinition(
                name="document_created_index",
                node_label="Document", 
                properties=["created_at"],
                description="Index on document creation dates"
            ),
            # Folk.app CRM indexes
            IndexDefinition(
                name="group_name_index",
                node_label="Group",
                properties=["name"],
                description="Index on Folk group names"
            ),
            IndexDefinition(
                name="deal_name_index",
                node_label="Deal",
                properties=["name"],
                description="Index on Folk deal names"
            ),
            IndexDefinition(
                name="deal_status_index",
                node_label="Deal",
                properties=["status"],
                description="Index on Folk deal status"
            ),
            IndexDefinition(
                name="opportunity_name_index",
                node_label="Opportunity",
                properties=["name"],
                description="Index on Folk opportunity names"
            ),
            IndexDefinition(
                name="custom_object_entity_type_index",
                node_label="CustomObject",
                properties=["entityType"],
                description="Index on custom object entity types"
            )
        ]
        
        # Vector indexes for hybrid search
        self.vector_indexes = [
            VectorIndexDefinition(
                name="person_bio_vector",
                node_label="Person",
                property="bio_embedding",
                dimensions=1536,
                similarity_function="cosine",
                description="Vector index for person bio embeddings"
            ),
            VectorIndexDefinition(
                name="project_concept_vector",
                node_label="Project", 
                property="concept_embedding",
                dimensions=1536,
                similarity_function="cosine",
                description="Vector index for project concept embeddings"
            ),
            VectorIndexDefinition(
                name="document_content_vector",
                node_label="Document",
                property="content_embedding", 
                dimensions=1536,
                similarity_function="cosine",
                description="Vector index for document content embeddings"
            ),
            VectorIndexDefinition(
                name="creative_concept_vector",
                node_label="CreativeConcept",
                property="description_embedding",
                dimensions=1536, 
                similarity_function="cosine",
                description="Vector index for creative concept embeddings"
            )
        ]
        
        # Entertainment industry schema relationships
        self.relationship_definitions = {
            "WORKS_FOR": {
                "description": "Person works for Organization",
                "properties": ["role", "start_date", "end_date", "is_active"]
            },
            "DIRECTED": {
                "description": "Person directed Project", 
                "properties": ["role_type", "project_phase", "credit_order"]
            },
            "PRODUCED": {
                "description": "Person or Organization produced Project",
                "properties": ["producer_type", "credit_order", "financial_stake"]
            },
            "WORKED_ON": {
                "description": "Person worked on Project in any capacity",
                "properties": ["role", "department", "credit_order", "union_status"]
            },
            "REPRESENTS": {
                "description": "Organization represents Person (talent agency)",
                "properties": ["representation_type", "start_date", "end_date", "is_active"]
            },
            "COLLABORATED_WITH": {
                "description": "Person collaborated with Person on projects",
                "properties": ["collaboration_count", "project_types", "last_collaboration"]
            },
            "PART_OF": {
                "description": "Project is part of larger Project or campaign",
                "properties": ["relationship_type", "sequence_order"]
            },
            "CREATED_FOR": {
                "description": "Project was created for Organization (client)",
                "properties": ["project_phase", "budget_range", "deliverables"]
            },
            "ATTACHED_TO": {
                "description": "Document is attached to Project",
                "properties": ["document_phase", "version", "is_final", "approval_status"]
            },
            "SIMILAR_TO": {
                "description": "AI-generated similarity between entities",
                "properties": ["similarity_score", "similarity_type", "calculated_at"]
            },
            # Folk.app CRM relationships
            "OWNS_CONTACT": {
                "description": "Person owns contact (data provenance)",
                "properties": ["imported_at", "source_system", "last_synced"]
            },
            "SOURCED": {
                "description": "Person sourced custom object (deal, opportunity)",
                "properties": ["sourced_at", "source_system", "last_updated"]
            },
            "WITH_CONTACT": {
                "description": "Custom object associated with contact",
                "properties": ["role_in_object", "primary_contact", "added_at"]
            },
            "FOR_ORGANIZATION": {
                "description": "Custom object for organization",
                "properties": ["relationship_type", "started_at", "is_active"]
            },
            "BELONGS_TO_GROUP": {
                "description": "Entity belongs to Folk group",
                "properties": ["added_at", "group_role", "is_active"]
            }
        }
    
    async def create_folk_custom_object_constraint(self, entity_type: str) -> bool:
        """
        Create constraint for a new Folk custom object entity type
        
        Args:
            entity_type: The entity type (e.g., 'Deal', 'Project', 'Opportunity')
            
        Returns:
            bool: True if constraint created successfully
        """
        
        try:
            constraint_name = f"{entity_type.lower()}_folk_id_unique"
            
            cypher = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{entity_type}) 
            REQUIRE n.folkId IS UNIQUE
            """
            
            result = await self.client.execute_query(cypher)
            
            if result.success:
                logger.info(f"Created constraint for {entity_type}: {constraint_name}")
                return True
            else:
                logger.error(f"Failed to create constraint for {entity_type}: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Exception creating constraint for {entity_type}: {e}")
            return False
    
    async def create_folk_custom_object_indexes(self, entity_type: str) -> Dict[str, bool]:
        """
        Create indexes for a new Folk custom object entity type
        
        Args:
            entity_type: The entity type (e.g., 'Deal', 'Project', 'Opportunity')
            
        Returns:
            Dict[str, bool]: Results for each index creation
        """
        
        results = {}
        
        indexes = [
            {
                "name": f"{entity_type.lower()}_name_index",
                "properties": ["name"]
            },
            {
                "name": f"{entity_type.lower()}_entity_type_index", 
                "properties": ["entityType"]
            },
            {
                "name": f"{entity_type.lower()}_created_index",
                "properties": ["createdAt"]
            }
        ]
        
        for index_config in indexes:
            try:
                properties_str = ", ".join([f"n.{prop}" for prop in index_config["properties"]])
                
                cypher = f"""
                CREATE INDEX {index_config["name"]} IF NOT EXISTS
                FOR (n:{entity_type})
                ON ({properties_str})
                """
                
                result = await self.client.execute_query(cypher)
                
                if result.success:
                    results[index_config["name"]] = True
                    logger.debug(f"Created index: {index_config['name']}")
                else:
                    results[index_config["name"]] = False
                    logger.error(f"Failed to create index {index_config['name']}: {result.error}")
                    
            except Exception as e:
                results[index_config["name"]] = False
                logger.error(f"Exception creating index {index_config['name']}: {e}")
        
        return results
    
    async def ensure_folk_custom_object_schema(self, entity_types: List[str]) -> Dict[str, Any]:
        """
        Ensure schema elements exist for all discovered Folk custom object entity types
        
        Args:
            entity_types: List of entity types to ensure (e.g., ['Deal', 'Project', 'Opportunity'])
            
        Returns:
            Dict with results for each entity type
        """
        
        results = {
            "entity_types_processed": [],
            "constraints_created": 0,
            "indexes_created": 0,
            "errors": []
        }
        
        for entity_type in entity_types:
            try:
                # Create constraint
                constraint_success = await self.create_folk_custom_object_constraint(entity_type)
                if constraint_success:
                    results["constraints_created"] += 1
                
                # Create indexes
                index_results = await self.create_folk_custom_object_indexes(entity_type)
                successful_indexes = sum(1 for success in index_results.values() if success)
                results["indexes_created"] += successful_indexes
                
                # Track processed types
                results["entity_types_processed"].append(entity_type)
                
                logger.info(f"Ensured schema for Folk custom object type: {entity_type}")
                
            except Exception as e:
                error_msg = f"Failed to ensure schema for {entity_type}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results

    async def create_core_schema(self) -> Dict[str, Any]:
        """
        Create complete core schema with constraints and indexes
        
        Returns:
            Dict with creation results and performance metrics
        """
        
        logger.info("Creating OneVice core schema...")
        start_time = time.time()
        
        results = {
            "constraints": {"created": 0, "failed": 0, "errors": []},
            "indexes": {"created": 0, "failed": 0, "errors": []},
            "vector_indexes": {"created": 0, "failed": 0, "errors": []},
            "execution_time": 0,
            "success": False
        }
        
        try:
            # Create constraints
            logger.info("Creating database constraints...")
            constraint_results = await self._create_constraints()
            results["constraints"] = constraint_results
            
            # Create traditional indexes  
            logger.info("Creating database indexes...")
            index_results = await self._create_indexes()
            results["indexes"] = index_results
            
            # Create vector indexes
            logger.info("Creating vector indexes...")
            vector_results = await self._create_vector_indexes()
            results["vector_indexes"] = vector_results
            
            results["execution_time"] = time.time() - start_time
            results["success"] = (
                constraint_results["failed"] == 0 and
                index_results["failed"] == 0 and
                vector_results["failed"] == 0
            )
            
            if results["success"]:
                logger.info(f"Core schema created successfully in {results['execution_time']:.2f}s")
            else:
                logger.warning("Core schema creation completed with some failures")
                
            return results
            
        except Exception as e:
            logger.error(f"Failed to create core schema: {e}")
            results["execution_time"] = time.time() - start_time
            results["error"] = str(e)
            return results
    
    async def _create_constraints(self) -> Dict[str, Any]:
        """Create all database constraints"""
        
        results = {"created": 0, "failed": 0, "errors": []}
        
        for constraint in self.core_constraints:
            try:
                cypher = f"""
                CREATE CONSTRAINT {constraint.name} 
                FOR (n:{constraint.node_label}) 
                REQUIRE n.{constraint.property} IS {constraint.constraint_type}
                """
                
                result = await self.client.execute_query(cypher)
                
                if result.success:
                    results["created"] += 1
                    logger.debug(f"Created constraint: {constraint.name}")
                else:
                    results["failed"] += 1
                    error_msg = f"Failed to create constraint {constraint.name}: {result.error}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Exception creating constraint {constraint.name}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    async def _create_indexes(self) -> Dict[str, Any]:
        """Create all traditional database indexes"""
        
        results = {"created": 0, "failed": 0, "errors": []}
        
        for index in self.core_indexes:
            try:
                properties_str = ", ".join([f"n.{prop}" for prop in index.properties])
                
                cypher = f"""
                CREATE INDEX {index.name}
                FOR (n:{index.node_label})
                ON ({properties_str})
                """
                
                result = await self.client.execute_query(cypher)
                
                if result.success:
                    results["created"] += 1
                    logger.debug(f"Created index: {index.name}")
                else:
                    results["failed"] += 1
                    error_msg = f"Failed to create index {index.name}: {result.error}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Exception creating index {index.name}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    async def _create_vector_indexes(self) -> Dict[str, Any]:
        """Create all vector indexes for embeddings"""
        
        results = {"created": 0, "failed": 0, "errors": []}
        
        for vector_index in self.vector_indexes:
            try:
                cypher = f"""
                CREATE VECTOR INDEX {vector_index.name}
                FOR (n:{vector_index.node_label}) 
                ON n.{vector_index.property}
                OPTIONS {{
                  indexConfig: {{
                    `vector.dimensions`: {vector_index.dimensions},
                    `vector.similarity_function`: '{vector_index.similarity_function}'
                  }}
                }}
                """
                
                result = await self.client.execute_query(cypher)
                
                if result.success:
                    results["created"] += 1
                    logger.debug(f"Created vector index: {vector_index.name}")
                else:
                    results["failed"] += 1
                    error_msg = f"Failed to create vector index {vector_index.name}: {result.error}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                results["failed"] += 1 
                error_msg = f"Exception creating vector index {vector_index.name}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    async def validate_schema(self) -> SchemaValidationResult:
        """
        Validate current database schema against expected schema
        
        Returns:
            SchemaValidationResult with detailed validation information
        """
        
        logger.info("Validating database schema...")
        
        try:
            # Get current database schema
            current_constraints = await self._get_current_constraints()
            current_indexes = await self._get_current_indexes() 
            current_vector_indexes = await self._get_current_vector_indexes()
            
            # Compare against expected schema
            expected_constraints = {c.name for c in self.core_constraints}
            expected_indexes = {i.name for i in self.core_indexes}
            expected_vector_indexes = {v.name for v in self.vector_indexes}
            
            # Find missing and extra schema elements
            missing_constraints = expected_constraints - current_constraints
            missing_indexes = expected_indexes - current_indexes  
            missing_vector_indexes = expected_vector_indexes - current_vector_indexes
            
            extra_constraints = current_constraints - expected_constraints
            extra_indexes = current_indexes - expected_indexes
            
            # Determine if schema is valid
            valid = (
                len(missing_constraints) == 0 and
                len(missing_indexes) == 0 and
                len(missing_vector_indexes) == 0
            )
            
            result = SchemaValidationResult(
                valid=valid,
                missing_constraints=list(missing_constraints),
                missing_indexes=list(missing_indexes),
                missing_vector_indexes=list(missing_vector_indexes),
                extra_constraints=list(extra_constraints), 
                extra_indexes=list(extra_indexes),
                errors=[],
                warnings=[]
            )
            
            # Add warnings for extra schema elements
            if extra_constraints:
                result.warnings.append(f"Found {len(extra_constraints)} unexpected constraints")
            if extra_indexes:
                result.warnings.append(f"Found {len(extra_indexes)} unexpected indexes")
            
            logger.info(f"Schema validation completed. Valid: {valid}")
            return result
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return SchemaValidationResult(
                valid=False,
                missing_constraints=[],
                missing_indexes=[],
                missing_vector_indexes=[],
                extra_constraints=[],
                extra_indexes=[],
                errors=[str(e)],
                warnings=[]
            )
    
    async def _get_current_constraints(self) -> set:
        """Get current database constraints"""
        
        result = await self.client.execute_query("SHOW CONSTRAINTS")
        
        if result.success:
            return {record.get("name", "") for record in result.records}
        else:
            logger.error(f"Failed to fetch constraints: {result.error}")
            return set()
    
    async def _get_current_indexes(self) -> set:
        """Get current database indexes (excluding vector indexes)"""
        
        result = await self.client.execute_query("SHOW INDEXES")
        
        if result.success:
            # Filter out vector indexes
            regular_indexes = {
                record.get("name", "") 
                for record in result.records 
                if record.get("type", "") != "VECTOR"
            }
            return regular_indexes
        else:
            logger.error(f"Failed to fetch indexes: {result.error}")
            return set()
    
    async def _get_current_vector_indexes(self) -> set:
        """Get current vector indexes"""
        
        result = await self.client.execute_query("SHOW INDEXES")
        
        if result.success:
            # Filter for vector indexes only
            vector_indexes = {
                record.get("name", "") 
                for record in result.records 
                if record.get("type", "") == "VECTOR"
            }
            return vector_indexes
        else:
            logger.error(f"Failed to fetch vector indexes: {result.error}")
            return set()
    
    async def drop_schema(self) -> Dict[str, Any]:
        """
        Drop all schema elements (USE WITH CAUTION)
        
        Returns:
            Dict with drop operation results
        """
        
        logger.warning("Dropping entire database schema...")
        start_time = time.time()
        
        results = {
            "constraints_dropped": 0,
            "indexes_dropped": 0, 
            "vector_indexes_dropped": 0,
            "execution_time": 0,
            "errors": []
        }
        
        try:
            # Drop all constraints
            current_constraints = await self._get_current_constraints()
            for constraint_name in current_constraints:
                try:
                    result = await self.client.execute_query(f"DROP CONSTRAINT {constraint_name}")
                    if result.success:
                        results["constraints_dropped"] += 1
                except Exception as e:
                    results["errors"].append(f"Failed to drop constraint {constraint_name}: {str(e)}")
            
            # Drop all indexes (including vector indexes)
            current_indexes = await self._get_current_indexes()
            current_vector_indexes = await self._get_current_vector_indexes()
            all_indexes = current_indexes.union(current_vector_indexes)
            
            for index_name in all_indexes:
                try:
                    result = await self.client.execute_query(f"DROP INDEX {index_name}")
                    if result.success:
                        if index_name in current_vector_indexes:
                            results["vector_indexes_dropped"] += 1
                        else:
                            results["indexes_dropped"] += 1
                except Exception as e:
                    results["errors"].append(f"Failed to drop index {index_name}: {str(e)}")
            
            results["execution_time"] = time.time() - start_time
            logger.warning(f"Schema dropped in {results['execution_time']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to drop schema: {e}")
            results["execution_time"] = time.time() - start_time
            results["errors"].append(str(e))
            return results
    
    def get_schema_documentation(self) -> Dict[str, Any]:
        """
        Generate comprehensive schema documentation
        
        Returns:
            Dict with complete schema documentation
        """
        
        return {
            "version": "1.0",
            "description": "OneVice Entertainment Industry Intelligence Platform Schema",
            "constraints": [
                {
                    "name": c.name,
                    "node_label": c.node_label,
                    "property": c.property,
                    "type": c.constraint_type,
                    "description": c.description
                }
                for c in self.core_constraints
            ],
            "indexes": [
                {
                    "name": i.name,
                    "node_label": i.node_label,
                    "properties": i.properties,
                    "type": i.index_type,
                    "description": i.description
                }
                for i in self.core_indexes
            ],
            "vector_indexes": [
                {
                    "name": v.name,
                    "node_label": v.node_label,
                    "property": v.property,
                    "dimensions": v.dimensions,
                    "similarity_function": v.similarity_function,
                    "description": v.description
                }
                for v in self.vector_indexes
            ],
            "relationships": self.relationship_definitions,
            "node_labels": [
                "Person", "Project", "Organization", "Document", "CreativeConcept",
                "Group", "Deal", "Opportunity", "CustomObject"
            ],
            "entertainment_industry_roles": [
                "Director", "Creative Director", "Producer", "Executive Producer",
                "Cinematographer", "Editor", "Composer", "Production Designer"
            ],
            "project_types": [
                "Music Video", "Commercial", "Feature Film", "Documentary",
                "Short Film", "Web Series", "Television"
            ]
        }