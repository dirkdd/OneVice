#!/usr/bin/env python3
"""
Test the fixed universal vector search function
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from database.neo4j_client import Neo4jClient
from app.ai.tools.universal_vector_search import universal_vector_search
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fixed_search():
    """Test the fixed universal vector search"""
    
    neo4j_client = Neo4jClient()
    await neo4j_client.connect()
    
    print("\n" + "="*70)
    print("TESTING FIXED UNIVERSAL VECTOR SEARCH")
    print("="*70 + "\n")
    
    try:
        # Test 1: Search for "boost mobile"
        print("1. TESTING SEARCH FOR 'boost mobile':")
        print("-" * 40)
        
        result = await universal_vector_search(
            query_text="boost mobile",
            neo4j_client=neo4j_client,
            max_results=10,
            similarity_threshold=0.6
        )
        
        print(f"Query: 'boost mobile'")
        print(f"Found: {result.get('found', False)}")
        print(f"Total results: {result.get('total_results', 0)}")
        print(f"People: {len(result.get('people', []))}")
        print(f"Projects: {len(result.get('projects', []))}")
        print(f"Organizations: {len(result.get('organizations', []))}")
        print(f"Documents: {len(result.get('documents', []))}")
        
        # Show sample results
        if result.get('people'):
            print(f"\nSample People Results:")
            for person in result['people'][:3]:
                entity = person.get('entity') or {}
                print(f"  - {entity.get('id', 'unknown')} (Role: {entity.get('role', 'none')}, Score: {person.get('score', 0)})")
        
        if result.get('organizations'):
            print(f"\nSample Organization Results:")
            for org in result['organizations'][:3]:
                entity = org.get('entity', {})
                print(f"  - {entity.get('id')} (Type: {entity.get('type')}, Score: {org.get('score')})")
        
        if result.get('projects'):
            print(f"\nSample Project Results:")
            for proj in result['projects'][:3]:
                entity = proj.get('entity', {})
                print(f"  - {entity.get('id')} (Type: {entity.get('type')}, Score: {proj.get('score')})")
        
        # Test 2: Search for "courtney phillips"
        print("\n\n2. TESTING SEARCH FOR 'courtney phillips':")
        print("-" * 40)
        
        result = await universal_vector_search(
            query_text="courtney phillips",
            neo4j_client=neo4j_client,
            max_results=10,
            similarity_threshold=0.6
        )
        
        print(f"Query: 'courtney phillips'")
        print(f"Found: {result.get('found', False)}")
        print(f"Total results: {result.get('total_results', 0)}")
        print(f"People: {len(result.get('people', []))}")
        print(f"Projects: {len(result.get('projects', []))}")
        print(f"Organizations: {len(result.get('organizations', []))}")
        print(f"Documents: {len(result.get('documents', []))}")
        
        # Show sample results
        if result.get('people'):
            print(f"\nSample People Results:")
            for person in result['people'][:3]:
                entity = person.get('entity') or {}
                print(f"  - {entity.get('id', 'unknown')} (Role: {entity.get('role', 'none')}, Score: {person.get('score', 0)})")
        
        # Test 3: Search for "treatment writer"
        print("\n\n3. TESTING SEARCH FOR 'treatment writer':")
        print("-" * 40)
        
        result = await universal_vector_search(
            query_text="treatment writer",
            neo4j_client=neo4j_client,
            max_results=10,
            similarity_threshold=0.6
        )
        
        print(f"Query: 'treatment writer'")
        print(f"Found: {result.get('found', False)}")
        print(f"Total results: {result.get('total_results', 0)}")
        print(f"People: {len(result.get('people', []))}")
        print(f"Projects: {len(result.get('projects', []))}")
        print(f"Organizations: {len(result.get('organizations', []))}")
        print(f"Documents: {len(result.get('documents', []))}")
        
        # Test 4: Search combining terms (like the original question)
        print("\n\n4. TESTING SEARCH FOR 'boost mobile treatment writer':")
        print("-" * 40)
        
        result = await universal_vector_search(
            query_text="boost mobile treatment writer",
            neo4j_client=neo4j_client,
            max_results=10,
            similarity_threshold=0.6
        )
        
        print(f"Query: 'boost mobile treatment writer'")
        print(f"Found: {result.get('found', False)}")
        print(f"Total results: {result.get('total_results', 0)}")
        print(f"People: {len(result.get('people', []))}")
        print(f"Projects: {len(result.get('projects', []))}")
        print(f"Organizations: {len(result.get('organizations', []))}")
        print(f"Documents: {len(result.get('documents', []))}")
        
        if result.get('found'):
            print("\n🎉 SUCCESS! The search is now working!")
            print("This should solve the 'No content available' issue.")
        else:
            print("\n❌ Search still not working as expected.")
        
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection
        if hasattr(neo4j_client, 'driver') and neo4j_client.driver:
            await neo4j_client.driver.close()
    
    print("\n" + "="*70)
    print("FIXED SEARCH TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_fixed_search())