#!/usr/bin/env python3
"""
Together.ai Connection and Integration Test for OneVice
Tests the LLMRouter with Together.ai as primary provider
"""

import os
import sys
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.router import LLMRouter, QueryComplexity
from llm.providers.together_provider import TogetherProvider
from security.rbac import UserRole, DataSensitivityLevel

async def test_together_provider():
    """Test direct Together.ai provider functionality"""
    
    print("🧪 Testing Together.ai Provider")
    print("=" * 50)
    
    api_key = os.getenv('TOGETHER_API_KEY')
    if not api_key:
        print("❌ TOGETHER_API_KEY not found in environment")
        return False
    
    try:
        provider = TogetherProvider(api_key)
        
        # Test connection
        print("⏳ Testing connection...")
        result = await provider.test_connection()
        
        if result["status"] == "success":
            print(f"✅ Connection successful")
            print(f"   📋 Model: {result['model']}")
            print(f"   📋 Response: {result['response']}")
            print(f"   📋 Usage: {result['usage']}")
        else:
            print(f"❌ Connection failed: {result['error']}")
            return False
        
        # Test Mixtral model
        print("\n⏳ Testing Mixtral-8x7B...")
        mixtral_response = await provider.complete(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "user", "content": "What is the capital of France? Respond in one sentence."}
            ],
            max_tokens=100,
            temperature=0.1
        )
        print(f"✅ Mixtral response: {mixtral_response['content'][:100]}...")
        print(f"   📊 Tokens used: {mixtral_response['usage']['total_tokens']}")
        
        # Test Llama 3 model
        print("\n⏳ Testing Llama-3-70B...")
        llama_response = await provider.complete(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=[
                {"role": "user", "content": "Analyze the benefits of using open-source LLMs. Provide 3 key points."}
            ],
            max_tokens=200,
            temperature=0.3
        )
        print(f"✅ Llama 3 response: {llama_response['content'][:150]}...")
        print(f"   📊 Tokens used: {llama_response['usage']['total_tokens']}")
        
        # Test embeddings
        print("\n⏳ Testing embeddings...")
        embeddings_response = await provider.get_embeddings([
            "OneVice AI system for entertainment industry",
            "Secure data processing with Together.ai"
        ])
        print(f"✅ Embeddings generated: {len(embeddings_response['embeddings'])} vectors")
        print(f"   📊 Dimension: {len(embeddings_response['embeddings'][0])}")
        
        await provider.close()
        return True
        
    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        return False

async def test_llm_router():
    """Test LLMRouter with security-first routing"""
    
    print("\n🧪 Testing LLMRouter Security Routing")
    print("=" * 50)
    
    try:
        router = LLMRouter()
        
        # Test 1: Sensitive data routing (should always go to Together.ai)
        print("⏳ Test 1: Sensitive data routing...")
        
        user_context = {
            "role": "Leadership",
            "data_sensitivity": DataSensitivityLevel.EXACT_BUDGETS.value,  # Most sensitive
            "user_id": "test_user_123"
        }
        
        optimal_model = await router.get_optimal_model(
            query="What is the budget breakdown for Project X?",
            user_role=UserRole.LEADERSHIP,
            data_sensitivity=DataSensitivityLevel.EXACT_BUDGETS.value,
            query_complexity=QueryComplexity.MODERATE
        )
        
        print(f"✅ Sensitive data routed to: {optimal_model}")
        assert "together:" in optimal_model, "Sensitive data should route to Together.ai"
        
        # Test 2: Non-sensitive data with complex query
        print("\n⏳ Test 2: Non-sensitive complex query...")
        
        user_context_non_sensitive = {
            "role": "Salesperson",
            "data_sensitivity": DataSensitivityLevel.SALES_MATERIALS.value,  # Least sensitive
            "user_id": "test_user_456"
        }
        
        complex_model = await router.get_optimal_model(
            query="Analyze the current market trends in the entertainment industry",
            user_role=UserRole.SALESPERSON,
            data_sensitivity=DataSensitivityLevel.SALES_MATERIALS.value,
            query_complexity=QueryComplexity.COMPLEX
        )
        
        print(f"✅ Complex query routed to: {complex_model}")
        
        # Test 3: Available models for different security levels
        print("\n⏳ Test 3: Available models by security level...")
        
        leadership_models = await router.get_available_models(
            UserRole.LEADERSHIP, 
            DataSensitivityLevel.EXACT_BUDGETS.value
        )
        print(f"✅ Leadership (sensitive): {leadership_models}")
        
        salesperson_models = await router.get_available_models(
            UserRole.SALESPERSON,
            DataSensitivityLevel.SALES_MATERIALS.value
        )
        print(f"✅ Salesperson (non-sensitive): {salesperson_models}")
        
        # Test 4: Provider status
        print("\n⏳ Test 4: Provider status...")
        status = router.get_provider_status()
        print(f"✅ Provider status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Router test failed: {e}")
        return False

async def test_full_integration():
    """Test full integration with actual query routing"""
    
    print("\n🧪 Testing Full Integration")
    print("=" * 50)
    
    try:
        router = LLMRouter()
        
        # Test sensitive data query
        print("⏳ Testing sensitive data query routing...")
        
        sensitive_context = {
            "role": "Leadership",
            "data_sensitivity": DataSensitivityLevel.CONTRACTS.value,
            "user_id": "test_integration"
        }
        
        response = await router.route_query(
            query="What are the key considerations for entertainment industry contracts?",
            user_context=sensitive_context,
            system_prompt="You are an AI assistant specializing in entertainment industry knowledge."
        )
        
        print(f"✅ Query processed successfully")
        print(f"   📋 Model used: {response['routing_info']['selected_model']}")
        print(f"   📋 Provider: {response['routing_info']['provider']}")
        print(f"   📋 Data sensitivity: {response['routing_info']['data_sensitivity']}")
        print(f"   📋 Response preview: {response.get('content', '')[:100]}...")
        print(f"   💰 Estimated cost: ${response['routing_info']['cost_estimate']:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Run all Together.ai integration tests"""
    
    print("🔍 OneVice Together.ai Integration Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check if Together.ai API key is available
    if not os.getenv('TOGETHER_API_KEY'):
        print("❌ Error: TOGETHER_API_KEY not found in .env file")
        print("   Please add your Together.ai API key to the .env file")
        sys.exit(1)
    
    test_results = []
    
    # Run tests
    test_results.append(("Together.ai Provider", await test_together_provider()))
    test_results.append(("LLM Router", await test_llm_router()))
    test_results.append(("Full Integration", await test_full_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed! Together.ai integration is ready.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())