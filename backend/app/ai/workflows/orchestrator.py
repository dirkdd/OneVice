"""
Agent Orchestrator

Multi-agent coordination system for entertainment industry AI agents.
Routes queries to appropriate agents and coordinates complex workflows.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime
from enum import Enum

import redis.asyncio as redis
from redis.asyncio import Redis

from ..config import AIConfig, AgentType
from ..llm.router import LLMRouter
from database.neo4j_client import Neo4jClient
from ..services.vector_service import VectorSearchService
from ..services.knowledge_service import KnowledgeGraphService
from ..agents.base_agent import BaseAgent
from ..agents.sales_agent import SalesIntelligenceAgent
from ..agents.talent_agent import TalentAcquisitionAgent
from ..agents.analytics_agent import LeadershipAnalyticsAgent
from ..tools.graph_tools import GraphQueryTools
from tools.folk_ingestion.folk_client import FolkClient
from ...core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)

class RoutingStrategy(str, Enum):
    """Agent routing strategies"""
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"

class AgentOrchestrator:
    """
    Orchestrates multiple AI agents for complex entertainment industry queries
    """
    
    def __init__(self, config: AIConfig):
        self.config = config
        
        # Initialize core services
        self.llm_router = LLMRouter(config)
        self.neo4j_client = Neo4jClient()  # Uses environment variables for config
        self.redis_client = redis.from_url(config.redis_url)
        
        # Initialize Folk API client for live CRM data
        self.folk_client = FolkClient(
            api_key=config.folk_api_key,
            base_url=config.folk_api_url
        ) if hasattr(config, 'folk_api_key') and config.folk_api_key else None
        
        # Initialize graph query tools (shared across agents)
        self.graph_tools = GraphQueryTools(
            neo4j_client=self.neo4j_client,
            folk_client=self.folk_client,
            redis_client=self.redis_client
        )
        
        # Initialize services
        self.vector_service = VectorSearchService(
            config, self.llm_router, self.neo4j_client, self.redis_client
        )
        self.knowledge_service = KnowledgeGraphService(
            config, self.neo4j_client, self.vector_service
        )
        
        # Initialize agents with graph tools
        self.agents: Dict[AgentType, BaseAgent] = {}
        self._initialize_agents()
        
        # Routing configuration
        self.routing_rules = self._setup_routing_rules()



    @classmethod
    async def create_orchestrator(cls, config: AIConfig) -> 'AgentOrchestrator':
        """
        Factory method to create and initialize orchestrator with all dependencies
        
        Args:
            config: AI configuration with database and service settings
            
        Returns:
            Fully initialized AgentOrchestrator instance
        """
        try:
            # Create orchestrator instance
            orchestrator = cls(config)
            
            # Initialize all services
            await orchestrator.initialize_services()
            
            # Validate graph tools initialization
            if orchestrator.graph_tools:
                await orchestrator._validate_graph_tools()
            
            logger.info("Agent orchestrator created successfully with all dependencies")
            return orchestrator
            
        except Exception as e:
            logger.error(f"Orchestrator creation failed: {e}")
            raise AIProcessingError(f"Failed to create orchestrator: {e}")

    async def _validate_graph_tools(self):
        """Validate graph tools initialization and connectivity"""
        
        try:
            # Test Neo4j connection
            test_query = "RETURN 1 as test"
            await self.neo4j_client.execute_query(test_query)
            logger.info("Graph tools Neo4j connection validated")
            
            # Test Redis connection if available
            if self.redis_client:
                await self.redis_client.ping()
                logger.info("Graph tools Redis connection validated")
            
            # Test Folk API connection if available
            if self.folk_client:
                # This would be a simple health check
                logger.info("Graph tools Folk API client initialized")
            
        except Exception as e:
            logger.warning(f"Graph tools validation warning: {e}")
            # Don't fail initialization, just warn

    def _initialize_agents(self):
        """Initialize all AI agents with graph query tools"""
        
        try:
            # Sales Intelligence Agent with LangGraph tool binding
            self.agents[AgentType.SALES] = SalesIntelligenceAgent(
                config=self.config,
                llm_router=self.llm_router,
                knowledge_service=self.knowledge_service,
                redis_client=self.redis_client
            )
            
            # Talent Acquisition Agent with talent-focused tools
            self.agents[AgentType.TALENT] = TalentAcquisitionAgent(
                config=self.config,
                llm_router=self.llm_router,
                knowledge_service=self.knowledge_service,
                redis_client=self.redis_client,
                neo4j_client=self.neo4j_client,
                folk_client=self.folk_client
            )
            
            # Leadership Analytics Agent with analytics-focused tools
            self.agents[AgentType.ANALYTICS] = LeadershipAnalyticsAgent(
                config=self.config,
                llm_router=self.llm_router,
                knowledge_service=self.knowledge_service,
                redis_client=self.redis_client,
                neo4j_client=self.neo4j_client,
                folk_client=self.folk_client
            )
            
            logger.info(f"Initialized {len(self.agents)} AI agents with graph query tools")
            
            # Log graph tools capabilities
            if self.graph_tools:
                logger.info("Graph tools capabilities:")
                logger.info("- Folk API integration: %s", "enabled" if self.folk_client else "disabled")
                logger.info("- Redis caching: %s", "enabled" if self.redis_client else "disabled") 
                logger.info("- Neo4j graph queries: enabled")
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            raise AIProcessingError(f"Agent initialization failed: {e}")

    def _setup_routing_rules(self) -> Dict[str, Dict]:
        """Setup routing rules for query classification"""
        
        return {
            "sales": {
                "keywords": ["lead", "sales", "market", "pricing", "revenue", "client", "prospect", "opportunity"],
                "agent": AgentType.SALES,
                "confidence_threshold": 0.7
            },
            "talent": {
                "keywords": ["talent", "hire", "crew", "skills", "team", "staff", "casting", "union"],
                "agent": AgentType.TALENT,
                "confidence_threshold": 0.7
            },
            "analytics": {
                "keywords": ["analytics", "performance", "metrics", "report", "analysis", "trend", "forecast", "kpi"],
                "agent": AgentType.ANALYTICS,
                "confidence_threshold": 0.7
            }
        }

    async def initialize_services(self):
        """Initialize all underlying services"""
        
        try:
            # Connect to Neo4j
            await self.neo4j_client.connect()
            logger.info("Neo4j connection initialized")
            
            # Test Redis connection
            await self.redis_client.ping()
            logger.info("Redis connection initialized")
            
            # Initialize vector indexes if needed
            # This would typically be done during deployment
            
            # Setup agents that require async initialization
            if AgentType.SALES in self.agents:
                await self.agents[AgentType.SALES].setup()
                logger.info("Sales Intelligence Agent setup completed")
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            raise AIProcessingError(f"Service initialization failed: {e}")

    async def route_query(
        self,
        query: str,
        user_context: Dict[str, Any],
        preferred_agent: Optional[AgentType] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route query to appropriate agent(s)
        
        Args:
            query: User query
            user_context: User context and permissions
            preferred_agent: Optional preferred agent type
            conversation_id: Optional conversation ID for continuity
            
        Returns:
            Agent response with routing metadata
        """
        
        try:
            # Determine routing strategy
            if preferred_agent:
                target_agent = preferred_agent
                strategy = RoutingStrategy.SINGLE_AGENT
            else:
                target_agent, strategy = await self._classify_query(query, user_context)
            
            # Route based on strategy
            if strategy == RoutingStrategy.SINGLE_AGENT:
                return await self._single_agent_response(
                    target_agent, query, user_context, conversation_id
                )
            
            elif strategy == RoutingStrategy.MULTI_AGENT:
                return await self._multi_agent_response(
                    query, user_context, conversation_id
                )
            
            else:
                # Default to sales agent for unknown queries
                return await self._single_agent_response(
                    AgentType.SALES, query, user_context, conversation_id
                )
                
        except Exception as e:
            logger.error(f"Query routing failed: {e}")
            raise AIProcessingError(f"Query routing failed: {e}")

    async def _classify_query(
        self,
        query: str,
        user_context: Dict[str, Any]
    ) -> tuple[AgentType, RoutingStrategy]:
        """Classify query to determine appropriate agent"""
        
        query_lower = query.lower()
        scores = {}
        
        # Score query against each domain
        for domain, rules in self.routing_rules.items():
            score = 0
            for keyword in rules["keywords"]:
                if keyword in query_lower:
                    score += 1
            
            # Normalize score
            if len(rules["keywords"]) > 0:
                scores[domain] = score / len(rules["keywords"])
            else:
                scores[domain] = 0
        
        # Find best match
        best_domain = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_domain]
        
        # Determine if multi-agent approach needed
        high_scoring_domains = [d for d, s in scores.items() if s >= 0.3]
        
        if len(high_scoring_domains) > 1:
            strategy = RoutingStrategy.MULTI_AGENT
            # Return primary agent
            target_agent = self.routing_rules[best_domain]["agent"]
        elif best_score >= self.routing_rules[best_domain]["confidence_threshold"]:
            strategy = RoutingStrategy.SINGLE_AGENT
            target_agent = self.routing_rules[best_domain]["agent"]
        else:
            # Default to sales for ambiguous queries
            strategy = RoutingStrategy.SINGLE_AGENT
            target_agent = AgentType.SALES
        
        logger.debug(f"Query classified: domain={best_domain}, score={best_score}, strategy={strategy}")
        
        return target_agent, strategy

    async def _single_agent_response(
        self,
        agent_type: AgentType,
        query: str,
        user_context: Dict[str, Any],
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get response from single agent"""
        
        agent = self.agents.get(agent_type)
        if not agent:
            raise AIProcessingError(f"Agent {agent_type} not available")
        
        try:
            response = await agent.chat(
                message=query,
                user_context=user_context,
                conversation_id=conversation_id
            )
            
            return {
                **response,
                "routing": {
                    "strategy": RoutingStrategy.SINGLE_AGENT,
                    "primary_agent": agent_type.value,
                    "agents_used": [agent_type.value]
                }
            }
            
        except Exception as e:
            logger.error(f"Single agent response failed for {agent_type}: {e}")
            raise AIProcessingError(f"Agent {agent_type} processing failed: {e}")

    async def _multi_agent_response(
        self,
        query: str,
        user_context: Dict[str, Any],
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Coordinate multi-agent response"""
        
        # For this implementation, we'll use a simplified approach
        # In production, this would involve more sophisticated coordination
        
        try:
            # Get responses from relevant agents in parallel
            agent_tasks = []
            
            for agent_type, agent in self.agents.items():
                task = agent.chat(
                    message=query,
                    user_context=user_context,
                    conversation_id=f"{conversation_id}_{agent_type.value}" if conversation_id else None
                )
                agent_tasks.append((agent_type, task))
            
            # Execute all agents
            agent_responses = await asyncio.gather(
                *[task for _, task in agent_tasks],
                return_exceptions=True
            )
            
            # Process responses
            successful_responses = {}
            for i, (agent_type, response) in enumerate(zip([a[0] for a in agent_tasks], agent_responses)):
                if not isinstance(response, Exception):
                    successful_responses[agent_type.value] = {
                        "content": response["content"],
                        "metadata": response["metadata"],
                        "timestamp": response["timestamp"]
                    }
                else:
                    logger.error(f"Agent {agent_type} failed: {response}")
            
            # Synthesize responses
            synthesized_response = await self._synthesize_responses(
                query, successful_responses, user_context
            )
            
            return {
                "content": synthesized_response,
                "conversation_id": conversation_id,
                "agent_type": "orchestrator",
                "routing": {
                    "strategy": RoutingStrategy.MULTI_AGENT,
                    "agents_used": list(successful_responses.keys()),
                    "agent_responses": successful_responses
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Multi-agent response failed: {e}")
            # Fallback to sales agent
            return await self._single_agent_response(
                AgentType.SALES, query, user_context, conversation_id
            )

    async def _synthesize_responses(
        self,
        query: str,
        agent_responses: Dict[str, Dict[str, Any]],
        user_context: Dict[str, Any]
    ) -> str:
        """Synthesize multiple agent responses into coherent answer"""
        
        if len(agent_responses) == 1:
            return list(agent_responses.values())[0]["content"]
        
        # Create synthesis prompt
        synthesis_prompt = f"""
        Original Query: {query}
        
        Multiple AI agents have provided insights:
        
        """
        
        for agent_name, response in agent_responses.items():
            synthesis_prompt += f"""
        {agent_name.title()} Agent Response:
        {response['content']}
        
        """
        
        synthesis_prompt += """
        Please synthesize these responses into a comprehensive, coherent answer that:
        1. Addresses the original query completely
        2. Integrates insights from all agents
        3. Identifies any complementary or conflicting information
        4. Provides clear, actionable recommendations
        5. Maintains the expertise level appropriate for the user
        
        Synthesized Response:
        """
        
        try:
            # Use primary LLM for synthesis
            synthesis_response = await self.llm_router.route_query(
                messages=[{"role": "user", "content": synthesis_prompt}],
                agent_type="orchestrator",
                complexity=self.llm_router._assess_complexity([{"role": "user", "content": synthesis_prompt}])
            )
            
            return synthesis_response["content"]
            
        except Exception as e:
            logger.error(f"Response synthesis failed: {e}")
            # Fallback to concatenation
            return "\n\n".join([
                f"**{agent.title()} Perspective:**\n{response['content']}"
                for agent, response in agent_responses.items()
            ])

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents and services"""
        
        status = {
            "orchestrator_status": "healthy",
            "agents": {},
            "services": {},
            "graph_tools": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check agents
        for agent_type, agent in self.agents.items():
            try:
                agent_status = await agent.get_agent_status()
                status["agents"][agent_type.value] = agent_status
            except Exception as e:
                status["agents"][agent_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Check services
        try:
            knowledge_health = await self.knowledge_service.health_check()
            status["services"]["knowledge_graph"] = knowledge_health
        except Exception as e:
            status["services"]["knowledge_graph"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check vector service
        try:
            vector_stats = await self.vector_service.get_service_stats()
            status["services"]["vector_search"] = {
                "status": "healthy",
                "stats": vector_stats
            }
        except Exception as e:
            status["services"]["vector_search"] = {
                "status": "error", 
                "error": str(e)
            }
        
        # Check graph tools status
        try:
            status["graph_tools"] = await self._get_graph_tools_status()
        except Exception as e:
            status["graph_tools"] = {
                "status": "error",
                "error": str(e)
            }
        
        return status

    async def _get_graph_tools_status(self) -> Dict[str, Any]:
        """Get comprehensive graph tools status"""
        
        tools_status = {
            "status": "healthy",
            "neo4j_connection": "unknown",
            "redis_connection": "unknown", 
            "folk_api_connection": "unknown",
            "cache_stats": {},
            "available_tools": []
        }
        
        try:
            # Test Neo4j connection
            await self.neo4j_client.execute_query("RETURN 1")
            tools_status["neo4j_connection"] = "healthy"
        except Exception as e:
            tools_status["neo4j_connection"] = f"error: {str(e)}"
            tools_status["status"] = "degraded"
        
        # Test Redis connection
        if self.redis_client:
            try:
                await self.redis_client.ping()
                tools_status["redis_connection"] = "healthy"
                
                # Get cache stats if possible
                try:
                    info = await self.redis_client.info()
                    tools_status["cache_stats"] = {
                        "used_memory": info.get("used_memory_human", "unknown"),
                        "connected_clients": info.get("connected_clients", 0),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0)
                    }
                except:
                    pass
                    
            except Exception as e:
                tools_status["redis_connection"] = f"error: {str(e)}"
        else:
            tools_status["redis_connection"] = "disabled"
        
        # Test Folk API connection
        if self.folk_client:
            tools_status["folk_api_connection"] = "enabled"
            # Add Folk API health check if available
        else:
            tools_status["folk_api_connection"] = "disabled"
        
        # List available graph tools
        if self.graph_tools:
            tools_status["available_tools"] = [
                "get_person_details",
                "find_collaborators", 
                "get_organization_profile",
                "search_projects_by_criteria",
                "find_similar_projects",
                "get_project_team_details",
                "get_creative_concepts_for_project",
                "find_creative_references",
                "search_documents_by_content",
                "get_document_by_id",
                "extract_project_insights", 
                "get_network_connections"
            ]
        
        return tools_status

    async def cleanup(self):
        """Cleanup all resources including graph tools"""
        
        logger.info("Cleaning up AI orchestrator...")
        
        # Cleanup agents
        for agent in self.agents.values():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Agent cleanup failed: {e}")
        
        # Cleanup graph tools connections
        if self.graph_tools:
            logger.info("Cleaning up graph tools connections...")
            # Graph tools share the same connections, so we clean them up here
            
        # Cleanup Folk client if available
        if self.folk_client:
            try:
                # Folk client cleanup if it has async cleanup method
                if hasattr(self.folk_client, 'cleanup'):
                    await self.folk_client.cleanup()
                logger.info("Folk API client cleaned up")
            except Exception as e:
                logger.error(f"Folk client cleanup failed: {e}")
        
        # Cleanup services
        try:
            await self.vector_service.cleanup()
        except Exception as e:
            logger.error(f"Vector service cleanup failed: {e}")
        
        try:
            await self.neo4j_client.close()
        except Exception as e:
            logger.error(f"Neo4j cleanup failed: {e}")
        
        try:
            await self.redis_client.close()
        except Exception as e:
            logger.error(f"Redis cleanup failed: {e}")
        
        logger.info("AI orchestrator cleanup completed")