#!/usr/bin/env python3
"""
Database Connection Test Script for OneVice
Tests all remote database connections from technical-roadmap.md Phase 1, Priority 2
"""

import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

def test_neo4j_connection() -> Dict[str, Any]:
    """Test Neo4j Aura connection"""
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI')
        username = os.getenv('NEO4J_USERNAME')
        password = os.getenv('NEO4J_PASSWORD')
        
        if not all([uri, username, password]):
            return {
                'service': 'Neo4j Aura',
                'status': 'FAIL',
                'error': 'Missing environment variables: NEO4J_URI, NEO4J_USERNAME, or NEO4J_PASSWORD'
            }
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Test connection with simple query
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()['test']
            
        driver.close()
        
        return {
            'service': 'Neo4j Aura',
            'status': 'SUCCESS',
            'uri': uri,
            'test_query': f'RETURN 1 -> {test_value}'
        }
        
    except Exception as e:
        return {
            'service': 'Neo4j Aura',
            'status': 'FAIL',
            'error': str(e)
        }

def test_redis_connection() -> Dict[str, Any]:
    """Test Redis Cloud connection using explicit Redis() constructor"""
    try:
        import redis
        from urllib.parse import urlparse
        
        redis_url = os.getenv('REDIS_URL')
        
        if not redis_url:
            return {
                'service': 'Redis Cloud',
                'status': 'FAIL',
                'error': 'Missing REDIS_URL environment variable'
            }
        
        # Parse Redis URL to extract components
        parsed = urlparse(redis_url)
        
        # Extract connection details
        host = parsed.hostname
        port = parsed.port or 6379
        username = parsed.username or 'default'
        password = parsed.password
        
        if not password:
            return {
                'service': 'Redis Cloud',
                'status': 'FAIL',
                'error': 'No password found in REDIS_URL'
            }
        
        # Connect using explicit Redis() constructor (matching working example)
        r = redis.Redis(
            host=host,
            port=port,
            username=username,
            password=password,
            decode_responses=True
        )
        
        # Test connection
        r.ping()
        
        # Test basic operations
        success = r.set('test_key', 'test_value', ex=60)  # Expires in 60 seconds
        test_value = r.get('test_key')  # Already decoded due to decode_responses=True
        r.delete('test_key')
        
        return {
            'service': 'Redis Cloud',
            'status': 'SUCCESS',
            'connection': f'{host}:{port}',
            'test_operation': f'SET/GET test -> {test_value}',
            'set_success': success
        }
        
    except Exception as e:
        return {
            'service': 'Redis Cloud',
            'status': 'FAIL',
            'error': str(e)
        }

def test_supabase_connection() -> Dict[str, Any]:
    """Test Supabase PostgreSQL connection"""
    try:
        import psycopg2
        
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            return {
                'service': 'Supabase PostgreSQL',
                'status': 'FAIL',
                'error': 'Missing DATABASE_URL environment variable'
            }
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test connection with simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        # Test table creation permission (then drop it)
        cursor.execute("CREATE TABLE IF NOT EXISTS connection_test (id SERIAL PRIMARY KEY, test_data TEXT);")
        cursor.execute("DROP TABLE IF EXISTS connection_test;")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'service': 'Supabase PostgreSQL',
            'status': 'SUCCESS',
            'version': version.split()[0:2],  # Just PostgreSQL version
            'test_operation': 'CREATE/DROP table test passed'
        }
        
    except Exception as e:
        return {
            'service': 'Supabase PostgreSQL',
            'status': 'FAIL',
            'error': str(e)
        }

def test_clerk_config() -> Dict[str, Any]:
    """Test Clerk environment variables (no actual connection test)"""
    try:
        clerk_secret = os.getenv('CLERK_SECRET_KEY')
        clerk_webhook = os.getenv('CLERK_WEBHOOK_SECRET')
        
        if not clerk_secret:
            return {
                'service': 'Clerk Authentication',
                'status': 'FAIL',
                'error': 'Missing CLERK_SECRET_KEY environment variable'
            }
        
        config_status = {
            'CLERK_SECRET_KEY': 'Present' if clerk_secret else 'Missing',
            'CLERK_WEBHOOK_SECRET': 'Present' if clerk_webhook else 'Missing'
        }
        
        return {
            'service': 'Clerk Authentication',
            'status': 'SUCCESS',
            'config': config_status,
            'note': 'Configuration validated (no connection test performed)'
        }
        
    except Exception as e:
        return {
            'service': 'Clerk Authentication',
            'status': 'FAIL',
            'error': str(e)
        }

def main():
    """Run all connection tests"""
    print("🔍 OneVice Database Connection Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if we're in the backend directory
    if not os.path.exists('.env'):
        print("❌ Error: .env file not found. Make sure you're in the backend directory.")
        sys.exit(1)
    
    # Run all tests
    tests = [
        test_neo4j_connection,
        test_redis_connection,
        test_supabase_connection,
        test_clerk_config
    ]
    
    results = []
    success_count = 0
    
    for test in tests:
        print(f"\n⏳ Testing {test.__name__.replace('test_', '').replace('_', ' ').title()}...")
        result = test()
        results.append(result)
        
        if result['status'] == 'SUCCESS':
            print(f"✅ {result['service']}: {result['status']}")
            success_count += 1
            
            # Print additional info if available
            for key, value in result.items():
                if key not in ['service', 'status']:
                    print(f"   📋 {key}: {value}")
        else:
            print(f"❌ {result['service']}: {result['status']}")
            print(f"   💥 Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Summary: {success_count}/{len(tests)} services connected successfully")
    
    if success_count == len(tests):
        print("🎉 All database connections are working!")
        print("\n🚀 Ready to proceed to Priority 3: Core Schema Implementation")
    else:
        print(f"⚠️  {len(tests) - success_count} connection(s) failed. Please check your .env file.")
    
    return success_count == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)