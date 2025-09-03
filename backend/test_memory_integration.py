#!/usr/bin/env python3
"""
Memory System Integration Test

Tests the complete memory system including:
- LangMem + Neo4j integration
- LangGraph checkpoint with Redis
- Background processing
- API endpoints
- WebSocket communication
"""

import asyncio
import json
import logging
from typing import Dict, Any
import os
from datetime import datetime

# Set up environment
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")

from app.ai.config import AIConfig
from app.services.memory_service import MemoryServiceManager
from app.ai.graph.connection import Neo4jClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemorySystemTester:
    """Comprehensive memory system tester"""
    
    def __init__(self):
        self.config = AIConfig()
        self.memory_service: MemoryServiceManager = None
        self.test_user_id = "test_user_001"
        self.test_results = {}
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting Memory System Integration Tests")
        print("=" * 60)
        
        try:
            # Initialize memory service
            await self.test_initialization()
            
            # Test core memory operations
            await self.test_memory_operations()
            
            # Test conversation handling
            await self.test_conversation_handling()
            
            # Test background processing
            await self.test_background_processing()
            
            # Test performance
            await self.test_performance()
            
            # Generate report
            self.generate_report()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            logger.error(f"Test suite error: {e}")
        finally:
            await self.cleanup()
    
    async def test_initialization(self):
        """Test memory service initialization"""
        print("\n🔧 Testing Memory Service Initialization")
        print("-" * 40)
        
        try:
            # Initialize service
            start_time = datetime.utcnow()
            self.memory_service = MemoryServiceManager(self.config)
            await self.memory_service.initialize()
            init_time = (datetime.utcnow() - start_time).total_seconds()
            
            print(f"✅ Memory service initialized in {init_time:.2f}s")
            
            # Test service stats
            stats = await self.memory_service.get_service_stats()
            print(f"✅ Service stats retrieved: {stats['service_status']}")
            
            # Test component health
            healthy_components = 0
            total_components = len(stats.get('components', {}))
            
            for component, status in stats.get('components', {}).items():
                if status.get('status') == 'healthy':
                    healthy_components += 1
                    print(f"  ✅ {component}: healthy")
                else:
                    print(f"  ⚠️  {component}: {status.get('status')}")
            
            self.test_results['initialization'] = {
                'status': 'passed',
                'init_time': init_time,
                'healthy_components': f"{healthy_components}/{total_components}",
                'details': stats
            }
            
        except Exception as e:
            print(f"❌ Initialization test failed: {e}")
            self.test_results['initialization'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    async def test_memory_operations(self):
        """Test core memory operations"""
        print("\n🧠 Testing Core Memory Operations")
        print("-" * 40)
        
        try:
            # Test memory search (should work even with no memories)
            search_results = await self.memory_service.search_memories(
                user_id=self.test_user_id,
                query="test query",
                limit=5
            )
            print(f"✅ Memory search completed: {len(search_results)} results")
            
            # Test memory consolidation
            consolidation_result = await self.memory_service.trigger_memory_consolidation(
                user_id=self.test_user_id,
                background=False
            )
            print(f"✅ Memory consolidation: {consolidation_result['status']}")
            
            # Test memory graph retrieval
            graph_data = await self.memory_service.get_memory_graph(
                user_id=self.test_user_id
            )
            print(f"✅ Memory graph retrieved: {len(graph_data.get('nodes', []))} nodes")
            
            self.test_results['memory_operations'] = {
                'status': 'passed',
                'search_results': len(search_results),
                'consolidation': consolidation_result['status'],
                'graph_nodes': len(graph_data.get('nodes', []))
            }
            
        except Exception as e:
            print(f"❌ Memory operations test failed: {e}")
            self.test_results['memory_operations'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    async def test_conversation_handling(self):
        """Test conversation handling with memory"""
        print("\n💬 Testing Conversation Handling")
        print("-" * 40)
        
        try:
            # Test chat processing
            messages = [
                "Hello, I'm working on a new film project",
                "I need to find a director for a sci-fi thriller",
                "Budget is around $2 million"
            ]
            
            conversation_id = f"test_conv_{datetime.utcnow().timestamp()}"
            responses = []
            
            for i, message in enumerate(messages):
                print(f"  Sending message {i+1}: {message[:30]}...")
                
                start_time = datetime.utcnow()
                response = await self.memory_service.process_chat_message(
                    user_id=self.test_user_id,
                    message=message,
                    conversation_id=conversation_id,
                    agent_preference="sales"
                )
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                responses.append({
                    'message': message,
                    'response_time': response_time,
                    'has_response': bool(response.get('content'))
                })
                
                print(f"    ✅ Response received in {response_time:.2f}s")
            
            # Test conversation retrieval
            conversations = await self.memory_service.get_user_conversations(
                user_id=self.test_user_id
            )
            print(f"✅ Conversation history: {len(conversations)} conversations")
            
            avg_response_time = sum(r['response_time'] for r in responses) / len(responses)
            
            self.test_results['conversation_handling'] = {
                'status': 'passed',
                'messages_processed': len(messages),
                'avg_response_time': round(avg_response_time, 2),
                'conversations_found': len(conversations)
            }
            
        except Exception as e:
            print(f"❌ Conversation handling test failed: {e}")
            self.test_results['conversation_handling'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    async def test_background_processing(self):
        """Test background processing capabilities"""
        print("\n⚡ Testing Background Processing")
        print("-" * 40)
        
        try:
            if not self.memory_service.background_processor:
                print("⚠️  Background processor not available")
                self.test_results['background_processing'] = {
                    'status': 'skipped',
                    'reason': 'background processor not available'
                }
                return
            
            # Get initial processing status
            initial_status = await self.memory_service.background_processor.get_processing_status()
            print(f"✅ Background processor status: {initial_status.get('is_running', 'unknown')}")
            
            # Queue some background tasks
            await self.memory_service.background_processor.queue_memory_extraction(
                user_id=self.test_user_id,
                conversation_id="test_conversation",
                messages=[
                    {"role": "user", "content": "Test message 1"},
                    {"role": "assistant", "content": "Test response 1"}
                ],
                priority=1
            )
            
            await self.memory_service.background_processor.queue_memory_consolidation(
                user_id=self.test_user_id,
                priority=2
            )
            
            print("✅ Background tasks queued")
            
            # Wait a moment for processing
            await asyncio.sleep(5)
            
            # Check final status
            final_status = await self.memory_service.background_processor.get_processing_status()
            
            self.test_results['background_processing'] = {
                'status': 'passed',
                'is_running': final_status.get('is_running', False),
                'queue_size': final_status.get('queue_size', 0),
                'metrics': final_status.get('metrics', {})
            }
            
        except Exception as e:
            print(f"❌ Background processing test failed: {e}")
            self.test_results['background_processing'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_performance(self):
        """Test system performance under load"""
        print("\n🚀 Testing Performance")
        print("-" * 40)
        
        try:
            # Test concurrent memory searches
            print("  Testing concurrent memory searches...")
            
            search_tasks = []
            for i in range(10):
                task = self.memory_service.search_memories(
                    user_id=self.test_user_id,
                    query=f"test query {i}",
                    limit=5
                )
                search_tasks.append(task)
            
            start_time = datetime.utcnow()
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            concurrent_time = (datetime.utcnow() - start_time).total_seconds()
            
            successful_searches = sum(1 for r in results if not isinstance(r, Exception))
            print(f"    ✅ {successful_searches}/10 concurrent searches in {concurrent_time:.2f}s")
            
            # Test memory system resource usage
            stats = await self.memory_service.get_service_stats()
            
            self.test_results['performance'] = {
                'status': 'passed',
                'concurrent_searches': f"{successful_searches}/10",
                'concurrent_time': round(concurrent_time, 2),
                'avg_search_time': round(concurrent_time / 10, 3),
                'service_health': stats.get('service_status')
            }
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            self.test_results['performance'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Test Results Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'passed')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'failed')
        skipped_tests = sum(1 for result in self.test_results.values() if result['status'] == 'skipped')
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Skipped: {skipped_tests}")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 40)
        
        for test_name, result in self.test_results.items():
            status_icon = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⚠️'
            }.get(result['status'], '❓')
            
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result['status']}")
            
            # Show key metrics
            for key, value in result.items():
                if key not in ['status', 'error', 'details']:
                    print(f"    {key}: {value}")
            
            if result['status'] == 'failed' and 'error' in result:
                print(f"    Error: {result['error']}")
        
        # Performance insights
        if 'performance' in self.test_results and self.test_results['performance']['status'] == 'passed':
            perf = self.test_results['performance']
            print(f"\n🚀 Performance Insights:")
            print(f"  - Concurrent search capability: {perf['concurrent_searches']}")
            print(f"  - Average search latency: {perf['avg_search_time']}s")
            print(f"  - System can handle ~{10 / perf['concurrent_time']:.1f} searches/second")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if failed_tests > 0:
            print("  - Review failed tests and fix underlying issues")
        if 'initialization' in self.test_results:
            init_time = self.test_results['initialization'].get('init_time', 0)
            if init_time > 10:
                print(f"  - Initialization time ({init_time:.1f}s) is high - consider lazy loading")
        if 'performance' in self.test_results:
            avg_time = self.test_results['performance'].get('avg_search_time', 0)
            if avg_time > 1.0:
                print(f"  - Search latency ({avg_time:.2f}s) is high - consider caching")
        
        print("\n" + "=" * 60)
        print("🏁 Memory System Integration Test Complete")
    
    async def cleanup(self):
        """Clean up test resources"""
        try:
            if self.memory_service:
                await self.memory_service.cleanup()
            print("✅ Test cleanup completed")
        except Exception as e:
            print(f"⚠️  Test cleanup failed: {e}")

async def main():
    """Main test execution"""
    tester = MemorySystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())