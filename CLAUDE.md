# OneVice AI-Powered Business Intelligence Platform

This file provides context for Claude Code instances working with the OneVice repository.

## Project Overview

OneVice is an AI-powered business intelligence hub for the entertainment industry, built with a modern tech stack focused on data sovereignty and intelligent agent orchestration.

### Core Architecture
- **Monorepo Structure**: Frontend (Next.js) and Backend (Python/FastAPI) workspaces
- **Frontend**: Next.js 15.5.2 with React 19, Tailwind CSS 4, TypeScript
- **Backend**: Python FastAPI with LangGraph 0.6.6+ for multi-agent orchestration
- **Databases**: Neo4j Aura (graph), PostgreSQL (structured), Redis (cache)
- **LLM Stack**: Together.ai (primary), Anthropic Claude (fallback)
- **Authentication**: Clerk with Okta SSO integration
- **Deployment**: Render platform with managed services

## Repository Structure

```
/
├── frontend/                 # Next.js application
│   ├── package.json         # React 19, Next.js 15.5.2, Tailwind CSS 4
│   └── .env.local           # Frontend environment variables
├── backend/                 # Python FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Backend environment variables
│   ├── database/           # Neo4j schema and connection management
│   ├── llm/                # LLM router with Together.ai integration
│   └── test_connections.py # Database connection testing utility
├── docs/                   # Comprehensive project documentation
│   ├── technical-roadmap.md # Primary implementation guide (1544 lines)
│   ├── prd.md              # Product requirements
│   ├── system-architecture.md
│   └── database-schema.md
├── render.yaml             # Infrastructure as Code for Render deployment
└── package.json           # Root workspace configuration
```

## Key Technologies & Versions

### Frontend Stack
- Next.js 15.5.2 with Turbopack for development
- React 19.1.0 (stable)
- Tailwind CSS 4 with PostCSS
- TypeScript 5+ with strict configuration
- ESLint with Next.js configuration

### Backend Stack
- Python FastAPI with async/await patterns
- LangGraph 0.6.6+ for multi-agent orchestration
- Neo4j Python driver for graph operations
- Redis for session management and caching
- Uvicorn ASGI server

### Data Layer
- **Neo4j Aura**: Graph database with vector indexes (1536 dimensions)
- **PostgreSQL**: Structured data via Render managed service
- **Redis**: Session store and caching via Redis Cloud

### AI/ML Integration
- **Together.ai**: Primary LLM provider (Mixtral, Llama 3 models)
- **Anthropic Claude**: Fallback provider for high-sensitivity operations
- **LangSmith**: Observability and tracing
- **Vector Search**: Hybrid graph + vector retrieval

## Common Commands

### Development Setup
```bash
# Install all dependencies
npm run setup

# Start frontend only
npm run dev

# Start backend only
npm run dev:backend

# Start both frontend and backend
npm run dev:full

# Test database connections
cd backend && python test_connections.py
```

### Build and Deploy
```bash
# Build frontend
npm run build

# Start production frontend
npm run start

# Backend production (auto-configured for Render)
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

## Environment Configuration

### Required Environment Variables

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=https://onevice-backend.onrender.com
NEXT_PUBLIC_WS_URL=wss://onevice-backend.onrender.com/ws
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=[clerk-key]
```

**Backend (.env):**
```
# Database Connections
DATABASE_URL=[postgresql-connection-string]
NEO4J_URI=[neo4j-aura-connection]
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=[neo4j-password]
REDIS_HOST=[redis-host]
REDIS_PORT=[redis-port]
REDIS_PASSWORD=[redis-password]

# LLM API Keys
TOGETHER_API_KEY=[together-api-key]
ANTHROPIC_API_KEY=[anthropic-api-key]

# Authentication
CLERK_SECRET_KEY=[clerk-secret]
OKTA_CLIENT_ID=[okta-client-id]
OKTA_CLIENT_SECRET=[okta-client-secret]

# Security
JWT_SECRET_KEY=[jwt-secret]
ENCRYPTION_KEY=[encryption-key]
```

