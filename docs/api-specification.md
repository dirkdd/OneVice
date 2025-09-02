# OneVice API Specification

**Version:** 1.0  
**Date:** September 1, 2025  
**Status:** Implementation Ready  
**OpenAPI Version:** 3.0.3

## 1. Overview

The OneVice API provides secure, role-based access to AI-powered business intelligence for the entertainment industry. The API supports both REST endpoints for standard operations and WebSocket connections for real-time AI agent streaming.

### 1.1 Base URLs

```
Development: https://onevice-backend-dev.onrender.com
Staging: https://onevice-backend-staging.onrender.com
Production: https://onevice-backend.onrender.com
Custom Domain: https://api.onevice.com (configured in Render)
WebSocket: wss://onevice-backend.onrender.com/ws
```

### 1.2 Authentication

All API endpoints require authentication via Clerk JWT tokens with Okta SSO integration.

```http
Authorization: Bearer <jwt_token>
```

### 1.3 Rate Limiting

- **Standard Users**: 100 requests per minute
- **Premium Users**: 500 requests per minute
- **Enterprise Users**: 2000 requests per minute

## 2. REST API Endpoints

### 2.1 Authentication Endpoints

#### POST /auth/login
Initiate login flow with Clerk authentication.

```json
{
  "endpoint": "/auth/login",
  "method": "POST",
  "description": "Initiate Clerk authentication flow",
  "request_body": {
    "email": "user@company.com",
    "redirect_url": "https://app.onevice.com/dashboard"
  },
  "response": {
    "status": 200,
    "body": {
      "auth_url": "https://clerk.onevice.com/auth/...",
      "session_id": "sess_2...",
      "expires_in": 3600
    }
  }
}
```

#### POST /auth/sso/okta
Handle Okta SSO authentication callback.

```json
{
  "endpoint": "/auth/sso/okta",
  "method": "POST",
  "description": "Process Okta SSO token exchange",
  "request_body": {
    "code": "oauth_code_from_okta",
    "state": "csrf_state_token"
  },
  "response": {
    "status": 200,
    "body": {
      "access_token": "jwt_token_here",
      "refresh_token": "refresh_token_here",
      "user": {
        "id": "user_2...",
        "email": "user@company.com",
        "role": "Leadership",
        "permissions": ["read:all", "write:projects"]
      }
    }
  }
}
```

#### POST /auth/refresh
Refresh JWT token using refresh token.

```json
{
  "endpoint": "/auth/refresh",
  "method": "POST",
  "request_body": {
    "refresh_token": "refresh_token_here"
  },
  "response": {
    "status": 200,
    "body": {
      "access_token": "new_jwt_token",
      "expires_in": 3600
    }
  }
}
```

### 2.2 User Management Endpoints

#### GET /users/profile
Get current user profile with role and permissions.

```json
{
  "endpoint": "/users/profile",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer <jwt_token>"
  },
  "response": {
    "status": 200,
    "body": {
      "id": "user_2...",
      "email": "user@company.com",
      "role": "Leadership",
      "permissions": ["read:all", "write:projects", "admin:users"],
      "data_sensitivity_level": 1,
      "created_at": "2025-01-01T00:00:00Z",
      "last_login": "2025-09-01T12:00:00Z",
      "preferences": {
        "theme": "dark",
        "notifications": true,
        "default_agent": "sales_intelligence"
      }
    }
  }
}
```

#### PUT /users/profile
Update user profile and preferences.

```json
{
  "endpoint": "/users/profile",
  "method": "PUT",
  "request_body": {
    "preferences": {
      "theme": "dark",
      "notifications": false,
      "default_agent": "case_study"
    }
  },
  "response": {
    "status": 200,
    "body": {
      "message": "Profile updated successfully",
      "updated_fields": ["preferences"]
    }
  }
}
```

### 2.3 AI Agent Query Endpoints

#### POST /agents/sales-intelligence/query
Query the Sales Intelligence Agent for contact and company research.

```json
{
  "endpoint": "/agents/sales-intelligence/query",
  "method": "POST",
  "description": "Research contacts, companies, and relationships",
  "request_body": {
    "query": "Research Cordae for upcoming music video pitch",
    "context": {
      "client_name": "Atlantic Records",
      "project_type": "Music Video",
      "budget_range": "$100k-300k"
    },
    "options": {
      "include_relationships": true,
      "depth": 2,
      "format": "detailed_brief"
    }
  },
  "response": {
    "status": 200,
    "body": {
      "query_id": "query_123456",
      "agent": "sales_intelligence",
      "result": {
        "summary": "Cordae is a Grammy-nominated rapper...",
        "entities": [
          {
            "name": "Cordae",
            "type": "Artist",
            "details": {
              "genre": "Hip-hop",
              "label": "Atlantic Records",
              "recent_projects": [...]
            }
          }
        ],
        "relationships": [...],
        "recommendations": [...]
      },
      "confidence_score": 0.92,
      "data_sources": ["neo4j", "industry_apis"],
      "processing_time_ms": 1847
    }
  }
}
```

