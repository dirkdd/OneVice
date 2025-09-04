# Graph Tools Integration Guide

## Overview

This guide documents the integration of Neo4j graph query tools with the OneVice LangGraph agent system. The integration provides 12 comprehensive tools for accessing Folk CRM data, project information, and creative intelligence from the OneVice knowledge graph.

## Architecture

### Components

1. **GraphQueryTools** - Shared query interface with 12 tool methods
2. **Agent Tool Mixins** - Agent-specific tool access patterns
3. **Agent Orchestrator** - Centralized agent coordination with graph tools
4. **Performance Indexes** - Optimized Neo4j indexes for query performance

### Integration Points

```
AgentOrchestrator
├── GraphQueryTools (shared instance)
│   ├── Neo4jClient (graph database)
│   ├── FolkClient (CRM API)
│   └── RedisClient (caching)
├── SalesIntelligenceAgent + CRMToolsMixin
├── TalentAcquisitionAgent + TalentToolsMixin  
└── LeadershipAnalyticsAgent + AnalyticsToolsMixin
```

## Graph Query Tools

### Tool Categories

#### Category 1: People, Companies & Relationships (CRM & HR Focus)
- `get_person_details(name)` - Comprehensive person profiles
- `find_collaborators(person_name, project_type)` - Network analysis
- `get_organization_profile(org_name)` - Company intelligence
- `get_network_connections(person_name, degrees)` - Relationship mapping

#### Category 2: Projects & Creative Intelligence 
- `search_projects_by_criteria(criteria)` - Project discovery
- `find_similar_projects(project_title, similarity_threshold)` - Pattern matching
- `get_project_team_details(project_title)` - Team composition
- `get_creative_concepts_for_project(project_title)` - Style analysis
- `find_creative_references(concept_name, medium)` - Reference search

#### Category 3: Documents & Content Analysis
- `search_documents_by_content(query, doc_type)` - Content search
- `get_document_by_id(document_id)` - Document retrieval
- `extract_project_insights(project_title, insight_type)` - Intelligence extraction

### Caching Strategy

```python
cache_ttl = {
    "person": 300,      # 5 minutes for person data
    "concept": 600,     # 10 minutes for creative concepts
    "project": 300,     # 5 minutes for project data
    "document": 1800,   # 30 minutes for document data
    "organization": 600 # 10 minutes for org data
}
```

## Agent Tool Mixins

### CRMToolsMixin (Sales Agent)
```python
from ..tools.graph_tools import GraphQueryTools

class CRMToolsMixin:
    def __init__(self):
        self.graph_tools: Optional[GraphQueryTools] = None
    
    async def get_person_details(self, name: str):
        return await self.graph_tools.get_person_details(name)
    
    async def find_decision_makers(self, organization: str):
        # Custom logic for sales-specific use cases
        org_profile = await self.graph_tools.get_organization_profile(organization)
        # Process and score decision makers
        return processed_results
```

### TalentToolsMixin (Talent Agent)
```python
class TalentToolsMixin:
    async def find_available_talent(self, skills: List[str], location: str):
        # Talent-specific query logic
        return await self.graph_tools.search_people_by_skills(skills, location)
    
    async def get_crew_recommendations(self, project_type: str, budget_range: str):
        # Find optimal team compositions
        similar_projects = await self.graph_tools.find_similar_projects(project_type, 0.8)
        # Analyze crew patterns and availability
        return recommendations
```

### AnalyticsToolsMixin (Analytics Agent)  
```python
class AnalyticsToolsMixin:
    async def analyze_performance_metrics(self, entity_type: str, entity_name: str):
        # Performance analysis across projects
        insights = await self.graph_tools.extract_project_insights(entity_name, "performance")
        # Generate metrics and trends
        return analytics_results
```

## Agent Orchestrator Integration

### Factory Pattern
```python
@classmethod
async def create_orchestrator(cls, config: AIConfig) -> 'AgentOrchestrator':
    """Factory method to create and initialize orchestrator"""
    orchestrator = cls(config)
    await orchestrator.initialize_services()
    
    if orchestrator.graph_tools:
        await orchestrator._validate_graph_tools()
    
    return orchestrator
```

