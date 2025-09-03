# Neo4j Schema Setup and Validation Procedures

**Version:** 1.0  
**Date:** September 2, 2025  
**Project:** OneVice Entertainment Intelligence Platform

## Overview

This document provides comprehensive procedures for Neo4j schema setup, validation, and management for the OneVice entertainment industry data platform, including error handling patterns and recovery procedures.

## Schema Overview

### Entertainment Industry Data Model

**Core Entity Types:**
- `Person` - Industry professionals (directors, actors, executives)
- `Project` - Entertainment projects (films, shows, games)
- `Company` - Production companies, studios, distributors
- `Location` - Filming locations, production facilities
- `Skill` - Professional skills and specialties
- `Equipment` - Production equipment and resources

**Primary Relationships:**
- `DIRECTED` - Person directed Project
- `WORKED_ON` - Person worked on Project
- `EMPLOYED_BY` - Person employed by Company
- `COLLABORATES_WITH` - Person collaborates with Person
- `LOCATED_AT` - Project/Company located at Location
- `REQUIRES` - Project requires Skill/Equipment

## Schema Setup Procedures

### Pre-Setup Checklist

Before running schema setup, verify:

- [ ] Neo4j Aura instance is accessible
- [ ] Database connection credentials are configured
- [ ] Neo4j Python driver 5.28.1+ is installed
- [ ] Backup of existing data (if applicable)
- [ ] Production deployment approval (for production)

### Setup Script Usage

**Location:** `/backend/database/setup_schema.py`

**Basic Usage:**
```bash
# Standard schema setup
cd backend && python database/setup_schema.py

# Verbose output for debugging
python database/setup_schema.py --verbose

# Validation only (no changes)
python database/setup_schema.py --validate-only

# Fresh setup (drops existing schema)
python database/setup_schema.py --drop-existing --force
```

**Advanced Usage:**
```bash
# Custom configuration file
python database/setup_schema.py --config-file /path/to/config.json

# Production deployment (non-interactive)
python database/setup_schema.py --force --verbose

# Staged deployment (validate first)
python database/setup_schema.py --validate-only && \
python database/setup_schema.py --force
```

### Schema Creation Commands

The schema setup creates the following elements:

**1. Node Constraints and Indexes**
```cypher
-- Person entity constraints
CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT person_email_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.email IS UNIQUE;

-- Project entity constraints  
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT project_title_unique IF NOT EXISTS FOR (p:Project) REQUIRE (p.title, p.year) IS UNIQUE;

-- Company entity constraints
CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE;

-- Location entity constraints
CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;

-- Skill entity constraints
CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE;

-- Equipment entity constraints
CREATE CONSTRAINT equipment_id_unique IF NOT EXISTS FOR (e:Equipment) REQUIRE e.id IS UNIQUE;
```

**2. Search Indexes**
```cypher
-- Text search indexes for name-based queries
CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name);
CREATE INDEX project_title_index IF NOT EXISTS FOR (p:Project) ON (p.title);
CREATE INDEX location_name_index IF NOT EXISTS FOR (l:Location) ON (l.name);

-- Category and type indexes for filtering
CREATE INDEX project_genre_index IF NOT EXISTS FOR (p:Project) ON (p.genre);
CREATE INDEX person_role_index IF NOT EXISTS FOR (p:Person) ON (p.primary_role);
CREATE INDEX company_type_index IF NOT EXISTS FOR (c:Company) ON (c.type);
```

**3. Vector Search Indexes**
```cypher
-- Vector indexes for AI-powered similarity search
CREATE VECTOR INDEX person_bio_embedding_index IF NOT EXISTS
FOR (p:Person) ON (p.bio_embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX project_description_embedding_index IF NOT EXISTS  
FOR (p:Project) ON (p.description_embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};
```

**4. Composite Indexes**
```cypher
-- Multi-property indexes for complex queries
CREATE INDEX project_year_genre_index IF NOT EXISTS FOR (p:Project) ON (p.year, p.genre);
CREATE INDEX person_role_location_index IF NOT EXISTS FOR (p:Person) ON (p.primary_role, p.location);
CREATE INDEX company_type_location_index IF NOT EXISTS FOR (c:Company) ON (c.type, p.location);
```

## Schema Validation Procedures

### Automated Validation Script

**Location:** `/backend/database/validate_schema.py`

