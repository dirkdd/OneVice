#!/usr/bin/env python3
"""
Modern Memory System Test

Simple test to validate the updated LangMem integration
without complex dependencies.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")

async def test_modern_memory():
    """Test the modern memory system components"""
    
    print("🧪 Modern Memory System Test")
    print("=" * 50)
    
    test_results = {}
    
    # Test 1: Import modern components
    print("\n1. Testing modern imports...")
    try:
        from app.ai.config import AIConfig
        from app.ai.memory.modern_langmem_manager import ModernLangMemManager
        from app.services.memory_service import MemoryServiceManager
        print("  ✅ Modern imports successful")
        test_results['imports'] = 'passed'
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        test_results['imports'] = 'failed'
        return test_results
    
    # Test 2: Configuration
    print("\n2. Testing configuration...")
    try:
        config = AIConfig()
        print(f"  ✅ Config loaded: AI models configured")
        test_results['config'] = 'passed'
    except Exception as e:
        print(f"  ❌ Config failed: {e}")
        test_results['config'] = 'failed'
        return test_results
    
    # Test 3: Memory service initialization (without DB connections)
    print("\n3. Testing memory service structure...")
    try:
        # Test service creation (without initialization)
        memory_service = MemoryServiceManager(config)
        print("  ✅ Memory service created successfully")
        print(f"  ✅ Service has {len([attr for attr in dir(memory_service) if not attr.startswith('_')])} public methods")
        test_results['service_creation'] = 'passed'
    except Exception as e:
        print(f"  ❌ Service creation failed: {e}")
        test_results['service_creation'] = 'failed'
        return test_results
    
    # Test 4: Modern LangMem manager structure
    print("\n4. Testing modern LangMem manager...")
    try:
        # Test memory schemas
        from app.ai.memory.modern_langmem_manager import UserPreference, ConversationEvent, BehaviorPattern
        
        # Create test instances
        preference = UserPreference(
            subject="user_123",
            predicate="prefers",
            object="sci-fi movies",
            context="mentioned during project discussion"
        )
        
        event = ConversationEvent(
            event_type="project_inquiry",
            participants=["user_123", "sales_agent"],
            summary="User inquired about sci-fi project directors"
        )
        
        pattern = BehaviorPattern(
            trigger="sci-fi project mentioned",
            action="suggest_experienced_directors",
            success_rate=0.85,
            usage_count=5
        )
        
        print("  ✅ Memory schemas created successfully")
        print(f"    - User preference: {preference.subject} {preference.predicate} {preference.object}")
        print(f"    - Conversation event: {event.event_type} with {len(event.participants)} participants")
        print(f"    - Behavior pattern: {pattern.trigger} -> {pattern.action} ({pattern.success_rate*100}% success)")
        test_results['schemas'] = 'passed'
        
    except Exception as e:
        print(f"  ❌ Schema test failed: {e}")
        test_results['schemas'] = 'failed'
    
    # Test 5: LangMem API availability
    print("\n5. Testing LangMem API availability...")
    try:
        from langmem import create_memory_manager, create_memory_store_manager
        print("  ✅ LangMem API functions available")
        print("    - create_memory_manager: ✅")
        print("    - create_memory_store_manager: ✅")
        test_results['langmem_api'] = 'passed'
    except Exception as e:
        print(f"  ❌ LangMem API test failed: {e}")
        test_results['langmem_api'] = 'failed'
    
    # Test 6: Storage infrastructure
    print("\n6. Testing storage infrastructure...")
    try:
        from langgraph.store.memory import InMemoryStore
        
        store = InMemoryStore(
            index={
                "dims": 1536,
                "embed": "openai:text-embedding-3-small"
            }
        )
        
        print("  ✅ InMemoryStore created successfully")
        print(f"    - Embedding dimensions: 1536")
        print(f"    - Store type: {type(store).__name__}")
        test_results['storage'] = 'passed'
        
    except Exception as e:
        print(f"  ❌ Storage test failed: {e}")
        test_results['storage'] = 'failed'
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result == 'passed')
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Modern memory system is ready.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the errors above.")
    
    return test_results

if __name__ == "__main__":
    asyncio.run(test_modern_memory())