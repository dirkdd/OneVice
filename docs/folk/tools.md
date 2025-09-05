### **Agent Tooling Specification Document**

**Objective:** To define a complete set of tools (functions) that LangGraph agents can use to query, analyze, and retrieve information from the London Alley Neo4j knowledge graph. These tools will serve as the primary interface between the agent's reasoning engine and the company's unified data asset.

---

## **Implementation Architecture**

### **Integration Strategy: Direct Neo4j Library Connection**

After comprehensive analysis of MCP Neo4j server vs direct library integration, we recommend **direct Neo4j library integration** for optimal performance:

**Key Benefits:**
- **Zero Latency**: Direct database connection eliminates MCP protocol overhead
- **Existing Infrastructure**: Leverages production-ready `backend/database/neo4j_client.py`
- **Full Control**: Complete query optimization and connection management
- **LangGraph Integration**: Seamless fit with existing BaseAgent architecture
- **Hybrid Model Support**: Efficient Folk API + graph data combination

### **Implementation Architecture Pattern**

```python
# backend/app/ai/tools/graph_tools.py
from ..agents.base_agent import BaseAgent
from ...database.neo4j_client import Neo4jClient
from ...tools.folk_ingestion.folk_client import FolkClient

class GraphQueryTools:
    """Neo4j graph query tools for LangGraph agents"""
    
    def __init__(self, neo4j_client: Neo4jClient, folk_client: FolkClient = None, redis_client = None):
        self.neo4j_client = neo4j_client
        self.folk_client = folk_client  # For hybrid queries
        self.redis_client = redis_client  # For query caching
        self.cache_ttl = 300  # 5 minutes default
    
    async def get_person_details(self, name: str) -> Dict[str, Any]:
        """Tool 1.1 implementation with caching"""
        cache_key = f"person_details:{name.lower()}"
        
        # Try cache first
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Execute graph query
        result = await self.neo4j_client.execute_query(query, {"name": name})
        
        # Cache result
        if self.redis_client and result:
            await self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(result))
        
        return result
```

### **BaseAgent Integration Pattern**

```python
# Enhanced BaseAgent with graph tools
class BaseAgent:
    def __init__(self, ...):
        # Existing initialization
        self.graph_tools = GraphQueryTools(
            neo4j_client=neo4j_client,
            folk_client=folk_client,
            redis_client=self.redis_client
        )
    
    async def _analyze_query(self, query: str, user_context: Dict[str, Any]):
        # Agent can now use self.graph_tools.get_person_details() etc.
        pass
```

---

### **Category 1: People, Companies & Relationships (CRM & HR Focus)**

These tools focus on the "who" and "how are they connected" questions, leveraging both production and Folk.app data.

**Tool 1.1: `get_person_details`**
*   **Description:** Retrieves a comprehensive profile for a specific person, including their roles, projects they've worked on, their employer, and any CRM groups they belong to.
*   **Parameters:** `name: str`
*   **Returns:** A dictionary containing the person's details, a list of projects with their roles, and associated organizations.
*   **Implementation Example:**
    ```python
    async def get_person_details(self, name: str) -> Dict[str, Any]:
        cache_key = f"person_details:{name.lower().replace(' ', '_')}"
        
        # Try cache first (5-minute TTL for person data)
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        cypher_query = """
        MATCH (p:Person)
        WHERE p.name CONTAINS $name OR p.fullName CONTAINS $name
        OPTIONAL MATCH (p)-[r:CONTRIBUTED_TO]->(proj:Project)
        OPTIONAL MATCH (p)-[:WORKS_FOR]->(org:Organization)
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(g:Group)
        OPTIONAL MATCH (internal:Person {isInternal: true})-[:OWNS_CONTACT]->(p)
        RETURN p {
            .name, .fullName, .email, .folkId, .isInternal,
            .bio, .skills, .location
        } AS person,
        org.name AS organization,
        collect(DISTINCT {project: proj.title, role: r.role, startDate: r.startDate}) AS projects,
        collect(DISTINCT g.name) AS groups,
        internal.name AS contact_owner
        """
        
        result = await self.neo4j_client.execute_query(
            cypher_query, 
            {"name": name}
        )
        
        if result and self.redis_client:
            await self.redis_client.setex(cache_key, 300, json.dumps(result, default=str))
        
        return result or {"error": "Person not found", "query": name}
    ```

