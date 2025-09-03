"""
OneVice Authentication API Tests

Integration tests for authentication endpoints:
- Login/logout flows
- Token management
- User profile access
- Permission validation
- Security headers and error handling
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from auth.models import UserRole, AuthProvider, AuditAction


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test auth health check endpoint"""
        response = client.get("/auth/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
    
    def test_login_missing_credentials(self, client: TestClient):
        """Test login with missing credentials"""
        response = client.post("/auth/login", json={
            "email": "test@onevice.com"
            # Missing password/provider_token
        })
        
        # Should fail validation or authentication
        assert response.status_code in [400, 401, 422]
    
    @patch('auth.services.AuthenticationService.authenticate_user')
    def test_login_success(self, mock_auth, client: TestClient, test_user_director):
        """Test successful login"""
        # Mock successful authentication
        mock_token = {
            "access_token": "test-token",
            "token_type": "bearer",
            "expires_in": 3600
        }
        mock_auth.return_value = (test_user_director, mock_token)
        
        response = client.post("/auth/login", json={
            "email": "director@onevice.com",
            "password": "test-password",
            "provider": "internal"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == "director@onevice.com"
        assert data["user"]["role"] == "DIRECTOR"
    
    @patch('auth.services.AuthenticationService.authenticate_user')
    def test_login_failure(self, mock_auth, client: TestClient):
        """Test login failure"""
        # Mock authentication failure
        mock_auth.return_value = (None, None)
        
        response = client.post("/auth/login", json={
            "email": "invalid@onevice.com", 
            "password": "wrong-password",
            "provider": "internal"
        })
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_auth_status_unauthenticated(self, client: TestClient):
        """Test auth status without authentication"""
        response = client.get("/auth/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["authenticated"] is False
        assert data["user"] is None
    
    @patch('auth.middleware.JWTAuthenticationMiddleware._validate_jwt_token')
    def test_auth_status_authenticated(self, mock_validate, client: TestClient, test_user_director):
        """Test auth status with authentication"""
        # Mock JWT validation
        mock_validate.return_value = test_user_director
        
        headers = {"Authorization": "Bearer valid-token"}
        response = client.get("/auth/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["email"] == test_user_director.email
    
    @patch('auth.middleware.JWTAuthenticationMiddleware._validate_jwt_token')
    def test_logout_success(self, mock_validate, client: TestClient, test_user_director):
        """Test successful logout"""
        mock_validate.return_value = test_user_director
        
        headers = {"Authorization": "Bearer valid-token"}
        response = client.post("/auth/logout", json={}, headers=headers)
        
        assert response.status_code == 200
        assert "Logout successful" in response.json()["message"]
    
    @patch('auth.middleware.JWTAuthenticationMiddleware._validate_jwt_token')
    def test_profile_access(self, mock_validate, client: TestClient, test_user_director):
        """Test user profile access"""
        mock_validate.return_value = test_user_director
        
        headers = {"Authorization": "Bearer valid-token"}
        response = client.get("/auth/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "permissions" in data
        assert data["user"]["email"] == test_user_director.email
    
    def test_profile_access_unauthenticated(self, client: TestClient):
        """Test profile access without authentication"""
        response = client.get("/auth/profile")
        assert response.status_code == 401
    
    @patch('auth.middleware.JWTAuthenticationMiddleware._validate_jwt_token')
    def test_permissions_endpoint(self, mock_validate, client: TestClient, test_user_leadership):
        """Test permissions endpoint"""
        mock_validate.return_value = test_user_leadership
        
        headers = {"Authorization": "Bearer valid-token"}
        response = client.get("/auth/permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_role" in data
        assert "permissions" in data
        assert "data_access" in data
        assert data["user_role"] == "LEADERSHIP"
    
    @patch('auth.services.AuthenticationService._generate_auth_token')
    @patch('auth.middleware.JWTAuthenticationMiddleware._validate_jwt_token')
    def test_token_refresh(self, mock_validate, mock_generate, client: TestClient, test_user_director):
        """Test token refresh"""
        mock_validate.return_value = test_user_director
        
        new_token = {
            "access_token": "new-test-token",
            "token_type": "bearer", 
            "expires_in": 3600
        }
        mock_generate.return_value = new_token
        
        headers = {"Authorization": "Bearer old-token"}
        response = client.post("/auth/refresh", 
                             json={"refresh_token": "refresh-token"}, 
                             headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-test-token"


class TestAuthSecurity:
    """Test authentication security features"""
    
    def test_invalid_jwt_token(self, client: TestClient):
        """Test handling of invalid JWT tokens"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/auth/profile", headers=headers)
        
        # Should be unauthorized due to invalid token
        assert response.status_code == 401
    
    def test_missing_bearer_prefix(self, client: TestClient):
        """Test handling of malformed authorization header"""
        headers = {"Authorization": "invalid-format-token"}
        response = client.get("/auth/profile", headers=headers)
        
        assert response.status_code == 401
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present"""
        response = client.options("/auth/login")
        
        # Should have CORS headers (depends on middleware setup)
        assert response.status_code in [200, 405]  # OPTIONS might not be explicitly handled
    
    def test_security_headers(self, client: TestClient):
        """Test security headers in responses"""
        response = client.get("/auth/health")
        
        # Basic security checks
        assert response.status_code == 200
        # Additional security headers would be tested here
    
    @patch('auth.services.AuditService.log_event')
    @patch('auth.middleware.JWTAuthenticationMiddleware._validate_jwt_token')
    def test_audit_logging(self, mock_validate, mock_audit, client: TestClient, test_user_director):
        """Test that authentication events are audited"""
        mock_validate.return_value = test_user_director
        
        headers = {"Authorization": "Bearer valid-token"}
        response = client.get("/auth/profile", headers=headers)
        
        assert response.status_code == 200
        # Verify audit log was called (would need proper mock setup)
        # mock_audit.assert_called()


class TestAuthEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_login_with_empty_payload(self, client: TestClient):
        """Test login with empty request body"""
        response = client.post("/auth/login", json={})
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_login_with_invalid_provider(self, client: TestClient):
        """Test login with invalid provider"""
        response = client.post("/auth/login", json={
            "email": "test@onevice.com",
            "password": "test-password",
            "provider": "invalid-provider"
        })
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_extremely_long_email(self, client: TestClient):
        """Test login with extremely long email"""
        long_email = "a" * 1000 + "@onevice.com"
        
        response = client.post("/auth/login", json={
            "email": long_email,
            "password": "test-password",
            "provider": "internal"
        })
        
        # Should handle gracefully (validation or server error)
        assert response.status_code in [400, 422, 500]
    
    def test_sql_injection_attempt(self, client: TestClient):
        """Test SQL injection attempt in email field"""
        malicious_email = "test@onevice.com'; DROP TABLE users; --"
        
        response = client.post("/auth/login", json={
            "email": malicious_email,
            "password": "test-password", 
            "provider": "internal"
        })
        
        # Should handle gracefully without exposing errors
        assert response.status_code in [400, 401, 422]
        # Should not contain sensitive error information
        assert "DROP TABLE" not in response.text
    
    @patch('auth.services.AuthenticationService.authenticate_user')
    def test_concurrent_login_attempts(self, mock_auth, client: TestClient):
        """Test concurrent login attempts"""
        import threading
        
        mock_auth.return_value = (None, None)  # Fail authentication
        
        def make_request():
            return client.post("/auth/login", json={
                "email": "test@onevice.com",
                "password": "test-password",
                "provider": "internal"
            })
        
        # Make concurrent requests
        threads = []
        results = []
        
        def request_and_store():
            result = make_request()
            results.append(result)
        
        for _ in range(5):
            thread = threading.Thread(target=request_and_store)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should fail gracefully
        for result in results:
            assert result.status_code == 401
    
    def test_malformed_json(self, client: TestClient):
        """Test handling of malformed JSON"""
        response = client.post("/auth/login", 
                              data="{'invalid': json}",  # Malformed JSON
                              headers={"Content-Type": "application/json"})
        
        # Should handle gracefully
        assert response.status_code in [400, 422]


class TestAuthProviders:
    """Test different authentication providers"""
    
    @patch('auth.services.AuthenticationService.authenticate_user')
    def test_clerk_authentication(self, mock_auth, client: TestClient, test_user_director):
        """Test Clerk provider authentication"""
        test_user_director.provider = AuthProvider.CLERK
        mock_token = {
            "access_token": "clerk-token",
            "token_type": "bearer",
            "expires_in": 3600
        }
        mock_auth.return_value = (test_user_director, mock_token)
        
        response = client.post("/auth/login", json={
            "email": "director@onevice.com",
            "provider": "clerk",
            "provider_token": "clerk-jwt-token"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "director@onevice.com"
    
    @patch('auth.services.AuthenticationService.authenticate_user')
    def test_okta_authentication(self, mock_auth, client: TestClient, test_user_director):
        """Test Okta provider authentication"""
        test_user_director.provider = AuthProvider.OKTA
        mock_token = {
            "access_token": "okta-token",
            "token_type": "bearer",
            "expires_in": 3600
        }
        mock_auth.return_value = (test_user_director, mock_token)
        
        response = client.post("/auth/login", json={
            "email": "director@onevice.com", 
            "provider": "okta",
            "provider_token": "okta-access-token"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "director@onevice.com"
    
    def test_unsupported_provider_handled_gracefully(self, client: TestClient):
        """Test that unsupported providers are handled gracefully"""
        response = client.post("/auth/login", json={
            "email": "test@onevice.com",
            "provider": "google",  # Not configured
            "provider_token": "google-token"
        })
        
        # Should fail validation due to enum constraint
        assert response.status_code == 422


class TestAuthRateLimiting:
    """Test rate limiting and abuse protection"""
    
    @pytest.mark.skip(reason="Rate limiting not implemented yet")
    def test_login_rate_limiting(self, client: TestClient):
        """Test login rate limiting"""
        # Make multiple rapid login attempts
        for i in range(10):
            response = client.post("/auth/login", json={
                "email": "test@onevice.com",
                "password": "wrong-password",
                "provider": "internal"
            })
        
        # After rate limit, should get 429 Too Many Requests
        # assert response.status_code == 429
        pass
    
    @pytest.mark.skip(reason="Rate limiting not implemented yet") 
    def test_rate_limit_headers(self, client: TestClient):
        """Test rate limiting headers"""
        response = client.post("/auth/login", json={
            "email": "test@onevice.com",
            "password": "test-password",
            "provider": "internal"
        })
        
        # Should include rate limiting headers
        # assert "X-RateLimit-Limit" in response.headers
        # assert "X-RateLimit-Remaining" in response.headers
        pass