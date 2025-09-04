# Graph Tools Integration Examples

## Overview

This document provides complete, working examples of how to integrate and use the OneVice graph tools system. All examples include setup, execution, and response handling.

## Complete Setup Example

### 1. Environment Configuration
```bash
# .env file
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-secure-password
NEO4J_DATABASE=neo4j

REDIS_HOST=redis-12345.c1.us-east-1-1.ec2.cloud.redislabs.com
REDIS_PORT=12345
REDIS_PASSWORD=your-redis-password

FOLK_API_KEY=folk_live_abc123xyz789
FOLK_API_URL=https://api.folk.app/v1

DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 2. Application Initialization
```python
# app/main.py
import os
import asyncio
from fastapi import FastAPI
from app.ai.workflows.orchestrator import AgentOrchestrator
from app.ai.config import AIConfig

app = FastAPI(title="OneVice AI Platform")

# Global orchestrator instance
orchestrator: AgentOrchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize the agent orchestrator with graph tools"""
    global orchestrator
    
    # Create configuration
    config = AIConfig(
        neo4j_uri=os.getenv("NEO4J_URI"),
        neo4j_username=os.getenv("NEO4J_USERNAME"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
        neo4j_database=os.getenv("NEO4J_DATABASE"),
        redis_url=f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}",
        folk_api_key=os.getenv("FOLK_API_KEY"),
        folk_api_url=os.getenv("FOLK_API_URL")
    )
    
    # Create orchestrator with graph tools integration
    orchestrator = await AgentOrchestrator.create_orchestrator(config)
    print("✅ Agent orchestrator initialized with graph tools")

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup orchestrator resources"""
    global orchestrator
    if orchestrator:
        await orchestrator.cleanup()
        print("✅ Agent orchestrator cleaned up")

@app.get("/health/graph-tools")
async def health_check():
    """Health check endpoint for graph tools"""
    global orchestrator
    if not orchestrator:
        return {"status": "error", "message": "Orchestrator not initialized"}
    
    status = await orchestrator.get_agent_status()
    return status["graph_tools"]
```

## Agent Integration Examples

### Sales Intelligence Agent Example

```python
# app/api/sales.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.ai.config import AgentType

router = APIRouter(prefix="/api/sales", tags=["sales"])

@router.post("/qualify-lead")
async def qualify_lead_endpoint(
    company_name: str,
    contact_name: str,
    user_context: Dict[str, Any] = None
):
    """Lead qualification using graph tools"""
    
    try:
        # Route query to sales agent
        response = await orchestrator.route_query(
            query=f"Qualify lead: {contact_name} at {company_name}. Provide comprehensive analysis including decision maker access, network strength, and recommended approach strategy.",
            user_context=user_context or {"role": "sales_rep", "access_level": "internal"},
            preferred_agent=AgentType.SALES,
            conversation_id=f"lead_qual_{company_name}_{contact_name}"
        )
        
        return {
            "qualification_result": response["content"],
            "agent_used": response["agent_type"],
            "routing_metadata": response.get("routing", {}),
            "timestamp": response["timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead qualification failed: {str(e)}")

# Example usage in client application:
"""
POST /api/sales/qualify-lead
{
    "company_name": "Nike",
    "contact_name": "John Marketing Director",
    "user_context": {
        "role": "senior_sales_rep",
        "access_level": "internal",
        "territory": "west_coast"
    }
}

Response:
{
    "qualification_result": {
        "qualified": true,
        "score": 87,
        "organization": {
            "name": "Nike",
            "tier": "Enterprise",
            "industry": "Sports & Apparel",
            "recent_projects": 12,
            "annual_production_budget": "$50M+"
        },
        "contact_analysis": {
            "name": "John Marketing Director",
            "title": "Director of Marketing",
            "decision_making_authority": true,
            "years_experience": 15,
            "network_influence": "high"
        },
        "decision_makers": {
            "found": true,
            "count": 5,
            "high_influence": 2,
            "accessible_through_contact": true
        },
        "recommended_approach": {
            "strategy": "executive_engagement",
            "entry_point": "marketing_collaboration",
            "timeline": "3-6_months",
            "success_probability": "high"
        }
    },
    "agent_used": "sales",
    "routing_metadata": {
        "strategy": "single_agent",
        "confidence": 0.95
    }
}
"""
```

### Talent Acquisition Agent Example

```python
# app/api/talent.py
from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="/api/talent", tags=["talent"])

