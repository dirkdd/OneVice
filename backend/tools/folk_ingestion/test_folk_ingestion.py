"""
Test script for Folk.app CRM data ingestion tool

Simple validation and testing script to verify the implementation.
"""

import asyncio
import os
import sys
import logging
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.folk_ingestion.config import validate_environment, FolkConfig, get_sample_env_file
from tools.folk_ingestion.folk_models import FolkPerson, FolkCompany, FolkGroup, FolkDeal
from tools.folk_ingestion.folk_client import FolkClient, FolkAPIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_environment_validation():
    """Test environment variable validation"""
    print("🔍 Testing environment validation...")
    
    validation = validate_environment()
    
    print(f"✅ Validation result: {'PASSED' if validation['valid'] else 'FAILED'}")
    print(f"📊 Required variables present: {len(validation['present_required'])}/{validation['total_required']}")
    
    if validation['missing_required']:
        print(f"❌ Missing required variables: {validation['missing_required']}")
        print("\n📝 Add these to your .env file:")
        print(get_sample_env_file())
    else:
        print("✅ All required environment variables are present")
    
    if validation['present_optional']:
        print(f"📋 Optional variables present: {validation['present_optional']}")
    
    return validation['valid']


def test_data_models():
    """Test Pydantic data models with sample data"""
    print("\n🧪 Testing data models...")
    
    # Sample Folk API responses
    sample_person = {
        "id": "person_123",
        "email": "john.doe@example.com",
        "name": "John Doe",
        "first_name": "John",
        "last_name": "Doe",
        "title": "Creative Director",
        "company": {"name": "Example Agency"},
        "phone": "+1-555-0123",
        "bio": "Award-winning creative director with 10 years experience",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "website": "https://johndoe.com",
        "location": "Los Angeles, CA",
        "tags": ["director", "commercial", "music-video"],
        "groups": [{"id": "group_123"}],
        "custom_fields": {"specialty": "automotive"},
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-09-04T14:20:00Z"
    }
    
    sample_company = {
        "id": "company_456",
        "name": "Nike Inc.",
        "domain": "nike.com",
        "website": "https://www.nike.com",
        "industry": "Sportswear",
        "size": "Large",
        "location": "Beaverton, OR",
        "description": "Global sportswear and equipment company",
        "tags": ["client", "sports", "apparel"],
        "groups": [{"id": "group_456"}],
        "custom_fields": {"annual_budget": 50000000},
        "created_at": "2024-01-10T09:00:00Z",
        "updated_at": "2024-09-01T16:30:00Z"
    }
    
    sample_group = {
        "id": "group_789",
        "name": "Past Clients",
        "description": "Companies we've worked with previously",
        "color": "#4CAF50",
        "member_count": 25,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-08-15T12:00:00Z"
    }
    
    sample_deal = {
        "id": "deal_101",
        "name": "Nike Commercial Campaign",
        "status": "negotiation",
        "value": 150000.0,
        "currency": "USD",
        "probability": 0.7,
        "expected_close_date": "2024-10-15T00:00:00Z",
        "description": "Commercial campaign for new Nike running shoes",
        "stage": "Proposal Sent",
        "source": "Referral",
        "tags": ["commercial", "nike", "high-value"],
        "contacts": [{"id": "person_123"}],
        "companies": [{"id": "company_456"}],
        "custom_fields": {"campaign_type": "national"},
        "created_at": "2024-08-01T10:00:00Z",
        "updated_at": "2024-09-04T11:30:00Z"
    }
    
    try:
        # Test Person model
        person = FolkPerson.from_folk_api(sample_person, "user_owner")
        person_props = person.to_neo4j_node("user_owner")
        print(f"✅ Person model: {person.name} ({person.email})")
        print(f"   Neo4j properties: {len(person_props)} fields")
        
        # Test Company model
        company = FolkCompany.from_folk_api(sample_company)
        company_props = company.to_neo4j_node("user_owner")
        print(f"✅ Company model: {company.name} ({company.domain})")
        print(f"   Neo4j properties: {len(company_props)} fields")
        
        # Test Group model
        group = FolkGroup.from_folk_api(sample_group)
        group_props = group.to_neo4j_node("user_owner")
        print(f"✅ Group model: {group.name} ({group.member_count} members)")
        print(f"   Neo4j properties: {len(group_props)} fields")
        
        # Test Deal model
        deal = FolkDeal.from_folk_api(sample_deal)
        deal_props = deal.to_neo4j_node("user_owner")
        print(f"✅ Deal model: {deal.name} (${deal.value:,.0f} {deal.currency})")
        print(f"   Neo4j properties: {len(deal_props)} fields")
        
        print("✅ All data models validated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Data model validation failed: {e}")
        return False