#### POST /agents/case-study/query
Query the Case Study Agent for project matching and template generation.

```json
{
  "endpoint": "/agents/case-study/query",
  "method": "POST",
  "description": "Find similar projects and generate case studies",
  "request_body": {
    "query": "Find similar music video projects for hip-hop artists with $100k-300k budget",
    "filters": {
      "project_type": "Music Video",
      "genre": "Hip-hop",
      "budget_range": "$100k-300k",
      "year_range": "2020-2025"
    },
    "options": {
      "max_results": 10,
      "similarity_threshold": 0.8,
      "include_creative_concepts": true
    }
  },
  "response": {
    "status": 200,
    "body": {
      "query_id": "query_789012",
      "agent": "case_study",
      "matches": [
        {
          "project": {
            "id": "proj_456",
            "name": "Drake - God's Plan",
            "type": "Music Video",
            "budget_tier": "$100k-300k",
            "director": "Karena Evans",
            "creative_director": "Director X"
          },
          "similarity_score": 0.94,
          "matching_aspects": ["budget", "genre", "viral_potential"]
        }
      ],
      "case_study_template": {
        "format": "pitch_deck",
        "sections": [...],
        "assets": [...]
      }
    }
  }
}
```

#### POST /agents/talent-discovery/query
Query the Talent Discovery Agent for multi-faceted talent search.

```json
{
  "endpoint": "/agents/talent-discovery/query",
  "method": "POST",
  "description": "Search for talent based on complex criteria",
  "request_body": {
    "query": "Find union directors with music video experience under $200k budget",
    "criteria": {
      "role": "Director",
      "union_status": "Union",
      "specialization": "Music Video",
      "max_budget": 200000,
      "availability": "next_30_days"
    },
    "options": {
      "include_portfolio": true,
      "include_availability": true,
      "max_results": 20
    }
  },
  "response": {
    "status": 200,
    "body": {
      "query_id": "query_345678",
      "agent": "talent_discovery",
      "results": [
        {
          "person": {
            "id": "person_789",
            "name": "Sarah Johnson",
            "role": "Director",
            "union_status": "DGA",
            "specialization": ["Music Video", "Commercial"],
            "budget_range": "$50k-250k"
          },
          "match_score": 0.88,
          "availability": {
            "status": "available",
            "next_available": "2025-09-15",
            "booking_rate": "$15k/day"
          },
          "portfolio": [...],
          "recent_projects": [...]
        }
      ],
      "filters_applied": {...}
    }
  }
}
```

#### POST /agents/bidding-support/query
Query the Bidding Support Agent for budget analysis and union rule integration.

```json
{
  "endpoint": "/agents/bidding-support/query",
  "method": "POST",
  "description": "Analyze budgets and integrate union rules",
  "request_body": {
    "query": "Create budget analysis for 3-day music video shoot in Los Angeles",
    "project_details": {
      "type": "Music Video",
      "duration_days": 3,
      "location": "Los Angeles, CA",
      "union_status": "Union",
      "crew_size": "Medium",
      "equipment_level": "Premium"
    },
    "options": {
      "include_union_rules": true,
      "include_risk_assessment": true,
      "format": "detailed_breakdown"
    }
  },
  "response": {
    "status": 200,
    "body": {
      "query_id": "query_901234",
      "agent": "bidding_support",
      "budget_analysis": {
        "total_estimate": "$275000",
        "breakdown": {
          "above_line": "$125000",
          "below_line": "$100000",
          "post_production": "$35000",
          "contingency": "$15000"
        },
        "union_requirements": {
          "dga_requirements": {...},
          "iatse_rates": {...},
          "sag_requirements": {...}
        }
      },
      "risk_assessment": {
        "overall_risk": "Medium",
        "risk_factors": [...],
        "mitigation_strategies": [...]
      },
      "comparable_projects": [...]
    }
  }
}
```

### 2.4 Project Management Endpoints

#### GET /projects
List projects with role-based filtering.

