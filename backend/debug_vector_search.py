#!/usr/bin/env python3
"""
Debug script to investigate why vector search returns no results
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

async def test_direct_queries():
    """Test direct Neo4j queries to understand the data structure"""
    
    neo4j_client = Neo4jClient()
    await neo4j_client.connect()
    
    print("\n" + "="*80)
    print("DEBUGGING VECTOR SEARCH - WHY NO RESULTS?")
    print("="*80 + "\n")
    
    # 1. Check what labels exist
    print("1. CHECKING WHAT LABELS EXIST IN DATABASE:")
    print("-" * 40)
    query = "CALL db.labels() YIELD label RETURN label ORDER BY label"
    result = await neo4j_client.execute_query(query)
    if result and result.records:
        labels = [r['label'] for r in result.records]
        print(f"Found labels: {labels}")
    else:
        print("No labels found!")
    
    # 2. Count nodes by label
    print("\n2. COUNTING NODES BY LABEL:")
    print("-" * 40)
    for label in ['Person', 'Project', 'Organization', 'Document', 'Chunk']:
        query = f"MATCH (n:{label}) RETURN count(n) as count"
        result = await neo4j_client.execute_query(query)
        if result and result.records:
            count = result.records[0]['count']
            print(f"{label}: {count} nodes")
    
    # 3. Check Person properties
    print("\n3. CHECKING PERSON NODE PROPERTIES:")
    print("-" * 40)
    query = """
    MATCH (p:Person)
    RETURN p.id, p.name, p.bio, p.role, p.company
    LIMIT 5
    """
    result = await neo4j_client.execute_query(query)
    if result and result.records:
        for record in result.records:
            print(f"Person: {dict(record)}")
    else:
        print("No Person nodes found!")
    
    # 4. Search for "boost" in any property
    print("\n4. SEARCHING FOR 'boost' IN ANY PROPERTY:")
    print("-" * 40)
    
    # Search in Person nodes
    query = """
    MATCH (n)
    WHERE ANY(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS 'boost')
    RETURN labels(n) as labels, n
    LIMIT 10
    """
    result = await neo4j_client.execute_query(query)
    if result and result.records:
        for record in result.records:
            print(f"Found in {record['labels']}: {dict(record['n'])}")
    else:
        print("No nodes containing 'boost' found!")
    
    # 5. Search for "courtney" or "phillips"
    print("\n5. SEARCHING FOR 'courtney' OR 'phillips':")
    print("-" * 40)
    query = """
    MATCH (n)
    WHERE ANY(prop IN keys(n) WHERE 
        toLower(toString(n[prop])) CONTAINS 'courtney' OR
        toLower(toString(n[prop])) CONTAINS 'phillips'
    )
    RETURN labels(n) as labels, n
    LIMIT 10
    """
    result = await neo4j_client.execute_query(query)
    if result and result.records:
        for record in result.records:
            print(f"Found in {record['labels']}: {dict(record['n'])}")
    else:
        print("No nodes containing 'courtney' or 'phillips' found!")
    
    # 6. Check Project nodes
    print("\n6. CHECKING PROJECT NODES:")
    print("-" * 40)
    query = """
    MATCH (p:Project)
    RETURN p.id, p.name, p.description, p.type
    LIMIT 5
    """
    result = await neo4j_client.execute_query(query)
    if result and result.records:
        for record in result.records:
            print(f"Project: {dict(record)}")
    else:
        print("No Project nodes found!")
    
    # 7. Check Organization nodes
    print("\n7. CHECKING ORGANIZATION NODES:")
    print("-" * 40)
    query = """
    MATCH (o:Organization)
    RETURN o.id, o.name, o.description, o.type
    LIMIT 5
    """
    result = await neo4j_client.execute_query(query)
    if result and result.records:
        for record in result.records:
            print(f"Organization: {dict(record)}")
    else:
        print("No Organization nodes found!")
    
    # 8. Check relationships
    print("\n8. CHECKING RELATIONSHIPS:")
    print("-" * 40)
    query = """
    MATCH (p:Person)-[r]->(proj:Project)
    RETURN p.id as person, type(r) as relationship, proj.id as project
    LIMIT 5
    """
    result = await neo4j_client.execute_query(query)
    if result and result.records:
        for record in result.records:
            print(f"{record['person']} --[{record['relationship']}]--> {record['project']}")
    else:
        print("No Person->Project relationships found!")
    
    # 9. Test the actual universal search query with debugging
    print("\n9. TESTING SIMPLIFIED UNIVERSAL SEARCH QUERY:")
    print("-" * 40)
    
    # Simplified query that should work
    test_query = """
    OPTIONAL MATCH (person:Person)
    WHERE person.id IS NOT NULL
    WITH collect(DISTINCT {
        type: 'Person',
        data: person {.id, .bio, .role, .company}
    }) AS people
    
    OPTIONAL MATCH (project:Project)
    WHERE project.id IS NOT NULL
    WITH people, collect(DISTINCT {
        type: 'Project',
        data: project {.id, .name, .description, .type}
    }) AS projects
    
    OPTIONAL MATCH (org:Organization)
    WHERE org.id IS NOT NULL
    WITH people, projects, collect(DISTINCT {
        type: 'Organization',
        data: org {.id, .name, .description, .type}
    }) AS orgs
    
    RETURN people, projects, orgs, 
           size(people) + size(projects) + size(orgs) as total
    """
    
    result = await neo4j_client.execute_query(test_query)
    if result and result.records:
        record = result.records[0]
        print(f"People found: {len(record.get('people', []))}")
        print(f"Projects found: {len(record.get('projects', []))}")
        print(f"Organizations found: {len(record.get('orgs', []))}")
        print(f"Total: {record.get('total', 0)}")
        
        # Show sample data
        if record.get('people'):
            print("\nSample Person:", record['people'][0] if record['people'] else None)
        if record.get('projects'):
            print("Sample Project:", record['projects'][0] if record['projects'] else None)
        if record.get('orgs'):
            print("Sample Organization:", record['orgs'][0] if record['orgs'] else None)
    else:
        print("Query returned no results!")
    
    # 10. Test search with actual query parameter
    print("\n10. TESTING SEARCH WITH 'boost mobile' PARAMETER:")
    print("-" * 40)
    
    search_query = """
    MATCH (n)
    WHERE ANY(prop IN keys(n) WHERE 
        toLower(toString(n[prop])) CONTAINS toLower($query)
    )
    RETURN labels(n)[0] as type, n, 
           [prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower($query) | prop] as matching_props
    LIMIT 20
    """
    
    result = await neo4j_client.execute_query(search_query, {"query": "boost mobile"})
    if result and result.records:
        print(f"Found {len(result.records)} results for 'boost mobile':")
        for record in result.records:
            print(f"  {record['type']}: {record['n'].get('id', 'no-id')} (matched in: {record['matching_props']})")
    else:
        print("No results found for 'boost mobile'!")
    
    # Test with just "boost"
    result = await neo4j_client.execute_query(search_query, {"query": "boost"})
    if result and result.records:
        print(f"\nFound {len(result.records)} results for just 'boost':")
        for record in result.records:
            print(f"  {record['type']}: {record['n'].get('id', 'no-id')} (matched in: {record['matching_props']})")
    
    # Test with "courtney"
    result = await neo4j_client.execute_query(search_query, {"query": "courtney"})
    if result and result.records:
        print(f"\nFound {len(result.records)} results for 'courtney':")
        for record in result.records:
            print(f"  {record['type']}: {record['n'].get('id', 'no-id')} (matched in: {record['matching_props']})")
    
    await neo4j_client.close()
    print("\n" + "="*80)
    print("DEBUG COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_direct_queries())