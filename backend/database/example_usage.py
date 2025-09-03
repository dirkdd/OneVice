#!/usr/bin/env python3
"""
OneVice Database Usage Examples

Demonstrates how to use the OneVice database schema implementation
for common entertainment industry queries and operations.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database import initialize_database, ConnectionConfig


async def example_person_queries(connection_manager):
    """Examples of person-related queries"""
    
    print("\n🎬 Person Query Examples")
    print("-" * 50)
    
    # Create sample person data
    create_person_query = """
    MERGE (p:Person {id: $id})
    SET p.name = $name,
        p.role = $role,
        p.bio = $bio,
        p.email = $email,
        p.created_at = datetime(),
        p.updated_at = datetime()
    RETURN p
    """
    
    sample_people = [
        {
            "id": "dir_ridley_scott",
            "name": "Ridley Scott",
            "role": "Director", 
            "bio": "Legendary filmmaker known for Alien, Blade Runner, and Gladiator",
            "email": "ridley@rsa-films.com"
        },
        {
            "id": "cd_spike_jonze",
            "name": "Spike Jonze",
            "role": "Creative Director",
            "bio": "Innovative director and creative director known for music videos and films",
            "email": "spike@anonymouscontent.com"
        }
    ]
    
    print("Creating sample person data...")
    for person in sample_people:
        result = await connection_manager.neo4j.execute_query(create_person_query, person)
        if result.success:
            print(f"✅ Created: {person['name']} ({person['role']})")
        else:
            print(f"❌ Failed to create: {person['name']} - {result.error}")
    
    # Query examples
    queries = [
        {
            "description": "Find all Directors",
            "query": """
                MATCH (p:Person)
                WHERE p.role = 'Director'
                RETURN p.name, p.bio
                ORDER BY p.name
            """
        },
        {
            "description": "Find Creative Directors vs Directors", 
            "query": """
                MATCH (p:Person)
                WHERE p.role IN ['Director', 'Creative Director']
                RETURN p.role, count(p) as count
            """
        },
        {
            "description": "Search by name pattern",
            "query": """
                MATCH (p:Person)
                WHERE p.name CONTAINS 'Scott'
                RETURN p.name, p.role, p.email
            """
        }
    ]
    
    for query_example in queries:
        print(f"\n📋 {query_example['description']}")
        result = await connection_manager.neo4j.execute_query(query_example["query"])
        
        if result.success:
            for record in result.records:
                print(f"   {record}")
        else:
            print(f"   ❌ Query failed: {result.error}")


async def example_project_queries(connection_manager):
    """Examples of project-related queries"""
    
    print("\n🎥 Project Query Examples")
    print("-" * 50)
    
    # Create sample project data
    create_project_query = """
    MERGE (proj:Project {id: $id})
    SET proj.name = $name,
        proj.type = $type,
        proj.status = $status,
        proj.budget_range = $budget_range,
        proj.description = $description,
        proj.created_at = datetime(),
        proj.updated_at = datetime()
    RETURN proj
    """
    
    sample_projects = [
        {
            "id": "mv_love_story_2024",
            "name": "Love Story Music Video",
            "type": "Music Video",
            "status": "In Development",
            "budget_range": "$50K-$100K",
            "description": "Romantic music video with cinematic storytelling"
        },
        {
            "id": "comm_nike_running_2024",
            "name": "Nike Running Commercial",
            "type": "Commercial",
            "status": "Pre-Production", 
            "budget_range": "$200K-$500K",
            "description": "High-energy commercial showcasing athletic performance"
        }
    ]
    
    print("Creating sample project data...")
    for project in sample_projects:
        result = await connection_manager.neo4j.execute_query(create_project_query, project)
        if result.success:
            print(f"✅ Created: {project['name']} ({project['type']})")
        else:
            print(f"❌ Failed to create: {project['name']} - {result.error}")
    
    # Query examples
    queries = [
        {
            "description": "Find all Music Videos",
            "query": """
                MATCH (p:Project)
                WHERE p.type = 'Music Video'
                RETURN p.name, p.budget_range, p.status
                ORDER BY p.name
            """
        },
        {
            "description": "Projects by budget range",
            "query": """
                MATCH (p:Project)
                RETURN p.budget_range, collect(p.name) as projects
                ORDER BY p.budget_range
            """
        },
        {
            "description": "Project status summary",
            "query": """
                MATCH (p:Project)
                RETURN p.status, count(p) as count
                ORDER BY count DESC
            """
        }
    ]
    
    for query_example in queries:
        print(f"\n📋 {query_example['description']}")
        result = await connection_manager.neo4j.execute_query(query_example["query"])
        
        if result.success:
            for record in result.records:
                print(f"   {record}")
        else:
            print(f"   ❌ Query failed: {result.error}")


async def example_relationship_queries(connection_manager):
    """Examples of relationship queries"""
    
    print("\n🔗 Relationship Query Examples")
    print("-" * 50)
    
    # Create relationships between existing entities
    relationship_queries = [
        {
            "description": "Connect director to project",
            "query": """
                MATCH (p:Person {id: 'dir_ridley_scott'}), (proj:Project {id: 'comm_nike_running_2024'})
                MERGE (p)-[r:DIRECTED {role_type: 'Director', credit_order: 1}]->(proj)
                RETURN p.name, proj.name, type(r)
            """
        },
        {
            "description": "Connect creative director to music video",
            "query": """
                MATCH (p:Person {id: 'cd_spike_jonze'}), (proj:Project {id: 'mv_love_story_2024'})
                MERGE (p)-[r:DIRECTED {role_type: 'Creative Director', credit_order: 1}]->(proj)
                RETURN p.name, proj.name, type(r)
            """
        }
    ]
    
    print("Creating sample relationships...")
    for rel_query in relationship_queries:
        result = await connection_manager.neo4j.execute_query(rel_query["query"])
        if result.success and result.records:
            record = result.records[0]
            print(f"✅ {record.get('p.name')} → {record.get('proj.name')}")
        else:
            print(f"❌ Failed: {rel_query['description']} - {result.error}")
    
    # Advanced relationship queries
    advanced_queries = [
        {
            "description": "Find director's projects and types",
            "query": """
                MATCH (p:Person)-[:DIRECTED]->(proj:Project)
                WHERE p.role = 'Director'
                RETURN p.name, 
                       collect(proj.type) as project_types,
                       count(proj) as total_projects
                ORDER BY total_projects DESC
            """
        },
        {
            "description": "Find collaboration patterns",
            "query": """
                MATCH (p1:Person)-[:WORKED_ON]->(proj:Project)<-[:WORKED_ON]-(p2:Person)
                WHERE p1.id < p2.id  // Avoid duplicates
                RETURN p1.name, p2.name, 
                       collect(proj.name) as shared_projects,
                       count(proj) as collaboration_count
                ORDER BY collaboration_count DESC
                LIMIT 10
            """
        },
        {
            "description": "Find people who work across project types",
            "query": """
                MATCH (p:Person)-[:DIRECTED|WORKED_ON]->(proj:Project)
                WITH p, collect(DISTINCT proj.type) as types
                WHERE size(types) > 1
                RETURN p.name, p.role, types
                ORDER BY size(types) DESC, p.name
            """
        }
    ]
    
    for query_example in advanced_queries:
        print(f"\n📋 {query_example['description']}")
        result = await connection_manager.neo4j.execute_query(query_example["query"])
        
        if result.success:
            for record in result.records:
                print(f"   {record}")
        else:
            print(f"   ❌ Query failed: {result.error}")


async def example_vector_search_setup(connection_manager):
    """Examples of vector search operations"""
    
    print("\n🔍 Vector Search Examples")
    print("-" * 50)
    
    # Note: This example uses placeholder embeddings
    # In production, you would generate real embeddings using your embedding service
    
    print("Setting up sample embeddings...")
    
    # Add sample embeddings to existing people
    embedding_queries = [
        {
            "query": """
                MATCH (p:Person {id: $id})
                SET p.bio_embedding = $embedding
                RETURN p.name
            """,
            "parameters": {
                "id": "dir_ridley_scott",
                "embedding": [0.1] * 1536  # Placeholder embedding
            }
        },
        {
            "query": """
                MATCH (p:Person {id: $id})
                SET p.bio_embedding = $embedding
                RETURN p.name
            """,
            "parameters": {
                "id": "cd_spike_jonze", 
                "embedding": [0.2] * 1536  # Placeholder embedding
            }
        }
    ]
    
    for embedding_query in embedding_queries:
        result = await connection_manager.neo4j.execute_query(
            embedding_query["query"], 
            embedding_query["parameters"]
        )
        if result.success and result.records:
            print(f"✅ Added embedding for: {result.records[0].get('p.name')}")
    
    # Vector search example (would work with real embeddings)
    print("\n📋 Vector similarity search example:")
    print("   Note: Requires real embeddings for meaningful results")
    
    vector_search_query = """
        CALL db.index.vector.queryNodes('person_bio_vector', 5, $query_embedding)
        YIELD node, score
        RETURN node.name, node.role, score
        ORDER BY score DESC
    """
    
    # This would be your actual query embedding in production
    query_embedding = [0.15] * 1536  # Placeholder
    
    result = await connection_manager.neo4j.execute_query(
        vector_search_query,
        {"query_embedding": query_embedding}
    )
    
    if result.success:
        print("   Results with placeholder embeddings:")
        for record in result.records:
            print(f"   {record}")
    else:
        print(f"   Vector search example failed: {result.error}")


async def cleanup_example_data(connection_manager):
    """Clean up example data"""
    
    print("\n🧹 Cleaning up example data...")
    
    cleanup_queries = [
        "MATCH (p:Person) WHERE p.id IN ['dir_ridley_scott', 'cd_spike_jonze'] DETACH DELETE p",
        "MATCH (proj:Project) WHERE proj.id IN ['mv_love_story_2024', 'comm_nike_running_2024'] DETACH DELETE proj"
    ]
    
    for query in cleanup_queries:
        result = await connection_manager.neo4j.execute_query(query)
        if result.success:
            deleted_count = result.summary.get("counters", {}).get("nodes_deleted", 0)
            if deleted_count > 0:
                print(f"✅ Deleted {deleted_count} nodes")
        else:
            print(f"❌ Cleanup failed: {result.error}")


async def main():
    """Main example execution"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        print("🚀 OneVice Database Usage Examples")
        print("=" * 60)
        
        # Initialize database
        print("\n📡 Initializing database connection...")
        init_result = await initialize_database(ensure_schema=True)
        
        if not init_result["success"]:
            print(f"❌ Failed to initialize database: {init_result.get('error')}")
            return
        
        connection_manager = init_result["connection_manager"]
        print("✅ Database initialized successfully")
        
        # Show schema status
        if init_result["schema_result"]["creation_required"]:
            print("✅ Database schema created")
        else:
            print("✅ Database schema already exists")
        
        # Run example queries
        await example_person_queries(connection_manager)
        await example_project_queries(connection_manager)
        await example_relationship_queries(connection_manager)
        await example_vector_search_setup(connection_manager)
        
        # Show health status
        print("\n🏥 Database Health Status")
        print("-" * 50)
        health = await connection_manager.health_check()
        print(f"Overall Status: {health['overall_status']}")
        
        for component, status in health["components"].items():
            component_status = status.get("status", "unknown")
            print(f"  {component}: {component_status}")
        
        # Cleanup example data
        await cleanup_example_data(connection_manager)
        
        # Close connections
        await connection_manager.close()
        
        print("\n🎉 Examples completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nExamples cancelled by user")
    except Exception as e:
        logger.error(f"Examples failed: {e}")
        print(f"\n❌ Examples failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())