**Tool 1.2: `find_people_at_organization`**
*   **Description:** Finds all people in the graph who are known to work for a specific company or organization.
*   **Parameters:** `organization_name: str`
*   **Returns:** A list of names of people who work at that organization.
*   **Example Cypher Query:**
    ```cypher
    MATCH (p:Person)-[:WORKS_FOR]->(o:Organization)
    WHERE o.name CONTAINS $organization_name
    RETURN p.name
    ```

**Tool 1.3: `get_deal_sourcer`**
*   **Description:** Identifies the internal London Alley team member who sourced a specific deal, with comprehensive relationship context.
*   **Parameters:** `deal_name: str`
*   **Returns:** Details about the internal person who sourced the deal, including their role and sourcing history.
*   **Implementation Example:**
    ```python
    async def get_deal_sourcer(self, deal_name: str) -> Dict[str, Any]:
        cypher_query = """
        MATCH (p:Person {isInternal: true})-[:SOURCED]->(d:Deal)
        WHERE d.name CONTAINS $deal_name
        
        // Get sourcing history for context
        OPTIONAL MATCH (p)-[:SOURCED]->(other_deals:Deal)
        WHERE other_deals <> d
        
        // Get their current role/department
        OPTIONAL MATCH (p)-[:WORKS_FOR]->(dept:Department)
        
        RETURN p {
            .name, .fullName, .email, .folkUserId
        } AS sourcer,
        d {
            .name, .status, .value, .currency, .folkId
        } AS deal,
        dept.name AS department,
        count(other_deals) AS total_deals_sourced,
        collect(other_deals.name)[..3] AS recent_other_deals
        """
        
        result = await self.neo4j_client.execute_query(
            cypher_query, 
            {"deal_name": deal_name}
        )
        
        if not result:
            return {"error": "Deal not found or not sourced by internal team", "query": deal_name}
        
        return result
    ```

**Tool 1.4: `get_deal_details_with_live_status`**
*   **Description:** Retrieves deal information using hybrid approach: rich context from graph + live status from Folk API for maximum accuracy.
*   **Parameters:** `deal_name: str`
*   **Returns:** A dictionary with deal details including live status updates.
*   **Implementation Pattern:**
    ```python
    async def get_deal_details_with_live_status(self, deal_name: str) -> Dict[str, Any]:
        # Step 1: Get rich context from graph (fast, cached)
        graph_query = """
        MATCH (sourcer:Person)-[:SOURCED]->(d:Deal)
        WHERE d.name CONTAINS $deal_name
        OPTIONAL MATCH (d)-[:WITH_CONTACT]->(contact:Person)
        OPTIONAL MATCH (d)-[:FOR_ORGANIZATION]->(org:Organization)
        RETURN d, sourcer.name AS sourced_by, 
               collect(contact.name) AS contacts,
               org.name AS organization
        """
        
        graph_data = await self.neo4j_client.execute_query(graph_query, {"deal_name": deal_name})
        
        # Step 2: Enrich with live Folk API data (if available)
        if graph_data and graph_data.get('d', {}).get('folkId') and self.folk_client:
            try:
                live_status = await self.folk_client.get_deal_status(graph_data['d']['folkId'])
                graph_data['live_status'] = live_status
                graph_data['data_freshness'] = 'live_api_enhanced'
            except Exception as e:
                graph_data['live_status'] = 'api_unavailable'
                graph_data['data_freshness'] = 'graph_only'
        
        return graph_data
    ```

---

### **Category 2: Projects & Creative DNA (Production & Creative Focus)**

These tools are for exploring past work, creative styles, and production details.

**Tool 2.1: `get_project_details`**
*   **Description:** Retrieves a full summary of a project, including its client, managing department, key crew members, and associated creative concepts.
*   **Parameters:** `project_title: str`
*   **Returns:** A dictionary containing the project's details.
*   **Example Cypher Query:**
    ```cypher
    MATCH (proj:Project {title: $project_title})
    OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
    OPTIONAL MATCH (proj)-[:FEATURES_CONCEPT]->(c:CreativeConcept)
    OPTIONAL MATCH (p:Person)-[r:CONTRIBUTED_TO]->(proj)
    RETURN proj, client.name, collect(c.name) AS concepts, collect({person: p.name, role: r.role}) AS crew
    ```

