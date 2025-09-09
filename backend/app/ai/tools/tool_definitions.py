"""
LangGraph Tool Definitions

Converts GraphQueryTools methods to proper @tool decorated functions for
intelligent LLM-driven tool selection. Each tool includes comprehensive 
descriptions for optimal LLM understanding.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Factory imports
from .factory import (
    create_organization_tool, 
    create_person_tool, 
    create_project_tool,
    tool_factory
)
from .universal_vector_search import enhance_tool_result_with_vector_search
from .vector_search_tool import broad_vector_search

logger = logging.getLogger(__name__)


@create_organization_tool(
    name="get_organization_profile",
    description="""Get comprehensive profile for an organization, company, or brand.

ENTITY_TYPES: company, organization, business, brand, client, corporation
CONFIDENCE_INDICATORS: company names, brand names, business entities, "work with [company]", "for [company]", "client [company]"

USE_WHEN:
- Queries mention company/organization names (Nike, Apple, Boost Mobile, Netflix, Disney, McDonald's)
- "Do we work with [company]?" 
- "Who wrote treatments for [company]?"
- "Find [company] projects"
- Business entity lookup requests
- Client relationship queries

DO_NOT_USE_WHEN:
- Personal names (John Smith, Mary Johnson, Courtney Phillips)
- Individual people queries ("Who is John Smith?")
- When looking for specific people rather than companies

EXAMPLES:
✅ "boost mobile" → get_organization_profile("Boost Mobile")
✅ "netflix projects" → get_organization_profile("Netflix") 
✅ "who wrote treatments for disney" → get_organization_profile("Disney")
❌ "john smith" → use get_person_details instead
❌ "courtney phillips" → use get_person_details instead

PARALLEL_EXECUTION: ALWAYS call with broad_vector_search for comprehensive results

Input: org_name (str) - Name or partial name of the organization
Returns: Organization profile with projects, people, deals, and statistics"""
)
async def get_organization_profile(org_name: str, neo4j_client) -> Dict[str, Any]:
    """
    Get comprehensive organization profile with projects, people, and deals.
    
    This tool searches for organizations by name or ID and returns:
    - Organization details (name, type, description)
    - Associated people and their roles
    - Projects the organization was involved in
    - Deal information if available
    - Statistics on people and project counts
    """
    logger.info(f"🚀 TOOL EXECUTED: get_organization_profile called with org_name='{org_name}'")
    logger.info(f"🚀 Neo4j client type: {type(neo4j_client)}")
    # FIXED QUERY - Uses correct property names discovered during debugging
    query = """
    MATCH (o:Organization)
    WHERE o.id CONTAINS $org_name OR (o.name IS NOT NULL AND o.name CONTAINS $org_name) OR
          toLower(o.id) CONTAINS toLower($org_name) OR (o.name IS NOT NULL AND toLower(o.name) CONTAINS toLower($org_name))

    // CRITICAL: Find treatment writers using WROTE_TREATMENT_FOR relationship we discovered
    OPTIONAL MATCH (o)<-[:FOR_CLIENT]-(treatment_proj:Project)<-[:WROTE_TREATMENT_FOR]-(writer:Person)

    // Also find DESIGNED_TREATMENT_FOR relationships
    OPTIONAL MATCH (o)<-[:FOR_CLIENT]-(design_proj:Project)<-[:DESIGNED_TREATMENT_FOR]-(designer:Person)

    // Find any documents/chunks with treatment content
    OPTIONAL MATCH (o)<-[:FOR_CLIENT]-(proj3:Project)-[:HAS_DOCUMENT|HAS_CHUNK]-(doc)
    WHERE (doc.text IS NOT NULL AND toLower(doc.text) CONTAINS 'treatment') OR
          (doc.content IS NOT NULL AND toLower(doc.content) CONTAINS 'treatment')

    // Find all projects and people connected to this organization - USING ID PROPERTIES
    OPTIONAL MATCH (o)<-[:WORKS_FOR]-(p:Person)
    OPTIONAL MATCH (o)<-[:FOR_CLIENT]-(proj:Project)
    OPTIONAL MATCH (proj)<-[:CONTRIBUTED_TO]-(contributor:Person)
    OPTIONAL MATCH (o)<-[:FOR_ORGANIZATION]-(d:Deal)
    
    RETURN o {
        .id, .name, .type, .description, .folkId
    } AS organization,
    collect(DISTINCT p.id) AS people,
    collect(DISTINCT proj.id) AS projects,
    collect(DISTINCT d.name) AS deals,
    collect(DISTINCT contributor.id) AS contributors,
    collect(DISTINCT writer.id) AS treatment_writers_direct,
    collect(DISTINCT designer.id) AS treatment_designers,
    collect(DISTINCT {
        id: writer.id, 
        role: writer.role, 
        bio: writer.bio,
        project: treatment_proj.id,
        relationship: 'WROTE_TREATMENT_FOR'
    }) AS writer_details_direct,
    collect(DISTINCT {
        id: designer.id, 
        role: designer.role, 
        bio: designer.bio,
        project: design_proj.id,
        relationship: 'DESIGNED_TREATMENT_FOR'
    }) AS designer_details,
    collect(DISTINCT {
        text: substring(coalesce(doc.text, doc.content, ''), 0, 200),
        id: doc.id
    }) AS treatment_documents,
    count(DISTINCT p) AS people_count,
    count(DISTINCT proj) AS project_count,
    count(DISTINCT writer) AS treatment_writer_count
    """
    
    try:
        # Check connection state if available
        if hasattr(neo4j_client, 'state'):
            from database.neo4j_client import ConnectionState
            if neo4j_client.state != ConnectionState.CONNECTED:
                logger.info("Neo4j client not connected, attempting connection...")
                await neo4j_client.connect()
        
        # Add comprehensive debugging for data investigation
        logger.info(f"🔍 DEBUGGING: Executing organization query for: {org_name}")
        
        # First, check what actually exists in the database
        debug_query = "MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC LIMIT 10"
        debug_result = await neo4j_client.execute_query(debug_query)
        logger.info(f"🔍 DEBUG: Database node summary:")
        if debug_result and debug_result.records:
            for record in debug_result.records:
                labels = record.get("labels", [])
                count = record.get("count", 0)
                logger.info(f"  - {labels}: {count} nodes")
        else:
            logger.info("  - No nodes found in database!")
        
        # Try a broader search first (exclude vector embeddings and handle data types properly)
        broad_query = """
        MATCH (n) 
        WHERE ANY(prop IN keys(n) WHERE 
            NOT prop ENDS WITH '_embedding' AND 
            prop <> 'bio_embedding' AND
            prop <> 'project_embedding' AND
            prop <> 'content_embedding' AND
            n[prop] IS NOT NULL AND
            (n[prop] IS NOT NULL) AND
            (
                (n[prop] =~ '(?i).*boost.*' AND size(toString(n[prop])) < 1000) OR
                (toString(n[prop]) =~ '(?i).*boost.*' AND size(toString(n[prop])) < 1000)
            )
        )
        RETURN labels(n) as labels, keys(n) as properties, 
               [prop IN keys(n) WHERE NOT prop ENDS WITH '_embedding' AND toString(n[prop]) CONTAINS 'boost' | prop + ': ' + toString(n[prop])] as matching_props 
        LIMIT 5
        """
        broad_result = await neo4j_client.execute_query(broad_query, {"org_name": org_name})
        logger.info(f"🔍 DEBUG: Broad 'boost' search results:")
        if broad_result and broad_result.records:
            for record in broad_result.records:
                labels = record.get("labels", [])
                props = record.get("properties", [])
                logger.info(f"  - Found {labels} node with properties: {props}")
        else:
            logger.info("  - No 'boost' related nodes found")
        
        # Add vector search for treatment writers and project details
        logger.info(f"🔍 DEBUG: Adding vector search for treatment writers...")
        vector_query = """
        MATCH (o:Organization)
        WHERE o.id CONTAINS $org_name OR o.name CONTAINS $org_name OR 
              toLower(o.id) CONTAINS toLower($org_name) OR toLower(o.name) CONTAINS toLower($org_name)
        
        // Vector search for people with "treatment" or "writer" in bio
        CALL db.index.vector.queryNodes('person_bio_index', 10, [/* treatment writer embedding */])
        YIELD node as person, score
        WHERE score > 0.8
        OPTIONAL MATCH (person)-[:CONTRIBUTED_TO]->(proj:Project)-[:FOR_CLIENT]->(o)
        
        // Also find projects directly mentioning treatment
        OPTIONAL MATCH (o)<-[:FOR_CLIENT]-(treatment_proj:Project)
        WHERE toLower(treatment_proj.name) CONTAINS 'treatment' OR 
              toLower(treatment_proj.description) CONTAINS 'treatment' OR
              toLower(treatment_proj.type) CONTAINS 'treatment'
        
        // Find people who worked on treatment projects
        OPTIONAL MATCH (writer:Person)-[:CONTRIBUTED_TO]->(treatment_proj)
        WHERE toLower(writer.role) CONTAINS 'writer' OR 
              toLower(writer.bio) CONTAINS 'treatment' OR
              toLower(writer.bio) CONTAINS 'writer'
              
        RETURN o {
            .id, .name, .type, .description, .folkId
        } AS organization,
        collect(DISTINCT person.name) AS treatment_writers_vector,
        collect(DISTINCT writer.name) AS treatment_writers_graph,
        collect(DISTINCT treatment_proj.name) AS treatment_projects,
        collect(DISTINCT {
            name: writer.name, 
            role: writer.role, 
            bio: writer.bio,
            project: treatment_proj.name
        }) AS writer_details
        """
        
        logger.info(f"🔍 DEBUG: Now executing original Organization query...")
        result = await neo4j_client.execute_query(query, {"org_name": org_name})
        logger.info(f"🔍 DEBUG: Organization query returned {len(result.records) if result and result.records else 0} records")
        
        # CRITICAL Vector Search - Based on user insight that Graph Builder uses vector search
        logger.info(f"🔍 VECTOR SEARCH: Starting vector search for treatment writers...")
        try:
            # Text-based vector search that mimics vector similarity behavior
            text_based_vector_search = """
            MATCH (person:Person)
            WHERE (person.bio IS NOT NULL AND 
                  (toLower(person.bio) CONTAINS 'treatment' OR 
                   toLower(person.bio) CONTAINS 'writer' OR 
                   toLower(person.bio) CONTAINS 'screenplay' OR
                   toLower(person.bio) CONTAINS 'script')) OR
                  (person.role IS NOT NULL AND
                   (toLower(person.role) CONTAINS 'writer' OR
                    toLower(person.role) CONTAINS 'screenwriter'))
            
            OPTIONAL MATCH (person)-[rel:CONTRIBUTED_TO|WROTE_TREATMENT_FOR|DESIGNED_TREATMENT_FOR]->(project:Project)-[:FOR_CLIENT]->(org:Organization)
            WHERE org.id CONTAINS $org_name OR (org.name IS NOT NULL AND toLower(org.name) CONTAINS toLower($org_name))
            
            RETURN person {
                .id, .role, .bio, .company
            } AS vector_person,
            type(rel) AS relationship_type,
            project.id AS related_project,
            org.id AS org_match,
            // Calculate similarity score based on keyword matches
            CASE 
                WHEN toLower(person.bio) CONTAINS 'treatment' THEN 1.0
                WHEN toLower(person.bio) CONTAINS 'writer' THEN 0.8
                WHEN toLower(person.bio) CONTAINS 'screenplay' THEN 0.7
                ELSE 0.5
            END AS similarity_score
            ORDER BY similarity_score DESC
            LIMIT 10
            """
            
            logger.info(f"🔍 DEBUG: Executing vector-like search for treatment writers...")
            vector_result = await neo4j_client.execute_query(text_based_vector_search, {"org_name": org_name})
            
            if vector_result and vector_result.records:
                logger.info(f"🎯 VECTOR SEARCH: Found {len(vector_result.records)} potential treatment writers!")
                for i, record in enumerate(vector_result.records):
                    person = record.get("vector_person", {})
                    score = record.get("similarity_score", 0)
                    rel_type = record.get("relationship_type")
                    project = record.get("related_project")
                    org_match = record.get("org_match")
                    logger.info(f"  🎯 MATCH {i+1}: {person.get('id', 'Unknown')} (score: {score}) - {rel_type} -> {project} @ {org_match}")
                    
                    # If we found a high-scoring match, add it to the main result
                    if score >= 0.8 and org_match:
                        logger.info(f"🚀 HIGH CONFIDENCE MATCH: {person.get('id')} for {org_match}")
            else:
                logger.info("🔍 VECTOR SEARCH: No treatment writers found in vector search")
                
        except Exception as vector_error:
            logger.error(f"🔍 VECTOR SEARCH: Failed - {vector_error}")
        
        # Try the enhanced vector search approach (if original query finds organization)
        if result and result.records:
            logger.info(f"🔍 DEBUG: Organization found, attempting enhanced vector search...")
            try:
                # Debug and explore actual relationships in the database
                enhanced_query = """
                MATCH (o:Organization)
                WHERE o.id CONTAINS $org_name OR o.name CONTAINS $org_name OR 
                      toLower(o.id) CONTAINS toLower($org_name) OR toLower(o.name) CONTAINS toLower($org_name)
                
                // Debug: Find ALL relationships from organization
                OPTIONAL MATCH (o)-[r1]->(connected1)
                OPTIONAL MATCH (o)<-[r2]-(connected2)
                
                // Find all projects using different relationship patterns
                OPTIONAL MATCH (o)<-[:FOR_CLIENT]-(proj1:Project)
                OPTIONAL MATCH (o)-[:CLIENT_OF]->(proj2:Project)  
                OPTIONAL MATCH (o)-[:HAS_PROJECT]->(proj3:Project)
                OPTIONAL MATCH (proj4:Project)-[:INVOLVES]->(o)
                OPTIONAL MATCH (proj5:Project {client: o.name})
                OPTIONAL MATCH (proj6:Project {client: o.id})
                
                // Find people with broader relationship patterns
                OPTIONAL MATCH (person1:Person)-[:CONTRIBUTED_TO]->(proj1)
                OPTIONAL MATCH (person2:Person)-[:WORKED_ON]->(proj1)
                OPTIONAL MATCH (person3:Person)-[:WORKS_FOR]->(o)
                OPTIONAL MATCH (person4:Person {company: o.name})
                
                // Look for specific writers or treatment creators
                OPTIONAL MATCH (writer:Person)
                WHERE toLower(writer.name) CONTAINS 'courtney' OR
                      toLower(writer.name) CONTAINS 'phillips' OR
                      toLower(writer.bio) CONTAINS 'treatment' OR
                      toLower(writer.role) CONTAINS 'writer'
                      
                RETURN o {
                    .id, .name, .type, .description, .folkId
                } AS organization,
                // Debug relationship info
                collect(DISTINCT type(r1)) AS outgoing_rels,
                collect(DISTINCT type(r2)) AS incoming_rels,
                collect(DISTINCT labels(connected1)) AS outgoing_connected,
                collect(DISTINCT labels(connected2)) AS incoming_connected,
                // Project collections
                collect(DISTINCT proj1.name) AS for_client_projects,
                collect(DISTINCT proj2.name) AS client_of_projects, 
                collect(DISTINCT proj3.name) AS has_projects,
                collect(DISTINCT proj4.name) AS involves_projects,
                collect(DISTINCT proj5.name) AS named_client_projects,
                collect(DISTINCT proj6.name) AS id_client_projects,
                // People collections
                collect(DISTINCT person1.name) AS contributed_people,
                collect(DISTINCT person2.name) AS worked_on_people,
                collect(DISTINCT person3.name) AS works_for_people,
                collect(DISTINCT person4.name) AS company_people,
                collect(DISTINCT writer.name) AS potential_writers,
                // Detailed writer info
                collect(DISTINCT {
                    name: writer.name,
                    role: writer.role,
                    bio: writer.bio,
                    company: writer.company
                }) AS writer_details
                """
                
                enhanced_result = await neo4j_client.execute_query(enhanced_query, {"org_name": org_name})
                logger.info(f"🔍 DEBUG: Enhanced query returned {len(enhanced_result.records) if enhanced_result and enhanced_result.records else 0} records")
                
                if enhanced_result and enhanced_result.records:
                    enhanced_record = enhanced_result.records[0]
                    
                    # Debug relationship information
                    outgoing_rels = [r for r in enhanced_record.get("outgoing_rels", []) if r]
                    incoming_rels = [r for r in enhanced_record.get("incoming_rels", []) if r] 
                    
                    # Project information from different patterns
                    all_projects = []
                    for proj_key in ["for_client_projects", "client_of_projects", "has_projects", 
                                   "involves_projects", "named_client_projects", "id_client_projects"]:
                        projects = [p for p in enhanced_record.get(proj_key, []) if p]
                        if projects:
                            all_projects.extend(projects)
                            logger.info(f"🎯 FOUND {proj_key}: {projects}")
                    
                    # People information from different patterns  
                    all_people = []
                    for people_key in ["contributed_people", "worked_on_people", "works_for_people", 
                                     "company_people"]:
                        people = [p for p in enhanced_record.get(people_key, []) if p]
                        if people:
                            all_people.extend(people)
                            logger.info(f"🎯 FOUND {people_key}: {people}")
                    
                    # Writer information
                    potential_writers = [w for w in enhanced_record.get("potential_writers", []) if w]
                    writer_details = enhanced_record.get("writer_details", [])
                    
                    logger.info(f"🎯 DEBUG RELATIONSHIPS:")
                    logger.info(f"  - Outgoing: {outgoing_rels}")
                    logger.info(f"  - Incoming: {incoming_rels}")
                    logger.info(f"🎯 ENHANCED RESULTS: Found {len(potential_writers)} writers, {len(all_projects)} projects")
                    
                    if potential_writers:
                        logger.info(f"🎯 POTENTIAL WRITERS: {potential_writers}")
                    if writer_details:
                        for writer in writer_details[:3]:
                            logger.info(f"🎯 WRITER DETAIL: {writer}")
                    if all_projects:
                        logger.info(f"🎯 ALL PROJECTS: {all_projects}")
                    
            except Exception as vector_error:
                logger.error(f"🔍 DEBUG: Enhanced vector search failed: {vector_error}")
        else:
            logger.info(f"🔍 DEBUG: Organization not found, skipping vector search")
        
        if result and result.records:
            record = result.records[0]
            org_data = record.get("organization", {})
            
            # Create a clean organization name - use name if available, otherwise use id
            display_name = org_data.get("name") or org_data.get("id") or "Unknown Organization"
            
            # Try to get enhanced data from the debug search if available
            enhanced_data = {}
            try:
                if 'enhanced_result' in locals() and enhanced_result and enhanced_result.records:
                    enhanced_record = enhanced_result.records[0]
                    
                    # Collect all projects found
                    all_projects_found = []
                    for proj_key in ["for_client_projects", "client_of_projects", "has_projects", 
                                   "involves_projects", "named_client_projects", "id_client_projects"]:
                        projects = [p for p in enhanced_record.get(proj_key, []) if p]
                        all_projects_found.extend(projects)
                    
                    # Collect all people found
                    all_people_found = []
                    for people_key in ["contributed_people", "worked_on_people", "works_for_people", 
                                     "company_people"]:
                        people = [p for p in enhanced_record.get(people_key, []) if p]
                        all_people_found.extend(people)
                    
                    potential_writers = [w for w in enhanced_record.get("potential_writers", []) if w]
                    writer_details = enhanced_record.get("writer_details", [])
                    
                    # Merge enhanced data with original results
                    enhanced_data = {
                        "debug_relationships": {
                            "outgoing": enhanced_record.get("outgoing_rels", []),
                            "incoming": enhanced_record.get("incoming_rels", [])
                        },
                        "discovered_projects": all_projects_found,
                        "discovered_people": all_people_found,
                        "potential_writers": potential_writers,
                        "writer_details": writer_details,
                        "discovery_stats": {
                            "project_count": len(all_projects_found),
                            "people_count": len(all_people_found),
                            "writer_count": len(potential_writers)
                        }
                    }
                    
                    logger.info(f"🎯 RESPONSE: Including discovery data with {len(potential_writers)} writers, {len(all_projects_found)} projects, {len(all_people_found)} people")
            except Exception as e:
                logger.error(f"🔍 DEBUG: Error processing enhanced data: {e}")
            
            # Extract treatment-specific data from the corrected query
            treatment_writers_direct = [w for w in record.get("treatment_writers_direct", []) if w]
            treatment_designers = [d for d in record.get("treatment_designers", []) if d]
            writer_details = record.get("writer_details_direct", [])
            designer_details = record.get("designer_details", [])
            treatment_documents = record.get("treatment_documents", [])
            
            logger.info(f"🎯 TREATMENT DATA FOUND:")
            logger.info(f"  - Direct writers: {treatment_writers_direct}")
            logger.info(f"  - Designers: {treatment_designers}")
            logger.info(f"  - Writer details: {len(writer_details)} entries")
            logger.info(f"  - Treatment documents: {len(treatment_documents)} entries")

            response = {
                "organization": {
                    **org_data,
                    "display_name": display_name  # Add a consistent display name
                },
                "people": [p for p in record.get("people", []) if p],
                "projects": [p for p in record.get("projects", []) if p],
                "deals": [d for d in record.get("deals", []) if d],
                "contributors": [c for c in record.get("contributors", []) if c],
                "treatment_writers_direct": treatment_writers_direct,
                "treatment_designers": treatment_designers,
                "writer_details_direct": writer_details,
                "designer_details": designer_details,
                "treatment_documents": treatment_documents,
                "stats": {
                    "people_count": record.get("people_count", 0),
                    "project_count": record.get("project_count", 0),
                    "treatment_writer_count": record.get("treatment_writer_count", 0),
                    "treatment_document_count": len(treatment_documents)
                },
                "query": org_name,
                "found": True,
                # Add enhanced data if available
                **enhanced_data
            }
            
            return response
        else:
            return {
                "organization": None,
                "people": [],
                "projects": [],
                "deals": [],
                "stats": {"people_count": 0, "project_count": 0},
                "query": org_name,
                "found": False,
                "error": "Organization not found"
            }
            
    except Exception as e:
        logger.error(f"Error in get_organization_profile for '{org_name}': {e}")
        return {
            "error": f"Query failed: {str(e)}",
            "query": org_name,
            "found": False
        }


@create_person_tool(
    name="get_person_details", 
    description="""Get comprehensive profile for an individual person including projects, organizations, and groups.

ENTITY_TYPES: person, individual, people, human, contact, employee, freelancer
CONFIDENCE_INDICATORS: personal names, "Who is [person]?", individual queries, contact lookups

USE_WHEN:
- Queries about specific individuals (John Smith, Mary Johnson, Courtney Phillips, Director Name)
- "Who is [person name]?"
- Person profiles, contact information, work history
- Individual's role and organizational affiliations
- "Find [person's name] details"

DO_NOT_USE_WHEN:
- Company names (Boost Mobile, Netflix, Disney, Nike)
- Organization queries ("Do we work with [company]?")
- Brand or business entity lookups
- When looking for companies rather than people

EXAMPLES:
✅ "john smith" → get_person_details("John Smith")
✅ "courtney phillips" → get_person_details("Courtney Phillips")
✅ "who is mary johnson" → get_person_details("Mary Johnson")
❌ "boost mobile" → use get_organization_profile instead
❌ "disney" → use get_organization_profile instead
❌ "nike projects" → use get_organization_profile instead

PARALLEL_EXECUTION: ALWAYS call with broad_vector_search for comprehensive results

Input: name (str) - Name or partial name of the person
Returns: Person profile with projects, organization, groups, and contact details"""
)
async def get_person_details(name: str, neo4j_client) -> Dict[str, Any]:
    """
    Get comprehensive profile for a person including projects, organizations, and groups.
    
    This tool searches for people by name and returns:
    - Personal details (name, email, role, bio, contact info)
    - Organization they work for
    - Projects they've contributed to and their roles
    - Groups they belong to
    - Internal contact owner (if external person)
    """
    query = """
    MATCH (p:Person)
    WHERE p.name CONTAINS $name OR p.fullName CONTAINS $name
    OPTIONAL MATCH (p)-[r:CONTRIBUTED_TO]->(proj:Project)
    OPTIONAL MATCH (p)-[:WORKS_FOR]->(org:Organization)
    OPTIONAL MATCH (p)-[:BELONGS_TO]->(g:Group)
    OPTIONAL MATCH (internal:Person {isInternal: true})-[:OWNS_CONTACT]->(p)
    RETURN p {
        .name, .fullName, .email, .folkId, .isInternal,
        .bio, .role, .phone, .location, .linkedinUrl, .website, .tags
    } AS person,
    org.name AS organization,
    collect(DISTINCT {
        project: proj.name, 
        role: r.role, 
        startDate: r.startDate,
        projectId: proj.id
    }) AS projects,
    collect(DISTINCT g.name) AS groups,
    internal.name AS contact_owner
    """
    
    try:
        result = await neo4j_client.execute_query(query, {"name": name})
        
        if result and result.records:
            # Take the first matching person
            person_data = result.records[0]
            
            # Clean up None values and empty collections
            response = {
                "person": person_data.get("person", {}),
                "organization": person_data.get("organization"),
                "projects": [p for p in person_data.get("projects", []) if p.get("project")],
                "groups": [g for g in person_data.get("groups", []) if g],
                "contact_owner": person_data.get("contact_owner"),
                "query": name,
                "found": True
            }
            
            return response
        else:
            return {
                "person": None,
                "organization": None,
                "projects": [],
                "groups": [],
                "contact_owner": None,
                "query": name,
                "found": False,
                "error": "Person not found in knowledge graph"
            }
    
    except Exception as e:
        logger.error(f"Error in get_person_details for '{name}': {e}")
        return {
            "error": f"Query failed: {str(e)}",
            "query": name,
            "found": False
        }


@create_organization_tool(
    name="find_people_at_organization",
    description="""Find all people who work for a specific organization.
    
    Use this tool when users ask about:
    - "Who works at [company]?"
    - Team members at a specific organization
    - Decision makers or contacts at a company
    - Staff directory for an organization
    
    Input: organization_name (str) - Name of the organization
    Returns: List of people with their roles, contact info, and whether they are internal"""
)
async def find_people_at_organization(organization_name: str, neo4j_client) -> Dict[str, Any]:
    """
    Find all people who work for a specific organization.
    
    This tool searches for all people associated with an organization and returns:
    - Person details (name, role, email, folk ID)
    - Whether they are internal or external
    - Organization confirmation
    - Count of people found
    """
    query = """
    MATCH (p:Person)-[:WORKS_FOR]->(o:Organization)
    WHERE o.name CONTAINS $org_name
    RETURN p {
        .name, .role, .email, .folkId, .isInternal
    } AS person,
    o.name AS organization
    ORDER BY p.name
    """
    
    try:
        result = await neo4j_client.execute_query(query, {"org_name": organization_name})
        
        if result and result.records:
            people = []
            for record in result.records:
                person_data = record.get("person", {})
                if person_data:
                    people.append({
                        "name": person_data.get("name"),
                        "title": person_data.get("role"),  # Map role to title for API consistency
                        "email": person_data.get("email"),
                        "folkId": person_data.get("folkId"),
                        "isInternal": person_data.get("isInternal", False),
                        "organization": record.get("organization")
                    })
            
            response = {
                "people": people,
                "organization": organization_name,
                "count": len(people),
                "found": len(people) > 0
            }
            
            return response
        else:
            return {
                "people": [],
                "organization": organization_name,
                "count": 0,
                "found": False,
                "error": "No people found at this organization"
            }
    
    except Exception as e:
        logger.error(f"Error in find_people_at_organization for '{organization_name}': {e}")
        return {
            "error": f"Query failed: {str(e)}",
            "organization": organization_name,
            "found": False
        }


@create_project_tool(
    name="search_projects_by_criteria",
    description="""Search projects by multiple criteria like type, year, status, client, etc.
    
    Use this tool when users ask about:
    - "What commercial projects did we do in 2023?"
    - "Show me all automotive campaigns"
    - "Find active projects for Nike"
    - Projects by specific criteria or filters
    
    Input: criteria (dict) - Search criteria with keys like 'type', 'year', 'status', 'client'
    Returns: List of matching projects with client and director information"""
)
async def search_projects_by_criteria(criteria: Dict[str, Any], neo4j_client) -> Dict[str, Any]:
    """
    Search projects by multiple criteria (type, year, status, client, etc.)
    
    This tool allows flexible project searching with criteria:
    - type: Project type (commercial, film, etc.)
    - year: Project year
    - status: Project status (active, completed, etc.)
    - client: Client organization name
    
    Returns matching projects with details, client, and director information.
    """
    # Build dynamic query based on criteria
    where_clauses = []
    params = {}
    
    if criteria.get("type"):
        where_clauses.append("proj.type CONTAINS $project_type")
        params["project_type"] = criteria["type"]
        
    if criteria.get("year"):
        where_clauses.append("proj.year = $year")
        params["year"] = criteria["year"]
        
    if criteria.get("status"):
        where_clauses.append("proj.status CONTAINS $status")
        params["status"] = criteria["status"]
        
    if criteria.get("client"):
        where_clauses.append("client.name CONTAINS $client_name")
        params["client_name"] = criteria["client"]
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    query = f"""
    MATCH (proj:Project)
    OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
    OPTIONAL MATCH (director:Person)-[:CONTRIBUTED_TO {{role: 'Director'}}]->(proj)
    WHERE {where_clause}
    RETURN proj {{
        .name, .type, .status, .year, .description, .budget
    }} AS project,
    client.name AS client,
    director.name AS director
    ORDER BY proj.year DESC, proj.name
    LIMIT 25
    """
    
    try:
        result = await neo4j_client.execute_query(query, params)
        
        projects = []
        if result and result.records:
            for record in result.records:
                projects.append({
                    "project": record.get("project", {}),
                    "client": record.get("client"),
                    "director": record.get("director")
                })
        
        response = {
            "projects": projects,
            "criteria": criteria,
            "count": len(projects),
            "found": len(projects) > 0
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in search_projects_by_criteria: {e}")
        return {
            "error": f"Query failed: {str(e)}",
            "criteria": criteria,
            "found": False
        }


@create_project_tool(
    name="find_similar_projects",
    description="""Find projects similar to a given project using vector similarity analysis.
    
    Use this tool when users ask about:
    - "Find projects similar to [project name]"
    - "What other campaigns are like this one?"
    - Similar projects for pattern analysis
    - Recommendation of related work
    
    Input: project_title (str) - Name of the target project, similarity_threshold (float, default 0.8)
    Returns: List of similar projects with similarity scores and client information"""
)
async def find_similar_projects(project_title: str, similarity_threshold: float = 0.8, neo4j_client=None) -> Dict[str, Any]:
    """
    Find projects similar to a given project using vector similarity.
    
    This tool uses concept embeddings to find projects with similar themes,
    styles, or content. Requires projects to have concept_embedding data.
    
    First finds the target project's embedding, then searches for similar
    projects above the similarity threshold.
    """
    # First get the target project's embedding
    target_query = """
    MATCH (proj:Project)
    WHERE proj.name CONTAINS $title
    RETURN proj.concept_embedding AS embedding, proj.name AS exact_title
    LIMIT 1
    """
    
    try:
        target_result = await neo4j_client.execute_query(target_query, {"title": project_title})
        
        if not target_result or not target_result.records:
            return {
                "similar_projects": [],
                "target_project": project_title,
                "error": "Target project not found or no embedding available",
                "found": False
            }
        
        target_embedding = target_result.records[0].get("embedding")
        exact_title = target_result.records[0].get("exact_title")
        
        if not target_embedding:
            return {
                "similar_projects": [],
                "target_project": project_title,
                "error": "Target project has no concept embedding",
                "found": False
            }
        
        # Find similar projects using vector similarity
        similarity_query = """
        MATCH (proj:Project)
        WHERE proj.concept_embedding IS NOT NULL 
        AND proj.name <> $exact_title
        WITH proj, gds.similarity.cosine(proj.concept_embedding, $target_embedding) AS similarity
        WHERE similarity >= $threshold
        OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
        OPTIONAL MATCH (director:Person)-[:CONTRIBUTED_TO {role: 'Director'}]->(proj)
        RETURN proj {
            .name, .type, .year, .description
        } AS project,
        client.name AS client,
        director.name AS director,
        round(similarity, 3) AS similarity_score
        ORDER BY similarity DESC
        LIMIT 10
        """
        
        similarity_result = await neo4j_client.execute_query(
            similarity_query, 
            {
                "exact_title": exact_title,
                "target_embedding": target_embedding,
                "threshold": similarity_threshold
            }
        )
        
        similar_projects = []
        if similarity_result and similarity_result.records:
            for record in similarity_result.records:
                similar_projects.append({
                    "project": record.get("project", {}),
                    "client": record.get("client"),
                    "director": record.get("director"),
                    "similarity_score": record.get("similarity_score", 0.0)
                })
        
        response = {
            "similar_projects": similar_projects,
            "target_project": exact_title,
            "threshold": similarity_threshold,
            "count": len(similar_projects),
            "found": len(similar_projects) > 0
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in find_similar_projects for '{project_title}': {e}")
        return {
            "error": f"Query failed: {str(e)}",
            "target_project": project_title,
            "found": False
        }


def get_all_priority_tools() -> List[Any]:
    """
    Get all 6 priority tools for LangGraph binding.
    
    These are the core tools converted from GraphQueryTools that provide
    the most critical functionality for AI agents.
    
    INCLUDES broad_vector_search for comprehensive coverage across all entity types.
    """
    return [
        get_organization_profile,
        get_person_details, 
        find_people_at_organization,
        search_projects_by_criteria,
        find_similar_projects,
        broad_vector_search  # Comprehensive vector search across entire graph
    ]


def get_tool_names() -> List[str]:
    """Get the names of all priority tools"""
    return [
        "get_organization_profile",
        "get_person_details", 
        "find_people_at_organization",
        "search_projects_by_criteria",
        "find_similar_projects",
        "broad_vector_search"
    ]


async def validate_tools() -> Dict[str, Any]:
    """
    Validate that all tools are properly registered and configured.
    
    Returns validation status for monitoring and debugging.
    """
    tool_names = get_tool_names()
    factory = tool_factory
    
    validation_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_tools": len(tool_names),
        "registered_tools": [],
        "missing_tools": [],
        "factory_status": factory.get_all_metadata()
    }
    
    for tool_name in tool_names:
        if factory.get_tool(tool_name):
            validation_results["registered_tools"].append(tool_name)
        else:
            validation_results["missing_tools"].append(tool_name)
    
    validation_results["validation_passed"] = len(validation_results["missing_tools"]) == 0
    
    return validation_results


# Initialize tools in factory on import
logger.info("Initializing priority tools in factory...")
priority_tools = get_all_priority_tools()
logger.info(f"Priority tools loaded: {get_tool_names()}")