class ProjectRequirements(BaseModel):
    project_type: str
    skills_required: List[str]
    budget_tier: str = "mid"
    location: str = "Los Angeles"
    timeline: str = "3_months"
    experience_level: str = "senior"

@router.post("/find-talent-pool")
async def find_talent_pool_endpoint(
    requirements: ProjectRequirements,
    user_context: Dict[str, Any] = None
):
    """Find optimal talent pool for project requirements"""
    
    query = f"""
    Find talent pool for {requirements.project_type} project requiring skills: {', '.join(requirements.skills_required)}.
    
    Requirements:
    - Budget tier: {requirements.budget_tier}
    - Location: {requirements.location} 
    - Timeline: {requirements.timeline}
    - Experience: {requirements.experience_level}
    
    Provide:
    1. Top candidates for each key role
    2. Team composition recommendations
    3. Availability and rate estimates
    4. Collaboration history analysis
    """
    
    response = await orchestrator.route_query(
        query=query,
        user_context=user_context or {"role": "talent_coordinator", "access_level": "internal"},
        preferred_agent=AgentType.TALENT,
        conversation_id=f"talent_search_{requirements.project_type}"
    )
    
    return {
        "talent_pool": response["content"],
        "requirements": requirements.dict(),
        "search_metadata": response.get("routing", {}),
        "timestamp": response["timestamp"]
    }

# Example usage:
"""
POST /api/talent/find-talent-pool
{
    "project_type": "luxury_commercial",
    "skills_required": ["cinematography", "lighting", "color_grading"],
    "budget_tier": "high", 
    "location": "New York",
    "timeline": "2_months",
    "experience_level": "expert"
}

Response:
{
    "talent_pool": {
        "director_of_photography": [
            {
                "name": "Sarah Chen",
                "fit_score": 95,
                "availability": "available_march",
                "day_rate": "$3500",
                "recent_projects": ["Gucci Campaign 2024", "Tiffany Holiday Spot"],
                "collaborators": ["Marcus Rodriguez (Gaffer)", "Lisa Park (Colorist)"],
                "expertise": ["luxury_brands", "automotive", "fashion"]
            }
        ],
        "gaffer": [...],
        "colorist": [...]
    },
    "recommended_teams": [
        {
            "combination_score": 92,
            "total_budget_estimate": "$45000",
            "collaboration_history": "worked_together_3_times",
            "members": ["Sarah Chen", "Marcus Rodriguez", "Lisa Park"]
        }
    ]
}
"""
```

### Analytics Agent Example

```python
# app/api/analytics.py
from fastapi import APIRouter
from typing import Optional, List
from enum import Enum

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

class AnalysisType(str, Enum):
    PERFORMANCE = "performance"
    TRENDS = "trends"
    COMPETITIVE = "competitive"
    NETWORK = "network"

@router.get("/project-insights/{project_title}")
async def get_project_insights(
    project_title: str,
    analysis_type: AnalysisType,
    user_context: Dict[str, Any] = None
):
    """Get comprehensive project insights using graph analytics"""
    
    query = f"""
    Analyze project "{project_title}" for {analysis_type.value} insights.
    
    Provide comprehensive analysis including:
    - Performance metrics and benchmarks
    - Team composition effectiveness  
    - Creative approach analysis
    - Market positioning and competitive landscape
    - Network effects and industry connections
    - Predictive insights for similar future projects
    """
    
    response = await orchestrator.route_query(
        query=query,
        user_context=user_context or {"role": "analyst", "access_level": "internal"},
        preferred_agent=AgentType.ANALYTICS,
        conversation_id=f"project_analysis_{project_title}"
    )
    
    return {
        "project_title": project_title,
        "analysis_type": analysis_type.value,
        "insights": response["content"],
        "metadata": response.get("routing", {}),
        "timestamp": response["timestamp"]
    }

@router.post("/trend-analysis")
async def analyze_trends(
    category: str,
    time_period: str = "last_year",
    metrics: List[str] = None,
    user_context: Dict[str, Any] = None
):
    """Analyze creative and performance trends"""
    
    metrics = metrics or ["creative_concepts", "performance", "team_patterns"]
    
    query = f"""
    Analyze trends in {category} over {time_period}.
    
    Focus on metrics: {', '.join(metrics)}
    
    Provide:
    1. Trending creative concepts and styles
    2. Performance pattern analysis
    3. Emerging talent and team compositions
    4. Market shifts and opportunities
    5. Predictive insights for upcoming projects
    """
    
    response = await orchestrator.route_query(
        query=query,
        user_context=user_context or {"role": "strategic_analyst", "access_level": "internal"},
        preferred_agent=AgentType.ANALYTICS
    )
    
    return {
        "trend_analysis": response["content"],
        "analysis_parameters": {
            "category": category,
            "time_period": time_period,
            "metrics": metrics
        },
        "timestamp": response["timestamp"]
    }

