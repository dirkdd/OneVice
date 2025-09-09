"""
Unit Tests for GraphQueryTools

Comprehensive test suite for all 12 graph query tool methods
with mock Neo4j data and performance validation.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.ai.tools.graph_tools import GraphQueryTools
from tests.ai.tools.fixtures import (
    MockNeo4jResult, MockRedisClient, MockFolkClient,
    create_person_query_result, create_organization_query_result,
    create_project_query_result, create_deal_query_result,
    create_empty_query_result, create_search_query_result,
    TEST_PERSON_DATA, TEST_ORGANIZATION_DATA, TEST_PROJECT_DATA,
    TEST_DEAL_DATA, TEST_DOCUMENT_DATA
)


class TestGraphQueryTools:
    """Test suite for GraphQueryTools class"""
    
    @pytest.fixture
    async def graph_tools(self, mock_neo4j_client, mock_redis_client, mock_folk_client):
        """Initialize GraphQueryTools with mocked dependencies"""
        return GraphQueryTools(
            neo4j_client=mock_neo4j_client,
            folk_client=mock_folk_client,
            redis_client=mock_redis_client
        )
    
    
    # ================================================================================
    # PERSON QUERY TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_get_person_details_success(self, graph_tools, mock_neo4j_client):
        """Test successful person details retrieval"""
        
        # Setup mock response
        mock_neo4j_client.execute_query.return_value = create_person_query_result("john_smith")
        
        # Execute test
        result = await graph_tools.get_person_details("John Smith")
        
        # Verify results
        assert result["found"] is True
        assert result["name"] == "John Smith"
        assert result["title"] == "Director of Photography" 
        assert result["email"] == "john.smith@example.com"
        assert "projects" in result
        
        # Verify query was called
        mock_neo4j_client.execute_query.assert_called_once()
        call_args = mock_neo4j_client.execute_query.call_args[0][0]
        assert "MATCH (p:Person" in call_args
        assert "John Smith" in call_args
    
    @pytest.mark.asyncio
    async def test_get_person_details_not_found(self, graph_tools, mock_neo4j_client):
        """Test person not found scenario"""
        
        # Setup mock response
        mock_neo4j_client.execute_query.return_value = create_empty_query_result()
        
        # Execute test
        result = await graph_tools.get_person_details("Nonexistent Person")
        
        # Verify results
        assert result["found"] is False
        assert "error" in result
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_person_details_with_caching(self, graph_tools, mock_neo4j_client, mock_redis_client):
        """Test person details with Redis caching"""
        
        # Setup cached data
        cached_data = {
            "found": True,
            "name": "John Smith",
            "title": "Director of Photography",
            "cached": True
        }
        await mock_redis_client.set("person_details:john smith", json.dumps(cached_data))
        
        # Execute test
        result = await graph_tools.get_person_details("John Smith")
        
        # Verify cached result returned
        assert result["found"] is True
        assert result["cached"] is True
        assert result["name"] == "John Smith"
        
        # Verify Neo4j was not called
        mock_neo4j_client.execute_query.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_find_people_at_organization(self, graph_tools, mock_neo4j_client):
        """Test finding people at an organization"""
        
        # Setup mock response
        org_result = create_organization_query_result("nike")
        mock_neo4j_client.execute_query.return_value = org_result
        
        # Execute test
        result = await graph_tools.find_people_at_organization("Nike")
        
        # Verify results
        assert result["found"] is True
        assert result["organization"] == "Nike"
        assert len(result["people"]) > 0
        assert result["people"][0]["person"] == "John Smith"
    
    
    # ================================================================================
    # PROJECT QUERY TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_get_project_details_success(self, graph_tools, mock_neo4j_client):
        """Test successful project details retrieval"""
        
        # Setup mock response
        mock_neo4j_client.execute_query.return_value = create_project_query_result("nike_campaign_2024")
        
        # Execute test
        result = await graph_tools.get_project_details("Nike Air Max Campaign 2024")
        
        # Verify results
        assert result["found"] is True
        assert result["title"] == "Nike Air Max Campaign 2024"
        assert result["type"] == "Commercial"
        assert result["status"] == "Completed"
        assert "crew" in result
        assert len(result["crew"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_project_vendors(self, graph_tools, mock_neo4j_client):
        """Test getting project vendor information"""
        
        # Setup mock response with vendor data
        vendor_data = [{
            "project": "Nike Air Max Campaign 2024",
            "vendors": [
                {"vendor": "Equipment Rental Co", "type": "Equipment", "cost": 25000},
                {"vendor": "Location Services", "type": "Location", "cost": 15000}
            ],
            "total_vendor_cost": 40000,
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(vendor_data)
        
        # Execute test
        result = await graph_tools.get_project_vendors("Nike Air Max Campaign 2024")
        
        # Verify results
        assert result["found"] is True
        assert result["project"] == "Nike Air Max Campaign 2024"
        assert len(result["vendors"]) == 2
        assert result["total_vendor_cost"] == 40000
    
    
    # ================================================================================
    # CREATIVE CONCEPT TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_find_projects_by_concept(self, graph_tools, mock_neo4j_client):
        """Test finding projects by creative concept"""
        
        # Setup mock response
        concept_projects = [{
            "concept": "Cinematic Style",
            "projects": [
                {
                    "project": TEST_PROJECT_DATA["nike_campaign_2024"],
                    "client": "Nike",
                    "relationship_strength": 0.95
                }
            ],
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(concept_projects)
        
        # Execute test
        result = await graph_tools.find_projects_by_concept("Cinematic Style")
        
        # Verify results
        assert result["found"] is True
        assert result["concept"] == "Cinematic Style" 
        assert len(result["projects"]) == 1
        assert result["projects"][0]["client"] == "Nike"
    
    @pytest.mark.asyncio
    async def test_find_projects_by_concept_with_related(self, graph_tools, mock_neo4j_client):
        """Test finding projects by concept with related concepts"""
        
        # Setup mock response for related concepts
        concept_projects = [{
            "concept": "Cinematic Style",
            "projects": [
                {"project": TEST_PROJECT_DATA["nike_campaign_2024"], "client": "Nike"}
            ],
            "related_concepts": ["Documentary Approach", "High-end Production"],
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(concept_projects)
        
        # Execute test
        result = await graph_tools.find_projects_by_concept("Cinematic Style", include_related=True)
        
        # Verify results
        assert result["found"] is True
        assert "related_concepts" in result
        assert len(result["related_concepts"]) == 2
    
    
    # ================================================================================
    # DEAL AND CRM TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_get_deal_sourcer(self, graph_tools, mock_neo4j_client):
        """Test getting deal sourcing attribution"""
        
        # Setup mock response
        deal_data = [{
            "deal": "Nike Q4 Campaign Deal",
            "sourcer": "Jane Doe",
            "sourcer_title": "Creative Director",
            "sourced_date": "2024-01-15",
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(deal_data)
        
        # Execute test
        result = await graph_tools.get_deal_sourcer("Nike Q4 Campaign Deal")
        
        # Verify results
        assert result["found"] is True
        assert result["deal"] == "Nike Q4 Campaign Deal"
        assert result["sourcer"] == "Jane Doe"
        assert result["sourcer_title"] == "Creative Director"
    
    @pytest.mark.asyncio
    async def test_get_deal_details_with_live_status(self, graph_tools, mock_neo4j_client, mock_folk_client):
        """Test getting deal details with live Folk API status"""
        
        # Setup Neo4j mock response
        deal_data = [{
            "dealId": "test_deal_001",
            "name": "Nike Q4 Campaign Deal",
            "folkId": "folk_deal_123",
            "status": "won",  # Cached status
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(deal_data)
        
        # Execute test
        result = await graph_tools.get_deal_details_with_live_status("Nike Q4 Campaign Deal")
        
        # Verify results
        assert result["found"] is True
        assert result["name"] == "Nike Q4 Campaign Deal"
        assert result["cached_status"] == "won"
        assert result["live_status"] == "won"  # From mock Folk client
        assert result["status_sync"] is True
    
    
    # ================================================================================
    # CONTRIBUTOR SEARCH TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_find_contributors_on_client_projects(self, graph_tools, mock_neo4j_client):
        """Test finding contributors who worked on client projects"""
        
        # Setup mock response
        contributor_data = [{
            "role": "Director",
            "client": "Nike",
            "contributors": [
                {
                    "person": "John Smith",
                    "title": "Director of Photography",
                    "projects_count": 3,
                    "latest_project": "Nike Air Max Campaign 2024"
                }
            ],
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(contributor_data)
        
        # Execute test
        result = await graph_tools.find_contributors_on_client_projects("Director", "Nike")
        
        # Verify results
        assert result["found"] is True
        assert result["role"] == "Director"
        assert result["client"] == "Nike"
        assert len(result["contributors"]) == 1
        assert result["contributors"][0]["projects_count"] == 3
    
    
    # ================================================================================
    # DOCUMENT SEARCH TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_search_documents_full_text(self, graph_tools, mock_neo4j_client):
        """Test full-text document search"""
        
        # Setup mock response
        document_results = [{
            "documents": [
                {
                    "documentId": "test_doc_001",
                    "title": "Nike Air Max Creative Brief",
                    "content": "Creative brief outlining campaign objectives",
                    "relevance_score": 0.95
                }
            ],
            "search_query": "creative brief nike",
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(document_results)
        
        # Execute test
        result = await graph_tools.search_documents_full_text("creative brief nike")
        
        # Verify results
        assert result["found"] is True
        assert result["search_query"] == "creative brief nike"
        assert len(result["documents"]) == 1
        assert result["documents"][0]["title"] == "Nike Air Max Creative Brief"
    
    @pytest.mark.asyncio
    async def test_find_documents_for_project(self, graph_tools, mock_neo4j_client):
        """Test finding all documents for a specific project"""
        
        # Setup mock response
        project_docs = [{
            "project": "Nike Air Max Campaign 2024",
            "documents": [
                {
                    "documentId": "test_doc_001",
                    "title": "Nike Air Max Creative Brief",
                    "documentType": "Creative Brief",
                    "sensitivityLevel": "INTERNAL"
                }
            ],
            "document_count": 1,
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(project_docs)
        
        # Execute test
        result = await graph_tools.find_documents_for_project("Nike Air Max Campaign 2024")
        
        # Verify results
        assert result["found"] is True
        assert result["project"] == "Nike Air Max Campaign 2024"
        assert result["document_count"] == 1
        assert len(result["documents"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_document_profile_details(self, graph_tools, mock_neo4j_client):
        """Test getting detailed document profile information"""
        
        # Setup mock response
        doc_profile = [{
            "documentId": "test_doc_001",
            "title": "Nike Air Max Creative Brief",
            "profile": {
                "word_count": 1500,
                "key_topics": ["creative direction", "brand strategy", "visual style"],
                "sentiment": "positive",
                "complexity_score": 0.7
            },
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(doc_profile)
        
        # Execute test
        result = await graph_tools.get_document_profile_details("test_doc_001")
        
        # Verify results
        assert result["found"] is True
        assert result["documentId"] == "test_doc_001"
        assert "profile" in result
        assert result["profile"]["word_count"] == 1500
        assert len(result["profile"]["key_topics"]) == 3
    
    
    # ================================================================================
    # ERROR HANDLING TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_neo4j_connection_error(self, graph_tools, mock_neo4j_client):
        """Test handling Neo4j connection errors"""
        
        # Setup mock to raise exception
        mock_neo4j_client.execute_query.side_effect = Exception("Connection failed")
        
        # Execute test
        result = await graph_tools.get_person_details("John Smith")
        
        # Verify error handling
        assert result["found"] is False
        assert "error" in result
        assert "Connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_redis_cache_error_graceful_fallback(self, graph_tools, mock_neo4j_client, mock_redis_client):
        """Test graceful fallback when Redis caching fails"""
        
        # Setup Redis to fail
        mock_redis_client.get = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        # Setup Neo4j success response
        mock_neo4j_client.execute_query.return_value = create_person_query_result("john_smith")
        
        # Execute test
        result = await graph_tools.get_person_details("John Smith")
        
        # Verify fallback to Neo4j worked
        assert result["found"] is True
        assert result["name"] == "John Smith"
        
        # Verify Neo4j was called despite Redis error
        mock_neo4j_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_folk_api_error_graceful_fallback(self, graph_tools, mock_neo4j_client, mock_folk_client):
        """Test graceful fallback when Folk API fails"""
        
        # Setup Neo4j response
        deal_data = [{
            "name": "Nike Q4 Campaign Deal",
            "folkId": "folk_deal_123",
            "status": "won",
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(deal_data)
        
        # Setup Folk API to fail
        mock_folk_client.get_deal_status = AsyncMock(side_effect=Exception("Folk API error"))
        
        # Execute test
        result = await graph_tools.get_deal_details_with_live_status("Nike Q4 Campaign Deal")
        
        # Verify graceful degradation
        assert result["found"] is True
        assert result["name"] == "Nike Q4 Campaign Deal"
        assert result["cached_status"] == "won"
        assert "live_status_error" in result
    
    
    # ================================================================================
    # PERFORMANCE TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_query_performance_tracking(self, graph_tools, mock_neo4j_client, performance_tracker):
        """Test query performance is within acceptable limits"""
        
        import time
        
        # Setup mock with slight delay to simulate real query
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms delay
            return create_person_query_result("john_smith")
        
        mock_neo4j_client.execute_query.side_effect = slow_query
        
        # Execute test with timing
        start_time = time.time()
        result = await graph_tools.get_person_details("John Smith")
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Verify performance
        assert result["found"] is True
        assert execution_time < 100  # Should be under 100ms
        
        # Track performance
        performance_tracker.record_query("get_person_details", execution_time, 1)
    
    @pytest.mark.asyncio
    async def test_caching_performance_improvement(self, graph_tools, mock_neo4j_client, mock_redis_client):
        """Test that caching improves query performance"""
        
        import time
        
        # Setup Neo4j with delay
        async def slow_neo4j_query(*args, **kwargs):
            await asyncio.sleep(0.02)  # 20ms delay
            return create_person_query_result("john_smith")
        
        mock_neo4j_client.execute_query.side_effect = slow_neo4j_query
        
        # First query (uncached) - should be slower
        start_time = time.time()
        result1 = await graph_tools.get_person_details("John Smith")
        first_query_time = (time.time() - start_time) * 1000
        
        # Second query (cached) - should be much faster
        start_time = time.time()
        result2 = await graph_tools.get_person_details("John Smith")
        second_query_time = (time.time() - start_time) * 1000
        
        # Verify caching worked
        assert result1["found"] is True
        assert result2["found"] is True
        assert second_query_time < first_query_time  # Cached should be faster
        
        # Verify Neo4j was called only once
        assert mock_neo4j_client.execute_query.call_count == 1
    
    
    # ================================================================================
    # INTEGRATION TESTS
    # ================================================================================
    
    @pytest.mark.asyncio
    async def test_hybrid_folk_neo4j_integration(self, graph_tools, mock_neo4j_client, mock_folk_client):
        """Test integration between Neo4j graph data and Folk API live data"""
        
        # Setup Neo4j response with Folk ID
        person_data = [{
            "name": "John Smith",
            "folkId": "folk_person_123",
            "title": "Director of Photography",
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(person_data)
        
        # Execute test
        result = await graph_tools.get_person_details("John Smith")
        
        # Verify hybrid data integration
        assert result["found"] is True
        assert result["name"] == "John Smith"
        assert result["folkId"] == "folk_person_123"
        
        # Verify Neo4j was queried
        mock_neo4j_client.execute_query.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_complex_multi_hop_query(self, graph_tools, mock_neo4j_client):
        """Test complex multi-hop graph traversal queries"""
        
        # Setup mock response for complex query
        complex_result = [{
            "path": "Person -> Project -> Client -> Other Projects",
            "person": "John Smith",
            "client_projects": [
                {
                    "project": "Nike Air Max Campaign 2024",
                    "client": "Nike",
                    "other_nike_projects": 3
                }
            ],
            "found": True
        }]
        mock_neo4j_client.execute_query.return_value = MockNeo4jResult(complex_result)
        
        # Execute complex query through contributor search
        result = await graph_tools.find_contributors_on_client_projects("Director", "Nike")
        
        # Verify complex query handling
        assert result["found"] is True
        assert "contributors" in result
        
        # Verify appropriate Cypher query was generated
        call_args = mock_neo4j_client.execute_query.call_args[0][0]
        assert "MATCH" in call_args
        assert "-[:" in call_args  # Should contain relationship patterns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])