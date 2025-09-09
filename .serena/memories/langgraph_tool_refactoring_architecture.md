# LangGraph Tool Refactoring - Comprehensive Architecture Analysis

## Project Context
OneVice backend has a GraphQueryTools class with 26 async methods (1,678 lines) that need to be converted to LangGraph @tool functions. Current architecture uses:
- LangGraph 0.6.6+ with StateGraph workflows
- Neo4j (5.15.0+) with async client and connection pooling (100 max connections)
- Redis caching with async client
- FastAPI backend with dependency injection patterns

## Key Files Analyzed
- `/backend/app/ai/tools/graph_tools.py`: 26 methods in GraphQueryTools class
- `/backend/app/ai/agents/base_agent.py`: LangGraph StateGraph integration
- `/backend/app/ai/tools/tool_mixins.py`: CRM/Talent/Analytics mixins
- `/backend/database/neo4j_client.py`: Async Neo4j client with connection management
- `/backend/app/ai/llm/router.py`: LLM routing with Together.ai primary

## Current Challenges Identified
1. **Dependency Injection**: GraphQueryTools.__init__ takes neo4j_client, folk_client, redis_client
2. **Async Patterns**: All methods are async, need LangGraph ToolNode compatibility
3. **Caching Logic**: Redis caching embedded in methods, needs extraction
4. **Error Handling**: Try/catch blocks need centralization 
5. **Connection Pooling**: Neo4j pool optimization for concurrent tools
6. **Testing**: Mocking strategy for database dependencies

## Recommended Architecture

### 1. Factory Pattern with Dependency Injection (PREFERRED)
```python
class ToolFactory:
    def __init__(self, neo4j_client, folk_client=None, redis_client=None):
        # Store dependencies
    
    def create_tools(self) -> Dict[str, Callable]:
        @tool
        async def get_person_details(name: str) -> Dict[str, Any]:
            # Access self.neo4j_client, self.redis_client here
        return {"get_person_details": get_person_details, ...}
```

### 2. Error Handling Strategy
- **Tenacity**: Exponential backoff retry (3 attempts)
- **Circuit Breaker**: Protect against cascade failures
- **Structured Responses**: Consistent error format across tools
- **Connection Management**: Semaphore for concurrency control (10-15 max)

### 3. Caching Architecture
- **Redis-backed**: Deterministic cache keys using parameter hashing
- **TTL Strategy**: person(5min), project(5min), concept(10min), document(30min)
- **Cache-aside**: Fallback execution on cache miss
- **JSON Serialization**: Handle datetime/complex objects

### 4. Performance Optimization
- **Connection Pooling**: Use existing Neo4j pool (100 connections)
- **Concurrency Control**: Semaphore-based limiting
- **Performance Monitoring**: Track execution times, error rates
- **Memory Management**: Async context managers

### 5. Testing Strategy
- **Unit Tests**: Mock dependencies with pytest-asyncio
- **Integration Tests**: Real Neo4j/Redis connections
- **Fixtures**: Reusable mock dependencies and sample data
- **Coverage**: All error paths and edge cases

### 6. Production Deployment
- **Feature Flags**: Gradual tool migration
- **A/B Routing**: Between legacy and new implementations
- **Monitoring**: Performance metrics and error tracking
- **Rollback**: Instant fallback capability

## Implementation Plan (10 Phases)
1. Create new tool architecture files structure
2. Implement ToolFactory with dependency injection
3. Convert first 5 GraphQueryTools methods to @tool functions
4. Implement caching, error handling, and performance monitoring
5. Create comprehensive test suite for new tools
6. Implement feature flag system for gradual migration
7. Update agent classes to use new tool architecture
8. Performance testing and optimization
9. Full migration of remaining 21 tools
10. Documentation and knowledge transfer

## Key Benefits
- ✅ Type Safety: Pydantic schemas with validation
- ✅ Performance: Connection pooling + caching + concurrency control
- ✅ Reliability: Circuit breakers + retries + error handling
- ✅ Testability: Comprehensive mock + integration test strategy
- ✅ Maintainability: Clean separation of concerns + dependency injection
- ✅ Production Ready: Feature flags + monitoring + gradual migration

## Next Steps
Start with most used tools: get_person_details, get_organization_profile, find_people_at_organization. Use Factory pattern for simplicity and type safety. Implement comprehensive testing from day one.

## Risk Mitigation
- Feature flags enable instant rollback
- Comprehensive test coverage prevents regressions
- Performance monitoring catches issues early
- Gradual migration reduces blast radius