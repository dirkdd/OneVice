"""
Tests for sales intelligence agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.agents.sales_agent import SalesIntelligenceAgent
from app.ai.config import AIConfig


class TestSalesIntelligenceAgent:
    """Test sales intelligence agent functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock AI configuration."""
        config = MagicMock(spec=AIConfig)
        config.agent_configs = {
            "sales": {
                "name": "Sales Intelligence Agent",
                "max_memory_items": 50,
                "capabilities": ["lead_qualification", "project_intelligence", "competitive_analysis"]
            }
        }
        return config
    
    @pytest.fixture
    def sales_agent(self, mock_config):
        """Create sales agent instance."""
        with patch('app.ai.agents.base_agent.redis.Redis'), \
             patch('app.ai.agents.sales_agent.KnowledgeGraphService'):
            agent = SalesIntelligenceAgent(mock_config)
            agent.knowledge_service = AsyncMock()
            return agent
    
    def test_system_prompt_generation(self, sales_agent):
        """Test sales agent system prompt."""
        system_prompt = sales_agent._get_system_prompt()
        
        assert "Sales Intelligence Agent" in system_prompt
        assert "entertainment industry" in system_prompt.lower()
        assert "lead qualification" in system_prompt.lower()
        assert "project intelligence" in system_prompt.lower()
    
    @pytest.mark.asyncio
    async def test_qualify_lead_complete_info(self, sales_agent, sample_person_data):
        """Test lead qualification with complete information."""
        user_context = {"user_id": "test-user", "role": "producer"}
        
        # Mock knowledge service responses
        sales_agent.knowledge_service.find_similar_talent.return_value = [
            {"name": "Similar Director", "experience_level": "Senior", "score": 0.85}
        ]
        sales_agent.knowledge_service.project_intelligence.return_value = {
            "recent_projects": [{"title": "Similar Project", "budget": "20M"}],
            "market_trends": ["Increased demand for drama content"]
        }
        
        result = await sales_agent.qualify_lead(sample_person_data, user_context)
        
        assert "qualification_score" in result
        assert "strengths" in result
        assert "concerns" in result
        assert "recommendations" in result
        assert result["qualification_score"] >= 0.7  # Should be high for complete info
    
    @pytest.mark.asyncio
    async def test_qualify_lead_incomplete_info(self, sales_agent):
        """Test lead qualification with incomplete information."""
        incomplete_data = {
            "name": "John Unknown",
            "bio": "Some director"
        }
        user_context = {"user_id": "test-user", "role": "producer"}
        
        sales_agent.knowledge_service.find_similar_talent.return_value = []
        sales_agent.knowledge_service.project_intelligence.return_value = {
            "recent_projects": [],
            "market_trends": []
        }
        
        result = await sales_agent.qualify_lead(incomplete_data, user_context)
        
        assert result["qualification_score"] < 0.5  # Should be low for incomplete info
        assert "insufficient information" in result["concerns"][0].lower()
    
    @pytest.mark.asyncio
    async def test_project_intelligence_analysis(self, sales_agent, sample_project_data):
        """Test project intelligence analysis."""
        user_context = {"user_id": "test-user", "role": "producer"}
        
        # Mock knowledge service responses
        sales_agent.knowledge_service.find_similar_projects.return_value = [
            {"title": "Similar Drama", "budget_range": "10M-50M", "success_score": 0.8}
        ]
        sales_agent.knowledge_service.get_talent_for_project.return_value = [
            {"name": "Available Director", "availability": "Available", "rate": "500K"}
        ]
        sales_agent.knowledge_service.get_market_analysis.return_value = {
            "genre_trends": ["Drama trending up"],
            "budget_benchmarks": {"avg_budget": "25M"},
            "competition": ["3 similar projects in development"]
        }
        
        result = await sales_agent.project_intelligence(sample_project_data, user_context)
        
        assert "feasibility_score" in result
        assert "talent_availability" in result
        assert "market_analysis" in result
        assert "recommendations" in result
        assert len(result["talent_availability"]) > 0
    
    @pytest.mark.asyncio
    async def test_competitive_analysis(self, sales_agent, sample_company_data):
        """Test competitive analysis functionality."""
        user_context = {"user_id": "test-user", "role": "analyst"}
        
        # Mock knowledge service responses
        sales_agent.knowledge_service.find_competitors.return_value = [
            {"name": "Competitor Studios", "size": "Large", "recent_projects": 5}
        ]
        sales_agent.knowledge_service.get_market_share_data.return_value = {
            "market_share": 0.15,
            "growth_rate": 0.08,
            "key_strengths": ["Strong IP portfolio"]
        }
        
        result = await sales_agent.competitive_analysis(sample_company_data, user_context)
        
        assert "competitive_position" in result
        assert "market_opportunities" in result
        assert "threats" in result
        assert "strategic_recommendations" in result
    
    @pytest.mark.asyncio
    async def test_conversation_with_sales_context(self, sales_agent):
        """Test conversation processing with sales context."""
        query = "Tell me about the viability of producing a $20M drama film"
        user_context = {"user_id": "test-user", "role": "producer"}
        
        with patch.object(sales_agent, '_load_conversation_memory', return_value=[]), \
             patch.object(sales_agent, '_save_conversation_memory'), \
             patch.object(sales_agent, 'llm_router') as mock_router:
            
            mock_router.route_query.return_value = {
                "choices": [{
                    "message": {
                        "content": "Based on market analysis, $20M drama films have shown strong performance..."
                    }
                }]
            }
            
            response = await sales_agent.process(query, user_context)
            
            assert "content" in response
            assert "market analysis" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_lead_scoring_algorithm(self, sales_agent):
        """Test lead scoring algorithm."""
        # High-quality lead
        high_quality_lead = {
            "name": "Steven Spielberg",
            "bio": "Legendary director with 50+ years experience",
            "skills": ["Directing", "Producing", "Storytelling"],
            "location": "Los Angeles, CA",
            "experience_level": "Master",
            "union_status": "DGA Member",
            "recent_projects": ["Award-winning films"],
            "availability": "Available"
        }
        
        # Mock similar talent with high scores
        sales_agent.knowledge_service.find_similar_talent.return_value = [
            {"name": "Similar Legend", "experience_level": "Master", "score": 0.95}
        ]
        sales_agent.knowledge_service.project_intelligence.return_value = {
            "recent_projects": [{"title": "Blockbuster", "success": True}],
            "market_trends": ["High demand for experienced directors"]
        }
        
        result = await sales_agent.qualify_lead(high_quality_lead, {"user_id": "test"})
        
        # High-quality lead should score very high
        assert result["qualification_score"] >= 0.9
        assert len(result["strengths"]) >= 3
        assert len(result["concerns"]) <= 1
    
    @pytest.mark.asyncio
    async def test_union_compliance_check(self, sales_agent):
        """Test union compliance checking in lead qualification."""
        union_member_lead = {
            "name": "Union Director",
            "bio": "Experienced union director",
            "union_status": "DGA Member",
            "experience_level": "Senior"
        }
        
        non_union_lead = {
            "name": "Non-Union Director", 
            "bio": "Independent director",
            "union_status": "Non-Union",
            "experience_level": "Mid-Level"
        }
        
        # Mock responses
        sales_agent.knowledge_service.find_similar_talent.return_value = []
        sales_agent.knowledge_service.project_intelligence.return_value = {
            "recent_projects": [],
            "market_trends": []
        }
        
        union_result = await sales_agent.qualify_lead(union_member_lead, {"user_id": "test"})
        non_union_result = await sales_agent.qualify_lead(non_union_lead, {"user_id": "test"})
        
        # Union member should score higher for union compliance
        union_strengths = " ".join(union_result["strengths"]).lower()
        assert "union" in union_strengths or "dga" in union_strengths
        
        # Non-union should have union compliance as a concern
        non_union_concerns = " ".join(non_union_result["concerns"]).lower()
        assert "union" in non_union_concerns or "compliance" in non_union_concerns
    
    @pytest.mark.asyncio
    async def test_error_handling_in_analysis(self, sales_agent, sample_person_data):
        """Test error handling in analysis methods."""
        user_context = {"user_id": "test-user"}
        
        # Mock knowledge service to raise an error
        sales_agent.knowledge_service.find_similar_talent.side_effect = Exception("Database error")
        
        result = await sales_agent.qualify_lead(sample_person_data, user_context)
        
        # Should return a result even with errors, but with lower confidence
        assert "qualification_score" in result
        assert "error" in result["concerns"][0].lower() or result["qualification_score"] < 0.5