## Database Schema

#### Neo4j Entertainment Industry Schema
- **Entities**: Person, Project, Company, Location, Skill, Equipment
- **Relationships**: DIRECTED, WORKED_ON, EMPLOYED_BY, COLLABORATES_WITH
- **Indexes**: Vector search (bio_embedding, project_embedding) for hybrid retrieval
- **Access Patterns**: Graph traversal + vector similarity for AI agent queries

### Neo4j Connection Configuration
- **Driver Version**: 5.15.0+ (tested with Python driver 5.28.1)
- **URI Schemes**: neo4j+s:// for encrypted Aura connections
- **Authentication**: Standard username/password auth
- **Connection Pooling**: Max 100 connections, 1-hour lifetime

### Data Sensitivity Levels (RBAC)
1. **PUBLIC**: General industry information
2. **INTERNAL**: Company-specific data
3. **CONFIDENTIAL**: Project details
4. **RESTRICTED**: Financial information
5. **HIGHLY_CONFIDENTIAL**: Strategic information
6. **TOP_SECRET**: Executive-level data

## LLM Integration Patterns

### Security-First Routing
- **Together.ai**: Default for sensitive data (levels 1-4)
- **Anthropic**: Fallback and high-security operations (levels 5-6)
- **Model Selection**: Automatic based on query complexity and data sensitivity

### Common LLM Operations
```python
# Route query based on sensitivity
model = await llm_router.get_optimal_model(
    query="Find similar directors",
    user_role=UserRole.ANALYST,
    data_sensitivity=DataSensitivityLevel.INTERNAL.value
)

# Execute with monitoring
response = await llm_router.chat_completion(
    model=model,
    messages=[{"role": "user", "content": query}],
    stream=True
)
```

## Development Workflow

### Phase-Based Implementation
1. **Phase 1**: Infrastructure setup and documentation migration ✅
2. **Phase 2**: Environment configuration and database connections ✅
3. **Phase 3**: Core schema implementation ✅
4. **Phase 4**: LLM integration and routing ✅
5. **Phase 5**: Authentication and authorization (In Progress)
6. **Phase 6**: Agent orchestration and workflows
7. **Phase 7**: Frontend components and UX
8. **Phase 8**: Production deployment and monitoring

### Testing Strategy
- **Database**: Use `test_connections.py` to verify all database connections
- **LLM**: Test model routing with different sensitivity levels
- **Frontend**: Next.js built-in testing with React Testing Library
- **E2E**: Planned Playwright integration for user journey testing

## Deployment Configuration

### Render Platform
- **Frontend**: Static site with Next.js build optimization
- **Backend**: Web service with uvicorn ASGI server
- **Databases**: Managed PostgreSQL and Redis services
- **Environment**: Production environment variables via Render dashboard

### Health Monitoring
- Backend health endpoint: `/health`
- Frontend health check: `/api/health`
- Database connection monitoring via connection manager
- LLM provider fallback and error handling

## Security Considerations

### Data Protection
- **Encryption**: All sensitive environment variables encrypted at rest
- **RBAC**: Role-based access control with 6-tier sensitivity model
- **LLM Security**: Data sovereignty via Together.ai for sensitive operations
- **Authentication**: Clerk + Okta SSO with JWT token validation

### Development Security
- No secrets in code - all sensitive data via environment variables
- Separate development and production environment configurations
- Database connection encryption (SSL) for all external connections

## Neo4j Troubleshooting Guide

### Known Driver Compatibility Issues

**Python Driver Version 5.28.1 Changes:**
- **max_retry_time parameter removed**: No longer supported, causes initialization failure
- **encrypted parameter conflicts**: Cannot be used with neo4j+s:// or bolt+s:// URI schemes
- **SummaryCounters serialization**: Use `._raw_data` attribute if available, fallback to empty dict
- **Result handling changes**: Must collect records before calling consume() on results

### Common Connection Issues

**1. max_retry_time Parameter Error**
```python
# ❌ WRONG - Causes "unexpected keyword argument 'max_retry_time'"
driver = GraphDatabase.driver(uri, auth=auth, max_retry_time=30)

# ✅ CORRECT - Parameter removed in v5.28.1
driver = GraphDatabase.driver(uri, auth=auth)
```

**2. Encrypted Parameter Conflicts**
```python
# ❌ WRONG - encrypted=True conflicts with neo4j+s:// scheme
driver = GraphDatabase.driver("neo4j+s://host:7687", auth=auth, encrypted=True)

# ✅ CORRECT - Encryption handled by URI scheme
driver = GraphDatabase.driver("neo4j+s://host:7687", auth=auth)
```

**3. Query Result Handling**
```python
# ❌ WRONG - Cannot access result.records after consume()
result = session.run("MATCH (n) RETURN n")
summary = result.consume()
records = result.records  # Will fail - records no longer available

# ✅ CORRECT - Collect records first, then consume for summary
result = session.run("MATCH (n) RETURN n")
records = [record.data() for record in result]
summary = result.consume()
```

**4. SummaryCounters Serialization**
```python
# ❌ WRONG - Direct serialization may fail
summary_data = {"counters": summary.counters}

# ✅ CORRECT - Use _raw_data with fallback
summary_data = {
    "counters": summary.counters._raw_data if hasattr(summary.counters, '_raw_data') else {}
}
```

### Environment Configuration

**Development (.env):**
```bash
NEO4J_URI=neo4j+s://dev-database-id.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-dev-password
NEO4J_DATABASE=neo4j
```

**Production (Render):**
```bash
NEO4J_URI=neo4j+s://prod-database-id.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-secure-prod-password
NEO4J_DATABASE=neo4j
```

### Connection Best Practices

1. **Use Connection Pooling**: Configure max_connection_pool_size for concurrent access
2. **Set Timeouts**: Use connection_timeout to prevent hanging connections
3. **Health Checks**: Implement periodic connectivity verification
4. **Error Handling**: Use try-catch blocks for all database operations
5. **Resource Cleanup**: Always close drivers and sessions properly

### Debugging Connection Issues

**Test Connection Script:**
```python
from neo4j import GraphDatabase

try:
    driver = GraphDatabase.driver(uri, auth=(username, password))
    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        print(f"Connection successful: {result.single()['test']}")
    driver.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

**Common Error Messages:**
- `"unexpected keyword argument 'max_retry_time'"` → Remove deprecated parameter
- `"Failed to establish encrypted connection"` → Check URI scheme compatibility
- `"Authentication failure"` → Verify credentials and database access
- `"ServiceUnavailable"` → Check network connectivity and firewall settings

## Documentation Sources

### Primary Guides
- **Primary Guide**: `docs/technical-roadmap.md` (most comprehensive implementation guide)
- **Database Design**: `docs/database-schema.md`
- **System Architecture**: `docs/system-architecture.md`
- **Product Requirements**: `docs/prd.md`

### Neo4j-Specific Documentation
- **Configuration Guide**: `docs/neo4j-configuration-guide.md` (comprehensive setup and best practices)
- **Driver Compatibility**: `docs/neo4j-driver-compatibility.md` (version-specific implementation patterns)
- **Troubleshooting Guide**: `docs/neo4j-troubleshooting-guide.md` (connection issues and solutions)
- **Environment Setup**: `docs/neo4j-environment-setup.md` (environment variable configuration)
- **Schema Procedures**: `docs/neo4j-schema-procedures.md` (schema setup and validation)

### Infrastructure
- **Infrastructure**: `render.yaml`

## Repository Information

- **Repository**: https://github.com/dirkdd/OneVice.git
- **Primary Branch**: main
- **License**: MIT
- **Maintainer**: OneVice Team
- **Current Version**: 2.0

---

*This file is automatically maintained. Update when major architecture changes occur.*