```json
{
  "endpoint": "/projects",
  "method": "GET",
  "parameters": {
    "page": 1,
    "limit": 20,
    "filter": "active",
    "sort": "created_at desc"
  },
  "response": {
    "status": 200,
    "body": {
      "projects": [
        {
          "id": "proj_123",
          "name": "Summer Campaign 2025",
          "type": "Commercial",
          "status": "In Production",
          "budget_tier": "$100k-300k", // Filtered based on user role
          "director": "John Smith",
          "creative_director": "Jane Doe",
          "client": "Nike",
          "created_at": "2025-08-15T10:00:00Z"
        }
      ],
      "pagination": {
        "page": 1,
        "limit": 20,
        "total": 45,
        "pages": 3
      }
    }
  }
}
```

#### GET /projects/{project_id}
Get detailed project information with RBAC filtering.

```json
{
  "endpoint": "/projects/{project_id}",
  "method": "GET",
  "response": {
    "status": 200,
    "body": {
      "id": "proj_123",
      "name": "Summer Campaign 2025",
      "type": "Commercial",
      "status": "In Production",
      "budget": {
        // Content filtered based on user role
        "tier": "$100k-300k",
        "approved": true
        // Exact amounts hidden for non-Leadership roles
      },
      "team": {
        "director": "John Smith",
        "creative_director": "Jane Doe",
        "producer": "Mike Johnson"
      },
      "timeline": {...},
      "documents": [...], // Filtered by sensitivity level
      "union_status": "Union"
    }
  }
}
```

### 2.5 Analytics and Metrics Endpoints

#### GET /analytics/dashboard
Get dashboard metrics filtered by role.

```json
{
  "endpoint": "/analytics/dashboard",
  "method": "GET",
  "parameters": {
    "timeframe": "30d",
    "role_filter": true
  },
  "response": {
    "status": 200,
    "body": {
      "overview": {
        "total_projects": 42,
        "active_projects": 15,
        "completed_this_month": 8,
        "pipeline_value": "$2.5M" // Only for Leadership role
      },
      "agent_usage": {
        "sales_intelligence": 145,
        "case_study": 89,
        "talent_discovery": 67,
        "bidding_support": 34
      },
      "performance_metrics": {
        "avg_response_time": "1.2s",
        "query_success_rate": "98.5%",
        "user_satisfaction": 4.7
      }
    }
  }
}
```

## 3. WebSocket API Specification

### 3.1 Connection Management

#### WebSocket Connection
Establish real-time connection for AI agent streaming.

```javascript
// Connection URL with authentication
const wsUrl = `wss://api.onevice.com/ws?token=${jwt_token}&user_id=${user_id}`;
const socket = new WebSocket(wsUrl);

// Connection event handlers
socket.onopen = (event) => {
  console.log('Connected to OneVice WebSocket');
  // Send initial connection message
  socket.send(JSON.stringify({
    type: 'connection',
    data: {
      client_version: '1.0.0',
      preferred_agents: ['sales_intelligence'],
      session_preferences: {...}
    }
  }));
};

socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleIncomingMessage(message);
};
```

### 3.2 Message Format Specification

#### Outgoing Message Format (Client → Server)

```json
{
  "message_id": "msg_123456789",
  "type": "agent_query",
  "timestamp": "2025-09-01T12:00:00Z",
  "data": {
    "agent": "sales_intelligence",
    "query": "Research Cordae for music video pitch",
    "context": {
      "thread_id": "thread_abc123",
      "user_role": "Salesperson",
      "project_context": "music_video_pitch"
    },
    "options": {
      "stream_response": true,
      "include_sources": true,
      "max_tokens": 2000
    }
  }
}
```

#### Incoming Message Format (Server → Client)

```json
{
  "message_id": "msg_123456789",
  "type": "agent_response_chunk",
  "timestamp": "2025-09-01T12:00:01Z",
  "data": {
    "agent": "sales_intelligence",
    "chunk_index": 1,
    "total_chunks": 5,
    "content": "Cordae, born Cordae Dunston, is a Grammy-nominated American rapper...",
    "metadata": {
      "confidence_score": 0.92,
      "processing_stage": "entity_analysis",
      "data_sources": ["neo4j_graph", "industry_apis"]
    }
  },
  "status": "streaming"
}
```

### 3.3 WebSocket Message Types

#### Connection Messages
```json
{
  "type": "connection",
  "data": {
    "status": "connected",
    "session_id": "sess_xyz789",
    "supported_agents": ["sales_intelligence", "case_study", "talent_discovery", "bidding_support"],
    "rate_limits": {
      "messages_per_minute": 100,
      "concurrent_queries": 3
    }
  }
}
```

#### Agent Query Messages
```json
{
  "type": "agent_query",
  "data": {
    "agent": "case_study",
    "query": "Find similar commercial projects",
    "context": {...},
    "options": {...}
  }
}
```

#### Streaming Response Messages
```json
{
  "type": "agent_response_chunk",
  "data": {
    "chunk_index": 3,
    "content": "Based on your requirements...",
    "metadata": {...}
  }
}
```

#### Response Complete Messages
```json
{
  "type": "agent_response_complete",
  "data": {
    "total_chunks": 5,
    "final_confidence_score": 0.89,
    "processing_time_ms": 2140,
    "sources_used": ["neo4j_graph", "union_apis", "industry_data"],
    "query_id": "query_final_123"
  }
}
```

#### Error Messages
```json
{
  "type": "error",
  "data": {
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please wait 60 seconds.",
    "retry_after": 60,
    "details": {
      "current_rate": 105,
      "limit": 100,
      "window": "1 minute"
    }
  }
}
```

#### Typing Indicator Messages
```json
{
  "type": "agent_typing",
  "data": {
    "agent": "sales_intelligence",
    "status": "processing",
    "estimated_completion": 3000,
    "stage": "analyzing_entities"
  }
}
```

### 3.4 Connection Health and Monitoring

#### Heartbeat Messages
```json
// Client → Server
{
  "type": "ping",
  "timestamp": "2025-09-01T12:00:00Z"
}

