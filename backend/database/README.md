# OneVice Database Schema Implementation

This module provides production-ready Neo4j database schema implementation for the OneVice entertainment industry intelligence platform.

## Overview

The OneVice database schema is specifically designed for entertainment industry data with focus on:

- **Person entities**: Directors, Creative Directors, Producers, and other industry professionals
- **Project entities**: Music Videos, Commercials, Films with proper classification
- **Organization entities**: Production Companies, Agencies, Clients
- **Document entities**: Scripts, Treatments, Presentations
- **Vector search capabilities**: Hybrid search combining graph traversal with semantic similarity

## Architecture

```
database/
├── __init__.py                 # Module exports
├── neo4j_client.py            # Neo4j connection and query execution
├── schema_manager.py          # Schema definition and management
├── connection_manager.py      # Connection coordination and health
├── setup_schema.py           # Schema initialization script
├── test_connections.py       # Comprehensive testing utility
├── monitoring.py             # Production monitoring and alerting
└── README.md                 # This documentation
```

## Quick Start

### 1. Environment Configuration

Set up your Neo4j environment variables:

```bash
# Neo4j Aura Configuration
export NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your-secure-password"
export NEO4J_DATABASE="neo4j"

# Optional Configuration
export NEO4J_MAX_CONNECTION_POOL_SIZE="100"
export NEO4J_CONNECTION_TIMEOUT="30"
export NEO4J_ENCRYPTED="true"
```

### 2. Initialize Database Schema

Run the schema setup script to create all constraints and indexes:

```bash
# Basic schema creation
python backend/database/setup_schema.py

# With verbose logging
python backend/database/setup_schema.py --verbose

# Validate existing schema only
python backend/database/setup_schema.py --validate-only

# Drop and recreate schema (DANGEROUS)
python backend/database/setup_schema.py --drop-existing --force
```

### 3. Test Database Connection

Verify your database setup with comprehensive testing:

```bash
# Basic connection test
python backend/database/test_connections.py

# Include performance benchmarking
python backend/database/test_connections.py --include-performance

# Save detailed report
python backend/database/test_connections.py --output-file test_report.json
```

## Core Components

### Neo4j Client (`neo4j_client.py`)

Production-ready Neo4j client with:
- Async connection management with automatic retry
- Transaction support with rollback capabilities
- Connection health monitoring
- Query performance tracking
- Connection pooling optimization

```python
from database import Neo4jClient, ConnectionConfig

# Initialize client
config = ConnectionConfig(
    uri="neo4j+s://your-instance.databases.neo4j.io:7687",
    username="neo4j",
    password="your-password"
)
client = Neo4jClient(config)

# Connect and execute queries
await client.connect()
result = await client.execute_query("MATCH (n:Person) RETURN count(n)")

# Use transactions
async with client.transaction() as tx:
    await tx.run("CREATE (p:Person {name: $name})", {"name": "John Doe"})
    await tx.run("CREATE (p:Person {name: $name})", {"name": "Jane Smith"})
```

### Schema Manager (`schema_manager.py`)

Manages the complete entertainment industry schema:

```python
from database import SchemaManager, Neo4jClient

schema_manager = SchemaManager(neo4j_client)

# Create complete schema
result = await schema_manager.create_core_schema()

# Validate existing schema
validation = await schema_manager.validate_schema()
print(f"Schema valid: {validation.valid}")

# Get schema documentation
docs = schema_manager.get_schema_documentation()
```

### Connection Manager (`connection_manager.py`)

Coordinates all database connections and provides health monitoring:

```python
from database import ConnectionManager, initialize_database

# Initialize with automatic schema setup
init_result = await initialize_database(ensure_schema=True)

# Get connection manager
connection_manager = init_result["connection_manager"]

# Access Neo4j client through manager
neo4j = connection_manager.neo4j

# Access schema manager
schema = connection_manager.schema

# Health check
health = await connection_manager.health_check()
print(f"Overall status: {health['overall_status']}")
```

## Database Schema

