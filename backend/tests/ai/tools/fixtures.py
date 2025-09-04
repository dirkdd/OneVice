"""
Test Fixtures for Graph Tools Testing

Provides comprehensive mock data and fixtures for testing
GraphQueryTools and agent tool mixins.
"""

import pytest
import json
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

# Test data constants
TEST_PERSON_DATA = {
    "john_smith": {
        "personId": "test_person_001",
        "name": "John Smith",
        "title": "Director of Photography",
        "email": "john.smith@example.com",
        "bio": "Experienced cinematographer with 10+ years in film industry",
        "folkId": "folk_person_123",
        "isInternal": False,
        "organization": "Independent",
        "skills": ["Cinematography", "Lighting", "Camera Operation"],
        "unionStatus": "DGA Member"
    },
    "jane_doe": {
        "personId": "test_person_002", 
        "name": "Jane Doe",
        "title": "Creative Director",
        "email": "jane.doe@example.com",
        "bio": "Award-winning creative director specializing in commercial campaigns",
        "folkId": "folk_person_456",
        "isInternal": True,
        "organization": "OneVice Productions",
        "skills": ["Creative Direction", "Brand Strategy", "Art Direction"],
        "unionStatus": "Non-union"
    },
    "mike_johnson": {
        "personId": "test_person_003",
        "name": "Mike Johnson", 
        "title": "Producer",
        "email": "mike.johnson@example.com",
        "bio": "Executive producer with expertise in high-budget commercials",
        "folkId": "folk_person_789",
        "isInternal": False,
        "organization": "Johnson Media Group",
        "skills": ["Production Management", "Budget Planning", "Client Relations"],
        "unionStatus": "PGA Member"
    }
}

TEST_ORGANIZATION_DATA = {
    "nike": {
        "organizationId": "test_org_001",
        "name": "Nike",
        "type": "Client",
        "description": "Global sportswear and athletic brand",
        "folkId": "folk_org_123",
        "tier": "Enterprise",
        "industry": "Sports & Apparel"
    },
    "onevice": {
        "organizationId": "test_org_002",
        "name": "OneVice Productions",
        "type": "Production Company", 
        "description": "Creative production company specializing in commercials",
        "folkId": "folk_org_456",
        "tier": "Agency",
        "industry": "Production"
    },
    "spotify": {
        "organizationId": "test_org_003",
        "name": "Spotify",
        "type": "Client",
        "description": "Music streaming and media services provider",
        "folkId": "folk_org_789",
        "tier": "Enterprise", 
        "industry": "Music & Media"
    }
}

TEST_PROJECT_DATA = {
    "nike_campaign_2024": {
        "projectId": "test_project_001",
        "title": "Nike Air Max Campaign 2024",
        "description": "Launch campaign for new Air Max line",
        "type": "Commercial",
        "status": "Completed",
        "year": 2024,
        "budget": 500000,
        "client": "Nike",
        "createdAt": datetime.now() - timedelta(days=90),
        "startDate": datetime.now() - timedelta(days=60),
        "endDate": datetime.now() - timedelta(days=30)
    },
    "spotify_video": {
        "projectId": "test_project_002",
        "title": "Spotify Artist Spotlight",
        "description": "Music video for emerging artist campaign",
        "type": "Music Video",
        "status": "In Production",
        "year": 2024,
        "budget": 150000,
        "client": "Spotify",
        "createdAt": datetime.now() - timedelta(days=30),
        "startDate": datetime.now() - timedelta(days=15),
        "endDate": datetime.now() + timedelta(days=15)
    }
}

TEST_CREATIVE_CONCEPT_DATA = {
    "cinematic_style": {
        "name": "Cinematic Style",
        "category": "Visual Style",
        "description": "High-end cinematic approach with dramatic lighting",
        "tags": ["cinematic", "dramatic", "high-end"]
    },
    "documentary_approach": {
        "name": "Documentary Approach",
        "category": "Narrative Style", 
        "description": "Real people, authentic stories, natural lighting",
        "tags": ["documentary", "authentic", "real"]
    }
}

TEST_DEAL_DATA = {
    "nike_q4_deal": {
        "dealId": "test_deal_001",
        "name": "Nike Q4 Campaign Deal",
        "folkId": "folk_deal_123",
        "status": "won",
        "stage": "Closed Won",
        "value": 750000,
        "probability": 1.0,
        "expectedCloseDate": datetime.now() - timedelta(days=30),
        "contactPerson": "John Smith",
        "organization": "Nike"
    },
    "spotify_pitch": {
        "dealId": "test_deal_002", 
        "name": "Spotify Artist Series Pitch",
        "folkId": "folk_deal_456",
        "status": "contacted",
        "stage": "Initial Contact",
        "value": 200000,
        "probability": 0.3,
        "expectedCloseDate": datetime.now() + timedelta(days=45),
        "contactPerson": "Jane Doe",
        "organization": "Spotify"
    }
}

