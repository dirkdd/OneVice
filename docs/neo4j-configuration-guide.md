# Neo4j Configuration Best Practices for OneVice

**Version:** 1.0  
**Date:** September 2, 2025  
**Compatibility:** Neo4j Python Driver 5.15.0 - 5.28.1+  

## Overview

This document provides comprehensive configuration guidelines for Neo4j implementation in the OneVice project, including driver compatibility requirements, connection patterns, and deployment best practices.

## Driver Version Compatibility

### Supported Versions
- **Neo4j Python Driver**: 5.15.0 - 5.28.1+ (recommended: 5.28.1)
- **Neo4j Database**: 4.4+ (Aura instances automatically updated)
- **Python**: 3.8+ (recommended: 3.11+)

### Breaking Changes in 5.28.1
1. **max_retry_time parameter removed** - Previously used for connection retry configuration
2. **encrypted parameter restrictions** - Cannot be used with secure URI schemes
3. **Result handling modifications** - Changes to record access patterns
4. **SummaryCounters serialization** - Internal structure modifications

## Connection Configuration

### URI Schemes and Encryption

**Neo4j Aura (Recommended for Production)**
```python
# ✅ CORRECT - Encryption handled by URI scheme
NEO4J_URI = "neo4j+s://database-id.databases.neo4j.io:7687"
encrypted = None  # Do not set encrypted parameter
```

**Bolt Protocol with SSL**
```python
# ✅ CORRECT - For custom SSL certificates
NEO4J_URI = "bolt+s://custom-host:7687"
encrypted = None  # Do not set encrypted parameter
```

**Local Development (Unencrypted)**
```python
# ✅ CORRECT - For local Neo4j instances
NEO4J_URI = "neo4j://localhost:7687"
encrypted = False  # Explicit unencrypted connection
```

### Connection Pool Configuration

```python
from neo4j import GraphDatabase

# Production-optimized configuration
driver = GraphDatabase.driver(
    uri,
    auth=(username, password),
    max_connection_lifetime=3600,        # 1 hour
    max_connection_pool_size=100,        # Concurrent connections
    connection_timeout=30,               # 30 seconds
    resolver=None                        # Custom DNS resolver if needed
)
```

### Async Driver Configuration

```python
from neo4j import AsyncGraphDatabase

# Async driver for FastAPI integration
async_driver = AsyncGraphDatabase.driver(
    uri,
    auth=(username, password),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,         # Lower for async usage
    connection_timeout=30
)
```

## Environment Variables

### Development Configuration (.env)

```bash
# Neo4j Aura Development Instance
NEO4J_URI=neo4j+s://dev-12345678.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=development-secure-password
NEO4J_DATABASE=neo4j

# Connection tuning (optional)
NEO4J_MAX_CONNECTION_LIFETIME=3600
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30

# Security flag (handled by URI scheme)
NEO4J_ENCRYPTED=true
```

### Production Configuration (Render Environment Variables)

```bash
# Neo4j Aura Production Instance
NEO4J_URI=neo4j+s://prod-87654321.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=production-ultra-secure-password
NEO4J_DATABASE=neo4j

# Production-optimized connection settings
NEO4J_MAX_CONNECTION_LIFETIME=7200
NEO4J_MAX_CONNECTION_POOL_SIZE=100
NEO4J_CONNECTION_TIMEOUT=45

# Security and monitoring
NEO4J_ENCRYPTED=true
NEO4J_HEALTH_CHECK_INTERVAL=300
```

## Query Best Practices

### Correct Result Handling Pattern

```python
async def execute_query_correct(session, query, parameters=None):
    """Correct way to handle Neo4j query results in driver 5.28.1+"""
    
    result = await session.run(query, parameters or {})
    
    # 1. Collect records first
    records = []
    async for record in result:
        records.append(record.data())
    
    # 2. Then consume for summary (records no longer accessible after this)
    summary = await result.consume()
    
    # 3. Handle SummaryCounters serialization safely
    return {
        "records": records,
        "summary": {
            "query_type": summary.query_type,
            "counters": summary.counters._raw_data if hasattr(summary.counters, '_raw_data') else {},
            "result_available_after": summary.result_available_after,
            "result_consumed_after": summary.result_consumed_after
        }
    }
```

### Transaction Management

```python
async def execute_transaction_correct(driver, queries):
    """Correct transaction handling pattern"""
    
    async with driver.session() as session:
        async with session.begin_transaction() as tx:
            try:
                results = []
                for query_data in queries:
                    result = await tx.run(query_data["query"], query_data["parameters"])
                    
                    # Collect records immediately
                    records = [record.data() async for record in result]
                    results.append(records)
                
                # Commit transaction
                await tx.commit()
                return results
                
            except Exception as e:
                # Automatic rollback on exception
                await tx.rollback()
                raise e
```

## Error Handling Patterns

### Connection Error Recovery

```python
import asyncio
from neo4j.exceptions import ServiceUnavailable, TransientError

async def robust_connection_handler(driver):
    """Robust connection handling with retry logic"""
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            async with driver.session() as session:
                # Test connectivity
                result = await session.run("RETURN 1 as test")
                await result.consume()
                return True
                
        except (ServiceUnavailable, TransientError) as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                raise e
        except Exception as e:
            # Non-recoverable error
            raise e
    
    return False
```

