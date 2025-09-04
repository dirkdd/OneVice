"""
Integration Tests for Agent Tool Mixins

Tests the specialized tool mixins for CRM, Talent, and Analytics agents
to ensure proper tool inheritance and functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.ai.tools.tool_mixins import (
    CRMToolsMixin, TalentToolsMixin, AnalyticsToolsMixin, 
    SharedToolsMixin
)
from tests.ai.tools.fixtures import (
    MockNeo4jResult, MockRedisClient, MockFolkClient,
    create_person_query_result, create_organization_query_result,
    create_project_query_result, create_deal_query_result,
    TEST_PERSON_DATA, TEST_PROJECT_DATA, TEST_DEAL_DATA
)


# Test classes that inherit from mixins
class TestCRMAgent(CRMToolsMixin):
    """Test agent class for CRM tools testing"""
    
    def __init__(self):
        self.graph_tools = None


class TestTalentAgent(TalentToolsMixin):
    """Test agent class for Talent tools testing"""
    
    def __init__(self):
        self.graph_tools = None


class TestAnalyticsAgent(AnalyticsToolsMixin):
    """Test agent class for Analytics tools testing"""
    
    def __init__(self):
        self.graph_tools = None


class TestSharedAgent(SharedToolsMixin):
    """Test agent class for Shared tools testing"""
    
    def __init__(self):
        self.graph_tools = None


class TestCRMToolsMixin:
    """Test suite for CRM Tools Mixin"""
    
    @pytest.fixture
    def crm_agent(self, mock_neo4j_client, mock_redis_client, mock_folk_client):
        """Create CRM agent with mocked dependencies"""
        agent = TestCRMAgent()
        agent.init_crm_tools(mock_neo4j_client, mock_folk_client, mock_redis_client)
        return agent
    
    @pytest.mark.asyncio
    async def test_init_crm_tools(self, crm_agent):
        """Test CRM tools initialization"""
        
        # Verify tools were initialized
        assert crm_agent.graph_tools is not None
        assert hasattr(crm_agent.graph_tools, 'neo4j_client')
        assert hasattr(crm_agent.graph_tools, 'folk_client')
        assert hasattr(crm_agent.graph_tools, 'redis_client')
    
    @pytest.mark.asyncio
    async def test_get_lead_profile(self, crm_agent):
        """Test CRM-specific lead profile retrieval"""
        
        # Setup mock response
        crm_agent.graph_tools.get_person_details = AsyncMock()
        crm_agent.graph_tools.get_person_details.return_value = {
            "found": True,
            "name": "John Smith",
            "title": "Director of Photography",
            "email": "john.smith@example.com",
            "organization": "Independent",
            "projects": [{"project": "Nike Campaign", "role": "DP"}],
            "contact_owner": "Jane Doe"
        }
        
        # Execute test
        result = await crm_agent.get_lead_profile("John Smith")
        
        # Verify CRM-specific context was added
        assert result["found"] is True
        assert result["name"] == "John Smith"
        assert "lead_context" in result
        assert result["lead_context"]["is_warm_lead"] is True  # Has projects
        assert result["lead_context"]["has_internal_contact"] is True  # Has owner
        assert result["lead_context"]["organization_size"] == "individual"
    
    @pytest.mark.asyncio
    async def test_find_decision_makers(self, crm_agent):
        """Test finding decision makers at target organization"""
        
        # Setup mock response
        crm_agent.graph_tools.find_people_at_organization = AsyncMock()
        crm_agent.graph_tools.find_people_at_organization.return_value = {
            "found": True,
            "organization": "Nike",
            "people": [
                {"person": "John Director", "title": "Creative Director", "email": "john@nike.com"},
                {"person": "Jane Manager", "title": "Marketing Manager", "email": "jane@nike.com"},
                {"person": "Bob Assistant", "title": "Assistant", "email": "bob@nike.com"}
            ]
        }
        
        # Execute test
        result = await crm_agent.find_decision_makers("Nike")
        
        # Verify decision maker scoring
        assert result["found"] is True
        assert "decision_makers" in result
        assert result["dm_count"] == 3
        
        # Verify scoring logic
        decision_makers = result["decision_makers"]
        director = next(p for p in decision_makers if "director" in p["title"].lower())
        assert director["decision_maker_score"] == "high"
        
        manager = next(p for p in decision_makers if "manager" in p["title"].lower())
        assert manager["decision_maker_score"] == "high"
        
        assistant = next(p for p in decision_makers if "assistant" in p["title"].lower())
        assert assistant["decision_maker_score"] == "medium"
    
    @pytest.mark.asyncio
    async def test_get_deal_attribution(self, crm_agent):
        """Test deal sourcing attribution"""
        
        # Setup mock response
        crm_agent.graph_tools.get_deal_sourcer = AsyncMock()
        crm_agent.graph_tools.get_deal_sourcer.return_value = {
            "found": True,
            "deal": "Nike Q4 Deal",
            "sourcer": "Jane Doe",
            "sourced_date": "2024-01-15"
        }
        
        # Execute test
        result = await crm_agent.get_deal_attribution("Nike Q4 Deal")
        
        # Verify attribution data
        assert result["found"] is True
        assert result["deal"] == "Nike Q4 Deal"
        assert result["sourcer"] == "Jane Doe"
    
    @pytest.mark.asyncio
    async def test_get_live_deal_status(self, crm_agent):
        """Test real-time deal status retrieval"""
        
        # Setup mock response
        crm_agent.graph_tools.get_deal_details_with_live_status = AsyncMock()
        crm_agent.graph_tools.get_deal_details_with_live_status.return_value = {
            "found": True,
            "name": "Nike Q4 Deal",
            "cached_status": "contacted",
            "live_status": "meeting_scheduled",
            "status_sync": False
        }
        
        # Execute test
        result = await crm_agent.get_live_deal_status("Nike Q4 Deal")
        
        # Verify live status integration
        assert result["found"] is True
        assert result["cached_status"] == "contacted"
        assert result["live_status"] == "meeting_scheduled"
        assert result["status_sync"] is False


class TestTalentToolsMixin:
    """Test suite for Talent Tools Mixin"""
    
    @pytest.fixture
    def talent_agent(self, mock_neo4j_client, mock_redis_client, mock_folk_client):
        """Create Talent agent with mocked dependencies"""
        agent = TestTalentAgent()
        agent.init_talent_tools(mock_neo4j_client, mock_folk_client, mock_redis_client)
        return agent
    
    @pytest.mark.asyncio
    async def test_init_talent_tools(self, talent_agent):
        """Test Talent tools initialization"""
        
        # Verify tools were initialized
        assert talent_agent.graph_tools is not None
        assert hasattr(talent_agent.graph_tools, 'neo4j_client')
    
    @pytest.mark.asyncio
    async def test_get_talent_profile(self, talent_agent):
        """Test talent-specific profile retrieval"""
        
        # Setup mock response
        talent_agent.graph_tools.get_person_details = AsyncMock()
        talent_agent.graph_tools.get_person_details.return_value = {
            "found": True,
            "name": "John Smith",
            "title": "Director of Photography",
            "projects": [
                {"role": "Director", "startDate": "2024-01-01"},
                {"role": "Cinematographer", "startDate": "2023-06-01"},
                {"role": "Director", "startDate": "2022-03-01"},
                {"role": "Producer", "startDate": "2021-01-01"},
            ]
        }
        
        # Execute test
        result = await talent_agent.get_talent_profile("John Smith")
        
        # Verify talent-specific context
        assert result["found"] is True
        assert "talent_context" in result
        assert result["talent_context"]["experience_level"] == "mid"  # 4 projects
        assert result["talent_context"]["project_count"] == 4
        assert result["talent_context"]["versatility_score"] == 3  # 3 unique roles
        assert "Director" in result["talent_context"]["primary_roles"]
    
    @pytest.mark.asyncio
    async def test_find_crew_by_style(self, talent_agent):
        """Test finding crew experienced in specific creative styles"""
        
        # Setup mock responses
        talent_agent.graph_tools.find_projects_by_concept = AsyncMock()
        talent_agent.graph_tools.find_projects_by_concept.return_value = {
            "found": True,
            "concept": "Cinematic Style",
            "projects": [
                {"project": {"title": "Nike Campaign"}, "client": "Nike"}
            ]
        }
        
        talent_agent.graph_tools.get_project_details = AsyncMock()
        talent_agent.graph_tools.get_project_details.return_value = {
            "found": True,
            "title": "Nike Campaign",
            "crew": [
                {"person": "John Smith", "role": "Director"},
                {"person": "Jane Doe", "role": "Producer"}
            ]
        }
        
        # Execute test
        result = await talent_agent.find_crew_by_style("Cinematic Style", role="Director")
        
        # Verify style-based crew matching
        assert result["found"] is True
        assert result["concept"] == "Cinematic Style"
        assert result["role"] == "Director"
        assert len(result["crew"]) == 1  # Only Director filtered
        assert result["crew"][0]["name"] == "John Smith"
        assert result["crew"][0]["concept_experience"] == 1
    
    @pytest.mark.asyncio
    async def test_find_experienced_crew(self, talent_agent):
        """Test finding crew with specific client experience"""
        
        # Setup mock response
        talent_agent.graph_tools.find_contributors_on_client_projects = AsyncMock()
        talent_agent.graph_tools.find_contributors_on_client_projects.return_value = {
            "found": True,
            "role": "Director",
            "client": "Nike",
            "contributors": [
                {"person": "John Smith", "projects_count": 3}
            ]
        }
        
        # Execute test
        result = await talent_agent.find_experienced_crew("Nike", "Director")
        
        # Verify client experience matching
        assert result["found"] is True
        assert result["role"] == "Director"
        assert result["client"] == "Nike"
        assert len(result["contributors"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_project_crew_needs(self, talent_agent):
        """Test analyzing project crew composition"""
        
        # Setup mock response
        talent_agent.graph_tools.get_project_details = AsyncMock()
        talent_agent.graph_tools.get_project_details.return_value = {
            "found": True,
            "title": "Nike Campaign",
            "crew": [
                {"person": "John Smith", "role": "Director"},
                {"person": "Jane Doe", "role": "Producer"},
                {"person": "Bob Johnson", "role": "Producer"}  # Duplicate role
            ]
        }
        
        # Execute test
        result = await talent_agent.get_project_crew_needs("Nike Campaign")
        
        # Verify crew analysis
        assert result["found"] is True
        assert "crew_analysis" in result
        
        analysis = result["crew_analysis"]
        assert analysis["crew_size"] == 3
        assert analysis["role_distribution"]["Producer"] == 2  # 2 producers
        assert "Cinematographer" in analysis["missing_standard_roles"]
        assert analysis["completion_score"] == 0.5  # 2/4 standard roles


class TestAnalyticsToolsMixin:
    """Test suite for Analytics Tools Mixin"""
    
    @pytest.fixture
    def analytics_agent(self, mock_neo4j_client, mock_redis_client, mock_folk_client):
        """Create Analytics agent with mocked dependencies"""
        agent = TestAnalyticsAgent()
        agent.init_analytics_tools(mock_neo4j_client, mock_folk_client, mock_redis_client)
        return agent
    
    @pytest.mark.asyncio
    async def test_init_analytics_tools(self, analytics_agent):
        """Test Analytics tools initialization"""
        
        # Verify tools were initialized
        assert analytics_agent.graph_tools is not None
    
    @pytest.mark.asyncio
    async def test_analyze_team_performance(self, analytics_agent):
        """Test team member performance analysis"""
        
        # Setup mock response
        analytics_agent.graph_tools.get_person_details = AsyncMock()
        analytics_agent.graph_tools.get_person_details.return_value = {
            "found": True,
            "name": "John Smith",
            "projects": [
                {"role": "Director", "startDate": "2024-01-01"},
                {"role": "Producer", "startDate": "2023-01-01"},
                {"role": "Director", "startDate": "2022-01-01"}
            ]
        }
        
        # Execute test
        result = await analytics_agent.analyze_team_performance("John Smith")
        
        # Verify performance analysis
        assert result["found"] is True
        assert "performance_metrics" in result
        
        metrics = result["performance_metrics"]
        assert metrics["total_projects"] == 3
        assert metrics["roles_diversity"] == 2  # Director and Producer
        assert metrics["recent_projects"] == 1  # 2024 projects
    
    @pytest.mark.asyncio
    async def test_analyze_creative_trends(self, analytics_agent):
        """Test creative concept trend analysis"""
        
        # Setup mock response
        analytics_agent.graph_tools.find_projects_by_concept = AsyncMock()
        analytics_agent.graph_tools.find_projects_by_concept.return_value = {
            "found": True,
            "concept": "Cinematic Style",
            "projects": [
                {"project": {"year": 2024}, "client": "Nike"},
                {"project": {"year": 2023}, "client": "Nike"},
                {"project": {"year": 2024}, "client": "Spotify"}
            ]
        }
        
        # Execute test
        result = await analytics_agent.analyze_creative_trends("Cinematic Style")
        
        # Verify trend analysis
        assert result["found"] is True
        assert "trend_analysis" in result
        
        analysis = result["trend_analysis"]
        assert analysis["year_distribution"] == {2024: 2, 2023: 1}
        assert analysis["client_distribution"] == {"Nike": 2, "Spotify": 1}
        assert analysis["trend_direction"] == "growing"  # Has 2024 projects
    
    @pytest.mark.asyncio
    async def test_analyze_vendor_performance(self, analytics_agent):
        """Test vendor performance analysis"""
        
        # Setup mock response
        analytics_agent.graph_tools.get_project_vendors = AsyncMock()
        analytics_agent.graph_tools.get_project_vendors.return_value = {
            "found": True,
            "project": "Nike Campaign",
            "vendors": [
                {"vendor": "Equipment Co", "cost": 25000},
                {"vendor": "Location Services", "cost": 15000}
            ],
            "total_vendor_cost": 40000
        }
        
        # Execute test
        result = await analytics_agent.analyze_vendor_performance("Nike Campaign")
        
        # Verify vendor analysis
        assert result["found"] is True
        assert result["project"] == "Nike Campaign"
        assert len(result["vendors"]) == 2
        assert result["total_vendor_cost"] == 40000
    
    @pytest.mark.asyncio
    async def test_search_project_documents(self, analytics_agent):
        """Test project document search"""
        
        # Setup mock response
        analytics_agent.graph_tools.search_documents_full_text = AsyncMock()
        analytics_agent.graph_tools.search_documents_full_text.return_value = {
            "found": True,
            "search_query": "creative brief",
            "documents": [
                {"title": "Nike Creative Brief", "relevance_score": 0.95}
            ]
        }
        
        # Execute test
        result = await analytics_agent.search_project_documents("creative brief")
        
        # Verify document search
        assert result["found"] is True
        assert result["search_query"] == "creative brief"
        assert len(result["documents"]) == 1


class TestSharedToolsMixin:
    """Test suite for Shared Tools Mixin"""
    
    @pytest.fixture
    def shared_agent(self, mock_neo4j_client, mock_redis_client, mock_folk_client):
        """Create Shared agent with mocked dependencies"""
        agent = TestSharedAgent()
        agent.init_all_tools(mock_neo4j_client, mock_folk_client, mock_redis_client)
        return agent
    
    @pytest.mark.asyncio
    async def test_init_all_tools(self, shared_agent):
        """Test that shared agent has access to all tool types"""
        
        # Verify tools were initialized
        assert shared_agent.graph_tools is not None
        
        # Verify shared agent inherits from all mixins
        assert isinstance(shared_agent, CRMToolsMixin)
        assert isinstance(shared_agent, TalentToolsMixin)
        assert isinstance(shared_agent, AnalyticsToolsMixin)
    
    @pytest.mark.asyncio
    async def test_shared_agent_has_all_tool_methods(self, shared_agent):
        """Test that shared agent can access methods from all mixins"""
        
        # Verify CRM methods
        assert hasattr(shared_agent, 'get_lead_profile')
        assert hasattr(shared_agent, 'find_decision_makers')
        
        # Verify Talent methods
        assert hasattr(shared_agent, 'get_talent_profile')
        assert hasattr(shared_agent, 'find_crew_by_style')
        
        # Verify Analytics methods
        assert hasattr(shared_agent, 'analyze_team_performance')
        assert hasattr(shared_agent, 'analyze_creative_trends')


class TestToolMixinErrors:
    """Test error handling in tool mixins"""
    
    @pytest.mark.asyncio
    async def test_uninitialized_tools_error(self):
        """Test error when trying to use tools before initialization"""
        
        agent = TestCRMAgent()
        # Don't initialize tools
        
        # Should raise error when trying to use tools
        with pytest.raises(AttributeError):
            await agent.get_lead_profile("John Smith")
    
    @pytest.mark.asyncio
    async def test_graph_tools_error_propagation(self, mock_neo4j_client, mock_redis_client, mock_folk_client):
        """Test that errors from GraphQueryTools are properly propagated"""
        
        agent = TestCRMAgent()
        agent.init_crm_tools(mock_neo4j_client, mock_folk_client, mock_redis_client)
        
        # Setup mock to raise exception
        agent.graph_tools.get_person_details = AsyncMock()
        agent.graph_tools.get_person_details.side_effect = Exception("Graph query failed")
        
        # Execute test and verify exception handling
        with pytest.raises(Exception, match="Graph query failed"):
            await agent.get_lead_profile("John Smith")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])