// Server → Client
{
  "type": "pong",
  "timestamp": "2025-09-01T12:00:00Z",
  "server_status": "healthy"
}
```

#### Connection Status Updates
```json
{
  "type": "connection_status",
  "data": {
    "status": "degraded",
    "message": "Experiencing high load. Responses may be delayed.",
    "estimated_delay": "2-5 seconds",
    "alternative_endpoints": [...]
  }
}
```

## 4. Security Specifications

### 4.1 JWT Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "onevice_key_1"
  },
  "payload": {
    "sub": "user_2NisonQDI5C",
    "iss": "https://clerk.onevice.com",
    "aud": "https://api.onevice.com",
    "exp": 1725196800,
    "iat": 1725193200,
    "role": "Leadership",
    "permissions": ["read:all", "write:projects", "admin:users"],
    "data_sensitivity_level": 1,
    "org_id": "org_london_alley"
  }
}
```

### 4.2 Rate Limiting Rules

```json
{
  "rate_limits": {
    "by_role": {
      "Salesperson": {
        "requests_per_minute": 100,
        "concurrent_websocket": 2,
        "query_complexity_max": 5
      },
      "Creative Director": {
        "requests_per_minute": 100,
        "concurrent_websocket": 2,
        "query_complexity_max": 5
      },
      "Director": {
        "requests_per_minute": 200,
        "concurrent_websocket": 3,
        "query_complexity_max": 8
      },
      "Leadership": {
        "requests_per_minute": 500,
        "concurrent_websocket": 5,
        "query_complexity_max": 10
      }
    },
    "by_endpoint": {
      "/agents/*/query": {
        "requests_per_minute": 20,
        "burst_limit": 5
      },
      "/projects": {
        "requests_per_minute": 100,
        "burst_limit": 20
      }
    }
  }
}
```

### 4.3 RBAC Response Filtering

```json
{
  "data_sensitivity_rules": {
    "1_budgets": {
      "Leadership": "full_access",
      "Director": "project_specific",
      "Salesperson": "ranges_only",
      "Creative Director": "ranges_only"
    },
    "2_contracts": {
      "Leadership": "full_access",
      "Director": "project_specific",
      "Salesperson": "no_access",
      "Creative Director": "no_access"
    },
    "3_internal_strategy": {
      "Leadership": "full_access",
      "Director": "project_specific",
      "Salesperson": "limited",
      "Creative Director": "limited"
    },
    "4_call_sheets": {
      "Leadership": "full_access",
      "Director": "full_access",
      "Salesperson": "full_access",
      "Creative Director": "full_access"
    },
    "5_scripts": {
      "Leadership": "full_access",
      "Director": "full_access",
      "Salesperson": "full_access",
      "Creative Director": "full_access"
    },
    "6_sales_decks": {
      "Leadership": "full_access",
      "Director": "full_access",
      "Salesperson": "full_access",
      "Creative Director": "full_access"
    }
  }
}
```

## 5. Error Handling and Status Codes

### 5.1 HTTP Status Codes

```json
{
  "status_codes": {
    "200": "OK - Request successful",
    "201": "Created - Resource created successfully",
    "400": "Bad Request - Invalid request format or parameters",
    "401": "Unauthorized - Invalid or missing authentication",
    "403": "Forbidden - Insufficient permissions for requested resource",
    "404": "Not Found - Requested resource does not exist",
    "429": "Too Many Requests - Rate limit exceeded",
    "500": "Internal Server Error - Server error occurred",
    "502": "Bad Gateway - Upstream service unavailable",
    "503": "Service Unavailable - Service temporarily unavailable"
  }
}
```

