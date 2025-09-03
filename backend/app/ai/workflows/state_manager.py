"""
Conversation State Manager

Manages conversation state and memory across multiple agents and sessions.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.asyncio import Redis

from ..config import AIConfig

logger = logging.getLogger(__name__)

class ConversationStateManager:
    """Manages conversation state across agents and sessions"""
    
    def __init__(self, config: AIConfig, redis_client: Optional[Redis] = None):
        self.config = config
        self.redis_client = redis_client or redis.from_url(config.redis_url)
        self.state_ttl = 3600  # 1 hour
        
    async def save_conversation_state(
        self,
        conversation_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """Save conversation state"""
        
        try:
            state_key = f"{self.config.redis_key_prefix}conversation:{conversation_id}"
            state_data = {
                **state,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.setex(
                state_key,
                self.state_ttl,
                json.dumps(state_data)
            )
            return True
            
        except Exception as e:
            logger.error(f"State save failed: {e}")
            return False
    
    async def load_conversation_state(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load conversation state"""
        
        try:
            state_key = f"{self.config.redis_key_prefix}conversation:{conversation_id}"
            state_data = await self.redis_client.get(state_key)
            
            if state_data:
                return json.loads(state_data)
            return None
            
        except Exception as e:
            logger.error(f"State load failed: {e}")
            return None