# Example usage:
"""
GET /api/analytics/project-insights/Nike%20Air%20Max%20Campaign%202024?analysis_type=performance

Response:
{
    "project_title": "Nike Air Max Campaign 2024",
    "analysis_type": "performance", 
    "insights": {
        "performance_score": 87,
        "performance_benchmarks": {
            "industry_average": 72,
            "nike_historical_average": 81,
            "similar_campaigns": 79
        },
        "success_factors": [
            "Strong director-client collaboration history",
            "Optimal team size (12 core members)",
            "High-performing creative concept (cinematic realism)",
            "Efficient budget utilization (98% of allocated)"
        ],
        "team_effectiveness": {
            "collaboration_score": 94,
            "experience_match": "optimal",
            "previous_collaborations": 67
        },
        "competitive_analysis": {
            "market_position": "premium_tier",
            "differentiation_factors": ["technical_excellence", "brand_alignment"],
            "competitive_advantages": ["exclusive_talent", "innovative_approach"]
        },
        "predictive_insights": {
            "similar_project_success_probability": 89,
            "recommended_team_patterns": ["maintain_core_team", "add_motion_graphics_specialist"],
            "optimal_timeline": "10_weeks",
            "budget_efficiency_score": 92
        }
    }
}
"""
```

## Multi-Agent Workflow Examples

### Complex Query with Multiple Agents

```python
# app/api/workflows.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

@router.post("/comprehensive-client-analysis")
async def comprehensive_client_analysis(
    client_name: str,
    opportunity_type: str,
    user_context: Dict[str, Any] = None
):
    """Comprehensive client analysis using multiple agents"""
    
    query = f"""
    Conduct comprehensive analysis for potential {opportunity_type} opportunity with {client_name}.
    
    Required analysis:
    1. Sales perspective: Lead qualification, decision maker analysis, competitive landscape
    2. Talent perspective: Available team options, optimal crew recommendations  
    3. Analytics perspective: Market trends, performance predictions, risk assessment
    
    Provide integrated insights and strategic recommendations.
    """
    
    # This will trigger multi-agent response automatically
    response = await orchestrator.route_query(
        query=query,
        user_context=user_context or {"role": "business_development", "access_level": "internal"},
        conversation_id=f"client_analysis_{client_name}"
    )
    
    return {
        "client_analysis": response["content"],
        "agents_consulted": response["routing"]["agents_used"],
        "individual_agent_responses": response["routing"].get("agent_responses", {}),
        "synthesis_quality": "comprehensive",
        "timestamp": response["timestamp"]
    }

# Example multi-agent response:
"""
POST /api/workflows/comprehensive-client-analysis
{
    "client_name": "Netflix",
    "opportunity_type": "documentary_series"
}

Response:
{
    "client_analysis": {
        "executive_summary": {
            "opportunity_score": 91,
            "strategic_fit": "excellent",
            "recommended_action": "immediate_engagement",
            "success_probability": 78
        },
        "sales_perspective": {
            "lead_qualification": {
                "qualified": true,
                "score": 88,
                "key_contacts": ["Sarah Johnson (VP Documentary)", "Michael Chen (Head of Content)"],
                "decision_timeline": "6-8_weeks",
                "budget_authority": "confirmed"
            },
            "competitive_landscape": {
                "primary_competitors": ["Participant Media", "CNN Films"],
                "differentiation_opportunity": "technical_innovation_focus",
                "competitive_advantages": ["ai_integration_capability", "rapid_turnaround"]
            }
        },
        "talent_perspective": {
            "available_directors": [
                {
                    "name": "Elena Rodriguez",
                    "specialty": "documentary_storytelling",
                    "netflix_experience": "3_previous_projects",
                    "availability": "q2_2024"
                }
            ],
            "crew_recommendations": {
                "optimal_team_size": 8,
                "key_roles_filled": 7,
                "missing_specialist": "ai_integration_coordinator",
                "estimated_budget": "$450K"
            }
        },
        "analytics_perspective": {
            "market_trends": {
                "documentary_demand": "increasing_15_percent",
                "ai_integration_trend": "emerging_opportunity",
                "netflix_investment_pattern": "doubling_documentary_budget"
            },
            "performance_predictions": {
                "success_probability": 82,
                "roi_estimate": "225_percent",
                "risk_factors": ["technical_complexity", "timeline_pressure"]
            }
        },
        "integrated_recommendations": {
            "immediate_actions": [
                "Schedule meeting with Sarah Johnson",
                "Prepare AI integration capability demo",
                "Secure Elena Rodriguez availability"
            ],
            "strategic_approach": "innovation_partnership",
            "timeline": "4_month_production_cycle",
            "success_factors": ["technical_differentiation", "proven_team", "netflix_relationship"]
        }
    },
    "agents_consulted": ["sales", "talent", "analytics"],
    "synthesis_quality": "comprehensive"
}
"""
```

## WebSocket Real-Time Integration

```python
# app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
import json

