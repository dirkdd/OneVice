#!/usr/bin/env python3
"""
Test the original question: "Who wrote the treatment for boost mobile?"
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

async def test_original_question():
    """Test the original question workflow"""
    
    neo4j_client = Neo4jClient()
    await neo4j_client.connect()
    
    print("\n" + "="*70)
    print("TESTING ORIGINAL QUESTION: 'Who wrote the treatment for boost mobile?'")
    print("="*70 + "\n")
    
    try:
        # Simulate the exact tool call that was made
        print("🔍 Calling universal_vector_search with 'boost mobile treatment writer'...")
        print("-" * 60)
        
        result = await universal_vector_search(
            "boost mobile treatment writer",
            neo4j_client
        )
        
        print(f"✅ TOOL EXECUTION COMPLETE")
        print(f"Found: {result.get('found', False)}")
        print(f"Total Results: {result.get('total_results', 0)}")
        print(f"Search Method: {result.get('search_method', 'unknown')}")
        print(f"Coverage: {result.get('coverage', 'unknown')}")
        
        print(f"\nSUMMARY:")
        summary = result.get('summary', {})
        print(f"  People Found: {summary.get('people_found', 0)}")
        print(f"  Projects Found: {summary.get('projects_found', 0)}")
        print(f"  Organizations Found: {summary.get('organizations_found', 0)}")
        print(f"  Documents Found: {summary.get('documents_found', 0)}")
        
        print(f"\nKEY INSIGHTS:")
        insights = result.get('key_insights', [])
        for i, insight in enumerate(insights, 1):
            insight_type = insight.get('type', 'unknown')
            insight_text = insight.get('insight', 'No insight available')
            print(f"  {i}. [{insight_type.upper()}] {insight_text}")
        
        # Check if we got the answer we expected
        people_found = summary.get('people_found', 0)
        projects_found = summary.get('projects_found', 0)
        
        if people_found > 0 and projects_found > 0:
            print(f"\n🎉 SUCCESS! The system now finds relevant data:")
            print(f"   - Found {people_found} people (including treatment writers)")
            print(f"   - Found {projects_found} projects (including Boost Mobile treatments)")
            print(f"   - This should solve the 'No content available' issue!")
        elif result.get('found', False):
            print(f"\n✅ PARTIAL SUCCESS - Data found but need to check relevance")
        else:
            print(f"\n❌ STILL NOT WORKING - No data found")
        
        # Also test broader search terms
        print(f"\n" + "-" * 60)
        print("🔍 Testing broader search: 'boost mobile'...")
        
        result2 = await universal_vector_search(
            "boost mobile",
            neo4j_client
        )
        
        if result2.get('found', False):
            summary2 = result2.get('summary', {})
            print(f"   Boost Mobile search: {result2.get('total_results', 0)} total results")
            print(f"   Organizations: {summary2.get('organizations_found', 0)}")
            print(f"   Projects: {summary2.get('projects_found', 0)}")
            print(f"   Documents: {summary2.get('documents_found', 0)}")
        
        print(f"\n" + "-" * 60)
        print("🔍 Testing broader search: 'courtney phillips'...")
        
        result3 = await universal_vector_search(
            "courtney phillips",
            neo4j_client
        )
        
        if result3.get('found', False):
            summary3 = result3.get('summary', {})
            print(f"   Courtney Phillips search: {result3.get('total_results', 0)} total results")
            print(f"   People: {summary3.get('people_found', 0)}")
            print(f"   Projects: {summary3.get('projects_found', 0)}")
            print(f"   Documents: {summary3.get('documents_found', 0)}")
        
    except Exception as e:
        print(f"❌ Error testing original question: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection properly
        if hasattr(neo4j_client, 'driver') and neo4j_client.driver:
            await neo4j_client.driver.close()
    
    print("\n" + "="*70)
    print("ORIGINAL QUESTION TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_original_question())