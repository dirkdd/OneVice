"""
Folk.app API Client

Provides async HTTP client for Folk.app API with comprehensive error handling,
rate limiting, and authentication support.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class FolkAPIError(Exception):
    """Base exception for Folk API errors"""
    pass


class FolkAuthenticationError(FolkAPIError):
    """Authentication failed with Folk API"""
    pass


class FolkRateLimitError(FolkAPIError):
    """Rate limit exceeded"""
    pass


class FolkAPIUnavailableError(FolkAPIError):
    """Folk API service unavailable"""
    pass


@dataclass
class FolkUser:
    """Folk user profile"""
    id: str
    email: str
    name: str
    company: Optional[str] = None


@dataclass
class APIResponse:
    """Folk API response wrapper"""
    data: Any
    success: bool
    status_code: int
    headers: Dict[str, str]
    error: Optional[str] = None


class FolkClient:
    """
    Async Folk.app API Client
    
    Features:
    - Authentication with API keys
    - Rate limiting with exponential backoff
    - Comprehensive error handling
    - Retry logic for transient failures
    - Request/response logging
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.folk.app/v1",
        rate_limit: int = 100,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """Initialize Folk API client"""
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Track API usage
        self._requests_made = 0
        self._errors_count = 0
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "OneVice-Folk-Integration/1.0"
            },
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        logger.info(f"Folk API client initialized for {base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info("Folk API client closed")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, FolkRateLimitError, FolkAPIUnavailableError))
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """Make authenticated request to Folk API with retry logic"""
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._requests_made += 1
        
        try:
            logger.debug(f"Folk API {method.upper()} {url} (attempt {self._requests_made})")
            
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                self._errors_count += 1
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limit hit, retrying after {retry_after}s")
                await asyncio.sleep(retry_after)
                raise FolkRateLimitError(f"Rate limit exceeded, retry after {retry_after}s")
            
            # Handle authentication errors
            if response.status_code == 401:
                self._errors_count += 1
                error_msg = "Authentication failed - check API key"
                logger.error(error_msg)
                raise FolkAuthenticationError(error_msg)
            
            # Handle service unavailable
            if response.status_code >= 500:
                self._errors_count += 1
                error_msg = f"Folk API unavailable (status {response.status_code})"
                logger.error(error_msg)
                raise FolkAPIUnavailableError(error_msg)
            
            # Handle client errors
            if response.status_code >= 400:
                self._errors_count += 1
                error_msg = f"API error {response.status_code}: {response.text}"
                
                # Special handling for 404 on deals - this is normal for groups without deals
                if response.status_code == 404 and "Deals" in response.text:
                    logger.debug(f"Group has no deals (expected): {error_msg}")
                else:
                    logger.error(error_msg)
                
                return APIResponse(
                    data=None,
                    success=False,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    error=error_msg
                )
            
            # Success response
            try:
                json_data = response.json()
            except Exception as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                json_data = {"raw_content": response.text}
            
            logger.debug(f"Folk API success: {response.status_code}")
            
            return APIResponse(
                data=json_data,
                success=True,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except httpx.RequestError as e:
            self._errors_count += 1
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            raise FolkAPIError(error_msg) from e
        
        except Exception as e:
            self._errors_count += 1
            error_msg = f"Unexpected error during API request: {str(e)}"
            logger.error(error_msg)
            raise FolkAPIError(error_msg) from e
    
    async def get_user_profile(self) -> FolkUser:
        """Get current user profile to identify data owner"""
        
        logger.info("Fetching Folk user profile")
        
        response = await self._make_request("GET", "/users/me")
        
        if not response.success:
            raise FolkAPIError(f"Failed to get user profile: {response.error}")
        
        # Folk API returns user data in data wrapper
        user_data = response.data.get("data", {})
        
        return FolkUser(
            id=user_data.get("id", ""),
            email=user_data.get("email", ""),
            name=user_data.get("fullName", ""),
            company=None  # Not available in /users/me response
        )
    
    async def get_people(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all people/contacts from Folk"""
        
        logger.info(f"Fetching people from Folk (limit: {limit}, offset: {offset})")
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        response = await self._make_request("GET", "/people", params=params)
        
        if not response.success:
            raise FolkAPIError(f"Failed to get people: {response.error}")
        
        # Folk API returns data in data.items structure
        people = response.data.get("data", {}).get("items", [])
        logger.info(f"Retrieved {len(people)} people from Folk")
        
        return people
    
    async def get_companies(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all companies from Folk"""
        
        logger.info(f"Fetching companies from Folk (limit: {limit}, offset: {offset})")
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        response = await self._make_request("GET", "/companies", params=params)
        
        if not response.success:
            raise FolkAPIError(f"Failed to get companies: {response.error}")
        
        # Folk API returns data in data.items structure
        companies = response.data.get("data", {}).get("items", [])
        logger.info(f"Retrieved {len(companies)} companies from Folk")
        
        return companies
    
    async def get_groups(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all groups from Folk"""
        
        logger.info(f"Fetching groups from Folk (limit: {limit}, offset: {offset})")
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        response = await self._make_request("GET", "/groups", params=params)
        
        if not response.success:
            raise FolkAPIError(f"Failed to get groups: {response.error}")
        
        # Folk API returns data in data.items structure
        groups = response.data.get("data", {}).get("items", [])
        logger.info(f"Retrieved {len(groups)} groups from Folk")
        
        return groups
    
    async def get_deals_for_group(self, group_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all deals for a specific group"""
        
        logger.info(f"Fetching deals for group {group_id} (limit: {limit}, offset: {offset})")
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        response = await self._make_request("GET", f"/groups/{group_id}/Deals", params=params)
        
        if not response.success:
            raise FolkAPIError(f"Failed to get deals for group {group_id}: {response.error}")
        
        # Folk API returns data in data.items structure
        deals = response.data.get("data", {}).get("items", [])
        logger.info(f"Retrieved {len(deals)} deals for group {group_id}")
        
        return deals
    
    async def get_all_people_paginated(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get all people with automatic pagination using nextLink"""
        
        all_people = []
        next_url = None
        
        while True:
            if next_url:
                # Extract cursor from nextLink URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(next_url)
                cursor = parse_qs(parsed.query).get('cursor', [None])[0]
                params = {"limit": page_size, "cursor": cursor} if cursor else {"limit": page_size}
            else:
                params = {"limit": page_size}
            
            response = await self._make_request("GET", "/people", params=params)
            
            if not response.success:
                raise FolkAPIError(f"Failed to get people: {response.error}")
            
            # Folk API returns data in data.items structure
            batch = response.data.get("data", {}).get("items", [])
            
            if not batch:
                break
            
            all_people.extend(batch)
            
            # Check for pagination nextLink
            next_url = response.data.get("data", {}).get("pagination", {}).get("nextLink")
            if not next_url:
                break
            
            # Rate limiting between requests
            await asyncio.sleep(0.1)
        
        logger.info(f"Retrieved total of {len(all_people)} people via pagination")
        return all_people
    
    async def get_all_companies_paginated(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get all companies with automatic pagination using nextLink"""
        
        all_companies = []
        next_url = None
        
        while True:
            if next_url:
                # Extract cursor from nextLink URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(next_url)
                cursor = parse_qs(parsed.query).get('cursor', [None])[0]
                params = {"limit": page_size, "cursor": cursor} if cursor else {"limit": page_size}
            else:
                params = {"limit": page_size}
            
            response = await self._make_request("GET", "/companies", params=params)
            
            if not response.success:
                raise FolkAPIError(f"Failed to get companies: {response.error}")
            
            # Folk API returns data in data.items structure
            batch = response.data.get("data", {}).get("items", [])
            
            if not batch:
                break
            
            all_companies.extend(batch)
            
            # Check for pagination nextLink
            next_url = response.data.get("data", {}).get("pagination", {}).get("nextLink")
            if not next_url:
                break
            
            # Rate limiting between requests
            await asyncio.sleep(0.1)
        
        logger.info(f"Retrieved total of {len(all_companies)} companies via pagination")
        return all_companies
    
    async def get_all_groups_paginated(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get all groups with automatic pagination using nextLink"""
        
        all_groups = []
        next_url = None
        
        while True:
            if next_url:
                # Extract cursor from nextLink URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(next_url)
                cursor = parse_qs(parsed.query).get('cursor', [None])[0]
                params = {"limit": page_size, "cursor": cursor} if cursor else {"limit": page_size}
            else:
                params = {"limit": page_size}
            
            response = await self._make_request("GET", "/groups", params=params)
            
            if not response.success:
                raise FolkAPIError(f"Failed to get groups: {response.error}")
            
            # Folk API returns data in data.items structure
            batch = response.data.get("data", {}).get("items", [])
            
            if not batch:
                break
            
            all_groups.extend(batch)
            
            # Check for pagination nextLink
            next_url = response.data.get("data", {}).get("pagination", {}).get("nextLink")
            if not next_url:
                break
            
            # Rate limiting between requests
            await asyncio.sleep(0.1)
        
        logger.info(f"Retrieved total of {len(all_groups)} groups via pagination")
        return all_groups
    
    async def get_all_deals_for_group_paginated(self, group_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get all deals for a specific group with automatic pagination using nextLink"""
        
        all_deals = []
        next_url = None
        
        while True:
            if next_url:
                # Extract cursor from nextLink URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(next_url)
                cursor = parse_qs(parsed.query).get('cursor', [None])[0]
                params = {"limit": page_size, "cursor": cursor} if cursor else {"limit": page_size}
            else:
                params = {"limit": page_size}
            
            response = await self._make_request("GET", f"/groups/{group_id}/Deals", params=params)
            
            if not response.success:
                raise FolkAPIError(f"Failed to get deals for group {group_id}: {response.error}")
            
            # Folk API returns data in data.items structure
            batch = response.data.get("data", {}).get("items", [])
            
            if not batch:
                break
            
            all_deals.extend(batch)
            
            # Check for pagination nextLink
            next_url = response.data.get("data", {}).get("pagination", {}).get("nextLink")
            if not next_url:
                break
            
            # Rate limiting between requests
            await asyncio.sleep(0.1)
        
        logger.info(f"Retrieved total of {len(all_deals)} deals for group {group_id} via pagination")
        return all_deals
    
    def discover_entity_types_from_data(self, people_data: List[Dict], companies_data: List[Dict]) -> Dict[str, List[str]]:
        """Discover entity types by parsing customFieldValues from people and companies"""
        
        group_entity_types = {}
        
        # Check companies customFieldValues
        for company in companies_data:
            custom_fields = company.get("customFieldValues", {})
            
            for group_id, group_fields in custom_fields.items():
                if not group_id.startswith("grp_"):
                    continue
                    
                if group_id not in group_entity_types:
                    group_entity_types[group_id] = set()
                
                # Look for array fields that contain entity references
                for field_name, field_value in group_fields.items():
                    if isinstance(field_value, list) and field_value:
                        # Check if items have entity-like structure
                        for item in field_value:
                            if isinstance(item, dict) and "entityType" in item:
                                group_entity_types[group_id].add(field_name)
        
        # Check people customFieldValues  
        for person in people_data:
            custom_fields = person.get("customFieldValues", {})
            
            for group_id, group_fields in custom_fields.items():
                if not group_id.startswith("grp_"):
                    continue
                    
                if group_id not in group_entity_types:
                    group_entity_types[group_id] = set()
                
                # Look for array fields that contain entity references
                for field_name, field_value in group_fields.items():
                    if isinstance(field_value, list) and field_value:
                        # Check if items have entity-like structure
                        for item in field_value:
                            if isinstance(item, dict) and "entityType" in item:
                                group_entity_types[group_id].add(field_name)
        
        # Convert sets to lists for easier handling
        result = {group_id: list(entity_types) for group_id, entity_types in group_entity_types.items()}
        
        logger.info(f"Discovered entity types: {result}")
        return result
    
    async def get_custom_objects(self, group_id: str, entity_type: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get custom objects of a specific entity type for a group"""
        
        logger.info(f"Fetching {entity_type} for group {group_id} (limit: {limit}, offset: {offset})")
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        response = await self._make_request("GET", f"/groups/{group_id}/{entity_type}", params=params)
        
        if not response.success:
            raise FolkAPIError(f"Failed to get {entity_type} for group {group_id}: {response.error}")
        
        # Folk API returns data in data.items structure
        objects = response.data.get("data", {}).get("items", [])
        logger.info(f"Retrieved {len(objects)} {entity_type} for group {group_id}")
        
        return objects
    
    async def get_all_custom_objects_paginated(self, group_id: str, entity_type: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get all custom objects of a specific entity type with automatic pagination"""
        
        all_objects = []
        next_url = None
        
        while True:
            if next_url:
                # Extract cursor from nextLink URL
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(next_url)
                cursor = parse_qs(parsed.query).get('cursor', [None])[0]
                params = {"limit": page_size, "cursor": cursor} if cursor else {"limit": page_size}
            else:
                params = {"limit": page_size}
            
            response = await self._make_request("GET", f"/groups/{group_id}/{entity_type}", params=params)
            
            if not response.success:
                raise FolkAPIError(f"Failed to get {entity_type} for group {group_id}: {response.error}")
            
            # Folk API returns data in data.items structure
            batch = response.data.get("data", {}).get("items", [])
            
            if not batch:
                break
            
            all_objects.extend(batch)
            
            # Check for pagination nextLink
            next_url = response.data.get("data", {}).get("pagination", {}).get("nextLink")
            if not next_url:
                break
            
            # Rate limiting between requests
            await asyncio.sleep(0.1)
        
        logger.info(f"Retrieved total of {len(all_objects)} {entity_type} for group {group_id} via pagination")
        return all_objects
    
    def get_stats(self) -> Dict[str, int]:
        """Get client usage statistics"""
        return {
            "requests_made": self._requests_made,
            "errors_count": self._errors_count,
            "success_rate": (self._requests_made - self._errors_count) / max(self._requests_made, 1)
        }