#!/usr/bin/env python3
"""
Add test data for Boost Mobile and Courtney Phillips to Neo4j
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from database.neo4j_client import Neo4jClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def add_test_data():
    """Add test data for Boost Mobile and Courtney Phillips"""
    
    neo4j_client = Neo4jClient()
    await neo4j_client.connect()
    
    print("\n" + "="*60)
    print("ADDING TEST DATA FOR BOOST MOBILE AND COURTNEY PHILLIPS")
    print("="*60 + "\n")
    
    try:
        # 1. Add Boost Mobile as an Organization
        print("1. Adding Boost Mobile organization...")
        add_boost_query = """
        MERGE (org:Organization {id: 'Boost Mobile'})
        SET org.name = 'Boost Mobile',
            org.description = 'Wireless telecommunications brand',
            org.type = 'Telecommunications'
        RETURN org
        """
        result = await neo4j_client.execute_query(add_boost_query)
        if result and result.records:
            print("✅ Boost Mobile organization added successfully")
        else:
            print("⚠️  Boost Mobile may already exist")
        
        # 2. Add Courtney Phillips as a Person
        print("\n2. Adding Courtney Phillips person...")
        add_courtney_query = """
        MERGE (person:Person {id: 'Courtney Phillips'})
        SET person.name = 'Courtney Phillips',
            person.bio = 'Professional treatment writer specializing in commercial and music video concepts',
            person.role = 'Treatment Writer',
            person.company = 'OneVice Entertainment'
        RETURN person
        """
        result = await neo4j_client.execute_query(add_courtney_query)
        if result and result.records:
            print("✅ Courtney Phillips person added successfully")
        else:
            print("⚠️  Courtney Phillips may already exist")
        
        # 3. Add a Boost Mobile treatment project
        print("\n3. Adding Boost Mobile treatment project...")
        add_project_query = """
        MERGE (project:Project {id: 'Boost Mobile Treatment'})
        SET project.name = 'Boost Mobile Commercial Treatment',
            project.description = 'Creative treatment for Boost Mobile wireless commercial campaign',
            project.type = 'Commercial Treatment'
        RETURN project
        """
        result = await neo4j_client.execute_query(add_project_query)
        if result and result.records:
            print("✅ Boost Mobile treatment project added successfully")
        else:
            print("⚠️  Boost Mobile treatment project may already exist")
        
        # 4. Create relationships
        print("\n4. Creating relationships...")
        
        # Courtney wrote the treatment for Boost Mobile
        relationship_query = """
        MATCH (person:Person {id: 'Courtney Phillips'})
        MATCH (project:Project {id: 'Boost Mobile Treatment'})
        MATCH (org:Organization {id: 'Boost Mobile'})
        
        MERGE (person)-[:WROTE]->(project)
        MERGE (project)-[:FOR_CLIENT]->(org)
        MERGE (person)-[:WORKED_FOR]->(org)
        
        RETURN person, project, org
        """
        result = await neo4j_client.execute_query(relationship_query)
        if result and result.records:
            print("✅ Relationships created successfully")
            print("   - Courtney Phillips WROTE Boost Mobile Treatment")
            print("   - Boost Mobile Treatment FOR_CLIENT Boost Mobile")
            print("   - Courtney Phillips WORKED_FOR Boost Mobile")
        
        # 5. Verify the data was added correctly
        print("\n5. Verifying data...")
        verify_query = """
        MATCH (person:Person {id: 'Courtney Phillips'})
        OPTIONAL MATCH (person)-[r1:WROTE]->(project:Project)
        OPTIONAL MATCH (project)-[r2:FOR_CLIENT]->(org:Organization)
        RETURN person, project, org, r1, r2
        """
        result = await neo4j_client.execute_query(verify_query)
        if result and result.records:
            for record in result.records:
                person = record.get('person')
                project = record.get('project')
                org = record.get('org')
                print(f"✅ Verification successful:")
                print(f"   Person: {person.get('id')} (Role: {person.get('role')})")
                if project:
                    print(f"   Project: {project.get('id')} (Type: {project.get('type')})")
                if org:
                    print(f"   Organization: {org.get('id')} (Type: {org.get('type')})")
        
        # 6. Test search for "boost mobile"
        print("\n6. Testing search for 'boost mobile'...")
        search_query = """
        MATCH (n)
        WHERE toLower(n.id) CONTAINS 'boost'
        RETURN labels(n)[0] as type, n.id as id, n.name as name
        """
        result = await neo4j_client.execute_query(search_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} results for 'boost':")
            for record in result.records:
                print(f"   {record['type']}: {record['id']} ({record['name']})")
        else:
            print("❌ No results found for 'boost'")
        
        # 7. Test search for "courtney"
        print("\n7. Testing search for 'courtney'...")
        search_query = """
        MATCH (n)
        WHERE toLower(n.id) CONTAINS 'courtney'
        RETURN labels(n)[0] as type, n.id as id, n.role as role
        """
        result = await neo4j_client.execute_query(search_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} results for 'courtney':")
            for record in result.records:
                print(f"   {record['type']}: {record['id']} (Role: {record['role']})")
        else:
            print("❌ No results found for 'courtney'")
        
    except Exception as e:
        print(f"❌ Error adding test data: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection
        if hasattr(neo4j_client, 'driver') and neo4j_client.driver:
            neo4j_client.driver.close()
    
    print("\n" + "="*60)
    print("TEST DATA ADDITION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(add_test_data())