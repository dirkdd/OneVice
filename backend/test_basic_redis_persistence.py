#!/usr/bin/env python3
"""
Test Basic Redis Persistence for Memory System
Validates Redis can store and retrieve conversation data
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

async def test_basic_redis_persistence():
    """Test basic Redis persistence functionality"""
    
    try:
        import redis.asyncio as redis
        
        print("🔍 OneVice Redis Persistence Test")
        print("=" * 40)
        
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            print("❌ REDIS_URL not configured")
            return False
        
        print(f"📋 Redis URL: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
        
        # Create Redis client
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        print("✅ Redis connection successful")
        
        # Test conversation state persistence
        thread_id = f"test_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conversation_key = f"conversation:{thread_id}"
        
        print(f"\n🔄 Testing conversation persistence with key: {conversation_key}")
        
        # Store conversation state
        conversation_data = {
            "thread_id": thread_id,
            "user_id": "test_user_123",
            "messages": [
                {"role": "user", "content": "Hello, I need help with sales leads"},
                {"role": "assistant", "content": "I'd be happy to help you with sales leads!"}
            ],
            "agent_type": "sales",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "metadata": {
                "routing_reason": "keyword_matching",
                "importance": 0.8
            }
        }
        
        # Store as JSON with expiration
        await redis_client.setex(
            conversation_key,
            3600,  # 1 hour expiration
            json.dumps(conversation_data)
        )
        print("  ✅ Conversation state stored")
        
        # Retrieve and verify
        retrieved_data = await redis_client.get(conversation_key)
        if retrieved_data:
            parsed_data = json.loads(retrieved_data)
            print(f"  ✅ Data retrieved: {parsed_data['thread_id']}")
            print(f"  ✅ Messages: {len(parsed_data['messages'])}")
            print(f"  ✅ Agent: {parsed_data['agent_type']}")
        else:
            print("  ❌ Failed to retrieve conversation data")
            return False
        
        # Test memory context storage
        memory_key = f"memory_context:{thread_id}"
        memory_context = {
            "user_id": "test_user_123",
            "total_memories": 15,
            "recent_topics": ["sales", "leads", "entertainment"],
            "behavioral_patterns": [
                {"trigger": "sales leads", "action": "route_to_sales", "success_rate": 0.95}
            ],
            "semantic_context": "User frequently asks about sales and lead generation",
            "last_accessed": datetime.now().isoformat()
        }
        
        await redis_client.setex(memory_key, 1800, json.dumps(memory_context))  # 30 min expiration
        print("  ✅ Memory context stored")
        
        # Test hash-based storage for agent state
        agent_state_key = f"agent_state:{thread_id}"
        agent_state = {
            "current_agent": "sales",
            "confidence": "0.9",
            "processing_time": "1.2",
            "memory_access_count": "3"
        }
        
        await redis_client.hset(agent_state_key, mapping=agent_state)
        await redis_client.expire(agent_state_key, 7200)  # 2 hours
        print("  ✅ Agent state stored (hash format)")
        
        # Verify hash retrieval
        retrieved_state = await redis_client.hgetall(agent_state_key)
        if retrieved_state:
            print(f"  ✅ Hash data retrieved: agent={retrieved_state.get('current_agent')}")
        
        # Test list-based storage for conversation history
        history_key = f"conversation_history:{thread_id}"
        messages = [
            json.dumps({"timestamp": datetime.now().isoformat(), "role": "user", "content": "Hello"}),
            json.dumps({"timestamp": datetime.now().isoformat(), "role": "assistant", "content": "Hi there!"})
        ]
        
        for message in messages:
            await redis_client.lpush(history_key, message)
        await redis_client.expire(history_key, 86400)  # 24 hours
        
        history_length = await redis_client.llen(history_key)
        print(f"  ✅ Message history stored: {history_length} messages")
        
        # Test key pattern matching
        test_keys = await redis_client.keys(f"*{thread_id}*")
        print(f"  ✅ Created test keys: {len(test_keys)}")
        
        # Cleanup test data
        if test_keys:
            await redis_client.delete(*test_keys)
            print(f"  🧹 Cleaned up {len(test_keys)} test keys")
        
        await redis_client.close()
        
        print("\n" + "=" * 40)
        print("✅ Redis persistence test successful!")
        print("🚀 Conversation and memory storage ready")
        return True
        
    except Exception as e:
        print(f"❌ Redis persistence test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_basic_redis_persistence())
    sys.exit(0 if result else 1)