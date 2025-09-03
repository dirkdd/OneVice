"""
Memory Type Definitions

Type definitions and schemas for the OneVice memory system,
including semantic, episodic, and procedural memory structures.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memories in the system"""
    SEMANTIC = "semantic"      # Facts, preferences, knowledge
    EPISODIC = "episodic"      # Specific interactions and events
    PROCEDURAL = "procedural"  # Behavioral patterns and optimizations


class MemoryImportance(str, Enum):
    """Memory importance levels for retention decisions"""
    CRITICAL = "critical"      # Core user preferences, key insights
    HIGH = "high"             # Important facts, significant events
    MEDIUM = "medium"         # Regular interactions, context
    LOW = "low"               # Casual mentions, temporary context


class UserMemory(BaseModel):
    """Base memory structure for user-related memories"""
    
    id: str = Field(..., description="Unique memory identifier")
    user_id: str = Field(..., description="Associated user ID")
    memory_type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(..., description="Memory content/description")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    importance: MemoryImportance = Field(MemoryImportance.MEDIUM, description="Memory importance")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access timestamp")
    access_count: int = Field(default=0, description="Number of times accessed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SemanticFact(UserMemory):
    """Semantic memory storing facts and knowledge"""
    
    memory_type: Literal[MemoryType.SEMANTIC] = Field(MemoryType.SEMANTIC)
    fact_type: str = Field(..., description="Type of fact (preference, skill, etc.)")
    confidence: float = Field(default=0.8, description="Confidence in fact accuracy", ge=0.0, le=1.0)
    source_conversation_id: Optional[str] = Field(None, description="Source conversation")
    related_entities: List[str] = Field(default_factory=list, description="Related entity IDs")


class EpisodicMemory(UserMemory):
    """Episodic memory storing specific interactions and events"""
    
    memory_type: Literal[MemoryType.EPISODIC] = Field(MemoryType.EPISODIC)
    conversation_id: str = Field(..., description="Associated conversation ID")
    agent_type: str = Field(..., description="Agent involved in interaction")
    interaction_summary: str = Field(..., description="Summary of interaction")
    outcome: Optional[str] = Field(None, description="Interaction outcome")
    emotion: Optional[str] = Field(None, description="Detected user emotion")
    topics: List[str] = Field(default_factory=list, description="Conversation topics")


class ProceduralMemory(UserMemory):
    """Procedural memory storing behavioral patterns and optimizations"""
    
    memory_type: Literal[MemoryType.PROCEDURAL] = Field(MemoryType.PROCEDURAL)
    pattern_type: str = Field(..., description="Type of pattern (preference, behavior, etc.)")
    trigger_condition: str = Field(..., description="Condition that triggers this pattern")
    action_taken: str = Field(..., description="Action or response pattern")
    success_rate: float = Field(default=0.0, description="Pattern success rate", ge=0.0, le=1.0)
    usage_count: int = Field(default=0, description="Number of times pattern was used")


class ConversationMemory(BaseModel):
    """Memory structure for conversation-level storage"""
    
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="Associated user ID")
    agent_types: List[str] = Field(default_factory=list, description="Agents involved")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Conversation start")
    end_time: Optional[datetime] = Field(None, description="Conversation end")
    message_count: int = Field(default=0, description="Number of messages")
    topics: List[str] = Field(default_factory=list, description="Main conversation topics")
    summary: Optional[str] = Field(None, description="Conversation summary")
    outcome: Optional[str] = Field(None, description="Conversation outcome")
    satisfaction: Optional[float] = Field(None, description="User satisfaction score", ge=0.0, le=1.0)
    extracted_facts: List[str] = Field(default_factory=list, description="IDs of extracted semantic facts")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemoryQuery(BaseModel):
    """Query structure for memory retrieval"""
    
    user_id: str = Field(..., description="User ID for memory query")
    query_text: str = Field(..., description="Query text for semantic search")
    memory_types: Optional[List[MemoryType]] = Field(None, description="Filter by memory types")
    min_importance: Optional[MemoryImportance] = Field(None, description="Minimum importance level")
    max_age_days: Optional[int] = Field(None, description="Maximum age in days")
    limit: int = Field(default=10, description="Maximum number of results", ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score", ge=0.0, le=1.0)
    include_metadata: bool = Field(default=False, description="Include memory metadata")


class MemorySearchResult(BaseModel):
    """Result structure for memory searches"""
    
    memory: UserMemory = Field(..., description="Retrieved memory")
    similarity_score: float = Field(..., description="Similarity score to query")
    relevance_explanation: Optional[str] = Field(None, description="Why this memory is relevant")
    related_memories: List[str] = Field(default_factory=list, description="IDs of related memories")


class MemoryStats(BaseModel):
    """Statistics about user's memory system"""
    
    user_id: str = Field(..., description="User ID")
    total_memories: int = Field(..., description="Total number of memories")
    memory_breakdown: Dict[MemoryType, int] = Field(..., description="Breakdown by memory type")
    importance_breakdown: Dict[MemoryImportance, int] = Field(..., description="Breakdown by importance")
    avg_access_frequency: float = Field(..., description="Average access frequency")
    oldest_memory_date: Optional[datetime] = Field(None, description="Date of oldest memory")
    most_recent_date: Optional[datetime] = Field(None, description="Date of most recent memory")
    top_topics: List[Dict[str, Any]] = Field(default_factory=list, description="Most common topics")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }