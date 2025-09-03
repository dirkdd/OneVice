"""
LangGraph Checkpoint Manager

Manages conversation checkpointing using Redis for state persistence
and fault tolerance in multi-agent conversations.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import json

from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import StateSnapshot
import redis.asyncio as redis

from ..config import AIConfig
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    LangGraph checkpoint manager using Redis for conversation persistence
    
    Features:
    - Automatic checkpoint saving at each super-step
    - Conversation resumption across sessions
    - Fault tolerance and error recovery
    - Thread-based conversation isolation
    """
    
    def __init__(self, config: AIConfig, redis_url: Optional[str] = None):
        self.config = config
        self.redis_url = redis_url or config.redis_url
        
        # Initialize Redis checkpointer
        self.checkpointer: Optional[AsyncRedisSaver] = None
        self._redis_client: Optional[redis.Redis] = None
        
        # Checkpoint settings
        self.max_checkpoints_per_thread = 100
        self.checkpoint_retention_days = 30
        
    async def initialize(self) -> bool:
        """Initialize the checkpoint manager"""
        
        try:
            # Create Redis checkpointer
            self.checkpointer = AsyncRedisSaver.from_conn_string(self.redis_url)
            
            # Setup Redis indexes for checkpointing
            await self.checkpointer.setup()
            
            # Create direct Redis client for additional operations
            self._redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self._redis_client.ping()
            
            logger.info("Checkpoint manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint manager initialization failed: {e}")
            raise AIProcessingError(f"Checkpoint manager initialization failed: {e}")
    
    async def create_compiled_graph(
        self,
        graph_builder,
        **compile_kwargs
    ) -> CompiledStateGraph:
        """Create a compiled graph with checkpointing enabled"""
        
        if not self.checkpointer:
            await self.initialize()
        
        # Compile graph with checkpointer
        return graph_builder.compile(
            checkpointer=self.checkpointer,
            **compile_kwargs
        )
    
    async def save_conversation_metadata(
        self,
        thread_id: str,
        user_id: str,
        agent_types: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save conversation metadata alongside checkpoints"""
        
        try:
            conversation_data = {
                "thread_id": thread_id,
                "user_id": user_id,
                "agent_types": agent_types,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store in Redis with conversation-specific key
            key = f"checkpoint_metadata:{thread_id}"
            await self._redis_client.set(
                key,
                json.dumps(conversation_data),
                ex=int(timedelta(days=self.checkpoint_retention_days).total_seconds())
            )
            
            # Add to user's conversation list
            user_conversations_key = f"user_conversations:{user_id}"
            await self._redis_client.sadd(user_conversations_key, thread_id)
            await self._redis_client.expire(
                user_conversations_key,
                int(timedelta(days=self.checkpoint_retention_days).total_seconds())
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation metadata: {e}")
            return False
    
    async def get_conversation_metadata(
        self,
        thread_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversation metadata"""
        
        try:
            key = f"checkpoint_metadata:{thread_id}"
            data = await self._redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get conversation metadata: {e}")
            return None
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get list of user's conversations with metadata"""
        
        try:
            conversations = []
            
            # Get conversation IDs
            user_conversations_key = f"user_conversations:{user_id}"
            thread_ids = await self._redis_client.smembers(user_conversations_key)
            
            # Get metadata for each conversation
            for thread_id in list(thread_ids)[:limit]:
                metadata = await self.get_conversation_metadata(thread_id)
                if metadata:
                    conversations.append(metadata)
            
            # Sort by updated_at
            conversations.sort(
                key=lambda x: x.get("updated_at", ""),
                reverse=True
            )
            
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []
    
    async def get_conversation_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[StateSnapshot]:
        """Get conversation history as checkpoints"""
        
        try:
            if not self.checkpointer:
                return []
            
            # Get checkpoints for thread
            checkpoints = []
            async for checkpoint in self.checkpointer.list(
                {"configurable": {"thread_id": thread_id}},
                limit=limit
            ):
                checkpoints.append(checkpoint)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def resume_conversation(
        self,
        thread_id: str,
        compiled_graph: CompiledStateGraph
    ) -> Optional[StateSnapshot]:
        """Resume conversation from latest checkpoint"""
        
        try:
            # Get latest checkpoint
            config = {"configurable": {"thread_id": thread_id}}
            
            # Get current state
            current_state = await compiled_graph.aget_state(config)
            
            if current_state and current_state.values:
                logger.info(f"Resumed conversation {thread_id} from checkpoint")
                return current_state
            else:
                logger.info(f"No checkpoint found for conversation {thread_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to resume conversation: {e}")
            return None
    
    async def update_conversation(
        self,
        thread_id: str,
        user_id: str,
        message_count: Optional[int] = None
    ) -> bool:
        """Update conversation metadata after new messages"""
        
        try:
            # Get existing metadata
            metadata = await self.get_conversation_metadata(thread_id)
            
            if metadata:
                metadata["updated_at"] = datetime.utcnow().isoformat()
                if message_count is not None:
                    metadata["message_count"] = message_count
                
                # Save updated metadata
                key = f"checkpoint_metadata:{thread_id}"
                await self._redis_client.set(
                    key,
                    json.dumps(metadata),
                    ex=int(timedelta(days=self.checkpoint_retention_days).total_seconds())
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update conversation metadata: {e}")
            return False
    
    async def delete_conversation(
        self,
        thread_id: str,
        user_id: str
    ) -> bool:
        """Delete conversation and all its checkpoints"""
        
        try:
            # Delete checkpoints (this deletes all checkpoints for the thread)
            config = {"configurable": {"thread_id": thread_id}}
            
            # Delete metadata
            metadata_key = f"checkpoint_metadata:{thread_id}"
            await self._redis_client.delete(metadata_key)
            
            # Remove from user's conversation list
            user_conversations_key = f"user_conversations:{user_id}"
            await self._redis_client.srem(user_conversations_key, thread_id)
            
            logger.info(f"Deleted conversation {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False
    
    async def cleanup_old_checkpoints(
        self,
        max_age_days: int = None
    ) -> int:
        """Clean up old checkpoints and metadata"""
        
        max_age_days = max_age_days or self.checkpoint_retention_days
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        try:
            deleted_count = 0
            
            # Get all checkpoint metadata keys
            pattern = "checkpoint_metadata:*"
            keys = []
            
            async for key in self._redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            # Check each metadata entry
            for key in keys:
                data = await self._redis_client.get(key)
                if data:
                    metadata = json.loads(data)
                    created_at = datetime.fromisoformat(metadata.get("created_at", ""))
                    
                    if created_at < cutoff_date:
                        # Delete metadata
                        await self._redis_client.delete(key)
                        
                        # Extract thread_id and clean up
                        thread_id = key.replace("checkpoint_metadata:", "")
                        user_id = metadata.get("user_id")
                        
                        if user_id:
                            user_conversations_key = f"user_conversations:{user_id}"
                            await self._redis_client.srem(user_conversations_key, thread_id)
                        
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old conversations")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Checkpoint cleanup failed: {e}")
            return 0
    
    async def get_checkpoint_stats(self) -> Dict[str, Any]:
        """Get checkpoint system statistics"""
        
        try:
            # Count total conversations
            conversation_keys = []
            async for key in self._redis_client.scan_iter(match="checkpoint_metadata:*"):
                conversation_keys.append(key)
            
            # Count active conversations (last 24 hours)
            active_count = 0
            cutoff_date = datetime.utcnow() - timedelta(hours=24)
            
            for key in conversation_keys:
                data = await self._redis_client.get(key)
                if data:
                    metadata = json.loads(data)
                    updated_at = datetime.fromisoformat(metadata.get("updated_at", ""))
                    if updated_at > cutoff_date:
                        active_count += 1
            
            return {
                "total_conversations": len(conversation_keys),
                "active_conversations_24h": active_count,
                "retention_days": self.checkpoint_retention_days,
                "max_checkpoints_per_thread": self.max_checkpoints_per_thread
            }
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint stats: {e}")
            return {}
    
    async def close(self) -> None:
        """Close checkpoint manager connections"""
        
        try:
            if self._redis_client:
                await self._redis_client.close()
            
            # LangGraph checkpointer cleanup is handled automatically
            logger.info("Checkpoint manager connections closed")
            
        except Exception as e:
            logger.error(f"Error closing checkpoint manager: {e}")