### Core Constraints

The schema implements unique constraints for all primary entities:

```cypher
-- Person entities
CREATE CONSTRAINT person_id_unique FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT person_email_unique FOR (p:Person) REQUIRE p.email IS UNIQUE;

-- Project entities  
CREATE CONSTRAINT project_id_unique FOR (p:Project) REQUIRE p.id IS UNIQUE;

-- Organization entities
CREATE CONSTRAINT organization_id_unique FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT organization_name_unique FOR (o:Organization) REQUIRE o.name IS UNIQUE;

-- Document entities
CREATE CONSTRAINT document_id_unique FOR (d:Document) REQUIRE d.id IS UNIQUE;
```

### Vector Indexes

Hybrid search capabilities through vector indexes:

```cypher
-- Person bio embeddings for semantic search
CREATE VECTOR INDEX person_bio_vector 
FOR (p:Person) ON p.bio_embedding 
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

-- Project concept embeddings
CREATE VECTOR INDEX project_concept_vector 
FOR (p:Project) ON p.concept_embedding 
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

-- Document content embeddings
CREATE VECTOR INDEX document_content_vector 
FOR (d:Document) ON d.content_embedding 
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};
```

### Entertainment Industry Relationships

The schema defines industry-specific relationships:

- **WORKS_FOR**: Person → Organization (employment/representation)
- **DIRECTED**: Person → Project (directorial role)
- **PRODUCED**: Person/Organization → Project (production role)
- **WORKED_ON**: Person → Project (any collaboration)
- **REPRESENTS**: Organization → Person (talent representation)
- **COLLABORATED_WITH**: Person ↔ Person (professional collaboration)
- **CREATED_FOR**: Project → Organization (client relationship)
- **ATTACHED_TO**: Document → Project (project documentation)
- **SIMILAR_TO**: Any ↔ Any (AI-generated similarity)

## Usage Examples

### Basic Query Execution

```python
from database import initialize_database

# Initialize database
result = await initialize_database()
connection_manager = result["connection_manager"]

# Execute queries
people_result = await connection_manager.neo4j.execute_query("""
    MATCH (p:Person)-[:DIRECTED]->(proj:Project)
    WHERE proj.type = 'Music Video'
    RETURN p.name, proj.name, proj.budget_range
    ORDER BY p.name
""")

for record in people_result.records:
    print(f"{record['p.name']} directed {record['proj.name']}")
```

### Vector Search Operations

```python
# Semantic search for similar persons
similar_directors = await connection_manager.neo4j.execute_query("""
    CALL db.index.vector.queryNodes('person_bio_vector', 10, $query_embedding)
    YIELD node, score
    WHERE node.role = 'Director'
    RETURN node.name, node.bio, score
    ORDER BY score DESC
""", {"query_embedding": your_query_embedding})
```

### Transaction-based Operations

```python
# Create person and related entities in transaction
queries = [
    {
        "query": "CREATE (p:Person {id: $id, name: $name, role: $role})",
        "parameters": {"id": "dir_001", "name": "John Director", "role": "Director"}
    },
    {
        "query": "CREATE (o:Organization {id: $id, name: $name, type: $type})",
        "parameters": {"id": "prod_001", "name": "Great Productions", "type": "Production Company"}
    },
    {
        "query": """
            MATCH (p:Person {id: $person_id}), (o:Organization {id: $org_id})
            CREATE (p)-[:WORKS_FOR {role: $role, start_date: $date}]->(o)
        """,
        "parameters": {
            "person_id": "dir_001", 
            "org_id": "prod_001",
            "role": "Director",
            "date": "2024-01-01"
        }
    }
]

results = await connection_manager.neo4j.execute_queries_in_transaction(queries)
```

## Monitoring and Alerting

### Start Monitoring

```python
from database.monitoring import get_database_monitor

# Get monitor instance
monitor = await get_database_monitor(connection_manager)

# Start continuous monitoring (60-second intervals)
await monitor.start_monitoring(interval=60)

# Get current status
status = await monitor.get_monitoring_status()
print(f"Active alerts: {status['alert_count']}")

# Generate detailed report
report = await monitor.generate_monitoring_report("monitoring_report.json")
```

