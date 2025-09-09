#!/usr/bin/env python3
"""
Investigate Neo4j relationships and data structure for Courtney Phillips and Boost Mobile
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

async def investigate_neo4j_relationships():
    """Investigate Neo4j data structure and relationships"""
    
    neo4j_client = Neo4jClient()
    await neo4j_client.connect()
    
    print("\n" + "="*70)
    print("INVESTIGATING NEO4J RELATIONSHIPS - COURTNEY PHILLIPS & BOOST MOBILE")
    print("="*70 + "\n")
    
    try:
        # 1. Check if Courtney Phillips exists as a Person entity
        print("1. SEARCHING FOR COURTNEY PHILLIPS AS PERSON ENTITY:")
        print("-" * 50)
        
        person_query = """
        MATCH (p:Person)
        WHERE toLower(p.id) CONTAINS 'courtney' 
        RETURN p.id, p.name, p.role, p.bio, labels(p) AS labels
        LIMIT 10
        """
        
        result = await neo4j_client.execute_query(person_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} Person entities with 'courtney':")
            for record in result.records:
                # Extract data directly from the record
                person_id = record.get('p.id', 'unknown')
                person_name = record.get('p.name', 'unknown') 
                person_role = record.get('p.role', 'unknown')
                labels = record.get('labels', [])
                print(f"  - ID: '{person_id}', Name: '{person_name}', Role: '{person_role}', Labels: {labels}")
        else:
            print("❌ No Person entities found with 'courtney'")
        
        # 2. Check all entities with 'courtney' regardless of label
        print("\n2. SEARCHING FOR ALL ENTITIES WITH 'COURTNEY':")
        print("-" * 50)
        
        all_courtney_query = """
        MATCH (n)
        WHERE toLower(n.id) CONTAINS 'courtney'
        RETURN n.id, n.name, n.role, n.type, labels(n) AS labels
        LIMIT 10
        """
        
        result = await neo4j_client.execute_query(all_courtney_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} entities with 'courtney':")
            for record in result.records:
                entity_id = record.get('n.id', 'unknown')
                entity_name = record.get('n.name', 'unknown')
                entity_role = record.get('n.role', 'unknown')
                entity_type = record.get('n.type', 'unknown')
                labels = record.get('labels', [])
                print(f"  - ID: '{entity_id}', Name: '{entity_name}', Role: '{entity_role}', Type: '{entity_type}', Labels: {labels}")
        else:
            print("❌ No entities found with 'courtney'")
        
        # 3. Check all Boost Mobile related projects/treatments
        print("\n3. SEARCHING FOR BOOST MOBILE PROJECTS/TREATMENTS:")
        print("-" * 50)
        
        boost_projects_query = """
        MATCH (p)
        WHERE toLower(p.id) CONTAINS 'boost'
        RETURN p.id, p.name, p.description, p.type, labels(p) AS labels
        LIMIT 10
        """
        
        result = await neo4j_client.execute_query(boost_projects_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} entities with 'boost':")
            for record in result.records:
                entity_id = record.get('p.id', 'unknown')
                entity_name = record.get('p.name', 'unknown')
                entity_type = record.get('p.type', 'unknown')
                entity_desc = record.get('p.description', '')
                labels = record.get('labels', [])
                print(f"  - ID: '{entity_id}', Name: '{entity_name}', Type: '{entity_type}', Labels: {labels}")
                if entity_desc:
                    print(f"    Description: {entity_desc[:100]}...")
        else:
            print("❌ No entities found with 'boost'")
        
        # 4. Check for relationships between entities containing 'courtney' and 'boost'
        print("\n4. SEARCHING FOR RELATIONSHIPS BETWEEN COURTNEY AND BOOST ENTITIES:")
        print("-" * 50)
        
        relationship_query = """
        MATCH (c)-[r]-(b)
        WHERE (toLower(c.id) CONTAINS 'courtney' OR toLower(c.name) CONTAINS 'courtney')
        AND (toLower(b.id) CONTAINS 'boost' OR toLower(b.name) CONTAINS 'boost')
        RETURN c.id AS courtney_id, type(r) AS relationship, b.id AS boost_id, 
               labels(c) AS courtney_labels, labels(b) AS boost_labels
        LIMIT 10
        """
        
        result = await neo4j_client.execute_query(relationship_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} relationships between Courtney and Boost entities:")
            for record in result.records:
                courtney_id = record.get('courtney_id', 'unknown')
                relationship = record.get('relationship', 'unknown')
                boost_id = record.get('boost_id', 'unknown')
                courtney_labels = record.get('courtney_labels', [])
                boost_labels = record.get('boost_labels', [])
                print(f"  - {courtney_id} --[{relationship}]--> {boost_id}")
                print(f"    Courtney Labels: {courtney_labels}, Boost Labels: {boost_labels}")
        else:
            print("❌ No direct relationships found between Courtney and Boost entities")
        
        # 5. Check what WORKED_ON or WROTE relationships exist
        print("\n5. SEARCHING FOR WORKED_ON/WROTE RELATIONSHIPS:")
        print("-" * 50)
        
        wrote_query = """
        MATCH (person)-[r:WORKED_ON|WROTE|CREATED]-(project)
        WHERE (toLower(person.id) CONTAINS 'courtney' OR toLower(project.id) CONTAINS 'boost')
        RETURN person.id AS person_id, type(r) AS relationship, project.id AS project_id,
               labels(person) AS person_labels, labels(project) AS project_labels
        LIMIT 10
        """
        
        result = await neo4j_client.execute_query(wrote_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} WORKED_ON/WROTE/CREATED relationships:")
            for record in result.records:
                person_id = record.get('person_id', 'unknown')
                relationship = record.get('relationship', 'unknown')
                project_id = record.get('project_id', 'unknown')
                person_labels = record.get('person_labels', [])
                project_labels = record.get('project_labels', [])
                print(f"  - {person_id} --[{relationship}]--> {project_id}")
                print(f"    Person Labels: {person_labels}, Project Labels: {project_labels}")
        else:
            print("❌ No WORKED_ON/WROTE/CREATED relationships found")
        
        # 6. Check for any relationship types that exist in the database
        print("\n6. CHECKING ALL RELATIONSHIP TYPES IN DATABASE:")
        print("-" * 50)
        
        rel_types_query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        ORDER BY relationshipType
        """
        
        result = await neo4j_client.execute_query(rel_types_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} relationship types:")
            rel_types = [record.get('relationshipType', 'unknown') for record in result.records]
            print(f"  Available relationships: {', '.join(rel_types)}")
        else:
            print("❌ No relationship types found")
        
        # 7. Check if the COURTNEY PHILLIPS X BOOST MOBILE entity contains author info
        print("\n7. DETAILED ANALYSIS OF 'COURTNEY PHILLIPS X BOOST MOBILE' ENTITY:")
        print("-" * 50)
        
        detailed_query = """
        MATCH (n)
        WHERE toLower(n.id) CONTAINS 'courtney' AND toLower(n.id) CONTAINS 'boost'
        RETURN n.id, n.name, n.role, n.bio, n.description, n.type, n.company, 
               labels(n) AS labels, properties(n) AS all_properties
        """
        
        result = await neo4j_client.execute_query(detailed_query)
        if result and result.records:
            print(f"✅ Found {len(result.records)} entities matching both 'courtney' and 'boost':")
            for record in result.records:
                entity_id = record.get('n.id', 'unknown')
                entity_name = record.get('n.name', 'unknown')
                entity_role = record.get('n.role', 'unknown')
                entity_type = record.get('n.type', 'unknown')
                entity_bio = record.get('n.bio', 'unknown')
                entity_desc = record.get('n.description', 'unknown')
                entity_company = record.get('n.company', 'unknown')
                labels = record.get('labels', [])
                all_props = record.get('all_properties', {})
                print(f"  - ID: '{entity_id}'")
                print(f"    Name: '{entity_name}'")
                print(f"    Role: '{entity_role}'")
                print(f"    Type: '{entity_type}'")
                print(f"    Bio: '{entity_bio}'")
                print(f"    Description: '{entity_desc}'")
                print(f"    Company: '{entity_company}'")
                print(f"    Labels: {labels}")
                print(f"    All Properties: {all_props}")
        else:
            print("❌ No entities found matching both 'courtney' and 'boost'")
        
    except Exception as e:
        print(f"❌ Error investigating relationships: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection properly
        if hasattr(neo4j_client, 'driver') and neo4j_client.driver:
            await neo4j_client.driver.close()
    
    print("\n" + "="*70)
    print("RELATIONSHIP INVESTIGATION COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(investigate_neo4j_relationships())