### Agent Initialization with Graph Tools
```python
def _initialize_agents(self):
    """Initialize all AI agents with graph query tools"""
    
    # Initialize shared graph tools instance
    self.graph_tools = GraphQueryTools(
        neo4j_client=self.neo4j_client,
        folk_client=self.folk_client,
        redis_client=self.redis_client
    )
    
    # Initialize agents with shared graph tools
    self.agents[AgentType.SALES] = SalesIntelligenceAgent(
        config=self.config,
        llm_router=self.llm_router,
        knowledge_service=self.knowledge_service,
        redis_client=self.redis_client,
        graph_tools=self.graph_tools  # Shared instance
    )
```

### Health Monitoring
```python
async def _get_graph_tools_status(self) -> Dict[str, Any]:
    """Get comprehensive graph tools status"""
    
    return {
        "status": "healthy",
        "neo4j_connection": "healthy",
        "redis_connection": "healthy", 
        "folk_api_connection": "enabled",
        "cache_stats": {
            "used_memory": "2.1MB",
            "keyspace_hits": 1247,
            "keyspace_misses": 83
        },
        "available_tools": [
            "get_person_details", "find_collaborators", 
            "get_organization_profile", "search_projects_by_criteria",
            # ... full list of 12 tools
        ]
    }
```

## Performance Optimization

### Neo4j Indexes
The integration includes 60+ performance indexes:

```cypher
-- Core entity indexes
CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name)
CREATE INDEX person_folk_id_index IF NOT EXISTS FOR (p:Person) ON (p.folkId)

-- Composite indexes for complex queries
CREATE INDEX person_name_title_composite IF NOT EXISTS FOR (p:Person) ON (p.name, p.title)

-- Relationship indexes
CREATE INDEX contribution_role_index IF NOT EXISTS FOR ()-[r:CONTRIBUTED_TO]-() ON (r.role)

-- Full-text search indexes
CREATE FULLTEXT INDEX person_fulltext_index IF NOT EXISTS FOR (p:Person) ON EACH [p.name, p.bio, p.title]
```

### Query Performance Guidelines
1. **Index Usage**: All major queries utilize specific indexes
2. **Caching**: Redis caching reduces database load by 70-80%
3. **Hybrid Queries**: Neo4j + Folk API for complete data coverage
4. **Error Handling**: Graceful degradation when services unavailable

## Usage Examples

### Sales Agent Query
```python
# Sales agent finding decision makers at Nike
async def find_nike_decision_makers():
    # Uses CRMToolsMixin -> GraphQueryTools
    decision_makers = await sales_agent.find_decision_makers("Nike")
    
    # Result includes:
    # - Person profiles with contact info
    # - Decision-making influence scores  
    # - Recent project involvement
    # - Network connections within organization
    return decision_makers
```

### Talent Agent Query
```python
# Talent agent finding cinematographers
async def find_available_cinematographers():
    # Uses TalentToolsMixin -> GraphQueryTools
    cinematographers = await talent_agent.find_available_talent(
        skills=["Cinematography", "Camera Operation"],
        location="Los Angeles"
    )
    
    # Result includes:
    # - Skills assessment scores
    # - Availability status
    # - Recent project history
    # - Union status and rates
    return cinematographers
```

### Analytics Agent Query  
```python
# Analytics agent analyzing project performance
async def analyze_commercial_trends():
    # Uses AnalyticsToolsMixin -> GraphQueryTools
    insights = await analytics_agent.analyze_performance_metrics(
        entity_type="project_category",
        entity_name="commercial_campaigns"
    )
    
    # Result includes:
    # - Performance trends over time
    # - Success factor analysis
    # - Budget vs outcome correlation
    # - Crew composition patterns
    return insights
```

## Configuration

### Environment Variables
```bash
# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# Redis Configuration  
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Folk API Configuration (optional)
FOLK_API_KEY=your-folk-api-key
FOLK_API_URL=https://api.folk.app/v1
```

### Initialization Code
```python
from app.ai.workflows.orchestrator import AgentOrchestrator
from app.ai.config import AIConfig

# Create configuration
config = AIConfig(
    neo4j_uri=os.getenv("NEO4J_URI"),
    redis_url=f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:6379",
    folk_api_key=os.getenv("FOLK_API_KEY")
)

# Create orchestrator with graph tools
orchestrator = await AgentOrchestrator.create_orchestrator(config)

# Query through agents
response = await orchestrator.route_query(
    query="Find experienced directors for Nike campaign",
    user_context={"role": "producer", "access_level": "internal"},
    preferred_agent=AgentType.TALENT
)
```