```python
#!/usr/bin/env python3
"""
Neo4j Schema Validation Script
Comprehensive validation of OneVice entertainment industry schema
"""

import asyncio
import logging
from typing import Dict, List, Any
from database.neo4j_client import get_neo4j_client
from database.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Validates Neo4j schema completeness and integrity"""
    
    REQUIRED_CONSTRAINTS = [
        "person_id_unique",
        "person_email_unique", 
        "project_id_unique",
        "project_title_unique",
        "company_id_unique",
        "location_id_unique",
        "skill_id_unique",
        "equipment_id_unique"
    ]
    
    REQUIRED_INDEXES = [
        "person_name_index",
        "company_name_index", 
        "project_title_index",
        "location_name_index",
        "project_genre_index",
        "person_role_index",
        "company_type_index"
    ]
    
    REQUIRED_VECTOR_INDEXES = [
        "person_bio_embedding_index",
        "project_description_embedding_index"
    ]
    
    def __init__(self):
        self.client = get_neo4j_client()
        self.validation_results = {
            "constraints": {"valid": [], "missing": [], "errors": []},
            "indexes": {"valid": [], "missing": [], "errors": []}, 
            "vector_indexes": {"valid": [], "missing": [], "errors": []},
            "data_integrity": {"valid": [], "issues": []},
            "performance": {"metrics": {}, "recommendations": []}
        }
    
    async def validate_full_schema(self) -> Dict[str, Any]:
        """Run complete schema validation"""
        
        logger.info("Starting comprehensive schema validation")
        
        try:
            # Ensure client is connected
            if not await self.client.connect():
                raise Exception("Failed to connect to Neo4j database")
            
            # Run validation checks
            await self._validate_constraints()
            await self._validate_indexes()
            await self._validate_vector_indexes()
            await self._validate_data_integrity()
            await self._validate_performance()
            
            # Generate summary
            summary = self._generate_validation_summary()
            
            logger.info("Schema validation completed")
            return {"success": True, "results": self.validation_results, "summary": summary}
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return {"success": False, "error": str(e), "results": self.validation_results}
    
    async def _validate_constraints(self):
        """Validate all required constraints exist"""
        
        logger.info("Validating database constraints")
        
        try:
            result = await self.client.execute_query("SHOW CONSTRAINTS")
            
            if not result.success:
                self.validation_results["constraints"]["errors"].append(
                    f"Failed to retrieve constraints: {result.error}"
                )
                return
            
            existing_constraints = [record["name"] for record in result.records if "name" in record]
            
            for required_constraint in self.REQUIRED_CONSTRAINTS:
                if required_constraint in existing_constraints:
                    self.validation_results["constraints"]["valid"].append(required_constraint)
                else:
                    self.validation_results["constraints"]["missing"].append(required_constraint)
            
            logger.info(f"Constraint validation: {len(self.validation_results['constraints']['valid'])} valid, "
                       f"{len(self.validation_results['constraints']['missing'])} missing")
                       
        except Exception as e:
            self.validation_results["constraints"]["errors"].append(str(e))
            logger.error(f"Constraint validation error: {e}")
    
    async def _validate_indexes(self):
        """Validate all required indexes exist"""
        
        logger.info("Validating database indexes")
        
        try:
            result = await self.client.execute_query("SHOW INDEXES")
            
            if not result.success:
                self.validation_results["indexes"]["errors"].append(
                    f"Failed to retrieve indexes: {result.error}"
                )
                return
            
            existing_indexes = [record["name"] for record in result.records if "name" in record]
            
            for required_index in self.REQUIRED_INDEXES:
                if required_index in existing_indexes:
                    self.validation_results["indexes"]["valid"].append(required_index)
                else:
                    self.validation_results["indexes"]["missing"].append(required_index)
            
            logger.info(f"Index validation: {len(self.validation_results['indexes']['valid'])} valid, "
                       f"{len(self.validation_results['indexes']['missing'])} missing")
                       
        except Exception as e:
            self.validation_results["indexes"]["errors"].append(str(e))
            logger.error(f"Index validation error: {e}")
    
    async def _validate_vector_indexes(self):
        """Validate vector indexes for AI operations"""
        
        logger.info("Validating vector indexes")
        
        try:
            # Neo4j 5.x vector index query
            result = await self.client.execute_query(
                "SHOW INDEXES WHERE type = 'VECTOR'"
            )
            
            if not result.success:
                self.validation_results["vector_indexes"]["errors"].append(
                    f"Failed to retrieve vector indexes: {result.error}"
                )
                return
            
            existing_vector_indexes = [record["name"] for record in result.records if "name" in record]
            
            for required_vector_index in self.REQUIRED_VECTOR_INDEXES:
                if required_vector_index in existing_vector_indexes:
                    self.validation_results["vector_indexes"]["valid"].append(required_vector_index)
                else:
                    self.validation_results["vector_indexes"]["missing"].append(required_vector_index)
            
            logger.info(f"Vector index validation: {len(self.validation_results['vector_indexes']['valid'])} valid, "
                       f"{len(self.validation_results['vector_indexes']['missing'])} missing")
                       
        except Exception as e:
            self.validation_results["vector_indexes"]["errors"].append(str(e))
            logger.error(f"Vector index validation error: {e}")
    
    async def _validate_data_integrity(self):
        """Validate data integrity and relationships"""
        
        logger.info("Validating data integrity")
        
        integrity_checks = [
            {
                "name": "orphaned_relationships",
                "query": """
                MATCH ()-[r]->()
                WHERE NOT EXISTS { 
                    MATCH (start)-[r]->(end) 
                    WHERE id(start) IS NOT NULL AND id(end) IS NOT NULL 
                }
                RETURN count(r) as orphaned_count
                """
            },
            {
                "name": "duplicate_person_emails", 
                "query": """
                MATCH (p1:Person), (p2:Person)
                WHERE p1.email = p2.email AND id(p1) < id(p2)
                RETURN count(*) as duplicate_count
                """
            },
            {
                "name": "missing_required_properties",
                "query": """
                MATCH (n)
                WHERE n.id IS NULL OR n.name IS NULL
                RETURN labels(n) as node_type, count(*) as missing_count
                """
            }
        ]
        
        for check in integrity_checks:
            try:
                result = await self.client.execute_query(check["query"])
                
                if result.success and result.records:
                    record = result.records[0]
                    
                    if check["name"] == "orphaned_relationships":
                        count = record.get("orphaned_count", 0)
                        if count == 0:
                            self.validation_results["data_integrity"]["valid"].append(
                                "No orphaned relationships found"
                            )
                        else:
                            self.validation_results["data_integrity"]["issues"].append(
                                f"Found {count} orphaned relationships"
                            )
                    
                    elif check["name"] == "duplicate_person_emails":
                        count = record.get("duplicate_count", 0)  
                        if count == 0:
                            self.validation_results["data_integrity"]["valid"].append(
                                "No duplicate person emails found"
                            )
                        else:
                            self.validation_results["data_integrity"]["issues"].append(
                                f"Found {count} duplicate person emails"
                            )
                    
                    elif check["name"] == "missing_required_properties":
                        if not result.records or not result.records[0]:
                            self.validation_results["data_integrity"]["valid"].append(
                                "No missing required properties found"
                            )
                        else:
                            for record in result.records:
                                node_type = record.get("node_type", "Unknown")
                                missing_count = record.get("missing_count", 0)
                                if missing_count > 0:
                                    self.validation_results["data_integrity"]["issues"].append(
                                        f"Found {missing_count} {node_type} nodes with missing required properties"
                                    )
                
            except Exception as e:
                logger.error(f"Data integrity check '{check['name']}' failed: {e}")
                self.validation_results["data_integrity"]["issues"].append(
                    f"Check '{check['name']}' failed: {str(e)}"
                )
    
    async def _validate_performance(self):
        """Validate performance characteristics"""
        
        logger.info("Validating performance metrics")
        
        try:
            # Get database statistics
            stats_query = """
            CALL apoc.meta.stats() YIELD labelCount, relTypeCount, propertyKeyCount, nodeCount, relCount
            RETURN labelCount, relTypeCount, propertyKeyCount, nodeCount, relCount
            """
            
            result = await self.client.execute_query(stats_query)
            
            if result.success and result.records:
                stats = result.records[0]
                self.validation_results["performance"]["metrics"] = {
                    "node_count": stats.get("nodeCount", 0),
                    "relationship_count": stats.get("relCount", 0), 
                    "label_count": stats.get("labelCount", 0),
                    "relationship_type_count": stats.get("relTypeCount", 0),
                    "property_key_count": stats.get("propertyKeyCount", 0)
                }
                
                # Performance recommendations
                node_count = stats.get("nodeCount", 0)
                if node_count > 100000:
                    self.validation_results["performance"]["recommendations"].append(
                        "Consider implementing query optimization for large dataset"
                    )
                
                if node_count > 1000000:
                    self.validation_results["performance"]["recommendations"].append(
                        "Consider implementing data partitioning strategies"
                    )
            
        except Exception as e:
            logger.warning(f"Performance validation failed (may require APOC): {e}")
            
            # Fallback to basic node count
            try:
                result = await self.client.execute_query("MATCH (n) RETURN count(n) as node_count")
                if result.success:
                    node_count = result.records[0].get("node_count", 0)
                    self.validation_results["performance"]["metrics"]["node_count"] = node_count
            except Exception as fallback_error:
                logger.error(f"Fallback performance check failed: {fallback_error}")
    
    def _generate_validation_summary(self) -> Dict[str, Any]:
        """Generate validation summary"""
        
        total_constraints = len(self.REQUIRED_CONSTRAINTS)
        valid_constraints = len(self.validation_results["constraints"]["valid"])
        
        total_indexes = len(self.REQUIRED_INDEXES)
        valid_indexes = len(self.validation_results["indexes"]["valid"])
        
        total_vector_indexes = len(self.REQUIRED_VECTOR_INDEXES)
        valid_vector_indexes = len(self.validation_results["vector_indexes"]["valid"])
        
        integrity_issues = len(self.validation_results["data_integrity"]["issues"])
        
        return {
            "overall_status": "HEALTHY" if (
                valid_constraints == total_constraints and
                valid_indexes == total_indexes and 
                valid_vector_indexes == total_vector_indexes and
                integrity_issues == 0
            ) else "ISSUES_FOUND",
            "constraint_completeness": f"{valid_constraints}/{total_constraints}",
            "index_completeness": f"{valid_indexes}/{total_indexes}",
            "vector_index_completeness": f"{valid_vector_indexes}/{total_vector_indexes}",
            "data_integrity_issues": integrity_issues,
            "performance_metrics": self.validation_results["performance"]["metrics"]
        }

async def main():
    """Run schema validation"""
    logging.basicConfig(level=logging.INFO)
    
    validator = SchemaValidator()
    results = await validator.validate_full_schema()
    
    if results["success"]:
        print("✅ Schema validation completed")
        print(f"📊 Summary: {results['summary']}")
        
        if results["summary"]["overall_status"] == "HEALTHY":
            print("🎉 Schema is healthy and complete!")
        else:
            print("⚠️  Schema has issues that should be addressed")
            
    else:
        print(f"❌ Schema validation failed: {results['error']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Manual Validation Queries

**Check Constraint Status:**
```cypher
-- List all constraints
SHOW CONSTRAINTS;