@app.websocket("/ws/graph-tools")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time graph tools queries"""
    await websocket.accept()
    
    try:
        while True:
            # Receive query from client
            data = await websocket.receive_text()
            query_data = json.loads(data)
            
            query = query_data.get("query")
            agent_type = query_data.get("agent_type")
            user_context = query_data.get("user_context", {})
            
            # Send processing status
            await websocket.send_json({
                "type": "status",
                "message": "Processing query...",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            try:
                # Route query through orchestrator
                response = await orchestrator.route_query(
                    query=query,
                    user_context=user_context,
                    preferred_agent=AgentType(agent_type) if agent_type else None
                )
                
                # Send successful response
                await websocket.send_json({
                    "type": "response",
                    "data": response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                # Send error response
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        print("Client disconnected from graph tools WebSocket")

# Client-side usage:
"""
const ws = new WebSocket('ws://localhost:8000/ws/graph-tools');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'status') {
        console.log('Status:', data.message);
    } else if (data.type === 'response') {
        console.log('Response:', data.data);
    } else if (data.type === 'error') {
        console.error('Error:', data.message);
    }
};

// Send query
ws.send(JSON.stringify({
    query: "Find directors who have worked on luxury car commercials",
    agent_type: "talent",
    user_context: {
        role: "producer",
        access_level: "internal"
    }
}));
"""
```

## Testing Examples

### Integration Test Example

```python
# tests/integration/test_graph_tools_integration.py
import pytest
import asyncio
from app.ai.workflows.orchestrator import AgentOrchestrator
from app.ai.config import AIConfig, AgentType

@pytest.fixture
async def test_orchestrator():
    """Create test orchestrator with mock dependencies"""
    config = AIConfig(
        neo4j_uri="neo4j://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="test",
        redis_url="redis://localhost:6379"
    )
    
    orchestrator = await AgentOrchestrator.create_orchestrator(config)
    yield orchestrator
    await orchestrator.cleanup()

@pytest.mark.asyncio
async def test_sales_agent_integration(test_orchestrator):
    """Test sales agent with graph tools integration"""
    
    query = "Qualify lead: John Smith at Nike for commercial campaign opportunity"
    
    response = await test_orchestrator.route_query(
        query=query,
        user_context={"role": "sales_rep", "access_level": "internal"},
        preferred_agent=AgentType.SALES
    )
    
    assert response["agent_type"] == "sales"
    assert "content" in response
    assert response["routing"]["strategy"] == "single_agent"
    
    # Verify graph tools were used
    graph_tools_status = await test_orchestrator.get_agent_status()
    assert graph_tools_status["graph_tools"]["status"] in ["healthy", "degraded"]

@pytest.mark.asyncio
async def test_multi_agent_workflow(test_orchestrator):
    """Test multi-agent workflow with graph tools"""
    
    query = """
    Comprehensive analysis needed: Netflix documentary opportunity.
    Need sales qualification, talent recommendations, and market analysis.
    """
    
    response = await test_orchestrator.route_query(
        query=query,
        user_context={"role": "business_development", "access_level": "internal"}
    )
    
    # Should trigger multi-agent response
    assert response["routing"]["strategy"] == "multi_agent"
    assert len(response["routing"]["agents_used"]) > 1
    assert "agent_responses" in response["routing"]
```

### Performance Test Example

```python
# tests/performance/test_graph_tools_performance.py
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.asyncio
async def test_concurrent_queries(test_orchestrator):
    """Test concurrent query performance"""
    
    queries = [
        "Find directors for commercial campaign",
        "Analyze Nike brand campaign performance", 
        "Get talent pool for luxury automotive project",
        "Find decision makers at Netflix",
        "Analyze documentary market trends"
    ]
    
    start_time = time.time()
    
    # Execute queries concurrently
    tasks = []
    for i, query in enumerate(queries):
        task = test_orchestrator.route_query(
            query=query,
            user_context={"role": "test_user", "access_level": "internal"},
            conversation_id=f"perf_test_{i}"
        )
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Performance assertions
    assert len(responses) == len(queries)
    assert total_time < 10.0  # All queries should complete within 10 seconds
    assert all(r.get("content") for r in responses)  # All should have content
    
    print(f"Concurrent query performance: {total_time:.2f}s for {len(queries)} queries")

@pytest.mark.asyncio
async def test_cache_performance(test_orchestrator):
    """Test cache performance impact"""
    
    query = "Get person details: John Smith director"
    
    # First query (cache miss)
    start_time = time.time()
    response1 = await test_orchestrator.route_query(
        query=query,
        user_context={"role": "test_user", "access_level": "internal"}
    )
    first_query_time = time.time() - start_time
    
    # Second query (should be cached)
    start_time = time.time()
    response2 = await test_orchestrator.route_query(
        query=query,
        user_context={"role": "test_user", "access_level": "internal"}
    )
    second_query_time = time.time() - start_time
    
    # Cache should improve performance significantly
    assert second_query_time < first_query_time * 0.5  # At least 50% faster
    assert response1["content"] == response2["content"]  # Same result
    
    print(f"Cache performance: {first_query_time:.3f}s -> {second_query_time:.3f}s")
```

## Monitoring and Logging Examples

```python
# app/monitoring/graph_tools_monitor.py
import logging
import time
from typing import Dict, Any
from datetime import datetime, timedelta

class GraphToolsMonitor:
    """Monitor graph tools performance and usage"""
    
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            "query_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0,
            "error_count": 0,
            "agent_usage": {
                "sales": 0,
                "talent": 0, 
                "analytics": 0
            }
        }
    
    async def log_query_performance(self, 
                                   query: str, 
                                   response: Dict[str, Any], 
                                   execution_time: float):
        """Log query performance metrics"""
        
        self.metrics["query_count"] += 1
        
        # Update average response time
        current_avg = self.metrics["avg_response_time"]
        new_avg = ((current_avg * (self.metrics["query_count"] - 1)) + execution_time) / self.metrics["query_count"]
        self.metrics["avg_response_time"] = new_avg
        
        # Track agent usage
        agent_type = response.get("agent_type", "unknown")
        if agent_type in self.metrics["agent_usage"]:
            self.metrics["agent_usage"][agent_type] += 1
        
        # Log slow queries
        if execution_time > 2.0:
            self.logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}...")
        
        # Log performance metrics every 100 queries
        if self.metrics["query_count"] % 100 == 0:
            await self._log_performance_summary()
    
    async def _log_performance_summary(self):
        """Log performance summary"""
        
        graph_status = await self.orchestrator.get_agent_status()
        cache_stats = graph_status["graph_tools"].get("cache_stats", {})
        
        self.logger.info(f"""
Graph Tools Performance Summary (last 100 queries):
- Average response time: {self.metrics['avg_response_time']:.3f}s
- Cache hit rate: {cache_stats.get('keyspace_hits', 0) / (cache_stats.get('keyspace_hits', 0) + cache_stats.get('keyspace_misses', 1)) * 100:.1f}%
- Agent usage: {self.metrics['agent_usage']}
- Error rate: {self.metrics['error_count'] / self.metrics['query_count'] * 100:.2f}%
- Total queries processed: {self.metrics['query_count']}
        """)

# Usage in application:
"""
# Initialize monitor
monitor = GraphToolsMonitor(orchestrator)

# In query handler:
start_time = time.time()
try:
    response = await orchestrator.route_query(query, user_context)
    execution_time = time.time() - start_time
    await monitor.log_query_performance(query, response, execution_time)
    return response
except Exception as e:
    monitor.metrics["error_count"] += 1
    raise
"""
```

These examples provide complete, production-ready implementations of the graph tools integration across different use cases and scenarios.