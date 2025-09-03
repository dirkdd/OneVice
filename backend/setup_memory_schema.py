#!/usr/bin/env python3
"""
Memory System Schema Setup for OneVice
Creates Neo4j schema with memory-specific nodes and vector indexes
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def setup_memory_schema():
    """Setup memory system schema in Neo4j"""
    
    # Get environment variables
    uri = os.getenv('NEO4J_URI')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    database = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    if not all([uri, username, password]):
        print("❌ Missing Neo4j environment variables")
        return False
    
    print("🏗️ OneVice Memory System Schema Setup")
    print("=" * 50)
    print(f"📋 Database: {uri}")
    print(f"📋 Username: {username}")
    print(f"📋 Database: {database}")
    
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session(database=database) as session:
            print("\n🔍 Testing connection...")
            result = session.run("RETURN 1 as test")
            test_value = result.single()['test']
            print(f"✅ Connection successful: {test_value}")
            
            # Create memory-specific constraints
            print("\n🏗️ Creating memory constraints...")
            constraints = [
                "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
                "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    constraint_name = constraint.split('FOR')[0].split('CONSTRAINT')[1].strip().split()[0]
                    print(f"  ✅ {constraint_name}")
                except Exception as e:
                    if "already exists" in str(e) or "equivalent constraint" in str(e):
                        constraint_name = constraint.split('FOR')[0].split('CONSTRAINT')[1].strip().split()[0]
                        print(f"  ⚠️ {constraint_name} (already exists)")
                    else:
                        print(f"  ❌ Constraint failed: {e}")
            
            # Create memory-specific indexes
            print("\n🗂️ Creating memory indexes...")
            indexes = [
                "CREATE INDEX memory_type_index IF NOT EXISTS FOR (m:Memory) ON (m.type)",
                "CREATE INDEX memory_importance_index IF NOT EXISTS FOR (m:Memory) ON (m.importance)",
                "CREATE INDEX memory_created_index IF NOT EXISTS FOR (m:Memory) ON (m.created_at)",
                "CREATE INDEX user_created_index IF NOT EXISTS FOR (u:User) ON (u.created_at)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    index_name = index.split('FOR')[0].split('INDEX')[1].strip().split()[0]
                    print(f"  ✅ {index_name}")
                except Exception as e:
                    if "already exists" in str(e) or "equivalent index" in str(e):
                        index_name = index.split('FOR')[0].split('INDEX')[1].strip().split()[0] 
                        print(f"  ⚠️ {index_name} (already exists)")
                    else:
                        print(f"  ❌ Index failed: {e}")
            
            # Create vector indexes for memory embeddings
            print("\n🎯 Creating vector indexes...")
            vector_indexes = [
                {
                    'name': 'memory_content_vector',
                    'query': '''
                    CREATE VECTOR INDEX memory_content_vector IF NOT EXISTS
                    FOR (m:Memory) ON (m.embedding)
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 1536,
                            `vector.similarity_function`: 'cosine'
                        }
                    }'''
                },
                {
                    'name': 'memory_summary_vector', 
                    'query': '''
                    CREATE VECTOR INDEX memory_summary_vector IF NOT EXISTS
                    FOR (m:Memory) ON (m.summary_embedding)
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 1536,
                            `vector.similarity_function`: 'cosine'
                        }
                    }'''
                }
            ]
            
            for vector_index in vector_indexes:
                try:
                    session.run(vector_index['query'])
                    print(f"  ✅ {vector_index['name']}")
                except Exception as e:
                    if "already exists" in str(e) or "equivalent index" in str(e):
                        print(f"  ⚠️ {vector_index['name']} (already exists)")
                    else:
                        print(f"  ❌ {vector_index['name']} failed: {e}")
            
            # Validate schema
            print("\n🔍 Validating schema...")
            
            # Check constraints
            constraints_result = session.run("SHOW CONSTRAINTS")
            constraint_count = len(list(constraints_result))
            print(f"  📋 Constraints: {constraint_count}")
            
            # Check indexes 
            indexes_result = session.run("SHOW INDEXES")
            index_count = len(list(indexes_result))
            print(f"  📋 Indexes: {index_count}")
            
        driver.close()
        
        print("\n" + "=" * 50)
        print("✅ Memory system schema setup completed successfully!")
        print("🚀 Ready for memory extraction and storage")
        return True
        
    except Exception as e:
        print(f"\n❌ Schema setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_memory_schema()
    sys.exit(0 if success else 1)