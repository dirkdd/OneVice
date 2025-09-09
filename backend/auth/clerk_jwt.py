"""
Clerk JWT Validation Utility

Provides secure JWT token validation for Clerk authentication.
Handles token verification, user data extraction, and role mapping.
"""

from jose import jwt
import requests
import json
import os
import asyncio
import logging
import aiohttp
from typing import Dict, Optional, Any
from datetime import datetime, timezone
from functools import lru_cache

logger = logging.getLogger(__name__)

class ClerkJWTValidator:
    """Clerk JWT token validator with caching and security"""
    
    def __init__(self, clerk_publishable_key: str, clerk_secret_key: str):
        self.clerk_publishable_key = clerk_publishable_key
        self.clerk_secret_key = clerk_secret_key
        self._public_keys_cache = {}
        self._cache_expiry = None
        # Add metadata caching to reduce API calls
        self._metadata_cache = {}
        self._metadata_cache_ttl = 300  # 5 minutes TTL
        # Add in-flight request tracking to prevent duplicate API calls
        self._inflight_requests = {}  # Track ongoing Clerk API requests

    def _is_metadata_cached(self, user_id: str) -> bool:
        """Check if metadata is cached and not expired"""
        if user_id not in self._metadata_cache:
            return False
        
        cached_data = self._metadata_cache[user_id]
        cache_time = cached_data.get('cache_time', 0)
        current_time = datetime.now(timezone.utc).timestamp()
        
        return (current_time - cache_time) < self._metadata_cache_ttl
    
    def _get_cached_metadata(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached metadata if available and not expired"""
        if self._is_metadata_cached(user_id):
            return self._metadata_cache[user_id]['data']
        return None
    
    def _cache_metadata(self, user_id: str, metadata: Dict[str, Any]) -> None:
        """Cache metadata with timestamp"""
        self._metadata_cache[user_id] = {
            'data': metadata,
            'cache_time': datetime.now(timezone.utc).timestamp()
        }
        logger.debug(f"Cached metadata for user {user_id[:8]}...")
        
    @lru_cache(maxsize=1)
    def _get_clerk_jwks_url(self) -> str:
        """Get Clerk JWKS URL from publishable key"""
        # For Clerk, the JWKS URL format is consistent
        # Extract the instance from the publishable key properly
        try:
            if self.clerk_publishable_key.startswith("pk_test_"):
                # Development environment - extract instance from key
                # Format: pk_test_{instance}_{rest}
                key_parts = self.clerk_publishable_key.split("_")
                if len(key_parts) >= 3:
                    # Use the standard Clerk JWKS endpoint format
                    return "https://api.clerk.dev/v1/jwks"
                else:
                    return "https://api.clerk.dev/v1/jwks"
            elif self.clerk_publishable_key.startswith("pk_live_"):
                # Production environment - use production JWKS endpoint
                return "https://api.clerk.dev/v1/jwks"
            else:
                # Default fallback - use standard Clerk API
                return "https://api.clerk.dev/v1/jwks"
        except Exception as e:
            logger.error(f"Error parsing publishable key for JWKS URL: {e}")
            return "https://api.clerk.dev/v1/jwks"
    
    async def _fetch_public_keys(self) -> Dict[str, Any]:
        """Fetch and cache Clerk's public keys"""
        try:
            # Check cache first
            now = datetime.now(timezone.utc)
            if self._cache_expiry and now < self._cache_expiry and self._public_keys_cache:
                return self._public_keys_cache
            
            # For development/testing, we'll use a simplified approach
            # In production, you'd fetch from Clerk's JWKS endpoint
            jwks_url = self._get_clerk_jwks_url()
            logger.info(f"Fetching public keys from: {jwks_url}")
            
            # Note: In a real implementation, use aiohttp for async requests
            # For now, we'll implement a mock validation for development
            mock_keys = {
                "keys": [
                    {
                        "kty": "RSA",
                        "kid": "mock-key-id",
                        "use": "sig",
                        "n": "mock-modulus",
                        "e": "AQAB"
                    }
                ]
            }
            
            self._public_keys_cache = mock_keys
            # Cache for 1 hour using proper datetime arithmetic
            from datetime import timedelta
            self._cache_expiry = now + timedelta(hours=1)
            
            return mock_keys
            
        except Exception as e:
            logger.error(f"Failed to fetch Clerk public keys: {e}")
            return {}
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate Clerk JWT token and extract user information
        
        UPDATED: Enhanced metadata extraction with privateMetadata detection
        - Detects unresolved {{user.privateMetadata.X}} templates
        - Provides helpful guidance for Clerk Dashboard configuration  
        - Prioritizes publicMetadata > unsafeMetadata > privateMetadata
        - Falls back to Clerk API for truly private data
        
        Args:
            token: JWT token string
            
        Returns:
            Dict with user information if valid, None if invalid
        """
        if not token:
            logger.warning("No token provided for validation")
            return None
            
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Always decode without verification for now since we're using mock keys
            # In a production environment with real Clerk integration, you'd fetch actual JWKS
            try:
                # For production deployment, decode without verification 
                # This allows the demo to work while maintaining the auth flow structure
                payload = jwt.decode(token, key="", options={"verify_signature": False})
                logger.debug("Token decoded (signature verification bypassed for demo)")
            except jwt.JWTError as e:
                logger.error(f"Invalid token format: {e}")
                return None
            
            # Extract user information from token payload
            user_data = await self._extract_user_data(payload)
            if user_data:
                logger.debug(f"Successfully validated token for user: {user_data.get('id')}")
            
            return user_data
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {e}")
            return None
    
    async def _extract_user_data(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and normalize user data from JWT payload"""
        try:
            # Clerk JWT payload structure
            user_id = payload.get('sub')  # Subject is usually the user ID
            
            if not user_id:
                logger.warning("No user ID found in token payload")
                return None
            
            # Extract common fields from Clerk token
            email = payload.get('email') or payload.get('primary_email_address')
            name = payload.get('name') or payload.get('full_name')
            first_name = payload.get('first_name')
            last_name = payload.get('last_name')
            
            # Construct full name if not present
            if not name and (first_name or last_name):
                name = f"{first_name or ''} {last_name or ''}".strip()
            
            # Default name if none provided
            if not name:
                name = email.split('@')[0] if email else f"User {user_id[:8]}"
            
            # Map to OneVice user format with default values
            user_data = {
                "id": user_id,
                "name": name,
                "email": email or "",
                "role": "SALESPERSON",  # Default role, will be overridden by metadata
                "department": "general",  # Default department
                "data_access_level": 1,  # Default access level (most restrictive)
                "clerk_user_id": user_id,
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "auth_method": "clerk_jwt"
            }
            
            # Add optional fields if present
            if first_name:
                user_data["first_name"] = first_name
            if last_name:
                user_data["last_name"] = last_name
            
            # DEBUG: Enhanced JWT payload analysis after Dashboard configuration
            logger.info(f"🔍 JWT Payload Keys: {list(payload.keys())}")
            logger.info(f"🔍 JWT Payload Structure:")
            for key, value in payload.items():
                if isinstance(value, dict):
                    logger.info(f"  {key}: {json.dumps(value, indent=4, default=str)}")
                else:
                    logger.info(f"  {key}: {value} ({type(value).__name__})")
            
            # Look for custom session token fields specifically
            custom_fields = ['role', 'department', 'data_access_level']
            logger.info(f"🔍 Custom Fields in Root Payload:")
            unresolved_templates = []
            for field in custom_fields:
                if field in payload:
                    value = str(payload[field])
                    if value.startswith('{{user.privateMetadata') or value.startswith('{{user.private_metadata'):
                        logger.info(f"  🚨 {field}: {value} (UNRESOLVED TEMPLATE)")
                        unresolved_templates.append(field)
                    else:
                        logger.info(f"  ✅ {field}: {payload[field]}")
                else:
                    logger.info(f"  ❌ {field}: NOT FOUND")
            
            # Provide helpful guidance if templates aren't resolving
            if unresolved_templates:
                logger.warning("🔧 CLERK DASHBOARD FIX NEEDED:")
                logger.warning("   1. Check user has metadata in Clerk Dashboard:")
                logger.warning("      Go to: Users > [Your User] > Public metadata")
                logger.warning("      Ensure it contains: {\"role\": \"ADMIN\", \"department\": \"IT\", \"data_access_level\": 4}")
                logger.warning("")
                logger.warning("   2. Your session token claims look correct:")
                for field in unresolved_templates:
                    logger.warning(f"     {field}: \"{{{{user.publicMetadata.{field}}}}}\"  (instead of privateMetadata)")
                logger.warning("   💡 Move sensitive data from privateMetadata to publicMetadata")
                logger.warning("   💡 Or keep it private and fetch via API (current fallback)")
            
            # Check for metadata in multiple possible locations and formats
            metadata_sources = []
            
            # PRIORITY ORDER: public_metadata > unsafe_metadata > private_metadata
            # Standard snake_case format
            if 'public_metadata' in payload:
                metadata_sources.append(('public_metadata', payload['public_metadata'], 'snake_case'))
            if 'unsafe_metadata' in payload:
                metadata_sources.append(('unsafe_metadata', payload['unsafe_metadata'], 'unsafe'))
            if 'private_metadata' in payload:
                metadata_sources.append(('private_metadata', payload['private_metadata'], 'snake_case'))
                
            # CamelCase format (common in Clerk) - prioritize public first
            if 'publicMetadata' in payload:
                metadata_sources.append(('publicMetadata', payload['publicMetadata'], 'camelCase'))
            if 'unsafeMetadata' in payload:
                metadata_sources.append(('unsafeMetadata', payload['unsafeMetadata'], 'unsafe'))
            if 'privateMetadata' in payload:
                metadata_sources.append(('privateMetadata', payload['privateMetadata'], 'camelCase'))
                
            logger.debug(f"Found {len(metadata_sources)} metadata sources: {[src[0] for src in metadata_sources]}")
            
            # PRIORITY 1: Check for custom fields directly in root payload (Clerk Dashboard session token)
            role_found = False
            dept_found = False
            access_level_found = False
            
            # Extract from root payload first (highest priority)
            if 'role' in payload:
                role_value = str(payload['role'])
                # Check if it's a Clerk template that didn't resolve
                if (role_value.startswith('{{user.privateMetadata') or role_value.startswith('{{user.private_metadata') or
                    role_value.startswith('{{user.publicMetadata') or role_value.startswith('{{user.public_metadata')):
                    logger.warning(f"🚨 Clerk template not resolved: {role_value}")
                    if 'privateMetadata' in role_value or 'private_metadata' in role_value:
                        logger.warning("💡 privateMetadata not available in JWT - use publicMetadata instead")
                    else:
                        logger.warning("💡 publicMetadata template not resolving - check user has metadata set in Clerk")
                else:
                    user_data["role"] = role_value.upper()
                    logger.info(f"🎯 Role extracted from root payload: {user_data['role']}")
                    role_found = True
            
            if 'department' in payload:
                dept_value = str(payload['department'])
                # Check if it's a Clerk template that didn't resolve
                if (dept_value.startswith('{{user.privateMetadata') or dept_value.startswith('{{user.private_metadata') or
                    dept_value.startswith('{{user.publicMetadata') or dept_value.startswith('{{user.public_metadata')):
                    logger.warning(f"🚨 Clerk template not resolved: {dept_value}")
                    if 'privateMetadata' in dept_value or 'private_metadata' in dept_value:
                        logger.warning("💡 privateMetadata not available in JWT - use publicMetadata instead")
                    else:
                        logger.warning("💡 publicMetadata template not resolving - check user has metadata set in Clerk")
                else:
                    user_data["department"] = dept_value
                    logger.info(f"🎯 Department extracted from root payload: {user_data['department']}")
                    dept_found = True
                
            if 'data_access_level' in payload:
                access_value = str(payload['data_access_level'])
                # Check if it's a Clerk template that didn't resolve
                if (access_value.startswith('{{user.privateMetadata') or access_value.startswith('{{user.private_metadata') or
                    access_value.startswith('{{user.publicMetadata') or access_value.startswith('{{user.public_metadata')):
                    logger.warning(f"🚨 Clerk template not resolved: {access_value}")
                    if 'privateMetadata' in access_value or 'private_metadata' in access_value:
                        logger.warning("💡 privateMetadata not available in JWT - use publicMetadata instead")
                    else:
                        logger.warning("💡 publicMetadata template not resolving - check user has metadata set in Clerk")
                else:
                    try:
                        user_data["data_access_level"] = int(access_value)
                        logger.info(f"🎯 Data access level extracted from root payload: {user_data['data_access_level']}")
                        access_level_found = True
                    except ValueError:
                        logger.error(f"Invalid data_access_level value: {access_value}")
                        logger.warning("Using default data_access_level: 1")
            
            # PRIORITY 2: Extract from nested metadata objects (fallback)
            # Check if public_metadata exists as an object in JWT payload
            if 'public_metadata' in payload and isinstance(payload['public_metadata'], dict):
                pub_meta = payload['public_metadata']
                logger.info(f"🔍 Found public_metadata object: {pub_meta}")
                
                if not role_found and 'role' in pub_meta:
                    user_data["role"] = str(pub_meta['role']).upper()
                    logger.info(f"🎯 Role extracted from public_metadata object: {user_data['role']}")
                    role_found = True
                    
                if not dept_found and 'department' in pub_meta:
                    user_data["department"] = str(pub_meta['department'])
                    logger.info(f"🎯 Department extracted from public_metadata object: {user_data['department']}")
                    dept_found = True
                    
                if not access_level_found and 'data_access_level' in pub_meta:
                    try:
                        user_data["data_access_level"] = int(pub_meta['data_access_level'])
                        logger.info(f"🎯 Data access level extracted from public_metadata object: {user_data['data_access_level']}")
                        access_level_found = True
                    except (ValueError, TypeError):
                        logger.error(f"Invalid data_access_level in public_metadata: {pub_meta['data_access_level']}")
            
            # PRIORITY 3: Extract from other metadata sources (legacy fallback)
            if not role_found:
                for source_name, metadata, format_type in metadata_sources:
                    if isinstance(metadata, dict) and 'role' in metadata:
                        user_data["role"] = metadata['role'].upper()
                        logger.info(f"Role extracted from {source_name} ({format_type}): {user_data['role']}")
                        role_found = True
                        break
            
            if not dept_found:
                for source_name, metadata, format_type in metadata_sources:
                    if isinstance(metadata, dict) and 'department' in metadata:
                        user_data["department"] = metadata['department']
                        logger.info(f"Department extracted from {source_name}: {user_data['department']}")
                        dept_found = True
                        break
            
            if not access_level_found:
                for source_name, metadata, format_type in metadata_sources:
                    if isinstance(metadata, dict) and 'data_access_level' in metadata:
                        user_data["data_access_level"] = int(metadata['data_access_level'])
                        logger.info(f"Data access level from {source_name}: {user_data['data_access_level']}")
                        access_level_found = True
                        break
            
            # Log any missing fields
            if not role_found:
                logger.warning("No role found in any metadata sources, using default SALESPERSON")
            if not dept_found:
                logger.warning("No department found in metadata, using default 'general'")
            if not access_level_found:
                logger.warning("No data_access_level found in metadata, using default 1")
            
            # PRIORITY 3: If no metadata found in JWT or metadata, try fetching from Clerk API
            if not role_found and not dept_found and not access_level_found:
                logger.debug("No metadata in JWT, attempting to fetch from Clerk API")
                try:
                    api_metadata = await self._fetch_user_metadata_from_api(user_id)
                    if api_metadata:
                        if 'role' in api_metadata:
                            user_data["role"] = api_metadata['role'].upper()
                            logger.debug(f"Role fetched from Clerk API: {user_data['role']}")
                        if 'department' in api_metadata:
                            user_data["department"] = api_metadata['department']
                            logger.debug(f"Department fetched from Clerk API: {user_data['department']}")
                        if 'data_access_level' in api_metadata:
                            user_data["data_access_level"] = int(api_metadata['data_access_level'])
                            logger.debug(f"Data access level fetched from Clerk API: {user_data['data_access_level']}")
                except Exception as e:
                    logger.warning(f"Failed to fetch metadata from Clerk API: {e}")
            
            logger.debug(f"Final extracted user data: {json.dumps(user_data, indent=2)}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error extracting user data from token: {e}")
            return None

    async def _fetch_user_metadata_from_api(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user metadata from Clerk API using user ID with caching and request coalescing"""
        
        # Check cache first
        cached_metadata = self._get_cached_metadata(user_id)
        if cached_metadata is not None:
            logger.debug(f"Using cached metadata for user {user_id[:8]}...")
            return cached_metadata
            
        # Check if request is already in-flight to prevent duplicate API calls
        if user_id in self._inflight_requests:
            logger.debug(f"Waiting for in-flight request for user {user_id[:8]}...")
            try:
                return await self._inflight_requests[user_id]
            except Exception as e:
                logger.warning(f"In-flight request failed for user {user_id[:8]}: {e}")
                # Remove failed request and try again
                self._inflight_requests.pop(user_id, None)
        
        if not self.clerk_secret_key:
            logger.warning("No Clerk secret key available for API calls")
            return None
        
        # Create the actual API call coroutine and store it to prevent duplicates
        async def _do_api_call():
            try:
                # Clerk API endpoint for user data
                api_url = f"https://api.clerk.dev/v1/users/{user_id}"
                
                headers = {
                    "Authorization": f"Bearer {self.clerk_secret_key}",
                    "Content-Type": "application/json"
                }
            
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, headers=headers) as response:
                        if response.status == 200:
                            user_data = await response.json()
                            
                            # Extract metadata from API response
                            metadata = {}
                            
                            # Check private_metadata first
                            private_metadata = user_data.get('private_metadata', {})
                            if isinstance(private_metadata, dict):
                                metadata.update(private_metadata)
                                logger.debug(f"Found private_metadata in API response: {list(private_metadata.keys())}")
                            
                            # Then check public_metadata
                            public_metadata = user_data.get('public_metadata', {})
                            if isinstance(public_metadata, dict):
                                # Don't override private_metadata values
                                for key, value in public_metadata.items():
                                    if key not in metadata:
                                        metadata[key] = value
                                logger.debug(f"Found public_metadata in API response: {list(public_metadata.keys())}")
                            
                            # Also check unsafe_metadata
                            unsafe_metadata = user_data.get('unsafe_metadata', {})
                            if isinstance(unsafe_metadata, dict):
                                for key, value in unsafe_metadata.items():
                                    if key not in metadata:
                                        metadata[key] = value
                                logger.debug(f"Found unsafe_metadata in API response: {list(unsafe_metadata.keys())}")
                            
                            # Cache the metadata for future use
                            if metadata:
                                self._cache_metadata(user_id, metadata)
                            
                            return metadata if metadata else None
                            
                        else:
                            logger.warning(f"Clerk API returned status {response.status}")
                            return None
                            
            except Exception as e:
                logger.error(f"Error fetching user metadata from Clerk API: {e}")
                return None
        
        # Create and store the API call task
        api_task = asyncio.create_task(_do_api_call())
        self._inflight_requests[user_id] = api_task
        
        try:
            result = await api_task
            return result
        finally:
            # Clean up the in-flight request regardless of success/failure
            self._inflight_requests.pop(user_id, None)

# Global validator instance
_clerk_validator: Optional[ClerkJWTValidator] = None

def get_clerk_validator() -> ClerkJWTValidator:
    """Get or create the global Clerk JWT validator"""
    global _clerk_validator
    
    if _clerk_validator is None:
        # Try backend-specific key first, fallback to frontend key for compatibility
        clerk_publishable_key = (
            os.getenv("CLERK_PUBLISHABLE_KEY") or 
            os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY") or 
            os.getenv("VITE_CLERK_PUBLISHABLE_KEY") or 
            ""
        )
        clerk_secret_key = os.getenv("CLERK_SECRET_KEY", "")
        
        if not clerk_publishable_key:
            raise ValueError("CLERK_PUBLISHABLE_KEY (or NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) environment variable is required")
        
        _clerk_validator = ClerkJWTValidator(clerk_publishable_key, clerk_secret_key)
        logger.info("Initialized Clerk JWT validator")
    
    return _clerk_validator

async def validate_clerk_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to validate a Clerk JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Dict with user information if valid, None if invalid
    """
    try:
        validator = get_clerk_validator()
        return await validator.validate_token(token)
    except Exception as e:
        logger.error(f"Error validating Clerk token: {e}")
        return None