### Available Metrics

The monitoring system tracks:

- **Connection Metrics**: State, attempts, performance
- **Query Performance**: Execution times, success rates
- **Schema Health**: Validation status, missing elements
- **Overall Health**: Component status, system health scores

### Alert Thresholds

Default alert thresholds:

```python
{
    "neo4j_avg_query_time": {"warning": 2.0, "critical": 5.0},
    "neo4j_connection_state": {"critical": 0},
    "neo4j_health_score": {"warning": 0.7, "critical": 0.3},
    "neo4j_schema_valid": {"critical": 0},
    "neo4j_missing_constraints": {"warning": 1, "critical": 3},
    "neo4j_missing_indexes": {"warning": 1, "critical": 3}
}
```

## Production Deployment

### Environment Variables

Required for production:

```bash
# Database Connection
NEO4J_URI=neo4j+s://production-instance.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=production-secure-password
NEO4J_DATABASE=neo4j

# Connection Optimization
NEO4J_MAX_CONNECTION_LIFETIME=3600
NEO4J_MAX_CONNECTION_POOL_SIZE=100
NEO4J_CONNECTION_TIMEOUT=30
NEO4J_MAX_RETRY_TIME=30
NEO4J_ENCRYPTED=true
```

### Deployment Checklist

1. **✅ Environment Setup**
   - Set all required environment variables
   - Verify Neo4j Aura instance accessibility
   - Configure connection security settings

2. **✅ Schema Initialization**
   ```bash
   python backend/database/setup_schema.py --verbose
   ```

3. **✅ Connection Testing**
   ```bash
   python backend/database/test_connections.py --include-performance --output-file production_test.json
   ```

4. **✅ Monitoring Setup**
   - Start monitoring service
   - Configure alert thresholds
   - Set up log aggregation

5. **✅ Performance Validation**
   - Verify query response times < 2 seconds
   - Confirm connection pool efficiency
   - Test concurrent user load

### Health Check Endpoints

Integrate health checks in your API:

```python
from fastapi import FastAPI
from database import get_connection_manager

app = FastAPI()

@app.get("/health/database")
async def database_health():
    connection_manager = await get_connection_manager()
    health = await connection_manager.health_check()
    
    return {
        "status": health["overall_status"],
        "components": health["components"],
        "timestamp": health["timestamp"]
    }
```

## Performance Considerations

### Query Optimization

- Use proper indexes for frequent query patterns
- Leverage vector indexes for semantic search
- Limit result sets with appropriate `LIMIT` clauses
- Use query parameters to prevent Cypher injection

### Connection Management

- Configure connection pool size based on expected load
- Monitor connection health and implement retry logic  
- Use transactions for multi-query operations
- Close connections properly to prevent resource leaks

### Vector Search Performance

- Ensure embeddings are properly indexed
- Use appropriate similarity functions (cosine recommended)
- Consider embedding dimensionality vs. performance trade-offs
- Cache frequently accessed embeddings

## Troubleshooting

### Common Issues

**Connection Failures:**
```bash
# Test basic connectivity
python backend/database/test_connections.py --verbose
```

**Schema Validation Errors:**
```bash
# Check current schema state
python backend/database/setup_schema.py --validate-only --verbose
```

**Performance Issues:**
```bash
# Run performance benchmarks
python backend/database/test_connections.py --include-performance
```

### Log Analysis

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Key log messages to monitor:
- Connection establishment/failures
- Query execution times > 2 seconds
- Schema validation warnings
- Alert notifications

## Support

For issues and questions:

1. Check the test results: `python backend/database/test_connections.py`
2. Review monitoring alerts: Check active alerts in monitoring dashboard
3. Validate schema: `python backend/database/setup_schema.py --validate-only`
4. Generate report: `python backend/database/test_connections.py --output-file debug_report.json`