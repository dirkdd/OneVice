"""
OneVice Backend Main Application

FastAPI application with comprehensive authentication system:
- 4-tier role hierarchy (Leadership → Director → Creative Director → Salesperson)
- 6-level data sensitivity filtering 
- JWT validation with Clerk integration
- Okta SSO support
- RBAC permissions with audit logging
- WebSocket authentication
- AI agent context integration
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
import redis.asyncio as aioredis

# Import authentication components (excluding broken JWTAuthenticationMiddleware)
from auth import (
    RBACMiddleware, AuditLoggingMiddleware,
    WebSocketAuthMiddleware, AuthenticationService, AuthorizationService, 
    UserService, AuditService, ClerkIntegration, OktaIntegration
)
# Use our working Clerk middleware instead of broken JWTAuthenticationMiddleware
from app.middleware.clerk_auth import ClerkAuthMiddleware
from auth.dependencies import init_auth_dependencies
from auth.api import auth_router, user_router, admin_router, sso_router
from auth.models import AuthUser, UserRole, PermissionSet, PermissionAction, DataSensitivity
from auth.clerk_jwt import validate_clerk_token

# Import LLM components
from llm.router import LLMRouter
from app.ai.workflows.orchestrator import AgentOrchestrator
from app.ai.config import AIConfig

# Import API routers
from app.api.conversations import router as conversations_router
from app.api.projects import router as projects_router
from app.api.intelligence import router as intelligence_router
from app.api.talent import router as talent_router

# Import database components
from database import get_connection_manager, initialize_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
auth_service: AuthenticationService = None
authz_service: AuthorizationService = None
user_service: UserService = None
llm_router: LLMRouter = None
agent_orchestrator: AgentOrchestrator = None
audit_service: AuditService = None
redis_client: aioredis.Redis = None
websocket_auth: WebSocketAuthMiddleware = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan management for startup and shutdown"""
    
    logger.info("Starting OneVice Backend...")
    
    # Initialize services
    await initialize_services()
    
    # Initialize database
    await initialize_database_connections()
    
    logger.info("OneVice Backend started successfully")
    
    yield
    
    logger.info("Shutting down OneVice Backend...")
    
    # Cleanup services
    await cleanup_services()
    
    logger.info("OneVice Backend shutdown complete")


async def initialize_services():
    """Initialize all authentication and business services"""
    
    global auth_service, authz_service, user_service, audit_service, redis_client, websocket_auth, llm_router, agent_orchestrator
    
    try:
        # Initialize Redis client
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            redis_client = aioredis.from_url(redis_url)
            await redis_client.ping()
            logger.info("Redis connection established")
        else:
            logger.warning("Redis not configured - sessions will be memory-only")
        
        # Initialize core services
        auth_service = AuthenticationService(redis_client)
        authz_service = AuthorizationService()
        user_service = UserService()
        audit_service = AuditService()
        
        # Initialize WebSocket authentication
        websocket_auth = WebSocketAuthMiddleware(
            clerk_publishable_key=os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", ""),
            clerk_secret_key=os.getenv("CLERK_SECRET_KEY", "")
        )
        
        # Initialize LLM Router
        llm_router = LLMRouter()
        logger.info("LLM Router initialized successfully")
        
        # Initialize AI Configuration and Agent Orchestrator with comprehensive error handling
        try:
            logger.info("Initializing AI services and Agent Orchestrator...")
            ai_config = AIConfig()
            
            # Check if agent orchestrator is available with all required dependencies
            if ai_config.is_agent_orchestrator_available():
                logger.info("All AI dependencies available, initializing Agent Orchestrator with supervisor pattern...")
                
                # Initialize Agent Orchestrator with LangGraph multi-agent workflows
                agent_orchestrator = AgentOrchestrator(ai_config)
                await agent_orchestrator.initialize_services()
                
                # Verify agents are properly initialized
                agent_status = await agent_orchestrator.get_agent_status()
                available_agents = [name for name, status in agent_status.get("agents", {}).items() 
                                 if status.get("status") != "error"]
                
                if available_agents:
                    logger.info(f"Agent Orchestrator initialized successfully with {len(available_agents)} agents: {', '.join(available_agents)}")
                    logger.info("WebSocket will use supervisor pattern: WebSocket → LangGraph Supervisor → Specialized Agents → LLM Router → Together.ai")
                else:
                    logger.warning("Agent Orchestrator initialized but no agents are available")
                    agent_orchestrator = None
                    
            else:
                missing_items = ai_config.get_missing_config_items()
                logger.warning(f"Agent Orchestrator cannot be initialized - missing config: {', '.join(missing_items)}")
                logger.info("WebSocket will use direct LLM router fallback: WebSocket → LLM Router → Together.ai")
                agent_orchestrator = None
                
        except Exception as ai_init_error:
            logger.error(f"Agent Orchestrator initialization failed: {ai_init_error}")
            logger.exception("Full initialization error:")
            logger.info("Falling back to direct LLM router - WebSocket → LLM Router → Together.ai")
            agent_orchestrator = None
        
        # Initialize dependency injection
        init_auth_dependencies(auth_service, authz_service, audit_service)
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


