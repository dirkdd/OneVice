# Neo4j Connection Troubleshooting Guide

**Version:** 1.0  
**Date:** September 2, 2025  
**Project:** OneVice Entertainment Intelligence Platform

## Quick Diagnostic Checklist

When experiencing Neo4j connection issues, work through this checklist systematically:

- [ ] Check Neo4j service status (Aura Console)
- [ ] Verify environment variables are set correctly
- [ ] Confirm network connectivity and firewall settings
- [ ] Test with minimal connection script
- [ ] Check driver version compatibility
- [ ] Review error logs for specific error messages
- [ ] Validate credentials and database access permissions

## Common Issues and Solutions

### 1. Driver Version Compatibility Issues

#### Issue: `TypeError: unexpected keyword argument 'max_retry_time'`

**Symptoms:**
```
TypeError: GraphDatabase.driver() got an unexpected keyword argument 'max_retry_time'
```

**Cause:** Using deprecated `max_retry_time` parameter with Neo4j driver 5.28.1+

**Solution:**
```python
# ❌ WRONG - Deprecated parameter
driver = GraphDatabase.driver(
    uri,
    auth=(username, password),
    max_retry_time=30  # This parameter was removed
)

# ✅ CORRECT - Remove deprecated parameter
driver = GraphDatabase.driver(
    uri,
    auth=(username, password),
    max_connection_lifetime=3600,
    connection_timeout=30
)
```

#### Issue: Encrypted Parameter Conflicts

**Symptoms:**
```
Failed to establish encrypted connection
neo4j.exceptions.ServiceUnavailable: Could not create encrypted connection
```

