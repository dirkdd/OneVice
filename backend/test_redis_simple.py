#!/usr/bin/env python3
"""
Simple Redis Connection Test for OneVice Memory System
Tests Redis connection with proper SSL configuration
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_redis_connection():
    """Test Redis Cloud connection with updated Redis library"""
    try:
        import redis
        
        redis_url = os.getenv('REDIS_URL')
        
        if not redis_url:
            print("❌ REDIS_URL environment variable not found")
            return False
        
        print(f"🔍 Testing Redis connection...")
        print(f"📋 URL: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
        
        # Use redis.from_url with SSL defaults
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        client.ping()
        
        # Test basic operations
        test_key = "onevice_test"
        test_value = "connection_test"
        
        client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = client.get(test_key)
        
        if retrieved_value == test_value:
            client.delete(test_key)  # Clean up
            print("✅ Redis Cloud: SUCCESS")
            print(f"   📋 Basic operations: SET/GET/DELETE -> {test_value}")
            return True
        else:
            print("❌ Redis Cloud: FAIL - Value mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Redis Cloud: FAIL")
        print(f"   💥 Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 OneVice Redis Connection Test")
    print("=" * 40)
    
    success = test_redis_connection()
    
    print("=" * 40)
    if success:
        print("🚀 Redis connection successful - memory system ready!")
        sys.exit(0)
    else:
        print("⚠️ Redis connection failed - check configuration")
        sys.exit(1)