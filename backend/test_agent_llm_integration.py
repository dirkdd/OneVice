#!/usr/bin/env python3
"""
Agent-LLM Integration Test

Test that agents can successfully communicate with LLM providers
through the router system.
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

# Mock API keys for testing (these would be real in production)
if not os.getenv("TOGETHER_API_KEY"):
    os.environ["TOGETHER_API_KEY"] = "mock-key-for-testing"
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "mock-key-for-testing"

async def test_agent_llm_integration():
    """Test agent LLM integration components"""
    
    print("🤖 Agent-LLM Integration Test")
    print("=" * 50)
    
    test_results = {}
    
    # Test 1: Import agent components
    print("\n1. Testing agent imports...")
    try:
        from app.ai.config import AIConfig
        from app.ai.llm.router import LLMRouter
        from app.ai.agents.sales_agent import SalesIntelligenceAgent
        print("  ✅ Agent imports successful")
        test_results['imports'] = 'passed'
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        test_results['imports'] = 'failed'
        return test_results
    
    # Test 2: Initialize LLM router
    print("\n2. Testing LLM router initialization...")
    try:
        config = AIConfig()
        llm_router = LLMRouter(config)
        
        print(f"  ✅ LLM router created")
        print(f"    - Available providers: {len(llm_router.providers)}")
        print(f"    - Provider stats initialized: {len(llm_router.provider_stats)}")
        
        test_results['router_init'] = 'passed'
    except Exception as e:
        print(f"  ❌ Router initialization failed: {e}")
        test_results['router_init'] = 'failed'
        return test_results
    
    # Test 3: Initialize agent with router
    print("\n3. Testing agent initialization...")
    try:
        sales_agent = SalesIntelligenceAgent(
            config=config,
            llm_router=llm_router
        )
        
        print(f"  ✅ Sales agent created")
        print(f"    - Agent type: {sales_agent.agent_type.value}")
        print(f"    - Has LLM router: {sales_agent.llm_router is not None}")
        print(f"    - Has LangGraph app: {sales_agent.app is not None}")
        
        test_results['agent_init'] = 'passed'
    except Exception as e:
        print(f"  ❌ Agent initialization failed: {e}")
        test_results['agent_init'] = 'failed'
        return test_results
    
    # Test 4: Test provider selection logic
    print("\n4. Testing provider selection...")
    try:
        from app.ai.llm.router import QueryComplexity, LLMProvider
        
        # Test complexity assessment
        test_messages = [
            {"role": "user", "content": "What is 2+2?"}
        ]
        
        complexity = llm_router._assess_complexity(test_messages)
        print(f"  ✅ Complexity assessment: {complexity}")
        
        # Test provider selection
        provider = llm_router._select_provider(
            complexity=complexity,
            agent_type="sales"
        )
        
        print(f"  ✅ Provider selection: {provider}")
        test_results['provider_selection'] = 'passed'
        
    except Exception as e:
        print(f"  ❌ Provider selection failed: {e}")
        test_results['provider_selection'] = 'failed'
    
    # Test 5: Test agent chat interface (without actual LLM call)
    print("\n5. Testing agent chat interface...")
    try:
        # Test the chat method exists and has proper signature
        chat_method = getattr(sales_agent, 'chat', None)
        if chat_method and callable(chat_method):
            print("  ✅ Agent chat method available")
            
            # Check if agent has the required methods
            methods = ['_initialize_conversation', '_process_query', '_generate_response', '_update_memory']
            available_methods = [method for method in methods if hasattr(sales_agent, method)]
            
            print(f"    - Available methods: {len(available_methods)}/{len(methods)}")
            for method in available_methods:
                print(f"      ✓ {method}")
            
            test_results['chat_interface'] = 'passed'
        else:
            print("  ❌ Agent chat method not found")
            test_results['chat_interface'] = 'failed'
            
    except Exception as e:
        print(f"  ❌ Chat interface test failed: {e}")
        test_results['chat_interface'] = 'failed'
    
    # Test 6: Test prompt template system
    print("\n6. Testing prompt template system...")
    try:
        from app.ai.llm.prompt_templates import PromptTemplateManager, PromptType
        
        prompt_manager = PromptTemplateManager()
        
        # Test if sales agent has proper prompt type
        sales_prompt_type = sales_agent._get_prompt_type()
        print(f"  ✅ Sales agent prompt type: {sales_prompt_type}")
        
        # Test prompt formatting
        formatted_messages = prompt_manager.format_conversation_prompt(
            agent_type=sales_prompt_type,
            user_query="Tell me about your sales capabilities",
            context={"user_id": "test_user"}
        )
        
        print(f"  ✅ Prompt formatted: {len(formatted_messages)} messages")
        if formatted_messages:
            print(f"    - System prompt available: {formatted_messages[0]['role'] == 'system'}")
        
        test_results['prompt_templates'] = 'passed'
        
    except Exception as e:
        print(f"  ❌ Prompt template test failed: {e}")
        test_results['prompt_templates'] = 'failed'
    
    # Summary
    print("\n📊 Integration Test Results")
    print("=" * 50)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result == 'passed')
    
    for test_name, status in test_results.items():
        icon = '✅' if status == 'passed' else '❌'
        formatted_name = test_name.replace('_', ' ').title()
        print(f"{icon} {formatted_name}: {status}")
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 Agent-LLM integration is ready!")
        print("💡 Next step: Set up API keys to enable real LLM calls")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} integration issue(s) found.")
    
    return test_results

if __name__ == "__main__":
    asyncio.run(test_agent_llm_integration())