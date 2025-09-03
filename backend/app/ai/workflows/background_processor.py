"""
Background Memory Processing

Asynchronous memory extraction, consolidation, and optimization
to maintain system performance while building comprehensive memory.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

import redis.asyncio as redis
from redis.asyncio import Redis

from ..memory.langmem_manager import LangMemManager
from ..memory.memory_types import MemoryType, MemoryImportance
from ..config import AIConfig
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

@dataclass
class ProcessingTask:
    """Background processing task"""
    task_id: str
    task_type: str
    user_id: str
    conversation_id: str
    data: Dict[str, Any]
    priority: int  # 1=high, 5=low
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3

class BackgroundMemoryProcessor:
    """
    Background processor for memory operations
    
    Features:
    - Async memory extraction from conversations
    - Memory consolidation and optimization
    - Relationship discovery and graph updates
    - Performance monitoring and metrics
    """
    
    def __init__(self, config: AIConfig, memory_manager: LangMemManager):
        self.config = config
        self.memory_manager = memory_manager
        
        # Redis for task queue
        self.redis_client: Optional[Redis] = None
        self.task_queue_key = "memory:background_tasks"
        self.processing_key = "memory:processing"
        self.results_key = "memory:results"
        
        # Processing control
        self.is_running = False
        self.max_concurrent_tasks = 5
        self.processing_interval = 10  # seconds
        self.batch_size = 10
        
        # Metrics
        self.metrics = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "memories_extracted": 0,
            "consolidations_performed": 0,
            "processing_time_avg": 0.0,
            "last_run": None
        }
    
    async def initialize(self):
        """Initialize background processor"""
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("Background memory processor initialized")
            
        except Exception as e:
            logger.error(f"Background processor initialization failed: {e}")
            raise AIProcessingError(f"Background processor init failed: {e}")
    
    async def start_processing(self):
        """Start background processing loop"""
        if self.is_running:
            logger.warning("Background processor already running")
            return
        
        self.is_running = True
        logger.info("Starting background memory processing...")
        
        try:
            while self.is_running:
                await self._process_batch()
                await asyncio.sleep(self.processing_interval)
                
        except Exception as e:
            logger.error(f"Background processing error: {e}")
        finally:
            self.is_running = False
            logger.info("Background memory processing stopped")
    
    async def stop_processing(self):
        """Stop background processing"""
        self.is_running = False
        logger.info("Stopping background memory processing...")
    
    async def queue_memory_extraction(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        priority: int = 3
    ):
        """
        Queue memory extraction task
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            messages: Messages to process
            priority: Task priority (1=high, 5=low)
        """
        try:
            task = ProcessingTask(
                task_id=f"extract_{conversation_id}_{datetime.utcnow().timestamp()}",
                task_type="memory_extraction",
                user_id=user_id,
                conversation_id=conversation_id,
                data={
                    "messages": messages,
                    "context": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "conversation"
                    }
                },
                priority=priority,
                created_at=datetime.utcnow()
            )
            
            await self._queue_task(task)
            logger.debug(f"Queued memory extraction task: {task.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to queue memory extraction: {e}")
    
    async def queue_memory_consolidation(
        self,
        user_id: str,
        memory_ids: Optional[List[str]] = None,
        priority: int = 4
    ):
        """
        Queue memory consolidation task
        
        Args:
            user_id: User ID
            memory_ids: Specific memory IDs to consolidate (optional)
            priority: Task priority
        """
        try:
            task = ProcessingTask(
                task_id=f"consolidate_{user_id}_{datetime.utcnow().timestamp()}",
                task_type="memory_consolidation",
                user_id=user_id,
                conversation_id="",
                data={
                    "memory_ids": memory_ids,
                    "context": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "consolidation_trigger"
                    }
                },
                priority=priority,
                created_at=datetime.utcnow()
            )
            
            await self._queue_task(task)
            logger.debug(f"Queued memory consolidation task: {task.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to queue memory consolidation: {e}")
    
    async def queue_relationship_discovery(
        self,
        user_id: str,
        memory_id: str,
        priority: int = 4
    ):
        """
        Queue relationship discovery task
        
        Args:
            user_id: User ID
            memory_id: Memory ID to find relationships for
            priority: Task priority
        """
        try:
            task = ProcessingTask(
                task_id=f"relations_{memory_id}_{datetime.utcnow().timestamp()}",
                task_type="relationship_discovery",
                user_id=user_id,
                conversation_id="",
                data={
                    "memory_id": memory_id,
                    "context": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "new_memory"
                    }
                },
                priority=priority,
                created_at=datetime.utcnow()
            )
            
            await self._queue_task(task)
            logger.debug(f"Queued relationship discovery task: {task.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to queue relationship discovery: {e}")
    
    async def _queue_task(self, task: ProcessingTask):
        """Add task to processing queue"""
        task_data = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "user_id": task.user_id,
            "conversation_id": task.conversation_id,
            "data": task.data,
            "priority": task.priority,
            "created_at": task.created_at.isoformat(),
            "retry_count": task.retry_count,
            "max_retries": task.max_retries
        }
        
        # Use priority score for sorting (lower = higher priority)
        priority_score = task.priority * 1000 + int(task.created_at.timestamp())
        
        await self.redis_client.zadd(
            self.task_queue_key,
            {json.dumps(task_data): priority_score}
        )
    
    async def _process_batch(self):
        """Process a batch of background tasks"""
        try:
            # Get tasks from queue
            tasks_data = await self.redis_client.zpopmin(
                self.task_queue_key,
                count=self.batch_size
            )
            
            if not tasks_data:
                return
            
            # Parse tasks
            tasks = []
            for task_json, _ in tasks_data:
                try:
                    task_dict = json.loads(task_json)
                    task = ProcessingTask(
                        task_id=task_dict["task_id"],
                        task_type=task_dict["task_type"],
                        user_id=task_dict["user_id"],
                        conversation_id=task_dict["conversation_id"],
                        data=task_dict["data"],
                        priority=task_dict["priority"],
                        created_at=datetime.fromisoformat(task_dict["created_at"]),
                        retry_count=task_dict.get("retry_count", 0),
                        max_retries=task_dict.get("max_retries", 3)
                    )
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Failed to parse task: {e}")
            
            if not tasks:
                return
            
            logger.info(f"Processing {len(tasks)} background tasks")
            
            # Process tasks concurrently
            semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
            processing_tasks = [
                self._process_task_with_semaphore(semaphore, task)
                for task in tasks
            ]
            
            results = await asyncio.gather(*processing_tasks, return_exceptions=True)
            
            # Update metrics
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            
            self.metrics["tasks_processed"] += successful
            self.metrics["tasks_failed"] += failed
            self.metrics["last_run"] = datetime.utcnow().isoformat()
            
            logger.info(f"Batch processed: {successful} success, {failed} failed")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
    
    async def _process_task_with_semaphore(self, semaphore: asyncio.Semaphore, task: ProcessingTask):
        """Process single task with semaphore control"""
        async with semaphore:
            return await self._process_single_task(task)
    
    async def _process_single_task(self, task: ProcessingTask) -> bool:
        """Process a single background task"""
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Processing task: {task.task_id} ({task.task_type})")
            
            if task.task_type == "memory_extraction":
                await self._process_memory_extraction(task)
            elif task.task_type == "memory_consolidation":
                await self._process_memory_consolidation(task)
            elif task.task_type == "relationship_discovery":
                await self._process_relationship_discovery(task)
            else:
                logger.warning(f"Unknown task type: {task.task_type}")
                return False
            
            # Store result
            result = {
                "task_id": task.task_id,
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "processing_time": (datetime.utcnow() - start_time).total_seconds()
            }
            
            await self.redis_client.setex(
                f"{self.results_key}:{task.task_id}",
                3600,  # 1 hour TTL
                json.dumps(result)
            )
            
            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            current_avg = self.metrics["processing_time_avg"]
            total_processed = self.metrics["tasks_processed"]
            self.metrics["processing_time_avg"] = (
                (current_avg * total_processed + processing_time) / (total_processed + 1)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Task processing failed: {task.task_id} - {e}")
            
            # Handle retry
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
                await self._queue_task(task)
                logger.info(f"Task {task.task_id} retried ({task.retry_count}/{task.max_retries})")
            else:
                # Store failure result
                result = {
                    "task_id": task.task_id,
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.utcnow().isoformat(),
                    "retry_count": task.retry_count
                }
                
                await self.redis_client.setex(
                    f"{self.results_key}:{task.task_id}",
                    3600,
                    json.dumps(result)
                )
            
            return False
    
    async def _process_memory_extraction(self, task: ProcessingTask):
        """Process memory extraction task"""
        messages = task.data["messages"]
        context = task.data.get("context", {})
        
        # Extract memories from conversation
        extracted_memories = await self.memory_manager.extract_memories_from_conversation(
            user_id=task.user_id,
            conversation_id=task.conversation_id,
            messages=messages,
            context=context
        )
        
        self.metrics["memories_extracted"] += len(extracted_memories)
        logger.debug(f"Extracted {len(extracted_memories)} memories from {task.conversation_id}")
    
    async def _process_memory_consolidation(self, task: ProcessingTask):
        """Process memory consolidation task"""
        memory_ids = task.data.get("memory_ids")
        
        # Perform consolidation
        consolidation_result = await self.memory_manager.consolidate_memories(
            user_id=task.user_id,
            memory_ids=memory_ids
        )
        
        self.metrics["consolidations_performed"] += 1
        logger.debug(f"Consolidated memories for user {task.user_id}")
    
    async def _process_relationship_discovery(self, task: ProcessingTask):
        """Process relationship discovery task"""
        memory_id = task.data["memory_id"]
        
        # Discover and create relationships
        relationships = await self.memory_manager.discover_memory_relationships(
            user_id=task.user_id,
            memory_id=memory_id
        )
        
        logger.debug(f"Discovered {len(relationships)} relationships for memory {memory_id}")
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get background processing status and metrics"""
        try:
            # Get queue stats
            queue_size = await self.redis_client.zcard(self.task_queue_key)
            processing_count = await self.redis_client.scard(self.processing_key)
            
            return {
                "is_running": self.is_running,
                "queue_size": queue_size,
                "processing_count": processing_count,
                "max_concurrent": self.max_concurrent_tasks,
                "metrics": self.metrics,
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing status: {e}")
            return {"error": str(e)}
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result of a specific task"""
        try:
            result_json = await self.redis_client.get(f"{self.results_key}:{task_id}")
            if result_json:
                return json.loads(result_json)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get task result: {e}")
            return None
    
    async def cleanup_old_results(self, max_age_hours: int = 24):
        """Clean up old task results"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # This would need implementation to scan and delete old results
            # For now, we rely on Redis TTL
            
            logger.info(f"Cleanup completed for results older than {max_age_hours} hours")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def close(self):
        """Close background processor"""
        try:
            await self.stop_processing()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Background memory processor closed")
            
        except Exception as e:
            logger.error(f"Error closing background processor: {e}")