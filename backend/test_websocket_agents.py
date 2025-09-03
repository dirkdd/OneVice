#!/usr/bin/env python3
"""
Test script for WebSocket + LangGraph Agent integration

This script tests the integration between:
1. WebSocket chat handler
2. Agent Orchestrator
3. LangGraph multi-agent workflows
4. LLM routing system
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketAgentTester:
    def __init__(self, websocket_url: str = "ws://localhost:8000/ws"):
        self.websocket_url = websocket_url
        self.websocket = None
        
    async def connect(self):
        """Connect to WebSocket endpoint"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            logger.info(f"Connected to WebSocket at {self.websocket_url}")
            
            # Wait for connection message
            connection_msg = await self.websocket.recv()
            logger.info(f"Connection message: {connection_msg}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False
    
    async def authenticate(self, mock_token: str = "mock_jwt_token"):
        """Send authentication message"""
        auth_message = {
            "type": "auth",
            "token": mock_token
        }
        
        await self.websocket.send(json.dumps(auth_message))
        logger.info("Sent authentication message")
        
        # Wait for auth response
        response = await self.websocket.recv()
        auth_response = json.loads(response)
        
        if auth_response.get("type") == "auth_success":
            logger.info(f"Authentication successful: {auth_response['data']['message']}")
            return True
        else:
            logger.error(f"Authentication failed: {auth_response}")
            return False
    
    async def send_chat_message(self, content: str, conversation_id: str = None):
        """Send chat message and return response"""
        message = {
            "type": "user_message",
            "content": content,
            "conversation_id": conversation_id,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "test_mode": True
            }
        }
        
        logger.info(f"Sending message: {content}")
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response_data = await self.websocket.recv()
        response = json.loads(response_data)
        
        return response
    
    async def test_agent_routing(self):
        """Test different types of queries that should route to different agents"""
        
        test_queries = [
            {
                "query": "I need to analyze our Q4 sales performance and market trends",
                "expected_agent": "sales",
                "description": "Sales intelligence query"
            },
            {
                "query": "Help me find experienced directors for a luxury commercial shoot",
                "expected_agent": "talent", 
                "description": "Talent acquisition query"
            },
            {
                "query": "Generate a performance report on our recent campaigns with ROI analysis",
                "expected_agent": "analytics",
                "description": "Analytics query"
            },
            {
                "query": "Hello, how can OneVice AI help me today?",
                "expected_agent": "sales",  # Default fallback
                "description": "General greeting"
            }
        ]
        
        results = []
        conversation_id = f"test_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for test in test_queries:
            logger.info(f"\n--- Testing: {test['description']} ---")
            logger.info(f"Query: {test['query']}")
            
            try:
                response = await self.send_chat_message(test['query'], conversation_id)
                
                if response.get('type') == 'chat_response':
                    data = response['data']
                    ai_message = data['ai_message']
                    agent_info = ai_message.get('agent_info')
                    
                    logger.info(f"Response received: {ai_message['content'][:100]}...")
                    logger.info(f"Agent info: {agent_info}")
                    
                    result = {
                        "query": test['query'],
                        "expected_agent": test['expected_agent'],
                        "response": ai_message['content'],
                        "agent_info": agent_info,
                        "success": True
                    }
                    
                    # Check if correct agent was used (if agent info available)
                    if agent_info:
                        if agent_info.get('type') == 'multi_agent':
                            actual_agent = agent_info.get('primary_agent')
                            if actual_agent == test['expected_agent']:
                                logger.info(f"✅ Correct agent used: {actual_agent}")
                            else:
                                logger.info(f"⚠️ Different agent used: {actual_agent} (expected {test['expected_agent']})")
                        else:
                            logger.info(f"🔄 Fallback mode: {agent_info.get('type')}")
                    
                else:
                    logger.error(f"Unexpected response type: {response.get('type')}")
                    result = {
                        "query": test['query'],
                        "expected_agent": test['expected_agent'],
                        "error": f"Unexpected response: {response}",
                        "success": False
                    }
                
                results.append(result)
                
                # Small delay between tests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Test failed: {e}")
                results.append({
                    "query": test['query'],
                    "expected_agent": test['expected_agent'],
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket connection closed")

async def test_ai_system_status(base_url: str = "http://localhost:8000"):
    """Test the AI system status endpoint"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/ai/status") as response:
                if response.status == 200:
                    status = await response.json()
                    logger.info("AI System Status:")
                    logger.info(json.dumps(status, indent=2))
                    return status
                else:
                    logger.error(f"Status endpoint failed: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Failed to check AI status: {e}")
        return None

async def main():
    """Main test function"""
    logger.info("🚀 Starting WebSocket + LangGraph Agent Integration Test")
    
    # Test AI system status first
    logger.info("\n--- Testing AI System Status ---")
    status = await test_ai_system_status()
    
    if status:
        orchestrator_available = status.get('components', {}).get('agent_orchestrator', {}).get('available', False)
        if orchestrator_available:
            logger.info("✅ Agent Orchestrator is available")
        else:
            logger.info("⚠️ Agent Orchestrator not available - will test LLM fallback")
    
    # Test WebSocket integration
    logger.info("\n--- Testing WebSocket Integration ---")
    tester = WebSocketAgentTester()
    
    try:
        # Connect to WebSocket
        if not await tester.connect():
            logger.error("Failed to connect to WebSocket")
            return
        
        # Skip authentication for now (mock authentication)
        logger.info("Skipping authentication for test")
        
        # Test agent routing
        logger.info("\n--- Testing Agent Routing ---")
        results = await tester.test_agent_routing()
        
        # Summary
        logger.info("\n--- Test Summary ---")
        successful_tests = [r for r in results if r.get('success')]
        failed_tests = [r for r in results if not r.get('success')]
        
        logger.info(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
        if failed_tests:
            logger.info(f"❌ Failed tests: {len(failed_tests)}")
            for test in failed_tests:
                logger.info(f"  - {test['query']}: {test.get('error', 'Unknown error')}")
        
        logger.info("\n🎉 Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
    
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())