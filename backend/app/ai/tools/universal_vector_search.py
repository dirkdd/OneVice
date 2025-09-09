#!/usr/bin/env python3
"""
Universal Vector Search Layer for Neo4j Tools

This module provides vector search functionality that can be used by any Neo4j tool
to find relevant data across the entire graph, similar to how Neo4j Graph Builder works.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

async def universal_vector_search(
    query_text: str, 
    neo4j_client, 
    max_results: int = 10,
    similarity_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Universal vector search that finds relevant data across the entire Neo4j graph.
    
    This mimics the Neo4j Graph Builder approach by searching across:
    - People (bio embeddings)
    - Projects (description embeddings) 
    - Documents (content embeddings)
    - Organizations (description embeddings)
    
    Args:
        query_text: The search query text
        neo4j_client: Neo4j client instance
        max_results: Maximum number of results to return
        similarity_threshold: Minimum similarity score to include
        
    Returns:
        Dict containing found people, projects, organizations, and documents
    """
    
    logger.info(f"🔍 UNIVERSAL VECTOR SEARCH: '{query_text}'")
    
    try:
        # Split query into individual words for better matching
        query_words = [word.strip().lower() for word in query_text.split() if len(word.strip()) > 2]
        
        # Universal search across all entity types with improved multi-word logic
        # Search for any word in the query, including all entities with __Entity__ label
        universal_search_query = """
        // Search across all entities with __Entity__ label - broader than specific types
        OPTIONAL MATCH (entity:__Entity__)
        WHERE entity.id IS NOT NULL 
        AND ANY(word IN $query_words WHERE toLower(entity.id) CONTAINS word)
        WITH collect(DISTINCT {
            type: 'Entity',
            entity: entity {.id, .role, .bio, .company, .name, .description, .type},
            score: 1.0,
            labels: labels(entity),
            relationships: []
        }) AS all_results
        
        // Categorize results by labels
        WITH all_results,
        [result IN all_results WHERE 'Person' IN result.labels] AS people_results,
        [result IN all_results WHERE 'Project' IN result.labels OR 'CreativeConcept' IN result.labels] AS project_results,
        [result IN all_results WHERE 'Organization' IN result.labels] AS org_results,
        [result IN all_results WHERE 'Document' IN result.labels OR 'Chunk' IN result.labels] AS doc_results
        
        RETURN people_results, project_results, org_results, doc_results,
               size(all_results) AS total_results
        """
        
        logger.info(f"🔍 Query words: {query_words}")
        
        # Execute the universal search with query words
        result = await neo4j_client.execute_query(universal_search_query, {
            "query_words": query_words
        })
        
        if result and result.records:
            record = result.records[0]
            
            people_results = record.get("people_results", [])
            project_results = record.get("project_results", [])
            org_results = record.get("org_results", [])
            doc_results = record.get("doc_results", [])
            total_results = record.get("total_results", 0)
            
            logger.info(f"🎯 UNIVERSAL SEARCH RESULTS: {total_results} total")
            logger.info(f"  👤 People: {len(people_results)}")
            logger.info(f"  🎬 Projects: {len(project_results)}")
            logger.info(f"  🏢 Organizations: {len(org_results)}")
            logger.info(f"  📄 Documents: {len(doc_results)}")
            
            # Log top results for debugging
            for person in people_results[:2]:
                entity = person.get('entity') or {}
                logger.info(f"    👤 {entity.get('id', 'unknown')} (score: {person.get('score', 0)})")
            
            for project in project_results[:2]:
                entity = project.get('entity') or {}
                logger.info(f"    🎬 {entity.get('id', 'unknown')} (score: {project.get('score', 0)})")
                
            for org in org_results[:2]:
                entity = org.get('entity') or {}
                logger.info(f"    🏢 {entity.get('id', 'unknown')} (score: {org.get('score', 0)})")
            
            return {
                "found": True,
                "people": people_results,
                "projects": project_results,
                "organizations": org_results,
                "documents": doc_results,
                "total_results": total_results,
                "query": query_text
            }
        else:
            logger.info("🔍 UNIVERSAL SEARCH: No results found")
            return {
                "found": False,
                "people": [],
                "projects": [],
                "organizations": [],
                "documents": [],
                "total_results": 0,
                "query": query_text
            }
            
    except Exception as e:
        logger.error(f"❌ UNIVERSAL VECTOR SEARCH failed: {e}")
        return {
            "found": False,
            "error": str(e),
            "people": [],
            "projects": [],
            "organizations": [],
            "documents": [],
            "total_results": 0,
            "query": query_text
        }

async def enhance_tool_result_with_vector_search(
    original_result: Dict[str, Any],
    search_query: str,
    neo4j_client,
    tool_name: str
) -> Dict[str, Any]:
    """
    Enhance any tool result with universal vector search data.
    
    This ensures all Neo4j tools get the benefit of comprehensive graph search,
    regardless of their specific implementation.
    """
    
    logger.info(f"🔍 ENHANCING {tool_name} with vector search for: '{search_query}'")
    
    # Run universal vector search
    vector_results = await universal_vector_search(search_query, neo4j_client)
    
    # Merge vector search results with original tool result
    enhanced_result = {
        **original_result,
        "vector_search": vector_results,
        "enhanced": True,
        "enhancement_summary": {
            "vector_people_found": len(vector_results.get("people", [])),
            "vector_projects_found": len(vector_results.get("projects", [])),
            "vector_orgs_found": len(vector_results.get("organizations", [])),
            "vector_docs_found": len(vector_results.get("documents", [])),
            "vector_total": vector_results.get("total_results", 0)
        }
    }
    
    logger.info(f"✅ ENHANCED {tool_name} with {vector_results.get('total_results', 0)} vector results")
    
    return enhanced_result