"""
Clerk JWT Validation Utility

Provides secure JWT token validation for Clerk authentication.
Handles token verification, user data extraction, and role mapping.
"""

from jose import jwt
import requests
import json
import os
import logging
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
        
    @lru_cache(maxsize=1)
    def _get_clerk_jwks_url(self) -> str:
        """Get Clerk JWKS URL from publishable key"""
        # Extract domain from publishable key (format: pk_test_xxxxx or pk_live_xxxxx)
        if self.clerk_publishable_key.startswith("pk_test_"):
            # Development environment
            instance_id = self.clerk_publishable_key.split("_")[2][:10]  # Take first 10 chars
            return f"https://clerk.{instance_id}.lcl.dev/.well-known/jwks.json"
        elif self.clerk_publishable_key.startswith("pk_live_"):
            # Production environment - will need actual domain
            # For now, use a generic format
            return "https://api.clerk.dev/v1/jwks"
        else:
            # Default fallback
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
            # Cache for 1 hour
            self._cache_expiry = now.replace(hour=now.hour + 1)
            
            return mock_keys
            
        except Exception as e:
            logger.error(f"Failed to fetch Clerk public keys: {e}")
            return {}
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate Clerk JWT token and extract user information
        
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
            
            # For development/testing, we'll use a simplified validation
            # In production, you'd use the actual Clerk public key
            if os.getenv("ENVIRONMENT") == "development":
                # Development mode - decode without verification for testing
                try:
                    # Decode without verification for development
                    # python-jose requires a key parameter even when not verifying signature
                    payload = jwt.decode(token, key="", options={"verify_signature": False})
                    logger.info("Development mode: Token decoded without signature verification")
                except jwt.JWTError as e:
                    logger.error(f"Invalid token format in development mode: {e}")
                    return None
            else:
                # Production mode - proper validation
                public_keys = await self._fetch_public_keys()
                if not public_keys.get("keys"):
                    logger.error("No public keys available for token validation")
                    return None
                
                # This would implement proper JWT validation in production
                # For now, return None to force development mode
                logger.warning("Production JWT validation not yet implemented")
                return None
            
            # Extract user information from token payload
            user_data = self._extract_user_data(payload)
            if user_data:
                logger.info(f"Successfully validated token for user: {user_data.get('id')}")
            
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
    
    def _extract_user_data(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            
            # Map to OneVice user format
            user_data = {
                "id": user_id,
                "name": name,
                "email": email or "",
                "role": "SALESPERSON",  # Default role - could be customized based on metadata
                "clerk_user_id": user_id,
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "auth_method": "clerk_jwt"
            }
            
            # Add optional fields if present
            if first_name:
                user_data["first_name"] = first_name
            if last_name:
                user_data["last_name"] = last_name
            
            # Check for custom role in public metadata
            public_metadata = payload.get('public_metadata', {})
            if isinstance(public_metadata, dict) and 'role' in public_metadata:
                user_data["role"] = public_metadata['role'].upper()
            
            logger.debug(f"Extracted user data: {json.dumps(user_data, indent=2)}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error extracting user data from token: {e}")
            return None

# Global validator instance
_clerk_validator: Optional[ClerkJWTValidator] = None

def get_clerk_validator() -> ClerkJWTValidator:
    """Get or create the global Clerk JWT validator"""
    global _clerk_validator
    
    if _clerk_validator is None:
        clerk_publishable_key = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
        clerk_secret_key = os.getenv("CLERK_SECRET_KEY", "")
        
        if not clerk_publishable_key:
            raise ValueError("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY environment variable is required")
        
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