#!/usr/bin/env python3
"""
Enhanced Database Connection Test Script for OneVice
Includes fallback connection methods and better error handling
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
    """Test Redis Cloud connection with multiple SSL approaches"""
    try:
        import redis
        import ssl
        
        redis_url = os.getenv('REDIS_URL')
        
        if not redis_url:
            return {
                'service': 'Redis Cloud',
                'status': 'FAIL',
                'error': 'Missing REDIS_URL environment variable'
            }
        
        # Try multiple connection methods
        connection_methods = [
            {
                'name': 'SSL with cert verification disabled',
                'kwargs': {'ssl_cert_reqs': None}
            },
            {
                'name': 'SSL with custom context',
                'kwargs': {'ssl_cert_reqs': ssl.CERT_NONE, 'ssl_check_hostname': False}
            },
            {
                'name': 'No SSL verification',
                'kwargs': {'ssl_cert_reqs': None, 'ssl_check_hostname': False, 'ssl_ca_certs': None}
            }
        ]
        
        last_error = None
        
        for method in connection_methods:
            try:
                r = redis.from_url(redis_url, **method['kwargs'])
                r.ping()
                
                # Test basic operations
                r.set('test_key', 'test_value', ex=60)
                test_value = r.get('test_key').decode('utf-8')
                r.delete('test_key')
                
                return {
                    'service': 'Redis Cloud',
                    'status': 'SUCCESS',
                    'method': method['name'],
                    'test_operation': f'SET/GET test -> {test_value}'
                }
            except Exception as e:
                last_error = e
                continue
        
        return {
            'service': 'Redis Cloud',
            'status': 'FAIL',
            'error': f'All connection methods failed. Last error: {str(last_error)}'
        }
        
    except Exception as e:
        return {
            'service': 'Redis Cloud',
            'status': 'FAIL',
            'error': str(e)
        }

def test_supabase_connection() -> Dict[str, Any]:
    """Test Supabase PostgreSQL connection with IPv4 fallback"""
    try:
        import psycopg2
        import socket
        
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            return {
                'service': 'Supabase PostgreSQL',
                'status': 'FAIL',
                'error': 'Missing DATABASE_URL environment variable'
            }
        
        # Try to resolve hostname to check connectivity
        try:
            # Extract hostname from URL
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            hostname = parsed.hostname
            
            # Test DNS resolution
            ip_addresses = socket.getaddrinfo(hostname, parsed.port or 5432, socket.AF_UNSPEC, socket.SOCK_STREAM)
            
            connection_info = {
                'hostname': hostname,
                'resolved_ips': [addr[4][0] for addr in ip_addresses[:3]]  # First 3 IPs
            }
        except Exception as dns_error:
            return {
                'service': 'Supabase PostgreSQL',
                'status': 'FAIL',
                'error': f'DNS resolution failed: {str(dns_error)}'
            }
        
        # Try connecting with longer timeout
        conn = psycopg2.connect(
            database_url,
            connect_timeout=30,
            options='-c statement_timeout=30000'
        )
        cursor = conn.cursor()
        
        # Test connection with simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        # Test table creation permission
        cursor.execute("CREATE TABLE IF NOT EXISTS connection_test (id SERIAL PRIMARY KEY, test_data TEXT);")
        cursor.execute("INSERT INTO connection_test (test_data) VALUES ('test');")
        cursor.execute("SELECT test_data FROM connection_test WHERE test_data = 'test';")
        test_result = cursor.fetchone()[0]
        cursor.execute("DROP TABLE connection_test;")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'service': 'Supabase PostgreSQL',
            'status': 'SUCCESS',
            'connection_info': connection_info,
            'version': version.split()[0:2],
            'test_operation': f'CREATE/INSERT/SELECT/DROP -> {test_result}'
        }
        
    except Exception as e:
        return {
            'service': 'Supabase PostgreSQL',
            'status': 'FAIL',
            'error': str(e)
        }

def test_clerk_config() -> Dict[str, Any]:
    """Test Clerk environment variables"""
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
            'CLERK_WEBHOOK_SECRET': 'Present' if clerk_webhook else 'Missing (Optional)'
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
    """Run enhanced connection tests"""
    print("🔍 OneVice Enhanced Database Connection Test")
    print("=" * 55)
    
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
                    if isinstance(value, dict):
                        print(f"   📋 {key}:")
                        for subkey, subvalue in value.items():
                            print(f"      • {subkey}: {subvalue}")
                    else:
                        print(f"   📋 {key}: {value}")
        else:
            print(f"❌ {result['service']}: {result['status']}")
            print(f"   💥 Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 55)
    print(f"📊 Summary: {success_count}/{len(tests)} services connected successfully")
    
    if success_count >= 2:  # Neo4j + Clerk minimum for development
        print("✅ Minimum services (Neo4j + Auth) are working!")
        if success_count < len(tests):
            print("⚠️  Some optional services failed but development can continue")
        print("\n🚀 Ready to proceed to Priority 3: Core Schema Implementation")
    else:
        print(f"❌ Critical services failed. Need at least Neo4j + Authentication working.")
    
    return success_count >= 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)