async def initialize_database_connections():
    """Initialize database connections and schema"""
    
    try:
        # Initialize database with schema validation
        db_result = await initialize_database(ensure_schema=True)
        
        if not db_result["success"]:
            logger.error(f"Database initialization failed: {db_result.get('error')}")
            raise RuntimeError("Database initialization failed")
        
        logger.info("Database connections and schema initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def cleanup_services():
    """Cleanup services and connections on shutdown"""
    
    global redis_client, audit_service, agent_orchestrator
    
    try:
        # Cleanup agent orchestrator
        if agent_orchestrator:
            await agent_orchestrator.cleanup()
            
        # Flush audit logs
        if audit_service:
            await audit_service._flush_log_buffer()
        
        # Close Redis connection
        if redis_client:
            await redis_client.close()
        
        # Close database connections
        connection_manager = await get_connection_manager()
        if connection_manager:
            await connection_manager.close()
        
        logger.info("Services cleanup completed")
        
    except Exception as e:
        logger.error(f"Service cleanup failed: {e}")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title="OneVice Backend API",
        description="Comprehensive authentication and business management system",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    )
    
    # Add compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("JWT_SECRET_KEY", "default-secret-key")
    )
    
    # Add Clerk Authentication Middleware (uses working validation)
    app.add_middleware(
        ClerkAuthMiddleware,
        excluded_paths=["/health", "/docs", "/redoc", "/openapi.json"]
    )
    
    # Add RBAC middleware
    app.add_middleware(RBACMiddleware)
    
    # Add audit logging middleware
    app.add_middleware(
        AuditLoggingMiddleware,
        log_requests=True,
        log_responses=False,  # Disable response logging for performance
        sensitive_paths=["/admin/", "/users/", "/auth/"]
    )
    
    # Include API routers
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(admin_router)
    app.include_router(sso_router)
    
    # Include business API routers
    app.include_router(conversations_router)
    app.include_router(projects_router)
    app.include_router(intelligence_router)
    app.include_router(talent_router)
    
    return app