**Tool 2.2: `find_projects_by_concept`**
*   **Description:** Finds all projects that are associated with a specific creative concept, theme, or style (e.g., "Nostalgia", "Dark Humor", "Synthwave").
*   **Parameters:** `concept_name: str`, `include_related: bool = False`
*   **Returns:** A list of project details with concept relationships and similarity scores.
*   **Implementation Example:**
    ```python
    async def find_projects_by_concept(self, concept_name: str, include_related: bool = False) -> List[Dict[str, Any]]:
        cache_key = f"projects_by_concept:{concept_name.lower()}:{include_related}"
        
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Base query for direct concept matches
        base_query = """
        MATCH (proj:Project)-[:FEATURES_CONCEPT]->(c:CreativeConcept)
        WHERE c.name CONTAINS $concept_name
        OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
        OPTIONAL MATCH (director:Person)-[r:CONTRIBUTED_TO {role: 'Director'}]->(proj)
        RETURN proj {
            .title, .projectId, .logline, .status, .year
        } AS project,
        collect(c.name) AS concepts,
        client.name AS client,
        director.name AS director,
        'direct_match' AS match_type
        """
        
        results = await self.neo4j_client.execute_query(
            base_query, 
            {"concept_name": concept_name}
        )
        
        # If include_related is True, also find projects with related concepts
        if include_related and results:
            related_query = """
            MATCH (c1:CreativeConcept)-[:RELATED_TO*1..2]->(c2:CreativeConcept)
            WHERE c1.name CONTAINS $concept_name
            MATCH (proj:Project)-[:FEATURES_CONCEPT]->(c2)
            WHERE NOT proj.title IN $existing_titles
            OPTIONAL MATCH (proj)-[:FOR_CLIENT]->(client:Organization)
            RETURN proj {
                .title, .projectId, .logline, .status, .year
            } AS project,
            collect(c2.name) AS concepts,
            client.name AS client,
            'related_concept' AS match_type
            """
            
            existing_titles = [r['project']['title'] for r in results]
            related_results = await self.neo4j_client.execute_query(
                related_query, 
                {"concept_name": concept_name, "existing_titles": existing_titles}
            )
            
            results.extend(related_results)
        
        # Cache results for 10 minutes (concept relationships change infrequently)
        if results and self.redis_client:
            await self.redis_client.setex(cache_key, 600, json.dumps(results, default=str))
        
        return results
    ```

**Tool 2.3: `find_contributors_on_client_projects`**
*   **Description:** Finds people who performed a specific role on projects for a given client. Useful for questions like "Who has directed for Nike?"
*   **Parameters:** `role: str`, `client_name: str`
*   **Returns:** A list of names.
*   **Example Cypher Query:**
    ```cypher
    MATCH (p:Person)-[r:CONTRIBUTED_TO]->(proj:Project)-[:FOR_CLIENT]->(o:Organization)
    WHERE r.role = $role AND o.name CONTAINS $client_name
    RETURN DISTINCT p.name
    ```

**Tool 2.4: `get_project_vendors`**
*   **Description:** Lists all external vendors that provided services for a specific project.
*   **Parameters:** `project_title: str`
*   **Returns:** A list of dictionaries, each with the vendor's name and the service they provided.
*   **Example Cypher Query:**
    ```cypher
    MATCH (o:Organization)-[r:PROVIDED_SERVICE]->(p:Project {title: $project_title})
    RETURN o.name, r.service
    ```

---

### **Category 3: Document & Content Analysis**

These tools allow the agent to "read" and analyze the content of the documents you've ingested.

**Tool 3.1: `find_documents_for_project`**
*   **Description:** Finds all ingested documents (like pitch decks, call sheets) related to a specific project.
*   **Parameters:** `project_title: str`
*   **Returns:** A list of documents with their types and IDs.
*   **Example Cypher Query:**
    ```cypher
    MATCH (d:Document)-[]->(p:Project {title: $project_title})
    RETURN d.title, d.documentType, d.documentId
    ```

**Tool 3.2: `get_document_profile_details`**
*   **Description:** Retrieves specific, structured information from the JSON `profile` of a document. Can be used to get a director's statement, a logline, or the color palette from a pitch deck.
*   **Parameters:** `document_id: str`, `json_path: str` (e.g., `'$.creative_rationale.director_statement'`)
*   **Returns:** The value from the specified path in the document's profile.
*   **Note:** This tool would execute a Cypher query to get the document node, then process the `profile` property in Python.

**Tool 3.3: `search_documents_full_text`**
*   **Description:** Performs a keyword search across the full text of all ingested documents using Neo4j full-text search capabilities.
*   **Parameters:** `search_query: str`, `limit: int = 10`
*   **Returns:** A list of document titles and relevant text snippets that match the query, ranked by relevance.
*   **Implementation Pattern:**
    ```python
    async def search_documents_full_text(self, search_query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # Use Neo4j full-text search with ranking
        cypher_query = """
        CALL db.index.fulltext.queryNodes('documentTextIndex', $search_query)
        YIELD node, score
        MATCH (node:Document)
        RETURN node.title AS title, 
               node.documentType AS type,
               node.documentId AS id,
               score,
               node.fullTextContent AS content
        ORDER BY score DESC
        LIMIT $limit
        """
        
        results = await self.neo4j_client.execute_query(
            cypher_query, 
            {"search_query": search_query, "limit": limit}
        )
        
        # Extract relevant snippets around search terms
        for result in results:
            result['snippet'] = self._extract_snippet(result['content'], search_query)
        
        return results
    
    def _extract_snippet(self, content: str, search_query: str, snippet_length: int = 200) -> str:
        """Extract relevant text snippet around search terms"""
        # Implementation for context-aware snippet extraction
        pass
    ```
*   **Index Requirement:** Requires `documentTextIndex` full-text index (see indexing section above)

---

---

## **Comprehensive Neo4j Index Requirements**

### **Performance-Critical Indexes**

These indexes are essential for tool performance and must be created before deployment:

```cypher
-- ================================================================================
-- CORE ENTITY INDEXES (Required for all tools)
-- ================================================================================

-- Person entity indexes (Tools 1.1, 1.2, 1.3, 2.3)
CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX person_internal_filter IF NOT EXISTS FOR (p:Person) ON (p.isInternal);
CREATE INDEX person_folk_id_index IF NOT EXISTS FOR (p:Person) ON (p.folkId);

-- Organization entity indexes (Tools 1.2, 2.3, 2.4)
CREATE INDEX organization_name_index IF NOT EXISTS FOR (o:Organization) ON (o.name);
CREATE INDEX organization_folk_id_index IF NOT EXISTS FOR (o:Organization) ON (o.folkId);

-- Project entity indexes (Tools 2.1, 2.3, 2.4, 3.1)
CREATE INDEX project_title_index IF NOT EXISTS FOR (p:Project) ON (p.title);
CREATE INDEX project_id_index IF NOT EXISTS FOR (p:Project) ON (p.projectId);

-- Creative Concept indexes (Tool 2.2)
CREATE INDEX creative_concept_name_index IF NOT EXISTS FOR (c:CreativeConcept) ON (c.name);

-- Document entity indexes (Tools 3.1, 3.2)
CREATE INDEX document_id_index IF NOT EXISTS FOR (d:Document) ON (d.documentId);
CREATE INDEX document_type_index IF NOT EXISTS FOR (d:Document) ON (d.documentType);

-- ================================================================================
-- FOLK INTEGRATION INDEXES (Dynamic Custom Objects)
-- ================================================================================

-- Deal entity indexes (Tools 1.3, 1.4)
CREATE INDEX deal_name_index IF NOT EXISTS FOR (d:Deal) ON (d.name);
CREATE INDEX deal_folk_id_index IF NOT EXISTS FOR (d:Deal) ON (d.folkId);
CREATE INDEX deal_status_index IF NOT EXISTS FOR (d:Deal) ON (d.status);

-- Dynamic custom object indexes (created by Folk ingestion tool)
-- These are created dynamically for discovered entity types:
-- CREATE INDEX {entity_type}_name_index IF NOT EXISTS FOR (o:{EntityType}) ON (o.name);
-- CREATE INDEX {entity_type}_folk_id_index IF NOT EXISTS FOR (o:{EntityType}) ON (o.folkId);

-- ================================================================================
-- FULL-TEXT SEARCH INDEXES (Tool 3.3 and flexible name matching)
-- ================================================================================

-- Document full-text search (Tool 3.3)
CREATE FULLTEXT INDEX documentTextIndex IF NOT EXISTS 
FOR (d:Document) ON EACH [d.fullTextContent, d.title, d.description];

-- Multi-entity name search (flexible matching across all tools)
CREATE FULLTEXT INDEX entityNamesIndex IF NOT EXISTS 
FOR (n:Person|Organization|Project|Deal|CreativeConcept) ON EACH [n.name, n.title];

-- ================================================================================
-- COMPOSITE INDEXES (Multi-property queries)
-- ================================================================================

-- Person-Organization relationship queries (Tool 1.2)
CREATE INDEX person_org_composite IF NOT EXISTS FOR ()-[r:WORKS_FOR]-() ON (r.startDate, r.endDate);

-- Project-Person contribution queries (Tools 2.1, 2.3)
CREATE INDEX contribution_role_index IF NOT EXISTS FOR ()-[r:CONTRIBUTED_TO]-() ON (r.role);

-- Project-Client relationship queries (Tool 2.3)
CREATE INDEX project_client_composite IF NOT EXISTS FOR ()-[r:FOR_CLIENT]-() ON (r.contractValue, r.startDate);
```