TEST_DOCUMENT_DATA = {
    "nike_creative_brief": {
        "documentId": "test_doc_001",
        "title": "Nike Air Max Creative Brief",
        "documentType": "Creative Brief",
        "content": "Creative brief outlining campaign objectives and visual direction",
        "sensitivityLevel": "INTERNAL",
        "projectId": "test_project_001",
        "createdAt": datetime.now() - timedelta(days=75)
    },
    "spotify_treatment": {
        "documentId": "test_doc_002",
        "title": "Spotify Artist Spotlight Treatment",
        "documentType": "Treatment",
        "content": "Detailed treatment for music video production approach",
        "sensitivityLevel": "CONFIDENTIAL", 
        "projectId": "test_project_002",
        "createdAt": datetime.now() - timedelta(days=25)
    }
}


class MockNeo4jResult:
    """Mock Neo4j query result"""
    
    def __init__(self, records: List[Dict[str, Any]], summary_data: Optional[Dict] = None):
        self.records = [MockNeo4jRecord(record) for record in records]
        self.summary = MockNeo4jSummary(summary_data or {})
    
    def __len__(self):
        return len(self.records)
    
    def __iter__(self):
        return iter(self.records)


class MockNeo4jRecord:
    """Mock Neo4j record"""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def __getitem__(self, key):
        return self._data[key]
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def data(self):
        return self._data
    
    def __contains__(self, key):
        return key in self._data


class MockNeo4jSummary:
    """Mock Neo4j result summary"""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self.counters = MockNeo4jCounters(data.get("counters", {}))
    
    def __getitem__(self, key):
        return self._data[key]
    
    def get(self, key, default=None):
        return self._data.get(key, default)


class MockNeo4jCounters:
    """Mock Neo4j summary counters"""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self._raw_data = data
    
    def __getitem__(self, key):
        return self._data.get(key, 0)
    
    def get(self, key, default=0):
        return self._data.get(key, default)


class MockRedisClient:
    """Mock Redis client for testing caching"""
    
    def __init__(self):
        self._data = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from mock cache"""
        return self._data.get(key)
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in mock cache"""
        self._data[key] = value
        return True
    
    async def delete(self, key: str) -> int:
        """Delete key from mock cache"""
        if key in self._data:
            del self._data[key]
            return 1
        return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in mock cache"""
        return key in self._data
    
    def clear_cache(self):
        """Clear all cached data (for testing)"""
        self._data.clear()


class MockFolkClient:
    """Mock Folk.app API client for testing"""
    
    def __init__(self):
        self.people_data = TEST_PERSON_DATA.copy()
        self.organization_data = TEST_ORGANIZATION_DATA.copy()
        self.deal_data = TEST_DEAL_DATA.copy()
    
    async def get_person_by_id(self, folk_id: str) -> Optional[Dict[str, Any]]:
        """Get person data by Folk ID"""
        for person_data in self.people_data.values():
            if person_data.get("folkId") == folk_id:
                return person_data
        return None
    
    async def get_organization_by_id(self, folk_id: str) -> Optional[Dict[str, Any]]:
        """Get organization data by Folk ID"""
        for org_data in self.organization_data.values():
            if org_data.get("folkId") == folk_id:
                return org_data
        return None
    
    async def get_deal_by_id(self, folk_id: str) -> Optional[Dict[str, Any]]:
        """Get deal data by Folk ID"""
        for deal_data in self.deal_data.values():
            if deal_data.get("folkId") == folk_id:
                return deal_data
        return None
    
    async def get_deal_status(self, folk_id: str) -> Optional[str]:
        """Get current deal status"""
        deal = await self.get_deal_by_id(folk_id)
        return deal.get("status") if deal else None


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client for testing"""
    client = AsyncMock()
    client.execute_query = AsyncMock()
    return client


@pytest.fixture  
def mock_redis_client():
    """Mock Redis client for testing"""
    return MockRedisClient()


@pytest.fixture
def mock_folk_client():
    """Mock Folk client for testing"""
    return MockFolkClient()


@pytest.fixture
def sample_person_data():
    """Sample person test data"""
    return TEST_PERSON_DATA.copy()