### Query Error Classification

```python
from neo4j.exceptions import ClientError, TransientError, DatabaseError

def classify_neo4j_error(error):
    """Classify Neo4j errors for appropriate handling"""
    
    if isinstance(error, ClientError):
        if "syntax error" in str(error).lower():
            return "SYNTAX_ERROR"
        elif "constraint" in str(error).lower():
            return "CONSTRAINT_VIOLATION"
        else:
            return "CLIENT_ERROR"
    
    elif isinstance(error, TransientError):
        return "TRANSIENT_ERROR"  # Retry recommended
    
    elif isinstance(error, DatabaseError):
        return "DATABASE_ERROR"   # Server-side issue
    
    else:
        return "UNKNOWN_ERROR"
```

## Performance Optimization

### Connection Pool Sizing

**Development Environment:**
- max_connection_pool_size: 10-20
- max_connection_lifetime: 1800 (30 minutes)
- connection_timeout: 15

**Production Environment:**
- max_connection_pool_size: 50-100
- max_connection_lifetime: 3600 (1 hour)
- connection_timeout: 30

### Query Optimization Patterns

```python
# Use parameters to enable query plan caching
query = "MATCH (p:Person {id: $person_id}) RETURN p"
parameters = {"person_id": "person-123"}

# Batch operations for bulk inserts
queries = [
    {"query": "CREATE (p:Person {id: $id, name: $name})", 
     "parameters": {"id": f"person-{i}", "name": f"Person {i}"}}
    for i in range(100)
]
```

## Health Monitoring

### Connection Health Check

```python
import time
from typing import Dict, Any

async def neo4j_health_check(driver) -> Dict[str, Any]:
    """Comprehensive Neo4j health check"""
    
    start_time = time.time()
    health_status = {
        "status": "unhealthy",
        "timestamp": start_time,
        "response_time": None,
        "error": None
    }
    
    try:
        async with driver.session() as session:
            # Test basic connectivity
            result = await session.run("RETURN 1 as test")
            test_value = await result.single()
            
            # Test write capability
            result = await session.run(
                "CREATE (t:HealthCheck {timestamp: $timestamp}) "
                "DELETE t RETURN 'write_test' as test",
                {"timestamp": start_time}
            )
            await result.consume()
            
            health_status.update({
                "status": "healthy",
                "response_time": time.time() - start_time
            })
    
    except Exception as e:
        health_status["error"] = str(e)
    
    return health_status
```

## Deployment Checklist

### Pre-deployment Verification

- [ ] Neo4j Aura instance provisioned and accessible
- [ ] Environment variables configured correctly
- [ ] Connection test script passes
- [ ] Schema migrations applied
- [ ] Indexes created and optimized
- [ ] Security constraints validated
- [ ] Health monitoring endpoints configured

### Post-deployment Monitoring

- [ ] Connection pool metrics available
- [ ] Query performance monitoring active
- [ ] Error rate tracking implemented
- [ ] Health check endpoints responding
- [ ] Log aggregation configured
- [ ] Backup verification completed

## Security Best Practices

### Connection Security

1. **Always use encrypted connections** (neo4j+s:// or bolt+s://)
2. **Store credentials in environment variables**, never in code
3. **Use separate instances** for development/staging/production
4. **Implement connection timeout** to prevent resource exhaustion
5. **Monitor failed authentication attempts**

### Query Security

```python
# ✅ CORRECT - Use parameterized queries
query = "MATCH (u:User {email: $email}) RETURN u"
parameters = {"email": user_email}

# ❌ WRONG - String concatenation enables injection
query = f"MATCH (u:User {{email: '{user_email}'}}) RETURN u"
```

## Troubleshooting Quick Reference

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `unexpected keyword argument 'max_retry_time'` | Using deprecated parameter | Remove max_retry_time from driver config |
| `Failed to establish encrypted connection` | URI scheme conflicts | Use neo4j+s:// URI without encrypted=True |
| `Authentication failure` | Invalid credentials | Check username/password in environment |
| `ServiceUnavailable` | Network/firewall issues | Verify connectivity and Aura instance status |
| `Cannot access records after consume` | Result handling error | Collect records before calling consume() |

## Migration Guide

### Upgrading from Driver 5.x < 5.28.1

1. **Remove deprecated parameters:**
   ```python
   # Remove these parameters:
   - max_retry_time
   - encrypted (when using secure URI schemes)
   ```

2. **Update result handling:**
   ```python
   # OLD pattern
   result = session.run(query)
   summary = result.consume()
   records = result.records  # Will fail
   
   # NEW pattern
   result = session.run(query)
   records = [record.data() for record in result]
   summary = result.consume()
   ```

3. **Update SummaryCounters access:**
   ```python
   # OLD pattern
   counters_data = summary.counters
   
   # NEW pattern
   counters_data = summary.counters._raw_data if hasattr(summary.counters, '_raw_data') else {}
   ```

## Support and Resources

- **Neo4j Python Driver Documentation**: https://neo4j.com/docs/api/python-driver/
- **Neo4j Aura Console**: https://console.neo4j.io/
- **OneVice Database Module**: `/backend/database/neo4j_client.py`
- **Connection Testing Script**: `/backend/test_connections_fixed.py`

---

*This document is maintained as part of the OneVice technical documentation. Update when driver versions or connection patterns change.*