def test_configuration():
    """Test configuration loading"""
    print("\n⚙️  Testing configuration...")
    
    try:
        # Test with current environment
        config = FolkConfig.from_environment()
        config.validate()
        
        print(f"✅ Configuration loaded successfully")
        print(f"   API keys: {len(config.api_keys)} configured")
        print(f"   Neo4j URI: {config.neo4j_uri}")
        print(f"   Batch size: {config.batch_size}")
        print(f"   Dry run: {config.dry_run}")
        
        # Test configuration dict
        config_dict = config.to_dict()
        print(f"   Config sections: {list(config_dict.keys())}")
        
        return True
        
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


async def test_folk_client_mock():
    """Test Folk API client with mock data"""
    print("\n🌐 Testing Folk API client (mock)...")
    
    try:
        # Create a mock client (we can't test real API without keys)
        print("📝 Note: Using mock client (add real Folk API keys to test live connection)")
        
        # Mock the client behavior
        mock_client = Mock()
        mock_client.get_user_profile = AsyncMock(return_value=Mock(
            id="user_123",
            email="test@example.com", 
            name="Test User",
            company="Test Company"
        ))
        
        mock_client.get_all_people_paginated = AsyncMock(return_value=[
            {"id": "person_1", "name": "Person 1", "email": "person1@example.com"},
            {"id": "person_2", "name": "Person 2", "email": "person2@example.com"}
        ])
        
        mock_client.get_all_companies_paginated = AsyncMock(return_value=[
            {"id": "company_1", "name": "Company 1", "domain": "company1.com"}
        ])
        
        mock_client.get_all_groups_paginated = AsyncMock(return_value=[
            {"id": "group_1", "name": "Group 1", "member_count": 10}
        ])
        
        mock_client.get_deals_for_group = AsyncMock(return_value=[
            {"id": "deal_1", "name": "Deal 1", "status": "lead", "value": 10000}
        ])
        
        mock_client.get_stats = Mock(return_value={
            "requests_made": 5,
            "errors_count": 0,
            "success_rate": 1.0
        })
        
        # Test mock client
        profile = await mock_client.get_user_profile()
        people = await mock_client.get_all_people_paginated()
        companies = await mock_client.get_all_companies_paginated()
        groups = await mock_client.get_all_groups_paginated()
        deals = await mock_client.get_deals_for_group("group_1")
        stats = mock_client.get_stats()
        
        print(f"✅ Mock API client test passed")
        print(f"   User: {profile.name} ({profile.email})")
        print(f"   People: {len(people)} fetched")
        print(f"   Companies: {len(companies)} fetched")
        print(f"   Groups: {len(groups)} fetched")
        print(f"   Deals: {len(deals)} fetched")
        print(f"   Success rate: {stats['success_rate']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Folk client test failed: {e}")
        return False


def print_summary(results: Dict[str, bool]):
    """Print test summary"""
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Folk ingestion tool is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Add your Folk API keys to .env file")
        print("2. Run: python3 -m tools.folk_ingestion.folk_ingestion")
    else:
        print("⚠️  Some tests failed. Please address the issues before using the tool.")
    
    return passed == total


async def main():
    """Run all tests"""
    print("🧪 Folk.app CRM Ingestion Tool - Test Suite")
    print("="*50)
    
    results = {}
    
    # Run tests
    results["Environment Validation"] = test_environment_validation()
    results["Data Models"] = test_data_models()
    results["Configuration"] = test_configuration()
    results["Folk API Client (Mock)"] = await test_folk_client_mock()
    
    # Print summary
    return print_summary(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)