**Cause:** Using `encrypted=True` parameter with secure URI schemes (neo4j+s://, bolt+s://)

**Solution:**
```python
# ❌ WRONG - Encryption conflict
driver = GraphDatabase.driver(
    "neo4j+s://database.neo4j.io:7687",
    auth=(username, password),
    encrypted=True  # Conflicts with secure URI
)

# ✅ CORRECT - Encryption handled by URI scheme
driver = GraphDatabase.driver(
    "neo4j+s://database.neo4j.io:7687",
    auth=(username, password)
    # No encrypted parameter needed
)
```

### 2. Authentication and Authorization Issues

#### Issue: Authentication Failure

**Symptoms:**
```
neo4j.exceptions.AuthError: Authentication failure (UNAUTHORIZED)
```

**Diagnostic Steps:**
1. Verify credentials in environment variables
2. Check Neo4j Aura instance status
3. Confirm user has database access permissions
4. Test credentials with Neo4j Browser

**Solution:**
```python
# Debug script to test authentication
import os
from neo4j import GraphDatabase

def test_authentication():
    uri = os.getenv('NEO4J_URI')
    username = os.getenv('NEO4J_USERNAME')  
    password = os.getenv('NEO4J_PASSWORD')
    
    print(f"URI: {uri}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 'auth test' as result")
            print(f"✅ Authentication successful: {result.single()['result']}")
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

test_authentication()
```

#### Issue: Database Access Denied

**Symptoms:**
```
neo4j.exceptions.Forbidden: Access denied (FORBIDDEN)
```

**Cause:** User lacks permissions for specific database operations

**Solution:**
1. Check user roles in Neo4j Aura Console
2. Ensure user has appropriate database permissions
3. For Aura instances, verify user is assigned to correct database

### 3. Network Connectivity Issues

#### Issue: Service Unavailable

**Symptoms:**
```
neo4j.exceptions.ServiceUnavailable: Could not resolve host
neo4j.exceptions.ServiceUnavailable: Connection refused
```

**Diagnostic Steps:**
```python
import socket
from urllib.parse import urlparse

def diagnose_connectivity(uri):
    """Diagnose network connectivity issues"""
    
    parsed = urlparse(uri)
    hostname = parsed.hostname
    port = parsed.port or 7687
    
    print(f"Testing connectivity to {hostname}:{port}")
    
    # Test DNS resolution
    try:
        ip_addresses = socket.getaddrinfo(hostname, port)
        print(f"✅ DNS resolution successful:")
        for addr in ip_addresses[:3]:
            print(f"   {addr[4][0]}")
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False
    
    # Test TCP connectivity
    try:
        sock = socket.create_connection((hostname, port), timeout=10)
        sock.close()
        print(f"✅ TCP connection successful")
        return True
    except Exception as e:
        print(f"❌ TCP connection failed: {e}")
        return False

# Test your connection
uri = "neo4j+s://your-database.databases.neo4j.io:7687"
diagnose_connectivity(uri)
```

**Common Solutions:**
- Check firewall settings (allow port 7687)
- Verify VPN or proxy configuration
- Confirm Neo4j Aura instance is running
- Test from different network location

### 4. Query Execution Issues

#### Issue: Result Handling After Consume

**Symptoms:**
```
AttributeError: 'Result' object has no attribute 'records'
RuntimeError: Result cannot be used after being consumed
```

**Cause:** Attempting to access records after calling `consume()` in driver 5.28.1+

**Solution:**
```python
# ❌ WRONG - Access after consume
def execute_query_wrong(session, query):
    result = session.run(query)
    summary = result.consume()  # Result consumed here
    records = result.records    # Will fail - no longer accessible
    return records, summary

# ✅ CORRECT - Collect before consume
def execute_query_correct(session, query):
    result = session.run(query)
    # Collect records first
    records = [record.data() for record in result]
    # Then consume for summary
    summary = result.consume()
    return records, summary
```

#### Issue: SummaryCounters Serialization

**Symptoms:**
```
TypeError: Object of type SummaryCounters is not JSON serializable
```

**Solution:**
```python
def safe_summary_extraction(summary):
    """Safely extract summary data for serialization"""
    return {
        "query_type": summary.query_type,
        "counters": (
            summary.counters._raw_data 
            if hasattr(summary.counters, '_raw_data')
            else {}
        ),
        "timing": {
            "result_available_after": summary.result_available_after,
            "result_consumed_after": summary.result_consumed_after
        }
    }
```

### 5. Connection Pool and Resource Issues

#### Issue: Connection Pool Exhaustion

**Symptoms:**
```
neo4j.exceptions.ClientError: Unable to acquire connection from pool
```

**Cause:** Not properly closing sessions or transactions

**Solution:**
```python
# ✅ CORRECT - Proper resource management
class Neo4jClient:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
            max_connection_pool_size=50,        # Reasonable limit
            max_connection_lifetime=3600,       # 1 hour
            connection_timeout=30               # 30 seconds
        )
    
    def execute_query_safe(self, query, parameters=None):
        """Execute query with proper resource management"""
        try:
            with self.driver.session() as session:  # Auto-closes session
                result = session.run(query, parameters or {})
                records = [record.data() for record in result]
                summary = result.consume()
                return records, summary
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def __del__(self):
        """Ensure driver is closed on destruction"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
```

### 6. SSL/TLS Certificate Issues

#### Issue: Certificate Verification Failure

**Symptoms:**
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**For Development Only (Not Production):**
```python
import ssl
from neo4j import GraphDatabase

# ⚠️ DEVELOPMENT ONLY - Never use in production
def create_development_driver(uri, username, password):
    """Development-only driver with relaxed SSL verification"""
    
    # Create custom SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Note: This approach may not work with all driver versions
    # Better to fix certificate issues properly
    
    return GraphDatabase.driver(
        uri,
        auth=(username, password),
        # SSL configuration varies by driver version
    )
```

**Production Solution:**
1. Use Neo4j Aura which provides valid certificates
2. Update system certificate store
3. Use proper certificate validation

### 7. Environment Configuration Issues

#### Issue: Missing Environment Variables

**Diagnostic Script:**
```python
import os

def validate_environment():
    """Validate Neo4j environment configuration"""
    
    required_vars = [
        'NEO4J_URI',
        'NEO4J_USERNAME', 
        'NEO4J_PASSWORD'
    ]
    
    optional_vars = [
        'NEO4J_DATABASE',
        'NEO4J_MAX_CONNECTION_POOL_SIZE',
        'NEO4J_CONNECTION_TIMEOUT'
    ]
    
    issues = []
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            issues.append(f"❌ Missing required variable: {var}")
        else:
            display_value = value if var != 'NEO4J_PASSWORD' else '*' * len(value)
            print(f"✅ {var}: {display_value}")
    
    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"📋 {var}: {value}")
        else:
            print(f"⚪ {var}: Using default")
    
    # Validate URI format
    uri = os.getenv('NEO4J_URI')
    if uri:
        if uri.startswith(('neo4j://', 'neo4j+s://', 'bolt://', 'bolt+s://')):
            print(f"✅ URI format valid: {uri.split('://')[0]}://...")
        else:
            issues.append(f"❌ Invalid URI format: {uri}")
    
    return len(issues) == 0, issues

# Run validation
is_valid, issues = validate_environment()
if issues:
    for issue in issues:
        print(issue)
else:
    print("🎉 Environment configuration is valid!")
```

## Comprehensive Debugging Script

Create this script as `/backend/debug_neo4j_connection.py`:

```python
#!/usr/bin/env python3
"""
Comprehensive Neo4j Connection Debugging Script
Run this script to diagnose Neo4j connection issues systematically
"""

import os
import sys
import socket
import time
from urllib.parse import urlparse
from dotenv import load_dotenv

try:
    from neo4j import GraphDatabase
    import neo4j
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_environment():
    """Test environment variables"""
    print_section("ENVIRONMENT VALIDATION")
    
    load_dotenv()
    
    required_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            display = value if var != 'NEO4J_PASSWORD' else '*' * len(value)
            print(f"✅ {var}: {display}")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    return all_good

def test_neo4j_import():
    """Test Neo4j driver import"""
    print_section("NEO4J DRIVER CHECK")
    
    if NEO4J_AVAILABLE:
        print(f"✅ Neo4j driver imported successfully")
        print(f"📋 Driver version: {neo4j.__version__}")
        
        # Check for version compatibility
        version_parts = neo4j.__version__.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        
        if major == 5 and minor >= 28:
            print("✅ Driver version compatible with OneVice")
            print("⚠️  Using updated patterns (no max_retry_time)")
        elif major == 5 and minor >= 15:
            print("⚠️  Driver version compatible but legacy")
            print("📋 Consider upgrading to 5.28.1+")
        else:
            print("❌ Driver version may not be compatible")
            
        return True
    else:
        print("❌ Neo4j driver not available")
        print("🔧 Install with: pip install neo4j==5.28.1")
        return False

def test_network_connectivity():
    """Test network connectivity"""
    print_section("NETWORK CONNECTIVITY")
    
    uri = os.getenv('NEO4J_URI')
    if not uri:
        print("❌ No NEO4J_URI to test")
        return False
    
    try:
        parsed = urlparse(uri)
        hostname = parsed.hostname
        port = parsed.port or 7687
        
        print(f"📋 Testing connection to {hostname}:{port}")
        
        # DNS resolution
        try:
            addresses = socket.getaddrinfo(hostname, port)
            print(f"✅ DNS resolution successful")
            print(f"📋 Resolved to: {addresses[0][4][0]}")
        except Exception as e:
            print(f"❌ DNS resolution failed: {e}")
            return False
        
        # TCP connectivity
        try:
            sock = socket.create_connection((hostname, port), timeout=10)
            sock.close()
            print(f"✅ TCP connection successful")
            return True
        except Exception as e:
            print(f"❌ TCP connection failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ URL parsing failed: {e}")
        return False

def test_neo4j_connection():
    """Test actual Neo4j connection"""
    print_section("NEO4J CONNECTION TEST")
    
    if not NEO4J_AVAILABLE:
        print("❌ Neo4j driver not available, skipping connection test")
        return False
    
    uri = os.getenv('NEO4J_URI')
    username = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not all([uri, username, password]):
        print("❌ Missing connection parameters")
        return False
    
    try:
        print("📋 Attempting driver initialization...")
        
        # Use driver 5.28.1+ compatible parameters
        driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
            max_connection_lifetime=3600,
            max_connection_pool_size=10,
            connection_timeout=30
        )
        
        print("✅ Driver initialized successfully")
        
        print("📋 Testing database connection...")
        with driver.session() as session:
            result = session.run("RETURN 1 as test, datetime() as timestamp")
            record = result.single()
            print(f"✅ Query executed successfully")
            print(f"📋 Test result: {record['test']}")
            print(f"📋 Server timestamp: {record['timestamp']}")
        
        print("📋 Testing write permissions...")
        with driver.session() as session:
            result = session.run(
                "CREATE (t:ConnectionTest {id: $id, timestamp: datetime()}) "
                "DELETE t RETURN 'write_test' as result",
                {"id": f"test_{int(time.time())}"}
            )
            record = result.single()
            print(f"✅ Write test successful: {record['result']}")
        
        driver.close()
        print("✅ Connection test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print(f"📋 Error type: {type(e).__name__}")
        
        # Provide specific guidance based on error type
        error_str = str(e).lower()
        if 'authentication' in error_str:
            print("🔧 Check your username and password")
        elif 'service unavailable' in error_str:
            print("🔧 Check network connectivity and instance status")
        elif 'max_retry_time' in error_str:
            print("🔧 Update driver to version 5.28.1+ or remove max_retry_time")
        elif 'encrypted' in error_str:
            print("🔧 Remove encrypted=True parameter with neo4j+s:// URI")
        
        return False

def main():
    """Run comprehensive Neo4j debugging"""
    print("🔍 OneVice Neo4j Connection Debugging")
    print(f"Python Version: {sys.version}")
    print(f"Current Directory: {os.getcwd()}")
    
    # Run all tests
    tests = [
        ("Environment Variables", test_environment),
        ("Neo4j Driver Import", test_neo4j_import),
        ("Network Connectivity", test_network_connectivity),
        ("Neo4j Connection", test_neo4j_connection)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print_section("SUMMARY")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Neo4j connection is working properly.")
    else:
        print("⚠️  Some tests failed. Review the errors above and fix issues.")
        print("\n🔧 Common fixes:")
        print("   - Verify environment variables in .env file")
        print("   - Check Neo4j Aura instance status")
        print("   - Update Neo4j driver: pip install neo4j==5.28.1")
        print("   - Check network/firewall settings")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## Quick Reference Commands

### Test Connection
```bash
# Run comprehensive debugging
cd backend && python debug_neo4j_connection.py

# Test with existing script
cd backend && python test_connections_fixed.py
```

### Check Driver Version
```python
import neo4j
print(f"Neo4j Driver Version: {neo4j.__version__}")
```

### Environment Variables Check
```bash
# Check if variables are set
echo $NEO4J_URI
echo $NEO4J_USERNAME
echo ${NEO4J_PASSWORD:0:5}...  # Show first 5 chars only
```

### Update Driver
```bash
pip install neo4j==5.28.1
```

## Emergency Recovery Steps

If all else fails, use this minimal recovery script:

```python
#!/usr/bin/env python3
"""
Emergency Neo4j Recovery Script
Minimal connection test for troubleshooting
"""

def emergency_test():
    """Last resort connection test"""
    try:
        from neo4j import GraphDatabase
        
        # Manually input credentials (for testing only)
        uri = "neo4j+s://YOUR_DATABASE.databases.neo4j.io:7687"
        username = "neo4j"
        password = "YOUR_PASSWORD"
        
        # Minimal driver configuration
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Simple test
        with driver.session() as session:
            result = session.run("RETURN 'connected' as status")
            status = result.single()["status"]
            print(f"✅ Emergency connection successful: {status}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Emergency connection failed: {e}")
        return False

if __name__ == "__main__":
    emergency_test()
```

---

*Run through these troubleshooting steps systematically when experiencing Neo4j connection issues. Most problems can be resolved by updating driver versions and fixing environment configuration.*