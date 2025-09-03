"""
OneVice Conversations API

Handles conversation management, message history, and chat functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

# Import auth dependencies
from auth.dependencies import get_current_user
from auth.models import AuthUser

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

# Models for conversation data
class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    sender_id: str
    sender_name: str
    sender_type: str = Field(default="user")  # "user" or "agent"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0
    last_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationWithMessages(Conversation):
    messages: List[Message] = Field(default_factory=list)

class CreateConversationRequest(BaseModel):
    title: str
    initial_message: Optional[str] = None

class AddMessageRequest(BaseModel):
    content: str
    sender_type: str = "user"

# Mock data for development
MOCK_CONVERSATIONS = [
    Conversation(
        id="conv_1",
        title="Project Analysis Discussion",
        user_id="user_123",
        created_at=datetime(2025, 1, 15, 10, 30, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 15, 14, 45, tzinfo=timezone.utc),
        message_count=12,
        last_message="Thanks for the detailed analysis on the client requirements.",
        metadata={"project_id": "proj_456", "priority": "high"}
    ),
    Conversation(
        id="conv_2", 
        title="Talent Discovery Strategy",
        user_id="user_123",
        created_at=datetime(2025, 1, 14, 9, 15, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 14, 16, 20, tzinfo=timezone.utc),
        message_count=8,
        last_message="The recommended directors match our budget constraints perfectly.",
        metadata={"department": "creative", "budget_range": "50k-100k"}
    ),
    Conversation(
        id="conv_3",
        title="Case Study Review",
        user_id="user_123", 
        created_at=datetime(2025, 1, 13, 11, 45, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 13, 15, 30, tzinfo=timezone.utc),
        message_count=15,
        last_message="The ROI calculations look accurate. Let's proceed with this approach.",
        metadata={"case_study_id": "cs_789", "status": "approved"}
    )
]

MOCK_MESSAGES = {
    "conv_1": [
        Message(
            id="msg_1",
            content="I need help analyzing the requirements for the upcoming commercial project.",
            sender_id="user_123",
            sender_name="Admin User",
            sender_type="user",
            timestamp=datetime(2025, 1, 15, 10, 30, tzinfo=timezone.utc)
        ),
        Message(
            id="msg_2", 
            content="I'd be happy to help analyze the project requirements. Could you share the project brief and any specific areas you'd like me to focus on?",
            sender_id="agent_ai",
            sender_name="OneVice AI",
            sender_type="agent",
            timestamp=datetime(2025, 1, 15, 10, 32, tzinfo=timezone.utc)
        ),
        Message(
            id="msg_3",
            content="The client is looking for a 60-second commercial with a focus on luxury aesthetics. Budget is around $150k.",
            sender_id="user_123", 
            sender_name="Admin User",
            sender_type="user",
            timestamp=datetime(2025, 1, 15, 10, 35, tzinfo=timezone.utc)
        ),
        Message(
            id="msg_4",
            content="Based on the luxury aesthetic requirement and $150k budget, I recommend focusing on high-end production values. Here are some key considerations:\n\n• Location: Premium venues or studio setups\n• Talent: Experienced actors with strong screen presence\n• Equipment: High-end cameras and lighting for that luxury look\n• Post-production: Color grading and sound design budget\n\nWould you like me to break down the budget allocation across these categories?",
            sender_id="agent_ai",
            sender_name="OneVice AI", 
            sender_type="agent",
            timestamp=datetime(2025, 1, 15, 10, 38, tzinfo=timezone.utc)
        )
    ]
}

@router.get("/recent", response_model=List[Conversation])
async def get_recent_conversations(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Get recent conversations for the current user"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Filter conversations by user and return most recent
        user_conversations = [
            conv for conv in MOCK_CONVERSATIONS 
            if conv.user_id == current_user.id or conv.user_id == "user_123"  # Mock data uses user_123
        ]
        
        # Sort by updated_at descending and limit results
        recent_conversations = sorted(
            user_conversations, 
            key=lambda x: x.updated_at, 
            reverse=True
        )[:limit]
        
        return recent_conversations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent conversations: {str(e)}"
        )

@router.post("", response_model=Conversation)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Create a new conversation"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        new_conversation = Conversation(
            title=request.title,
            user_id=current_user.id,
            message_count=1 if request.initial_message else 0,
            last_message=request.initial_message
        )
        
        # In a real implementation, save to database
        MOCK_CONVERSATIONS.append(new_conversation)
        
        # Add initial message if provided
        if request.initial_message:
            initial_msg = Message(
                content=request.initial_message,
                sender_id=current_user.id,
                sender_name=current_user.name,
                sender_type="user"
            )
            MOCK_MESSAGES[new_conversation.id] = [initial_msg]
        
        return new_conversation
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create conversation: {str(e)}"
        )

@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Get a specific conversation with messages"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Find the conversation
        conversation = next(
            (conv for conv in MOCK_CONVERSATIONS if conv.id == conversation_id), 
            None
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check if user has access to this conversation
        if conversation.user_id != current_user.id and conversation.user_id != "user_123":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get messages for this conversation
        messages = MOCK_MESSAGES.get(conversation_id, [])
        
        # Create conversation with messages
        conversation_with_messages = ConversationWithMessages(
            **conversation.dict(),
            messages=messages
        )
        
        return conversation_with_messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )

@router.post("/{conversation_id}/messages", response_model=Message)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Add a message to a conversation"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Find the conversation
        conversation = next(
            (conv for conv in MOCK_CONVERSATIONS if conv.id == conversation_id), 
            None
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check if user has access to this conversation
        if conversation.user_id != current_user.id and conversation.user_id != "user_123":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create new message
        new_message = Message(
            content=request.content,
            sender_id=current_user.id,
            sender_name=current_user.name,
            sender_type=request.sender_type
        )
        
        # Add message to conversation
        if conversation_id not in MOCK_MESSAGES:
            MOCK_MESSAGES[conversation_id] = []
        
        MOCK_MESSAGES[conversation_id].append(new_message)
        
        # Update conversation metadata
        conversation.message_count += 1
        conversation.last_message = request.content
        conversation.updated_at = datetime.now(timezone.utc)
        
        return new_message
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add message: {str(e)}"
        )

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Delete a conversation"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Find the conversation
        conversation_index = next(
            (i for i, conv in enumerate(MOCK_CONVERSATIONS) if conv.id == conversation_id), 
            None
        )
        
        if conversation_index is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = MOCK_CONVERSATIONS[conversation_index]
        
        # Check if user has access to this conversation
        if conversation.user_id != current_user.id and conversation.user_id != "user_123":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete conversation and messages
        del MOCK_CONVERSATIONS[conversation_index]
        if conversation_id in MOCK_MESSAGES:
            del MOCK_MESSAGES[conversation_id]
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )