#!/usr/bin/env python3
"""
Simple Database Connection Test

Quick validation of database connectivity without complex setup.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")

async def test_connections():
    """Test basic database connections"""
    
    print("🔌 Simple Database Connection Test")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Neo4j connection
    print("\n1. Testing Neo4j connection...")
    try:
        from app.ai.config import AIConfig
        from app.ai.graph.connection import Neo4jClient
        
        config = AIConfig()
        neo4j_client = Neo4jClient(config)
        
        # Test connection with timeout
        connection_task = asyncio.create_task(neo4j_client.connect())
        
        try:
            await asyncio.wait_for(connection_task, timeout=10.0)
            print("  ✅ Neo4j connection successful")
            results['neo4j'] = 'passed'
            
            # Test simple query
            test_result = await neo4j_client.run_query("RETURN 'Hello Neo4j' as message")
            if test_result:
                print(f"    ✅ Query test: {test_result[0]['message']}")
            
            await neo4j_client.close()
            
        except asyncio.TimeoutError:
            print("  ⚠️  Neo4j connection timed out (10s)")
            results['neo4j'] = 'timeout'
        except Exception as e:
            print(f"  ❌ Neo4j connection failed: {e}")
            results['neo4j'] = 'failed'
        
    except Exception as e:
        print(f"  ❌ Neo4j import/setup failed: {e}")
        results['neo4j'] = 'import_failed'
    
    # Test 2: Redis connection
    print("\n2. Testing Redis connection...")
    try:
        import redis.asyncio as redis
        
        config = AIConfig()
        redis_client = redis.from_url(config.redis_url)
        
        # Test connection with timeout
        ping_task = asyncio.create_task(redis_client.ping())
        
        try:
            pong = await asyncio.wait_for(ping_task, timeout=5.0)
            if pong:
                print("  ✅ Redis connection successful")
                results['redis'] = 'passed'
                
                # Test simple operation
                await redis_client.set("test_key", "Hello Redis")
                value = await redis_client.get("test_key")
                print(f"    ✅ Redis test: {value.decode()}")
                await redis_client.delete("test_key")
            
            await redis_client.close()
            
        except asyncio.TimeoutError:
            print("  ⚠️  Redis connection timed out (5s)")
            results['redis'] = 'timeout'
        except Exception as e:
            print(f"  ❌ Redis connection failed: {e}")
            results['redis'] = 'failed'
        
    except Exception as e:
        print(f"  ❌ Redis import/setup failed: {e}")
        results['redis'] = 'import_failed'
    
    # Test 3: PostgreSQL connection
    print("\n3. Testing PostgreSQL connection...")
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        # Test connection with timeout
        connection_task = asyncio.create_task(test_postgresql())
        
        try:
            await asyncio.wait_for(connection_task, timeout=10.0)
            print("  ✅ PostgreSQL connection successful")
            results['postgresql'] = 'passed'
            
        except asyncio.TimeoutError:
            print("  ⚠️  PostgreSQL connection timed out (10s)")
            results['postgresql'] = 'timeout'
        except Exception as e:
            print(f"  ❌ PostgreSQL connection failed: {e}")
            results['postgresql'] = 'failed'
        
    except Exception as e:
        print(f"  ❌ PostgreSQL import/setup failed: {e}")
        results['postgresql'] = 'import_failed'
    
    # Summary
    print("\n📊 Connection Test Results")
    print("=" * 50)
    
    for service, status in results.items():
        icon = {
            'passed': '✅',
            'failed': '❌', 
            'timeout': '⚠️',
            'import_failed': '🚫'
        }.get(status, '❓')
        
        print(f"{icon} {service.title()}: {status}")
    
    # Overall assessment
    working_connections = sum(1 for status in results.values() if status == 'passed')
    total_services = len(results)
    
    print(f"\nWorking connections: {working_connections}/{total_services}")
    
    if working_connections == total_services:
        print("🎉 All database connections are working!")
    elif working_connections > 0:
        print("⚠️  Some connections are working. Check failed services.")
    else:
        print("❌ No database connections are working.")
    
    return results


async def test_postgresql():
    """Test PostgreSQL connection"""
    from app.core.database import engine
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 'Hello PostgreSQL' as message"))
        row = result.fetchone()
        print(f"    ✅ PostgreSQL test: {row[0]}")


if __name__ == "__main__":
    asyncio.run(test_connections())