### 5.2 Error Response Format

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Request rate limit exceeded",
    "details": {
      "current_rate": 105,
      "limit": 100,
      "window": "1 minute",
      "retry_after": 60
    },
    "timestamp": "2025-09-01T12:00:00Z",
    "request_id": "req_123456789",
    "documentation_url": "https://docs.onevice.com/errors#rate-limit"
  }
}
```

### 5.3 Validation Errors

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "invalid_fields": [
        {
          "field": "query",
          "error": "Query cannot be empty",
          "provided": ""
        },
        {
          "field": "agent",
          "error": "Invalid agent type",
          "provided": "invalid_agent",
          "valid_options": ["sales_intelligence", "case_study", "talent_discovery", "bidding_support"]
        }
      ]
    }
  }
}
```

## 6. Performance Requirements

### 6.1 Response Time Targets

```json
{
  "performance_targets": {
    "rest_endpoints": {
      "authentication": "< 500ms",
      "user_profile": "< 200ms",
      "project_list": "< 800ms",
      "agent_queries": "< 2000ms"
    },
    "websocket": {
      "connection_establishment": "< 100ms",
      "message_delivery": "< 50ms",
      "streaming_latency": "< 200ms",
      "heartbeat_response": "< 25ms"
    },
    "agent_processing": {
      "simple_queries": "< 2000ms",
      "complex_queries": "< 8000ms",
      "streaming_first_chunk": "< 1000ms",
      "chunk_interval": "< 100ms"
    }
  }
}
```

### 6.2 Throughput Requirements

```json
{
  "throughput_targets": {
    "concurrent_users": 100,
    "requests_per_second": 1000,
    "websocket_connections": 500,
    "concurrent_agent_queries": 50,
    "database_queries_per_second": 2000
  }
}
```

## 7. Render Deployment Configuration

### 7.1 Service Architecture

The OneVice API is deployed using Render's managed services with automatic scaling and load balancing:

```yaml
services:
  - name: onevice-backend
    type: web
    runtime: python
    plan: standard  # 2GB RAM, 1 CPU
    healthCheckPath: /health
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
    
  - name: onevice-worker
    type: worker
    runtime: python
    plan: starter
    startCommand: python worker.py
```

### 7.2 Environment Management

**Development Environment**: 
- URL: `https://onevice-backend-dev.onrender.com`
- Branch: `develop`
- Database: `onevice-postgres-dev`

**Staging Environment**:
- URL: `https://onevice-backend-staging.onrender.com`  
- Branch: `main` (preview deployments)
- Database: `onevice-postgres-staging`

**Production Environment**:
- URL: `https://onevice-backend.onrender.com`
- Custom Domain: `https://api.onevice.com`
- Branch: `main`
- Database: `onevice-postgres` (Standard plan)

### 7.3 Auto-scaling Configuration

```json
{
  "scaling_policy": {
    "web_services": {
      "min_instances": 1,
      "max_instances": 10,
      "scale_up_threshold": "80% CPU or 500 concurrent connections",
      "scale_down_threshold": "40% CPU for 5 minutes"
    },
    "worker_services": {
      "min_instances": 1,
      "max_instances": 5,
      "scale_based_on": "queue_depth",
      "scale_up_threshold": "> 100 pending jobs",
      "scale_down_threshold": "< 10 pending jobs for 10 minutes"
    }
  }
}
```

### 7.4 Health Check Endpoints

All Render services implement standardized health checks:

```http
GET /health
```

```json
{
  "status": "healthy",
  "timestamp": "2025-09-01T12:00:00Z",
  "version": "2.0.0",
  "environment": "production",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "neo4j": "healthy",
    "external_apis": "healthy"
  },
  "metrics": {
    "uptime_seconds": 86400,
    "active_connections": 45,
    "memory_usage": "1.2GB",
    "cpu_usage": "35%"
  }
}
```

### 7.5 Monitoring and Alerts

**Render Native Monitoring**:
- Service health dashboards
- Resource usage metrics
- Deployment status tracking
- Real-time logging

**LangSmith Integration**:
- AI agent performance tracking
- Cost monitoring
- Quality metrics
- User interaction analytics

**Alert Configuration**:
- Service downtime alerts
- High error rate notifications  
- Performance degradation warnings
- Resource usage thresholds

---

**Document Status**: Ready for Implementation  
**Last Updated**: September 1, 2025  
**Deployment Platform**: Render  
**Next Review**: Upon completion of backend API implementation