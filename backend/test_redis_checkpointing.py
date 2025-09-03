#!/usr/bin/env python3
"""
Test Redis Checkpointing for LangGraph Memory System
Validates Redis-based conversation persistence
"""

import os
import sys
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

load_dotenv()

async def test_redis_checkpointing():
    """Test Redis checkpointing functionality"""
    
    try:
        import redis.asyncio as redis
        from langgraph_checkpoint_redis import RedisSaver
        from langgraph.graph import StateGraph, START, END
        from langchain_core.messages import HumanMessage, AIMessage
        from dataclasses import dataclass
        from typing import List
        
        print("🔍 OneVice Redis Checkpointing Test")
        print("=" * 40)
        
        # Test Redis connection
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            print("❌ REDIS_URL not configured")
            return False
        
        print(f"📋 Redis URL: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
        
        # Create Redis client
        redis_client = redis.from_url(redis_url, decode_responses=False)  # Checkpointing needs raw bytes
        await redis_client.ping()
        print("✅ Redis connection successful")
        
        # Create Redis saver for checkpointing
        checkpointer = RedisSaver(redis_client)
        print("✅ Redis checkpointer initialized")
        
        # Define simple state for testing
        @dataclass
        class TestState:
            messages: List[str]
            counter: int = 0
        
        def increment_node(state: TestState) -> TestState:
            state.counter += 1
            state.messages.append(f"Step {state.counter}")
            return state
        
        def finalize_node(state: TestState) -> TestState:
            state.messages.append("Completed")
            return state
        
        # Create simple workflow
        workflow = StateGraph(TestState)
        workflow.add_node("increment", increment_node)
        workflow.add_node("finalize", finalize_node)
        workflow.add_edge(START, "increment")
        workflow.add_edge("increment", "finalize")
        workflow.add_edge("finalize", END)
        
        # Compile with checkpointer
        app = workflow.compile(checkpointer=checkpointer)
        print("✅ Workflow compiled with Redis checkpointer")
        
        # Test conversation persistence
        thread_id = f"test_thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config = {"configurable": {"thread_id": thread_id}}
        
        print(f"\n🔄 Testing checkpointing with thread: {thread_id}")
        
        # Run first iteration
        initial_state = TestState(messages=["Starting"], counter=0)
        result1 = await app.ainvoke(initial_state, config=config)
        print(f"  ✅ First run: {result1.messages}")
        
        # Get checkpoint
        checkpoint = await checkpointer.aget(config)
        if checkpoint:
            print("  ✅ Checkpoint saved successfully")
        else:
            print("  ❌ No checkpoint found")
            return False
        
        # Test checkpoint retrieval
        history = [c async for c in checkpointer.alist(config, limit=10)]
        print(f"  ✅ Checkpoint history: {len(history)} items")
        
        # Cleanup test data
        test_keys = []
        cursor = b'0'
        while cursor:
            cursor, keys = await redis_client.scan(cursor, match=f"*{thread_id}*", count=100)
            test_keys.extend(keys)
        
        if test_keys:
            await redis_client.delete(*test_keys)
            print(f"  🧹 Cleaned up {len(test_keys)} test keys")
        
        await redis_client.close()
        
        print("\n" + "=" * 40)
        print("✅ Redis checkpointing test successful!")
        print("🚀 LangGraph conversation persistence ready")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure langgraph-checkpoint-redis is installed")
        return False
    except Exception as e:
        print(f"❌ Checkpointing test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_redis_checkpointing())
    sys.exit(0 if result else 1)