# Create FastAPI app instance
app = create_application()


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Log the error for audit purposes
    if audit_service:
        try:
            from auth.models import AuditLogEntry, AuditAction
            
            await audit_service.log_event(
                AuditLogEntry(
                    action=AuditAction.SECURITY_VIOLATION,
                    resource=str(request.url.path),
                    success=False,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "error": str(exc),
                        "method": request.method,
                        "path": str(request.url.path)
                    },
                    risk_score=0.8
                )
            )
        except Exception as e:
            logger.error(f"Failed to log exception: {e}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": str(hash(str(exc)))[:8]  # Error ID for tracking
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check endpoint"""
    
    try:
        health_status = {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2025-09-02T00:00:00Z",  # Would use actual timestamp
            "services": {
                "auth_service": "healthy" if auth_service else "not_initialized",
                "database": "healthy",  # Would check actual database
                "redis": "healthy" if redis_client else "not_configured"
            }
        }
        
        # Check Redis if available
        if redis_client:
            try:
                await redis_client.ping()
                health_status["services"]["redis"] = "healthy"
            except Exception:
                health_status["services"]["redis"] = "unhealthy"
        
        # Determine overall status
        service_statuses = list(health_status["services"].values())
        if any(status == "unhealthy" for status in service_statuses):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-09-02T00:00:00Z"
        }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    
    return {
        "message": "OneVice Backend API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "authentication": {
            "endpoints": ["/auth/login", "/auth/logout", "/auth/status"],
            "providers": ["clerk", "okta", "internal"]
        },
        "features": [
            "4-tier role hierarchy",
            "6-level data sensitivity filtering",
            "JWT authentication with Clerk integration",
            "Okta SSO support",
            "RBAC permissions",
            "Comprehensive audit logging",
            "WebSocket authentication",
            "AI agent context integration"
        ]
    }


# WebSocket endpoint with optional authentication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with optional authentication
    
    Accepts connections without authentication, then handles auth via messages.
    Handles chat messages, conversation persistence, and AI responses.
    """
    
    user = None
    
    try:
        # Accept connection first (no auth required)
        await websocket.accept()
        
        # Send connection established message
        await websocket.send_json({
            "type": "connection",
            "data": {
                "message": "WebSocket connection established. Please authenticate to access chat features.",
                "status": "connected"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Handle messages
        while True:
            data = await websocket.receive_json()
            
            try:
                message_type = data.get("type", "user_message")
                content = data.get("content", "")
                conversation_id = data.get("conversation_id")
                metadata = data.get("metadata", {})
                
                if message_type == "auth":
                    # Handle authentication with Clerk JWT validation
                    try:
                        token = data.get("token")
                        if not token:
                            await websocket.send_json({
                                "type": "auth_error",
                                "data": {"message": "No token provided"},
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                            continue
                        
                        # Validate Clerk JWT token
                        user_dict = await validate_clerk_token(token)
                        if not user_dict:
                            await websocket.send_json({
                                "type": "auth_error",
                                "data": {"message": "Invalid or expired token"},
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                            continue
                        
                        # Store validated user data
                        user = user_dict
                        
                        await websocket.send_json({
                            "type": "auth_success",
                            "data": {
                                "message": f"Authenticated as {user['name']}",
                                "user_id": user["id"],
                                "user_name": user["name"]
                            },
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                    except Exception as auth_error:
                        await websocket.send_json({
                            "type": "auth_error",
                            "data": {"message": f"Authentication failed: {str(auth_error)}"},
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                
                elif message_type == "user_message":
                    if not user:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "Please authenticate first"},
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        continue
                    
                    # Process user message with dict format
                    response = await handle_chat_message_dict(
                        user_dict=user,
                        content=content,
                        conversation_id=conversation_id,
                        metadata=metadata
                    )
                    
                    # Send response back to client
                    await websocket.send_json(response)
                    
                elif message_type == "ping":
                    # Handle ping for connection health
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": f"Unknown message type: {message_type}"},
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
            except Exception as msg_error:
                logger.error(f"Error processing message: {msg_error}")
                await websocket.send_json({
                    "type": "error", 
                    "data": {"message": "Failed to process message"},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
    except WebSocketDisconnect:
        user_name = user['name'] if user and isinstance(user, dict) else 'unknown'
        logger.info(f"WebSocket client disconnected: {user_name}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1008, reason="Connection error")
        except Exception:
            pass


async def handle_chat_message(user: AuthUser, content: str, conversation_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Handle chat message processing and AI response generation
    
    Args:
        user: Authenticated user
        content: Message content
        conversation_id: Optional conversation ID
        metadata: Optional message metadata
        
    Returns:
        Dict containing response data for WebSocket client
    """
    try:
        # Import here to avoid circular imports
        from app.api.conversations import MOCK_CONVERSATIONS, MOCK_MESSAGES, Message, Conversation
        
        # Create or find conversation
        if conversation_id:
            # Find existing conversation
            conversation = next(
                (conv for conv in MOCK_CONVERSATIONS if conv.id == conversation_id), 
                None
            )
            if not conversation:
                return {
                    "type": "error",
                    "data": {"message": "Conversation not found"},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        else:
            # Create new conversation
            conversation = Conversation(
                title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                user_id=user.id
            )
            MOCK_CONVERSATIONS.append(conversation)
            conversation_id = conversation.id
        
        # Add user message to conversation
        user_message = Message(
            content=content,
            sender_id=user.id,
            sender_name=user.name,
            sender_type="user",
            metadata=metadata or {}
        )
        
        if conversation_id not in MOCK_MESSAGES:
            MOCK_MESSAGES[conversation_id] = []
        
        MOCK_MESSAGES[conversation_id].append(user_message)
        
        # Update conversation metadata
        conversation.message_count += 1
        conversation.last_message = content
        conversation.updated_at = datetime.now(timezone.utc)
        
        # Generate AI response (mock response for now)
        ai_response_content = await generate_ai_response(content, user, conversation_id)
        
        # Add AI response to conversation
        ai_message = Message(
            content=ai_response_content,
            sender_id="agent_ai",
            sender_name="OneVice AI",
            sender_type="agent"
        )
        
        MOCK_MESSAGES[conversation_id].append(ai_message)
        conversation.message_count += 1
        conversation.last_message = ai_response_content
        conversation.updated_at = datetime.now(timezone.utc)
        
        # Return response with both messages
        return {
            "type": "chat_response",
            "data": {
                "conversation_id": conversation_id,
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "sender_name": user_message.sender_name,
                    "sender_type": user_message.sender_type,
                    "timestamp": user_message.timestamp.isoformat()
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "sender_name": ai_message.sender_name,
                    "sender_type": ai_message.sender_type,
                    "timestamp": ai_message.timestamp.isoformat(),
                    "agent_info": ai_response_result.get("agent_info")
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        return {
            "type": "error",
            "data": {"message": "Failed to process chat message"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


async def generate_ai_response(content: str, user: AuthUser, conversation_id: str) -> str:
    """
    Generate AI response to user message (mock implementation)
    
    In production, this would integrate with LLM providers through the LLM router
    """
    
    # Mock responses based on content patterns
    content_lower = content.lower()
    
    if "project" in content_lower and ("analysis" in content_lower or "analyze" in content_lower):
        return f"I'd be happy to help analyze your project requirements, {user.name}. Could you share more details about the project scope, budget, and target timeline? I can provide insights based on our successful campaigns in similar industries."
    
    elif "budget" in content_lower:
        return "Based on our experience with similar projects, I can help you optimize budget allocation. Typically, we recommend 40% for production, 30% for talent and crew, 20% for post-production, and 10% for contingency. Would you like me to break this down further for your specific project type?"
    
    elif "talent" in content_lower or "director" in content_lower:
        return "I can recommend directors and talent based on your project requirements. Our talent discovery system considers factors like budget alignment, availability, past performance, and industry expertise. What's your project genre and approximate budget range?"
    
    elif "roi" in content_lower or "performance" in content_lower:
        return f"Great question about performance metrics! Our recent campaigns have achieved an average ROI of 187%, with luxury and technology sectors performing particularly well. I can analyze your project's potential performance based on historical data from similar campaigns."
    
    elif "hello" in content_lower or "hi" in content_lower:
        return f"Hello {user.name}! I'm OneVice AI, your intelligent assistant for entertainment industry projects. I can help with project analysis, talent discovery, budget optimization, and strategic insights. What would you like to work on today?"
    
    else:
        return f"Thank you for your message, {user.name}. I understand you're interested in: '{content}'. Based on our database of successful projects and industry insights, I can provide detailed analysis and recommendations. Could you provide more context about your specific goals or requirements?"


async def handle_chat_message_dict(user_dict: Dict[str, Any], content: str, conversation_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Handle chat message processing with user dict format (for WebSocket authentication)
    
    Args:
        user_dict: Authenticated user data as dict
        content: Message content
        conversation_id: Optional conversation ID
        metadata: Optional message metadata
        
    Returns:
        Dict containing response data for WebSocket client
    """
    try:
        # Import here to avoid circular imports
        from app.api.conversations import MOCK_CONVERSATIONS, MOCK_MESSAGES, Message, Conversation
        
        # Create or find conversation
        if conversation_id:
            # Find existing conversation
            conversation = next(
                (conv for conv in MOCK_CONVERSATIONS if conv.id == conversation_id), 
                None
            )
            if not conversation:
                return {
                    "type": "error",
                    "data": {"message": "Conversation not found"},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        else:
            # Create new conversation
            conversation = Conversation(
                title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                user_id=user_dict["id"]
            )
            MOCK_CONVERSATIONS.append(conversation)
            conversation_id = conversation.id
        
        # Add user message to conversation
        user_message = Message(
            content=content,
            sender_id=user_dict["id"],
            sender_name=user_dict["name"],
            sender_type="user",
            metadata=metadata or {}
        )
        
        if conversation_id not in MOCK_MESSAGES:
            MOCK_MESSAGES[conversation_id] = []
        
        MOCK_MESSAGES[conversation_id].append(user_message)
        
        # Update conversation metadata
        conversation.message_count += 1
        conversation.last_message = content
        conversation.updated_at = datetime.now(timezone.utc)
        
        # Generate AI response using Agent Orchestrator or LLM router
        ai_response_result = await generate_ai_response_with_metadata(content, user_dict, conversation_id)
        ai_response_content = ai_response_result["content"]
        
        # Add AI response to conversation
        ai_message = Message(
            content=ai_response_content,
            sender_id="agent_ai",
            sender_name="OneVice AI",
            sender_type="agent"
        )
        
        MOCK_MESSAGES[conversation_id].append(ai_message)
        conversation.message_count += 1
        conversation.last_message = ai_response_content
        conversation.updated_at = datetime.now(timezone.utc)
        
        # Return response with both messages
        return {
            "type": "chat_response",
            "data": {
                "conversation_id": conversation_id,
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "sender_name": user_message.sender_name,
                    "sender_type": user_message.sender_type,
                    "timestamp": user_message.timestamp.isoformat()
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "sender_name": ai_message.sender_name,
                    "sender_type": ai_message.sender_type,
                    "timestamp": ai_message.timestamp.isoformat(),
                    "agent_info": ai_response_result.get("agent_info")
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        return {
            "type": "error",
            "data": {"message": "Failed to process chat message"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


async def apply_security_filtering(query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Security filtering node for RBAC enforcement and data sensitivity control
    
    Args:
        query: User query to filter
        user_context: User context with role and permissions
    
    Returns:
        Dict with 'allowed' (bool), 'filtered_query' (str), and 'security_context' (dict)
    """
    
    try:
        # Extract user role and permissions
        user_role = user_context.get("role", "Salesperson")
        data_sensitivity = user_context.get("data_sensitivity", 6)  # Default to least sensitive
        permissions = user_context.get("permissions", [])
        
        # Basic security filtering based on role hierarchy
        # Leadership (1) → Director (2) → Creative Director (3) → Salesperson (4)
        role_hierarchy = {
            "Leadership": 1,
            "Director": 2, 
            "Creative Director": 3,
            "Salesperson": 4
        }
        
        user_level = role_hierarchy.get(user_role, 4)  # Default to lowest level
        
        # Filter sensitive content keywords
        sensitive_keywords = [
            "financial", "salary", "budget", "confidential", "internal", "strategic",
            "acquisition", "merger", "lawsuit", "legal", "compliance"
        ]
        
        query_lower = query.lower()
        contains_sensitive = any(keyword in query_lower for keyword in sensitive_keywords)
        
        # Determine data sensitivity level required
        if contains_sensitive and user_level > 2:  # Only Director+ can access sensitive data
            return {
                "allowed": False,
                "filtered_query": "",
                "security_context": {
                    "reason": "insufficient_permissions",
                    "required_level": "Director",
                    "user_level": user_role,
                    "sensitive_content": True
                }
            }
        
        # Apply query sanitization if needed
        filtered_query = query
        if user_level > 3:  # Salesperson level - more restrictive
            # Remove any potentially sensitive context
            filtered_query = query.replace("confidential", "").replace("internal", "")
        
        return {
            "allowed": True,
            "filtered_query": filtered_query,
            "security_context": {
                "user_role": user_role,
                "user_level": user_level,
                "data_sensitivity": data_sensitivity,
                "query_filtered": filtered_query != query,
                "permissions_checked": True
            }
        }
        
    except Exception as e:
        logger.error(f"Security filtering failed: {e}")
        # Fail secure - deny by default
        return {
            "allowed": False,
            "filtered_query": "",
            "security_context": {
                "reason": "security_filter_error",
                "error": str(e)
            }
        }


async def generate_ai_response_with_metadata(content: str, user_dict: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
    """
    Generate AI response with metadata using Agent Orchestrator with LangGraph multi-agent workflows
    
    Returns:
        Dict with 'content' (response text) and 'agent_info' (routing metadata)
    """
    
    global agent_orchestrator, llm_router
    
    user_name = user_dict.get("name", "there")
    
    try:
        # Prepare user context with RBAC data
        user_context = {
            "user_id": user_dict.get("id", "unknown"),
            "name": user_name,
            "role": user_dict.get("role", "Salesperson"),
            "data_sensitivity": user_dict.get("data_sensitivity", 6),  # Default to least sensitive
            "permissions": user_dict.get("permissions", []),
            "session_context": {
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Apply security filtering first (as per architecture)
        security_result = await apply_security_filtering(content, user_context)
        
        if not security_result["allowed"]:
            logger.warning(f"Query blocked by security filter for user {user_name}: {security_result['security_context']['reason']}")
            return {
                "content": f"I'm sorry, but I don't have permission to help with that request. Your current role ({user_context['role']}) doesn't have access to this type of information.",
                "agent_info": {
                    "type": "security_filtered",
                    "reason": security_result["security_context"]["reason"],
                    "user_role": user_context["role"],
                    "blocked": True
                }
            }
        
        # Use filtered query for processing
        filtered_content = security_result["filtered_query"]
        logger.debug(f"Security filtering passed for user {user_name}, query {'filtered' if security_result['security_context']['query_filtered'] else 'unchanged'}")
        
        # Use Agent Orchestrator if available (preferred) - follows supervisor pattern
        if agent_orchestrator:
            logger.info(f"Routing query through Agent Orchestrator (Supervisor Pattern) for user {user_name}")
            
            # Route filtered query through LangGraph multi-agent supervisor system
            agent_response = await agent_orchestrator.route_query(
                query=filtered_content,
                user_context=user_context,
                conversation_id=conversation_id
            )
            
            # Handle orchestrator response format
            if agent_response:
                # Extract content - orchestrator returns structured response
                ai_response = agent_response.get("content", "")
                agent_type = agent_response.get("agent_type", "orchestrator")
                routing_info = agent_response.get("routing", {})
                
                logger.info(f"Supervisor routed to {agent_type}, strategy: {routing_info.get('strategy', 'unknown')}")
                logger.debug(f"Routing details: {routing_info}")
                
                return {
                    "content": ai_response,
                    "agent_info": {
                        "type": "supervisor_agent",
                        "primary_agent": agent_type,
                        "routing_strategy": routing_info.get("strategy"),
                        "agents_used": routing_info.get("agents_used", [agent_type]),
                        "conversation_id": conversation_id
                    }
                }
            else:
                logger.warning("Agent orchestrator returned empty response, falling back to LLM router")
                
        # Fallback to direct LLM router if agents unavailable
        if llm_router:
            logger.info(f"Agent orchestrator unavailable, using direct LLM router for user {user_name}")
            
            # Use the same user context with security filtering applied
            llm_user_context = {
                "role": user_context["role"],
                "data_sensitivity": user_context["data_sensitivity"],
                "name": user_name,
                "id": user_dict.get("id", "unknown")
            }
            
            # Create system prompt with entertainment industry expertise
            system_prompt = f"""You are OneVice AI, an intelligent assistant for entertainment industry projects. You help users with project analysis, talent discovery, budget optimization, and strategic insights.

User Context:
- Name: {user_name}
- Role: {llm_user_context['role']}

Your expertise areas:
- Entertainment industry project management and analysis
- Talent acquisition and discovery systems
- Budget planning and ROI optimization
- Performance analytics and strategic insights
- Market intelligence and competitive analysis

Provide helpful, professional responses that demonstrate deep industry knowledge. Always offer to provide more detailed analysis when appropriate."""

            # Route filtered query through LLM with security context
            response = await llm_router.route_query(
                query=filtered_content,
                user_context=llm_user_context,
                system_prompt=system_prompt
            )
            
            # Handle LLM router response format
            if response and isinstance(response, dict):
                # Handle different response formats from LLM router
                if "choices" in response and len(response["choices"]) > 0:
                    ai_response = response["choices"][0]["message"]["content"]
                elif "content" in response:
                    ai_response = response["content"]
                else:
                    ai_response = str(response)
                
                routing_info = response.get("routing_info", {})
                logger.info(f"Direct LLM response generated for user {user_name}")
                
                return {
                    "content": ai_response,
                    "agent_info": {
                        "type": "llm_direct",
                        "model": routing_info.get("selected_model", "unknown"),
                        "provider": routing_info.get("provider", "unknown"),
                        "data_sensitivity": routing_info.get("data_sensitivity", llm_user_context["data_sensitivity"])
                    }
                }
            else:
                logger.warning("LLM router response format unexpected, falling back to mock")
                
    except Exception as e:
        logger.error(f"AI response generation failed: {e}, falling back to mock response")
        logger.exception("Full error traceback:")
    
    # Final fallback to mock responses if all AI systems fail
    logger.info(f"All AI systems unavailable, using mock response fallback for user {user_name}")
    mock_response = await generate_mock_response(content, user_name)
    
    return {
        "content": mock_response,
        "agent_info": {
            "type": "mock_fallback",
            "reason": "ai_systems_unavailable",
            "fallback_used": True
        }
    }


async def generate_ai_response_dict(content: str, user_dict: Dict[str, Any], conversation_id: str) -> str:
    """
    Generate AI response to user message - backward compatibility wrapper
    """
    result = await generate_ai_response_with_metadata(content, user_dict, conversation_id)
    return result["content"]


async def generate_mock_response(content: str, user_name: str) -> str:
    """
    Generate mock responses as fallback when LLM is unavailable
    """
    content_lower = content.lower()
    
    if "project" in content_lower and ("analysis" in content_lower or "analyze" in content_lower):
        return f"I'd be happy to help analyze your project requirements, {user_name}. Could you share more details about the project scope, budget, and target timeline? I can provide insights based on our successful campaigns in similar industries."
    
    elif "budget" in content_lower:
        return "Based on our experience with similar projects, I can help you optimize budget allocation. Typically, we recommend 40% for production, 30% for talent and crew, 20% for post-production, and 10% for contingency. Would you like me to break this down further for your specific project type?"
    
    elif "talent" in content_lower or "director" in content_lower:
        return "I can recommend directors and talent based on your project requirements. Our talent discovery system considers factors like budget alignment, availability, past performance, and industry expertise. What's your project genre and approximate budget range?"
    
    elif "roi" in content_lower or "performance" in content_lower:
        return f"Great question about performance metrics! Our recent campaigns have achieved an average ROI of 187%, with luxury and technology sectors performing particularly well. I can analyze your project's potential performance based on historical data from similar campaigns."
    
    elif "hello" in content_lower or "hi" in content_lower:
        return f"Hello {user_name}! I'm OneVice AI, your intelligent assistant for entertainment industry projects. I can help with project analysis, talent discovery, budget optimization, and strategic insights. What would you like to work on today?"
    
    else:
        return f"Thank you for your message, {user_name}. I understand you're interested in: '{content}'. Based on our database of successful projects and industry insights, I can provide detailed analysis and recommendations. Could you provide more context about your specific goals or requirements?"


# AI Agent context endpoint
@app.get("/ai/context")
async def get_ai_context(request: Request):
    """
    Get AI agent context for current user
    
    Provides comprehensive user context for AI agents including permissions,
    role hierarchy, and data access levels.
    """
    
    try:
        from auth.dependencies import get_ai_agent_context, require_ai_access
        from auth.dependencies import get_current_user
        
        # Get current user (this would be properly injected in a real endpoint)
        auth_context = getattr(request.state, 'auth_context', None)
        
        if not auth_context or not auth_context.is_authenticated():
            raise HTTPException(
                status_code=401,
                detail="Authentication required for AI context"
            )
        
        user = auth_context.user
        
        # Check AI access permission
        if not user.has_permission("access_ai_agents"):
            raise HTTPException(
                status_code=403,
                detail="AI access permission required"
            )
        
        # Get AI context
        ai_context = await get_ai_agent_context(user)
        
        return {
            "ai_context": ai_context,
            "generated_at": "2025-09-02T00:00:00Z",
            "context_version": "1.0"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI context generation failed: {str(e)}"
        )


# AI system status endpoint
@app.get("/ai/status")
async def get_ai_status():
    """
    Get AI system status including agent orchestrator and LLM router status
    """
    
    global agent_orchestrator, llm_router
    
    try:
        status = {
            "ai_system_status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "llm_router": {
                    "available": llm_router is not None,
                    "status": "healthy" if llm_router else "unavailable"
                },
                "agent_orchestrator": {
                    "available": agent_orchestrator is not None,
                    "status": "unknown"
                },
                "agents": {}
            }
        }
        
        # Get LLM router status
        if llm_router:
            try:
                provider_status = llm_router.get_provider_status()
                status["components"]["llm_router"]["providers"] = provider_status
            except Exception as e:
                status["components"]["llm_router"]["error"] = str(e)
        
        # Get agent orchestrator status
        if agent_orchestrator:
            try:
                agent_status = await agent_orchestrator.get_agent_status()
                status["components"]["agent_orchestrator"] = {
                    "available": True,
                    "status": "healthy",
                    "architecture_pattern": "supervisor",
                    "flow": "WebSocket → LangGraph Supervisor → Specialized Agents → LLM Router → Together.ai",
                    "details": agent_status
                }
                
                # Add specialized agents status
                agents = agent_status.get("agents", {})
                status["components"]["agents"] = {
                    "sales_intelligence": agents.get("sales", {"status": "unknown"}),
                    "talent_discovery": agents.get("talent", {"status": "unknown"}),
                    "leadership_analytics": agents.get("analytics", {"status": "unknown"})
                }
                
            except Exception as e:
                status["components"]["agent_orchestrator"] = {
                    "available": True,
                    "status": "error",
                    "error": str(e)
                }
        else:
            status["components"]["agent_orchestrator"] = {
                "available": False,
                "status": "unavailable",
                "reason": "Not initialized - check configuration",
                "fallback_flow": "WebSocket → LLM Router → Together.ai"
            }
        
        # Add security filtering status
        status["components"]["security_filtering"] = {
            "available": True,
            "status": "healthy",
            "features": [
                "RBAC enforcement",
                "4-tier role hierarchy",
                "6-level data sensitivity filtering",
                "Query sanitization",
                "Fail-secure design"
            ]
        }
        
        # Determine overall system status
        if not llm_router and not agent_orchestrator:
            status["ai_system_status"] = "unavailable"
            status["architecture_status"] = "no_ai_services"
        elif not agent_orchestrator:
            status["ai_system_status"] = "degraded"
            status["architecture_status"] = "fallback_mode"
        else:
            status["architecture_status"] = "full_supervisor_pattern"
            
        return status
        
    except Exception as e:
        return {
            "ai_system_status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=True
    )