@pytest.fixture
def sample_organization_data():
    """Sample organization test data"""
    return TEST_ORGANIZATION_DATA.copy()


@pytest.fixture
def sample_project_data():
    """Sample project test data"""
    return TEST_PROJECT_DATA.copy()


@pytest.fixture
def sample_deal_data():
    """Sample deal test data"""  
    return TEST_DEAL_DATA.copy()


@pytest.fixture
def sample_document_data():
    """Sample document test data"""
    return TEST_DOCUMENT_DATA.copy()


@pytest.fixture
def sample_creative_concept_data():
    """Sample creative concept test data"""
    return TEST_CREATIVE_CONCEPT_DATA.copy()


def create_person_query_result(person_key: str, include_projects: bool = True) -> MockNeo4jResult:
    """Create mock Neo4j result for person queries"""
    
    person_data = TEST_PERSON_DATA[person_key].copy()
    
    if include_projects:
        # Add sample project data
        person_data["projects"] = [
            {
                "project": TEST_PROJECT_DATA["nike_campaign_2024"],
                "role": "Director of Photography",
                "startDate": "2024-01-15",
                "endDate": "2024-03-30"
            }
        ]
    
    return MockNeo4jResult([person_data])


def create_organization_query_result(org_key: str) -> MockNeo4jResult:
    """Create mock Neo4j result for organization queries"""
    
    org_data = TEST_ORGANIZATION_DATA[org_key].copy()
    
    # Add sample people at organization
    org_data["people"] = [
        {
            "person": TEST_PERSON_DATA["john_smith"]["name"],
            "title": TEST_PERSON_DATA["john_smith"]["title"],
            "email": TEST_PERSON_DATA["john_smith"]["email"]
        }
    ]
    
    return MockNeo4jResult([org_data])


def create_project_query_result(project_key: str, include_crew: bool = True) -> MockNeo4jResult:
    """Create mock Neo4j result for project queries"""
    
    project_data = TEST_PROJECT_DATA[project_key].copy()
    
    if include_crew:
        # Add sample crew data
        project_data["crew"] = [
            {
                "person": TEST_PERSON_DATA["john_smith"]["name"],
                "role": "Director of Photography",
                "personId": TEST_PERSON_DATA["john_smith"]["personId"]
            },
            {
                "person": TEST_PERSON_DATA["jane_doe"]["name"],
                "role": "Creative Director", 
                "personId": TEST_PERSON_DATA["jane_doe"]["personId"]
            }
        ]
    
    return MockNeo4jResult([project_data])


def create_deal_query_result(deal_key: str) -> MockNeo4jResult:
    """Create mock Neo4j result for deal queries"""
    
    deal_data = TEST_DEAL_DATA[deal_key].copy()
    return MockNeo4jResult([deal_data])


def create_empty_query_result() -> MockNeo4jResult:
    """Create mock Neo4j result with no records"""
    return MockNeo4jResult([])


def create_search_query_result(search_type: str, query: str) -> MockNeo4jResult:
    """Create mock Neo4j result for search queries"""
    
    if search_type == "person":
        if "john" in query.lower():
            return create_person_query_result("john_smith")
        elif "jane" in query.lower():
            return create_person_query_result("jane_doe")
    
    elif search_type == "organization":
        if "nike" in query.lower():
            return create_organization_query_result("nike")
        elif "spotify" in query.lower():
            return create_organization_query_result("spotify")
    
    elif search_type == "project":
        if "nike" in query.lower():
            return create_project_query_result("nike_campaign_2024")
        elif "spotify" in query.lower():
            return create_project_query_result("spotify_video")
    
    return create_empty_query_result()


# Performance test helpers
class PerformanceTracker:
    """Track query performance in tests"""
    
    def __init__(self):
        self.queries = []
    
    def record_query(self, query: str, execution_time: float, result_count: int):
        """Record query performance"""
        self.queries.append({
            "query": query,
            "execution_time": execution_time,
            "result_count": result_count,
            "timestamp": datetime.now()
        })
    
    def get_avg_execution_time(self) -> float:
        """Get average execution time across all queries"""
        if not self.queries:
            return 0.0
        return sum(q["execution_time"] for q in self.queries) / len(self.queries)
    
    def get_slowest_query(self) -> Optional[Dict[str, Any]]:
        """Get the slowest recorded query"""
        if not self.queries:
            return None
        return max(self.queries, key=lambda q: q["execution_time"])
    
    def reset(self):
        """Reset performance tracking"""
        self.queries.clear()


@pytest.fixture
def performance_tracker():
    """Performance tracking fixture"""
    return PerformanceTracker()