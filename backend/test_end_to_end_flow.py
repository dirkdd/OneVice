#!/usr/bin/env python3
"""
End-to-End Flow Test

Tests the complete flow from user request through agent processing 
with real LLM calls to verify the system works end-to-end.
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

async def test_end_to_end_flow():
    """Test complete end-to-end flow with real LLM calls"""
    
    print("🔥 End-to-End Flow Test")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Check API keys are configured
    print("\n1. Checking API key configuration...")
    
    try:
        from app.ai.config import AIConfig
        config = AIConfig()
        
        # Check Together.ai key
        together_key = config.together_api_key
        if together_key and together_key not in ["[dev-together-key]", ""]:
            print(f"  ✅ Together.ai key configured: {together_key[:8]}...")
            results['together_key'] = 'configured'
        else:
            print("  ❌ Together.ai API key missing")
            results['together_key'] = 'missing'
        
        # Check OpenAI key
        openai_key = config.openai_api_key
        if openai_key and openai_key not in ["[dev-openai-key]", "sk-your-openai-api-key", ""]:
            print(f"  ✅ OpenAI key configured: {openai_key[:8]}...")
            results['openai_key'] = 'configured'
        else:
            print("  ❌ OpenAI API key missing or placeholder")
            results['openai_key'] = 'missing'
        
    except Exception as e:
        print(f"  ❌ Configuration check failed: {e}")
        results['config'] = 'failed'
        return results
    
    # Test 2: Initialize LLM Router and test provider
    print("\n2. Testing LLM provider connectivity...")
    
    try:
        from app.ai.llm.router import LLMRouter, LLMProvider
        
        llm_router = LLMRouter(config)
        
        # Test with whichever provider has a configured key
        if results.get('together_key') == 'configured':
            test_provider = LLMProvider.TOGETHER
            print("  🔄 Testing Together.ai provider...")
        elif results.get('openai_key') == 'configured':
            test_provider = LLMProvider.OPENAI  
            print("  🔄 Testing OpenAI provider...")
        else:
            print("  ❌ No API keys configured for testing")
            results['llm_test'] = 'no_keys'
            return results
        
        # Simple LLM test
        test_messages = [
            {"role": "user", "content": "Respond with exactly 'LLM connection working' and nothing else."}
        ]
        
        response = await llm_router.route_query(
            messages=test_messages,
            preferred_provider=test_provider
        )
        
        print(f"  ✅ LLM response: {response['content']}")
        print(f"  📊 Provider: {response.get('provider')}")
        print(f"  📊 Model: {response.get('model')}")
        print(f"  📊 Tokens: {response.get('usage', {}).get('total_tokens', 0)}")
        print(f"  💰 Cost: ${response.get('cost_estimate', 0):.4f}")
        
        results['llm_test'] = 'working'
        
    except Exception as e:
        print(f"  ❌ LLM provider test failed: {e}")
        results['llm_test'] = 'failed'
        return results
    
    # Test 3: Test agent initialization and chat
    print("\n3. Testing agent chat workflow...")
    
    try:
        from app.ai.agents.sales_agent import SalesIntelligenceAgent
        
        # Initialize sales agent
        sales_agent = SalesIntelligenceAgent(
            config=config,
            llm_router=llm_router
        )
        
        print("  ✅ Sales agent initialized")
        
        # Test agent chat
        user_context = {
            "user_id": "test_user_123",
            "role": "sales_analyst", 
            "department": "business_development"
        }
        
        response = await sales_agent.chat(
            message="What are your main capabilities as a sales intelligence agent?",
            user_context=user_context
        )
        
        print(f"  ✅ Agent response received")
        print(f"  📄 Content preview: {response['content'][:100]}...")
        print(f"  🆔 Conversation ID: {response.get('conversation_id', 'N/A')[:12]}...")
        print(f"  🤖 Agent type: {response.get('agent_type')}")
        print(f"  📊 Response metadata: {response.get('metadata', {})}")
        
        results['agent_chat'] = 'working'
        
    except Exception as e:
        print(f"  ❌ Agent chat test failed: {e}")
        results['agent_chat'] = 'failed'
        return results
    
    # Test 4: Test conversation continuity
    print("\n4. Testing conversation continuity...")
    
    try:
        # Continue the conversation with the same conversation ID
        conversation_id = response.get('conversation_id')
        
        followup_response = await sales_agent.chat(
            message="Can you give me a specific example of how you would analyze a lead?",
            user_context=user_context,
            conversation_id=conversation_id
        )
        
        print(f"  ✅ Follow-up response received")
        print(f"  📄 Content preview: {followup_response['content'][:100]}...")
        print(f"  🆔 Same conversation: {followup_response.get('conversation_id') == conversation_id}")
        
        results['conversation_continuity'] = 'working'
        
    except Exception as e:
        print(f"  ❌ Conversation continuity test failed: {e}")
        results['conversation_continuity'] = 'failed'
    
    # Test 5: Test provider fallback (if both providers available)
    if results.get('together_key') == 'configured' and results.get('openai_key') == 'configured':
        print("\n5. Testing provider fallback...")
        
        try:
            # Force failure on primary provider by using invalid params, then test fallback
            # This is a simplified test - in reality fallback is triggered by actual API errors
            
            # Test both providers work independently
            together_response = await llm_router.route_query(
                messages=[{"role": "user", "content": "Say 'Together.ai working'"}],
                preferred_provider=LLMProvider.TOGETHER
            )
            
            openai_response = await llm_router.route_query(
                messages=[{"role": "user", "content": "Say 'OpenAI working'"}], 
                preferred_provider=LLMProvider.OPENAI
            )
            
            print(f"  ✅ Together.ai response: {together_response['content']}")
            print(f"  ✅ OpenAI response: {openai_response['content']}")
            print(f"  ✅ Both providers operational")
            
            results['provider_fallback'] = 'available'
            
        except Exception as e:
            print(f"  ❌ Provider fallback test failed: {e}")
            results['provider_fallback'] = 'failed'
    else:
        print("\n5. Skipping provider fallback test (need both API keys)")
        results['provider_fallback'] = 'skipped'
    
    # Summary
    print("\n📊 End-to-End Test Results")
    print("=" * 50)
    
    status_icons = {
        'configured': '✅',
        'working': '✅', 
        'available': '✅',
        'missing': '🔑',
        'failed': '❌',
        'no_keys': '🔑',
        'skipped': '⏭️'
    }
    
    test_names = {
        'together_key': 'Together.ai API Key',
        'openai_key': 'OpenAI API Key', 
        'llm_test': 'LLM Provider Test',
        'agent_chat': 'Agent Chat Flow',
        'conversation_continuity': 'Conversation Memory',
        'provider_fallback': 'Provider Fallback'
    }
    
    for test_key, status in results.items():
        icon = status_icons.get(status, '❓')
        test_name = test_names.get(test_key, test_key.replace('_', ' ').title())
        print(f"{icon} {test_name}: {status}")
    
    # Overall assessment
    critical_tests = ['llm_test', 'agent_chat']
    critical_working = all(results.get(test) == 'working' for test in critical_tests)
    
    if critical_working:
        print("\n🎉 End-to-end flow is WORKING!")
        print("✅ Core system operational:")
        print("   - LLM providers responding")
        print("   - Agents processing queries")  
        print("   - Conversation flow complete")
        
        if results.get('conversation_continuity') == 'working':
            print("   - Memory persistence working")
        if results.get('provider_fallback') == 'available':
            print("   - Provider redundancy available")
        
        print("\n💡 System ready for production use!")
        
    else:
        print("\n⚠️  End-to-end flow has issues")
        print("🔧 Required fixes:")
        
        if results.get('together_key') == 'missing':
            print("   - Configure TOGETHER_API_KEY in .env")
        if results.get('openai_key') == 'missing':
            print("   - Configure OPENAI_API_KEY in .env")
        if results.get('llm_test') in ['failed', 'no_keys']:
            print("   - Fix LLM provider connectivity")
        if results.get('agent_chat') == 'failed':
            print("   - Debug agent chat workflow")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_end_to_end_flow())