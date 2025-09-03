"""
Entertainment Industry Schema

Defines Neo4j schema for entertainment industry knowledge graph
including nodes, relationships, and vector indexes.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

from .connection import Neo4jClient

logger = logging.getLogger(__name__)

class NodeLabel(str, Enum):
    """Entertainment industry node labels"""
    PERSON = "Person"
    PROJECT = "Project"  
    COMPANY = "Company"
    LOCATION = "Location"
    SKILL = "Skill"
    EQUIPMENT = "Equipment"
    UNION = "Union"
    ROLE = "Role"
    CLIENT = "Client"
    GENRE = "Genre"

class RelationshipType(str, Enum):
    """Entertainment industry relationship types"""
    WORKED_ON = "WORKED_ON"
    DIRECTED = "DIRECTED"
    PRODUCED = "PRODUCED"
    EDITED = "EDITED"
    FILMED = "FILMED"
    EMPLOYED_BY = "EMPLOYED_BY"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    LOCATED_IN = "LOCATED_IN"
    HAS_SKILL = "HAS_SKILL"
    OWNS_EQUIPMENT = "OWNS_EQUIPMENT"
    MEMBER_OF = "MEMBER_OF"
    PLAYED_ROLE = "PLAYED_ROLE"
    HIRED_BY = "HIRED_BY"
    BELONGS_TO_GENRE = "BELONGS_TO_GENRE"
    SIMILAR_TO = "SIMILAR_TO"

class EntertainmentSchema:
    """
    Entertainment industry Neo4j schema manager
    """
    
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client
        
    async def initialize_schema(self) -> bool:
        """Initialize complete entertainment industry schema"""
        
        try:
            # Create constraints and indexes
            await self._create_constraints()
            await self._create_indexes()
            await self._create_vector_indexes()
            
            logger.info("Entertainment schema initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            return False

    async def _create_constraints(self) -> None:
        """Create uniqueness constraints"""
        
        constraints = [
            # Person constraints
            f"CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:{NodeLabel.PERSON}) REQUIRE p.id IS UNIQUE",
            f"CREATE CONSTRAINT person_email_unique IF NOT EXISTS FOR (p:{NodeLabel.PERSON}) REQUIRE p.email IS UNIQUE",
            
            # Project constraints  
            f"CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:{NodeLabel.PROJECT}) REQUIRE p.id IS UNIQUE",
            
            # Company constraints
            f"CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:{NodeLabel.COMPANY}) REQUIRE c.id IS UNIQUE",
            f"CREATE CONSTRAINT company_name_unique IF NOT EXISTS FOR (c:{NodeLabel.COMPANY}) REQUIRE c.name IS UNIQUE",
            
            # Location constraints
            f"CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:{NodeLabel.LOCATION}) REQUIRE l.id IS UNIQUE",
            
            # Union constraints
            f"CREATE CONSTRAINT union_code_unique IF NOT EXISTS FOR (u:{NodeLabel.UNION}) REQUIRE u.code IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                await self.neo4j.run_write_query(constraint)
                logger.debug(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint creation failed: {e}")

    async def _create_indexes(self) -> None:
        """Create performance indexes"""
        
        indexes = [
            # Person indexes
            f"CREATE INDEX person_name IF NOT EXISTS FOR (p:{NodeLabel.PERSON}) ON (p.name)",
            f"CREATE INDEX person_skills IF NOT EXISTS FOR (p:{NodeLabel.PERSON}) ON (p.skills)",
            f"CREATE INDEX person_location IF NOT EXISTS FOR (p:{NodeLabel.PERSON}) ON (p.location)",
            f"CREATE INDEX person_union_status IF NOT EXISTS FOR (p:{NodeLabel.PERSON}) ON (p.union_status)",
            
            # Project indexes
            f"CREATE INDEX project_name IF NOT EXISTS FOR (p:{NodeLabel.PROJECT}) ON (p.name)",
            f"CREATE INDEX project_type IF NOT EXISTS FOR (p:{NodeLabel.PROJECT}) ON (p.type)",
            f"CREATE INDEX project_status IF NOT EXISTS FOR (p:{NodeLabel.PROJECT}) ON (p.status)",
            f"CREATE INDEX project_date IF NOT EXISTS FOR (p:{NodeLabel.PROJECT}) ON (p.date)",
            f"CREATE INDEX project_budget IF NOT EXISTS FOR (p:{NodeLabel.PROJECT}) ON (p.budget)",
            
            # Company indexes  
            f"CREATE INDEX company_name IF NOT EXISTS FOR (c:{NodeLabel.COMPANY}) ON (c.name)",
            f"CREATE INDEX company_type IF NOT EXISTS FOR (c:{NodeLabel.COMPANY}) ON (c.type)",
            f"CREATE INDEX company_location IF NOT EXISTS FOR (c:{NodeLabel.COMPANY}) ON (c.location)",
            
            # Equipment indexes
            f"CREATE INDEX equipment_type IF NOT EXISTS FOR (e:{NodeLabel.EQUIPMENT}) ON (e.type)",
            f"CREATE INDEX equipment_availability IF NOT EXISTS FOR (e:{NodeLabel.EQUIPMENT}) ON (e.available)",
        ]
        
        for index in indexes:
            try:
                await self.neo4j.run_write_query(index)
                logger.debug(f"Created index: {index}")
            except Exception as e:
                logger.warning(f"Index creation failed: {e}")

    async def _create_vector_indexes(self) -> None:
        """Create vector indexes for semantic search"""
        
        vector_indexes = [
            {
                "name": "person_bio_vector",
                "label": NodeLabel.PERSON,
                "property": "bio_embedding",
                "dimensions": 1536  # OpenAI embedding dimension
            },
            {
                "name": "project_description_vector", 
                "label": NodeLabel.PROJECT,
                "property": "description_embedding",
                "dimensions": 1536
            },
            {
                "name": "company_description_vector",
                "label": NodeLabel.COMPANY,
                "property": "description_embedding", 
                "dimensions": 1536
            }
        ]
        
        for index_config in vector_indexes:
            try:
                success = await self.neo4j.create_vector_index(**index_config)
                if success:
                    logger.debug(f"Created vector index: {index_config['name']}")
            except Exception as e:
                logger.warning(f"Vector index creation failed: {e}")

    async def create_sample_data(self) -> bool:
        """Create sample entertainment industry data"""
        
        try:
            # Sample people
            await self._create_sample_people()
            
            # Sample companies
            await self._create_sample_companies()
            
            # Sample projects
            await self._create_sample_projects()
            
            # Sample relationships
            await self._create_sample_relationships()
            
            logger.info("Sample data created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Sample data creation failed: {e}")
            return False

    async def _create_sample_people(self) -> None:
        """Create sample person nodes"""
        
        sample_people = [
            {
                "id": "person_001",
                "name": "Alex Rodriguez",
                "email": "alex.rodriguez@example.com",
                "role": "Director",
                "skills": ["directing", "cinematography", "editing"],
                "experience_years": 12,
                "location": "Los Angeles, CA",
                "union_status": ["DGA"],
                "day_rate": 2500,
                "bio": "Award-winning director specializing in music videos and commercials with over 12 years of experience."
            },
            {
                "id": "person_002", 
                "name": "Maria Santos",
                "email": "maria.santos@example.com",
                "role": "Producer",
                "skills": ["producing", "project_management", "budgeting"],
                "experience_years": 8,
                "location": "New York, NY",
                "union_status": ["PGA"],
                "day_rate": 1800,
                "bio": "Creative producer with extensive experience in commercial and music video production."
            },
            {
                "id": "person_003",
                "name": "David Kim",
                "email": "david.kim@example.com", 
                "role": "Cinematographer",
                "skills": ["cinematography", "lighting", "camera_operation"],
                "experience_years": 15,
                "location": "Los Angeles, CA",
                "union_status": ["IATSE_600"],
                "day_rate": 2200,
                "bio": "Master cinematographer known for innovative lighting techniques and visual storytelling."
            }
        ]
        
        for person in sample_people:
            query = f"""
            CREATE (p:{NodeLabel.PERSON} {{
                id: $id,
                name: $name,
                email: $email,
                role: $role,
                skills: $skills,
                experience_years: $experience_years,
                location: $location,
                union_status: $union_status,
                day_rate: $day_rate,
                bio: $bio,
                created_at: datetime(),
                updated_at: datetime()
            }})
            """
            await self.neo4j.run_write_query(query, person)

    async def _create_sample_companies(self) -> None:
        """Create sample company nodes"""
        
        sample_companies = [
            {
                "id": "company_001",
                "name": "Stellar Productions",
                "type": "Production Company",
                "location": "Los Angeles, CA",
                "size": "Medium",
                "specialties": ["music_videos", "commercials"],
                "description": "Leading production company specializing in music videos and high-end commercials."
            },
            {
                "id": "company_002",
                "name": "Creative Vision Studios", 
                "type": "Post Production",
                "location": "New York, NY",
                "size": "Large",
                "specialties": ["editing", "color_grading", "sound_design"],
                "description": "Full-service post-production facility with state-of-the-art equipment."
            }
        ]
        
        for company in sample_companies:
            query = f"""
            CREATE (c:{NodeLabel.COMPANY} {{
                id: $id,
                name: $name,
                type: $type,
                location: $location,
                size: $size,
                specialties: $specialties,
                description: $description,
                created_at: datetime(),
                updated_at: datetime()
            }})
            """
            await self.neo4j.run_write_query(query, company)

    async def _create_sample_projects(self) -> None:
        """Create sample project nodes"""
        
        sample_projects = [
            {
                "id": "project_001",
                "name": "Summer Vibes Music Video",
                "type": "Music Video",
                "status": "Completed",
                "date": "2024-06-15",
                "budget": 75000,
                "client": "Major Record Label",
                "location": "Miami, FL",
                "description": "High-energy music video featuring tropical locations and dynamic cinematography."
            },
            {
                "id": "project_002",
                "name": "Tech Company Commercial",
                "type": "Commercial", 
                "status": "In Production",
                "date": "2024-09-01",
                "budget": 150000,
                "client": "TechCorp Inc",
                "location": "San Francisco, CA",
                "description": "Corporate commercial showcasing innovative technology solutions."
            }
        ]
        
        for project in sample_projects:
            query = f"""
            CREATE (p:{NodeLabel.PROJECT} {{
                id: $id,
                name: $name,
                type: $type,
                status: $status,
                date: date($date),
                budget: $budget,
                client: $client,
                location: $location,
                description: $description,
                created_at: datetime(),
                updated_at: datetime()
            }})
            """
            await self.neo4j.run_write_query(query, project)

    async def _create_sample_relationships(self) -> None:
        """Create sample relationships"""
        
        relationships = [
            # Person-Project relationships
            {
                "query": f"""
                MATCH (p:{NodeLabel.PERSON} {{id: 'person_001'}}), (proj:{NodeLabel.PROJECT} {{id: 'project_001'}})
                CREATE (p)-[:{RelationshipType.DIRECTED} {{
                    role: 'Director',
                    start_date: date('2024-05-01'),
                    end_date: date('2024-06-15'),
                    day_rate: 2500
                }}]->(proj)
                """
            },
            {
                "query": f"""
                MATCH (p:{NodeLabel.PERSON} {{id: 'person_002'}}), (proj:{NodeLabel.PROJECT} {{id: 'project_001'}})
                CREATE (p)-[:{RelationshipType.PRODUCED} {{
                    role: 'Producer',
                    start_date: date('2024-04-15'),
                    end_date: date('2024-06-30'),
                    day_rate: 1800
                }}]->(proj)
                """
            },
            # Person-Company relationships
            {
                "query": f"""
                MATCH (p:{NodeLabel.PERSON} {{id: 'person_001'}}), (c:{NodeLabel.COMPANY} {{id: 'company_001'}})
                CREATE (p)-[:{RelationshipType.COLLABORATES_WITH} {{
                    relationship_type: 'Frequent Collaborator',
                    since: date('2020-01-01'),
                    projects_count: 15
                }}]->(c)
                """
            }
        ]
        
        for rel in relationships:
            await self.neo4j.run_write_query(rel["query"])

    async def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information and statistics"""
        
        try:
            # Get node counts by label
            node_counts_query = """
            CALL db.labels() YIELD label
            CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {})
            YIELD value
            RETURN label, value.count as count
            """
            
            try:
                node_counts = await self.neo4j.run_query(node_counts_query)
            except:
                # Fallback without APOC
                node_counts = []
                for label in NodeLabel:
                    try:
                        result = await self.neo4j.run_query(f"MATCH (n:{label.value}) RETURN count(n) as count")
                        if result:
                            node_counts.append({"label": label.value, "count": result[0]["count"]})
                    except:
                        continue
            
            # Get relationship counts
            rel_counts_query = """
            CALL db.relationshipTypes() YIELD relationshipType
            CALL apoc.cypher.run('MATCH ()-[r:' + relationshipType + ']->() RETURN count(r) as count', {})
            YIELD value  
            RETURN relationshipType, value.count as count
            """
            
            try:
                rel_counts = await self.neo4j.run_query(rel_counts_query)
            except:
                # Fallback without APOC
                rel_counts = []
            
            # Get indexes
            indexes_query = "SHOW INDEXES"
            try:
                indexes = await self.neo4j.run_query(indexes_query)
            except:
                indexes = []
            
            # Get constraints
            constraints_query = "SHOW CONSTRAINTS"
            try:
                constraints = await self.neo4j.run_query(constraints_query)
            except:
                constraints = []
            
            return {
                "node_labels": [label.value for label in NodeLabel],
                "relationship_types": [rel.value for rel in RelationshipType],
                "node_counts": node_counts,
                "relationship_counts": rel_counts,
                "indexes": indexes,
                "constraints": constraints,
                "vector_indexes": [
                    "person_bio_vector",
                    "project_description_vector", 
                    "company_description_vector"
                ]
            }
            
        except Exception as e:
            logger.error(f"Schema info retrieval failed: {e}")
            return {"error": str(e)}

    async def validate_schema(self) -> Dict[str, Any]:
        """Validate schema integrity"""
        
        validation_results = {
            "constraints": {"passed": 0, "failed": 0, "errors": []},
            "indexes": {"passed": 0, "failed": 0, "errors": []},
            "data_quality": {"passed": 0, "failed": 0, "errors": []}
        }
        
        try:
            # Validate constraints
            for label in NodeLabel:
                try:
                    # Check for duplicate IDs
                    duplicate_query = f"""
                    MATCH (n:{label.value})
                    WITH n.id as id, count(*) as count
                    WHERE count > 1
                    RETURN id, count
                    """
                    duplicates = await self.neo4j.run_query(duplicate_query)
                    
                    if duplicates:
                        validation_results["constraints"]["failed"] += 1
                        validation_results["constraints"]["errors"].append(
                            f"Duplicate IDs found in {label.value}: {duplicates}"
                        )
                    else:
                        validation_results["constraints"]["passed"] += 1
                        
                except Exception as e:
                    validation_results["constraints"]["failed"] += 1
                    validation_results["constraints"]["errors"].append(
                        f"Constraint validation failed for {label.value}: {e}"
                    )
            
            # Validate data quality
            quality_checks = [
                {
                    "name": "People with valid emails",
                    "query": f"MATCH (p:{NodeLabel.PERSON}) WHERE p.email =~ '.+@.+\\..+' RETURN count(p) as valid_count"
                },
                {
                    "name": "Projects with valid dates", 
                    "query": f"MATCH (p:{NodeLabel.PROJECT}) WHERE p.date IS NOT NULL RETURN count(p) as valid_count"
                }
            ]
            
            for check in quality_checks:
                try:
                    result = await self.neo4j.run_query(check["query"])
                    if result and result[0]["valid_count"] > 0:
                        validation_results["data_quality"]["passed"] += 1
                    else:
                        validation_results["data_quality"]["failed"] += 1
                        validation_results["data_quality"]["errors"].append(
                            f"Data quality check failed: {check['name']}"
                        )
                except Exception as e:
                    validation_results["data_quality"]["failed"] += 1
                    validation_results["data_quality"]["errors"].append(
                        f"Data quality check error for {check['name']}: {e}"
                    )
            
            validation_results["overall_status"] = "passed" if (
                validation_results["constraints"]["failed"] == 0 and
                validation_results["data_quality"]["failed"] == 0
            ) else "failed"
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return {
                "overall_status": "error",
                "error": str(e)
            }