-- Check specific constraint
SHOW CONSTRAINTS WHERE name = 'person_id_unique';
```

**Check Index Status:**
```cypher  
-- List all indexes
SHOW INDEXES;

-- Check index usage statistics
SHOW INDEXES YIELD name, state, populationPercent, type
WHERE state <> 'ONLINE';
```

**Check Vector Index Status:**
```cypher
-- List vector indexes
SHOW INDEXES WHERE type = 'VECTOR';

-- Check vector index configuration
SHOW INDEXES YIELD name, options, type
WHERE type = 'VECTOR';
```

## Error Handling Patterns

### Connection Error Recovery

```python
async def robust_schema_operation(client, operation_name, cypher_query):
    """Execute schema operation with robust error handling"""
    
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Ensure connection
            if not await client._ensure_connected():
                raise Exception("Database connection failed")
            
            # Execute operation
            result = await client.execute_query(cypher_query)
            
            if result.success:
                logger.info(f"✅ {operation_name} completed successfully")
                return result
            else:
                raise Exception(f"Operation failed: {result.error}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️  {operation_name} attempt {attempt + 1} failed: {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"❌ {operation_name} failed after {max_retries} attempts: {e}")
                raise e
    
    return None
```

### Constraint Creation Error Handling

```python
async def create_constraint_safe(client, constraint_name, cypher_command):
    """Create constraint with error handling"""
    
    try:
        # Check if constraint already exists
        check_result = await client.execute_query(
            f"SHOW CONSTRAINTS WHERE name = '{constraint_name}'"
        )
        
        if check_result.success and check_result.records:
            logger.info(f"📋 Constraint '{constraint_name}' already exists")
            return True
        
        # Create constraint
        result = await client.execute_query(cypher_command)
        
        if result.success:
            logger.info(f"✅ Created constraint: {constraint_name}")
            return True
        else:
            # Handle specific constraint errors
            error_msg = result.error.lower() if result.error else ""
            
            if "already exists" in error_msg:
                logger.info(f"📋 Constraint '{constraint_name}' already exists")
                return True
            elif "duplicate" in error_msg:
                logger.error(f"❌ Cannot create constraint '{constraint_name}': duplicate data exists")
                logger.info("🔧 Clean up duplicate data before creating constraint")
                return False
            elif "invalid" in error_msg:
                logger.error(f"❌ Invalid constraint definition for '{constraint_name}': {result.error}")
                return False
            else:
                logger.error(f"❌ Failed to create constraint '{constraint_name}': {result.error}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Constraint creation error for '{constraint_name}': {e}")
        return False
```

### Index Creation Error Handling

```python
async def create_index_safe(client, index_name, cypher_command):
    """Create index with error handling and progress monitoring"""
    
    try:
        # Check if index already exists
        check_result = await client.execute_query(
            f"SHOW INDEXES WHERE name = '{index_name}'"
        )
        
        if check_result.success and check_result.records:
            existing_index = check_result.records[0]
            state = existing_index.get("state", "UNKNOWN")
            
            if state == "ONLINE":
                logger.info(f"📋 Index '{index_name}' already exists and is online")
                return True
            elif state in ["POPULATING", "BUILDING"]:
                logger.info(f"⏳ Index '{index_name}' is still building, waiting...")
                return await wait_for_index_online(client, index_name)
            else:
                logger.warning(f"⚠️  Index '{index_name}' exists but is in state: {state}")
                return False
        
        # Create index
        logger.info(f"🔧 Creating index: {index_name}")
        result = await client.execute_query(cypher_command)
        
        if result.success:
            logger.info(f"✅ Index creation initiated: {index_name}")
            
            # Wait for index to come online
            return await wait_for_index_online(client, index_name)
        else:
            logger.error(f"❌ Failed to create index '{index_name}': {result.error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Index creation error for '{index_name}': {e}")
        return False

async def wait_for_index_online(client, index_name, max_wait_time=300):
    """Wait for index to come online"""
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            result = await client.execute_query(
                f"SHOW INDEXES WHERE name = '{index_name}'"
            )
            
            if result.success and result.records:
                state = result.records[0].get("state", "UNKNOWN")
                population_percent = result.records[0].get("populationPercent", 0)
                
                if state == "ONLINE":
                    logger.info(f"✅ Index '{index_name}' is now online")
                    return True
                elif state in ["POPULATING", "BUILDING"]:
                    logger.info(f"⏳ Index '{index_name}' building: {population_percent:.1f}% complete")
                else:
                    logger.error(f"❌ Index '{index_name}' failed to build: {state}")
                    return False
            
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            logger.error(f"Error checking index status: {e}")
            await asyncio.sleep(5)
    
    logger.error(f"❌ Timeout waiting for index '{index_name}' to come online")
    return False
```

## Recovery Procedures

### Schema Corruption Recovery

**1. Backup Current State:**
```bash
# Export current data (if any)
cd backend && python -c "
from database.neo4j_client import get_neo4j_client
import asyncio

async def backup_data():
    client = get_neo4j_client()
    await client.connect()
    result = await client.execute_query('MATCH (n) RETURN count(n) as node_count')
    print(f'Current nodes: {result.records[0][\"node_count\"]}')

asyncio.run(backup_data())
"
```

**2. Drop and Recreate Schema:**
```bash
# WARNING: This will drop all schema elements
python database/setup_schema.py --drop-existing --force --verbose
```

**3. Validate Recovery:**
```bash
python database/validate_schema.py
```

### Constraint Violation Recovery

**Find Constraint Violations:**
```cypher
-- Find duplicate person IDs
MATCH (p:Person)
WITH p.id as person_id, collect(p) as persons
WHERE size(persons) > 1
RETURN person_id, size(persons) as duplicate_count;

-- Find duplicate emails
MATCH (p:Person)  
WITH p.email as email, collect(p) as persons
WHERE size(persons) > 1 AND email IS NOT NULL
RETURN email, size(persons) as duplicate_count;
```

**Clean Up Duplicates:**
```cypher
-- Remove duplicate persons (keep first occurrence)
MATCH (p:Person)
WITH p.id as person_id, collect(p) as persons
WHERE size(persons) > 1
FOREACH (person in persons[1..] | DELETE person);
```

## Performance Optimization

### Index Performance Monitoring

**Check Index Usage:**
```cypher
-- Monitor index usage (Neo4j 5.x)
CALL db.indexes() YIELD 
  name, 
  state, 
  populationPercent, 
  uniqueValuesSelectivity,
  updatesSinceEstimation
RETURN name, state, populationPercent, uniqueValuesSelectivity;
```

**Query Performance Analysis:**
```cypher
-- Profile expensive queries
PROFILE MATCH (p:Person {name: 'John Smith'})
RETURN p.id, p.email;

-- Explain query execution plan
EXPLAIN MATCH (p:Person)-[r:WORKED_ON]->(proj:Project)
WHERE proj.year > 2020
RETURN p.name, proj.title;
```

### Schema Optimization Recommendations

**Index Optimization:**
1. Create indexes on frequently queried properties
2. Use composite indexes for multi-property queries
3. Monitor and remove unused indexes
4. Optimize vector indexes for AI queries

**Constraint Optimization:**
1. Use unique constraints to enforce data quality
2. Avoid over-constraining in development
3. Plan constraint creation for production data volumes
4. Consider performance impact of constraints on writes

## Automated Schema Management

### CI/CD Integration

**GitHub Actions Workflow Example:**
```yaml
name: Schema Validation
on: [push, pull_request]

jobs:
  validate-schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Validate Schema
        run: |
          cd backend
          python database/validate_schema.py
        env:
          NEO4J_URI: ${{ secrets.NEO4J_URI }}
          NEO4J_USERNAME: ${{ secrets.NEO4J_USERNAME }}
          NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
```

### Deployment Scripts

**Production Schema Deployment:**
```bash
#!/bin/bash
# deploy_schema_production.sh

set -e  # Exit on any error

echo "🚀 OneVice Production Schema Deployment"
echo "======================================"

# Validation check
echo "📋 Pre-deployment validation..."
python database/validate_schema.py --environment=production

# Backup current schema (if supported)
echo "💾 Creating schema backup..."
# Add backup commands here

# Deploy schema changes
echo "🔧 Deploying schema updates..."
python database/setup_schema.py --force --verbose

# Post-deployment validation
echo "✅ Post-deployment validation..."
python database/validate_schema.py --environment=production

echo "🎉 Schema deployment completed successfully!"
```

## Troubleshooting Common Issues

### Issue: Constraint Creation Fails with Duplicate Data

**Error Message:**
```
Unable to create constraint: existing data violates constraint
```

**Solution:**
1. Identify duplicates with validation queries
2. Clean up duplicate data manually or with scripts
3. Retry constraint creation

### Issue: Index Creation Takes Too Long

**Symptoms:**
- Index stuck in "POPULATING" state
- High CPU usage during index creation

**Solutions:**
1. Check data volume and complexity
2. Consider creating index during low-traffic periods
3. Monitor system resources
4. Break large datasets into smaller batches

### Issue: Vector Index Configuration Errors

**Error Message:**
```
Invalid vector index configuration: dimensions mismatch
```

**Solution:**
1. Verify vector dimensions match embedding model (1536 for OpenAI)
2. Check similarity function compatibility
3. Validate existing vector data format

## Best Practices Summary

### Development Environment
- Use smaller connection pools
- Enable query logging for debugging
- Validate schema changes frequently
- Use separate development database instance

### Production Environment  
- Implement comprehensive backup procedures
- Use production-optimized connection settings
- Monitor schema performance continuously
- Plan schema changes during maintenance windows
- Implement gradual rollout for major changes

### Error Handling
- Always implement retry logic for schema operations
- Log all schema operations with appropriate detail
- Validate operations before and after execution
- Provide clear error messages and recovery instructions

---

*This document should be updated when schema requirements change or when new Neo4j features become available.*