### **Index Management Integration**

Integrate index creation with the existing schema manager:

```python
# backend/database/schema_manager.py - Enhanced with tool indexes
class SchemaManager:
    async def create_tool_performance_indexes(self) -> Dict[str, bool]:
        """Create all indexes required for optimal tool performance"""
        indexes = [
            "CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX organization_name_index IF NOT EXISTS FOR (o:Organization) ON (o.name)",
            # ... all indexes from above
        ]
        
        results = {}
        for index_query in indexes:
            try:
                await self.execute_query(index_query)
                results[index_query] = True
            except Exception as e:
                logger.error(f"Index creation failed: {index_query} - {e}")
                results[index_query] = False
        
        return results
    
    async def create_dynamic_folk_indexes(self, entity_types: List[str]) -> Dict[str, bool]:
        """Create indexes for discovered Folk custom object types"""
        results = {}
        for entity_type in entity_types:
            indexes = [
                f"CREATE INDEX {entity_type.lower()}_name_index IF NOT EXISTS FOR (o:{entity_type}) ON (o.name)",
                f"CREATE INDEX {entity_type.lower()}_folk_id_index IF NOT EXISTS FOR (o:{entity_type}) ON (o.folkId)"
            ]
            
            for index_query in indexes:
                try:
                    await self.execute_query(index_query)
                    results[f"{entity_type}_{index_query.split('_')[1]}"] = True
                except Exception as e:
                    logger.error(f"Dynamic index creation failed: {index_query} - {e}")
                    results[f"{entity_type}_{index_query.split('_')[1]}"] = False
        
        return results
```

### **Performance Optimization Strategy**

1. **Query Caching**: Redis-based caching for frequently accessed data (5-minute TTL)
2. **Connection Pooling**: Leverage existing Neo4j connection pool (max 100 connections)
3. **Batch Operations**: Group related queries to minimize round trips
4. **Index Monitoring**: Regular performance analysis of query execution plans

---

## **Integration Checklist**

### **Pre-Implementation Requirements**

- [ ] **Neo4j Client**: Verify `backend/database/neo4j_client.py` is production-ready
- [ ] **Schema Manager**: Confirm dynamic constraint creation capabilities
- [ ] **Redis Client**: Ensure Redis is available for query caching
- [ ] **Folk Client**: Verify `backend/tools/folk_ingestion/folk_client.py` for hybrid queries
- [ ] **BaseAgent Framework**: Confirm LangGraph integration in `app/ai/agents/base_agent.py`

### **Implementation Steps**

1. **Create GraphQueryTools Class**: Implement tool interface layer
2. **Integrate with BaseAgent**: Add graph tools as agent capabilities
3. **Create Performance Indexes**: Execute all required index creation scripts
4. **Implement Caching Strategy**: Redis-based query result caching
5. **Add Error Handling**: Integrate with existing error management patterns
6. **Test Tool Performance**: Validate query execution times and caching effectiveness

### **Success Metrics**

- **Query Performance**: < 100ms for cached queries, < 500ms for complex graph traversals
- **Cache Hit Rate**: > 70% for frequently accessed person/organization data
- **API Integration**: < 200ms additional latency for Folk hybrid queries
- **Error Recovery**: Graceful degradation when Folk API unavailable

By implementing this comprehensive tooling specification, LangGraph agents will have high-performance access to the complete OneVice knowledge graph, seamlessly blending production data, Folk CRM insights, and creative intelligence in a unified, scalable system.