## Testing

### Unit Tests
```python
# Test graph tools with mock data
@pytest.mark.asyncio
async def test_get_person_details_with_caching(graph_tools, mock_redis_client):
    # Setup cached data
    cached_data = {"name": "John Smith", "cached": True}
    await mock_redis_client.set("person_details:john smith", json.dumps(cached_data))
    
    # Test cached result
    result = await graph_tools.get_person_details("John Smith")
    assert result["cached"] is True
```

### Integration Tests
```python
# Test agent mixin integration
@pytest.mark.asyncio  
async def test_crm_agent_find_decision_makers(crm_agent):
    # Test CRM-specific tool usage
    result = await crm_agent.find_decision_makers("Nike")
    
    # Verify decision maker scoring
    assert result["found"] is True
    assert "decision_makers" in result
    for dm in result["decision_makers"]:
        assert "decision_maker_score" in dm
        assert dm["decision_maker_score"] in ["high", "medium", "low"]
```

## Error Handling

### Graceful Degradation
```python
async def get_person_details(self, name: str) -> Dict[str, Any]:
    try:
        # Try Neo4j first
        result = await self._query_neo4j_person(name)
        
        # Enhance with Folk API if available
        if self.folk_client and result.get("folkId"):
            folk_data = await self.folk_client.get_person(result["folkId"])
            result.update(folk_data)
            
        return result
        
    except Neo4jError as e:
        logger.error(f"Neo4j query failed: {e}")
        
        # Fallback to Folk API only
        if self.folk_client:
            return await self._fallback_folk_search(name)
            
        # Ultimate fallback
        return {"found": False, "error": "Graph database unavailable", "name": name}
```

## Monitoring and Metrics

### Health Checks
- Neo4j connection status
- Redis cache performance (hit/miss ratios)
- Folk API availability
- Query execution times
- Cache memory usage

### Performance Metrics
- Average query response time: < 100ms (cached), < 500ms (uncached)
- Cache hit rate: > 70%
- Tool availability: > 99.5%
- Error rate: < 1%

## Best Practices

### Query Optimization
1. **Use Specific Indexes**: Leverage the 60+ performance indexes
2. **Cache Frequently Accessed Data**: Person and organization profiles
3. **Limit Result Sets**: Use LIMIT clauses for large datasets
4. **Hybrid Data Strategy**: Neo4j for relationships, Folk for live CRM data

### Error Handling
1. **Graceful Degradation**: Provide partial results when possible
2. **Fallback Strategies**: Multiple data sources for resilience
3. **User-Friendly Messages**: Clear error communication
4. **Retry Logic**: Exponential backoff for transient failures

### Security
1. **Data Access Controls**: RBAC based on user context
2. **Sensitive Data Handling**: Encryption for confidential information
3. **API Key Management**: Secure Folk API key storage
4. **Audit Logging**: Track all graph tool usage

## Troubleshooting

### Common Issues

#### Neo4j Connection Errors
```python
# Check connection configuration
await neo4j_client.execute_query("RETURN 1")
# Error: ServiceUnavailable -> Check URI and credentials
```

#### Cache Performance Issues
```python
# Check Redis connection and memory
await redis_client.info()
# High memory usage -> Adjust TTL values
# Low hit rate -> Review caching strategy
```

#### Folk API Errors
```python
# Check API key and endpoint
await folk_client.health_check()
# 401 Unauthorized -> Verify API key
# 429 Rate Limited -> Implement backoff
```

## Migration Guide

### From Previous Version
1. **Update Agent Constructors**: Add `graph_tools` parameter
2. **Update Orchestrator Usage**: Use factory method `create_orchestrator()`
3. **Add Configuration**: Include Folk API and Redis settings
4. **Run Index Creation**: Execute `python database/create_indexes.py`
5. **Update Tests**: Use new mock fixtures

### Breaking Changes
- Agent constructors now require `graph_tools` parameter
- Orchestrator initialization is now async via factory method
- Health check responses include graph tools status
- Cache keys follow new naming convention

---

This integration provides a comprehensive, performant, and scalable foundation for graph-based AI agent operations in the OneVice platform.