#!/usr/bin/env python3
"""
Test script to verify Neo4j syntax fix for universal vector search
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

from database.neo4j_client import Neo4jClient
from app.ai.tools.universal_vector_search import universal_vector_search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_neo4j_syntax_fix():
    """Test that the Neo4j universal vector search no longer has syntax errors"""
    
    try:
        # Initialize Neo4j client
        client = Neo4jClient()
        await client.connect()
        logger.info("✅ Neo4j connection established")
        
        # Test the query that was previously failing
        test_query = "boost mobile treatment writer"
        logger.info(f"🧪 Testing query: '{test_query}'")
        
        # This should not throw a syntax error anymore
        result = await universal_vector_search(
            query_text=test_query,
            neo4j_client=client,
            max_results=5,
            similarity_threshold=0.3
        )
        
        logger.info("✅ Query executed successfully - no syntax errors!")
        logger.info(f"📊 Results found:")
        logger.info(f"  - People: {len(result.get('people', []))}")
        logger.info(f"  - Projects: {len(result.get('projects', []))}")
        logger.info(f"  - Organizations: {len(result.get('organizations', []))}")
        logger.info(f"  - Documents: {len(result.get('documents', []))}")
        
        # Check if we found any relevant data
        total_results = (len(result.get('people', [])) + 
                        len(result.get('projects', [])) + 
                        len(result.get('organizations', [])) + 
                        len(result.get('documents', [])))
        
        if total_results > 0:
            logger.info(f"✅ Found {total_results} total results - data retrieval working!")
            
            # Look specifically for COURTNEY PHILLIPS and Boost Mobile
            people = result.get('people', [])
            orgs = result.get('organizations', [])
            
            courtney_found = any('courtney' in str(person).lower() or 'phillips' in str(person).lower() 
                               for person in people)
            boost_found = any('boost' in str(org).lower() or 'mobile' in str(org).lower() 
                             for org in orgs)
            
            if courtney_found:
                logger.info("✅ COURTNEY PHILLIPS data found!")
            if boost_found:
                logger.info("✅ Boost Mobile data found!")
                
        else:
            logger.warning("⚠️  No results found - may need data verification")
        
        # Close connection
        await client.close()
        logger.info("✅ Test completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_neo4j_syntax_fix())
    exit_code = 0 if success else 1
    sys.exit(exit_code)