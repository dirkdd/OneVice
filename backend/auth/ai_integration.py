"""
OneVice AI Agent Context Integration

Provides comprehensive user context and permissions for AI agents:
- User role and permission context
- Data access level filtering
- Organization hierarchy information
- Session and security context
- Audit trail integration
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import uuid4

from .models import (
    AuthUser, UserRole, DataSensitivity, PermissionAction,
    AuditAction, AuditLogEntry
)
from .services import AuditService

logger = logging.getLogger(__name__)


class AIContextProvider:
    """
    AI Agent Context Provider
    
    Generates comprehensive context information for AI agents based on
    authenticated user permissions and organizational hierarchy.
    """
    
    def __init__(self, audit_service: Optional[AuditService] = None):
        self.audit_service = audit_service or AuditService()
    
    async def get_user_context(
        self,
        user: AuthUser,
        session_id: Optional[str] = None,
        request_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AI agent context for user
        
        Args:
            user: Authenticated user
            session_id: Current session ID
            request_info: Additional request context
            
        Returns:
            Dictionary with complete user context for AI agents
        """
        
        try:
            # Log AI context access
            await self._log_ai_context_access(user, session_id, request_info)
            
            # Build comprehensive context
            context = {
                "user_identity": await self._get_user_identity_context(user),
                "permissions": await self._get_permission_context(user),
                "data_access": await self._get_data_access_context(user),
                "organizational": await self._get_organizational_context(user),
                "security": await self._get_security_context(user, session_id),
                "ai_capabilities": await self._get_ai_capabilities_context(user),
                "session": await self._get_session_context(user, session_id),
                "metadata": {
                    "context_id": str(uuid4()),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0",
                    "ttl_seconds": 3600  # Context valid for 1 hour
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to generate AI context for user {user.id}: {e}")
            # Return minimal context on error
            return await self._get_minimal_context(user)
    
    async def _get_user_identity_context(self, user: AuthUser) -> Dict[str, Any]:
        """Get user identity information for AI context"""
        
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.name,
            "role_level": user.role.value,
            "provider": user.provider.value,
            "is_active": user.is_active,
            "account_created": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    async def _get_permission_context(self, user: AuthUser) -> Dict[str, Any]:
        """Get detailed permission context for AI agents"""
        
        return {
            "actions": [action.value for action in user.permissions.actions],
            "action_count": len(user.permissions.actions),
            "data_access_level": user.permissions.data_access_level.name,
            "data_access_numeric": user.permissions.data_access_level.value,
            "context_metadata": user.permissions.context,
            "can_manage_users": user.has_permission(PermissionAction.CREATE_USER),
            "can_access_admin": user.has_permission(PermissionAction.SYSTEM_CONFIG),
            "can_view_reports": user.has_permission(PermissionAction.VIEW_REPORTS),
            "can_export_data": user.has_permission(PermissionAction.EXPORT_DATA),
            "can_manage_projects": user.has_permission(PermissionAction.MANAGE_PROJECTS)
        }
    
    async def _get_data_access_context(self, user: AuthUser) -> Dict[str, Any]:
        """Get data access level context for filtering AI responses"""
        
        access_levels = {}
        sensitive_data_access = []
        
        for level in DataSensitivity:
            can_access = user.can_access_data(level)
            access_levels[level.name.lower()] = can_access
            
            if can_access and level.value >= 4:  # Restricted and above
                sensitive_data_access.append(level.name)
        
        return {
            "access_levels": access_levels,
            "max_data_level": user.permissions.data_access_level.name,
            "max_data_numeric": user.permissions.data_access_level.value,
            "sensitive_data_access": sensitive_data_access,
            "can_access_public": access_levels.get("public", False),
            "can_access_internal": access_levels.get("internal", False),
            "can_access_confidential": access_levels.get("confidential", False),
            "can_access_restricted": access_levels.get("restricted", False),
            "can_access_secret": access_levels.get("secret", False),
            "can_access_top_secret": access_levels.get("top_secret", False),
            "data_filtering_required": True,
            "filter_instructions": await self._get_data_filter_instructions(user)
        }
    
    async def _get_organizational_context(self, user: AuthUser) -> Dict[str, Any]:
        """Get organizational hierarchy and relationship context"""
        
        # Get role hierarchy information
        hierarchy = UserRole.get_hierarchy()
        accessible_roles = hierarchy.get(user.role.name, [user.role.name])
        
        # Get data access matrix
        data_matrix = DataSensitivity.get_access_matrix()
        accessible_data_levels = data_matrix.get(user.role, [])
        
        return {
            "role_hierarchy": {
                "current_role": user.role.name,
                "role_level": user.role.value,
                "accessible_roles": accessible_roles,
                "can_manage_roles": accessible_roles[1:] if len(accessible_roles) > 1 else [],
                "reports_to": await self._get_reporting_structure(user),
                "team_members": await self._get_team_members(user)
            },
            "data_governance": {
                "accessible_data_levels": [level.name for level in accessible_data_levels],
                "data_steward": user.role in [UserRole.DIRECTOR, UserRole.LEADERSHIP],
                "compliance_officer": user.role == UserRole.LEADERSHIP
            },
            "department_context": await self._get_department_context(user)
        }
    
    async def _get_security_context(
        self,
        user: AuthUser,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get security-related context for AI agents"""
        
        return {
            "session_id": session_id,
            "authentication_provider": user.provider.value,
            "mfa_enabled": False,  # TODO: Implement MFA checking
            "security_clearance": user.permissions.data_access_level.name,
            "audit_required": True,
            "sensitive_operations_allowed": user.role.value >= 3,  # Director and above
            "admin_operations_allowed": user.role == UserRole.LEADERSHIP,
            "security_warnings": await self._get_security_warnings(user),
            "compliance_requirements": {
                "audit_all_actions": True,
                "data_classification_required": True,
                "approval_required_for": await self._get_approval_requirements(user)
            }
        }
    
    async def _get_ai_capabilities_context(self, user: AuthUser) -> Dict[str, Any]:
        """Get AI-specific capabilities and restrictions"""
        
        # Determine AI capabilities based on role
        ai_capabilities = {
            "can_access_ai": user.has_permission(PermissionAction.ACCESS_AI_AGENTS),
            "can_configure_ai": user.has_permission(PermissionAction.CONFIGURE_AI),
            "can_view_ai_logs": user.has_permission(PermissionAction.VIEW_AI_LOGS),
            "data_analysis_level": "full" if user.role.value >= 3 else "limited",
            "report_generation": user.has_permission(PermissionAction.VIEW_REPORTS),
            "data_export": user.has_permission(PermissionAction.EXPORT_DATA),
            "system_integration": user.role.value >= 4
        }
        
        # AI restrictions based on role
        ai_restrictions = []
        if user.role == UserRole.SALESPERSON:
            ai_restrictions.extend([
                "No access to sensitive customer data",
                "Limited to sales-related queries",
                "Cannot access financial reports"
            ])
        elif user.role == UserRole.CREATIVE_DIRECTOR:
            ai_restrictions.extend([
                "Limited financial data access",
                "Cannot access personnel records",
                "Project-focused capabilities"
            ])
        elif user.role == UserRole.DIRECTOR:
            ai_restrictions.extend([
                "Cannot access top secret data",
                "Limited system administration"
            ])
        
        return {
            "capabilities": ai_capabilities,
            "restrictions": ai_restrictions,
            "suggested_use_cases": await self._get_ai_use_cases(user),
            "model_access": {
                "general_purpose": True,
                "specialized_models": user.role.value >= 3,
                "admin_models": user.role == UserRole.LEADERSHIP
            }
        }
    
    async def _get_session_context(
        self,
        user: AuthUser,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get session-related context"""
        
        return {
            "session_id": session_id,
            "active": session_id is not None,
            "context_scope": "full" if user.role.value >= 3 else "limited",
            "conversation_memory": "enabled",
            "personalization": {
                "role_based": True,
                "department_focused": True,
                "experience_level": "expert" if user.role.value >= 3 else "standard"
            }
        }
    
    async def _get_data_filter_instructions(self, user: AuthUser) -> List[str]:
        """Get specific data filtering instructions for AI"""
        
        instructions = [
            f"Filter all data to {user.permissions.data_access_level.name} level or below",
            "Always classify response data with sensitivity levels",
            "Redact information above user's access level"
        ]
        
        if user.role == UserRole.SALESPERSON:
            instructions.extend([
                "Focus on sales and customer-facing information",
                "Avoid financial and operational details",
                "Limit to public and internal data"
            ])
        elif user.role == UserRole.CREATIVE_DIRECTOR:
            instructions.extend([
                "Include project and creative information",
                "Limit financial data to project budgets",
                "Avoid personnel and compensation data"
            ])
        elif user.role == UserRole.DIRECTOR:
            instructions.extend([
                "Include operational and strategic information",
                "Access to departmental financial data",
                "Exclude top secret strategic information"
            ])
        
        return instructions
    
    async def _get_reporting_structure(self, user: AuthUser) -> Dict[str, Any]:
        """Get reporting structure information"""
        
        # TODO: Implement actual organizational chart lookup
        reporting_map = {
            UserRole.SALESPERSON: "Director",
            UserRole.CREATIVE_DIRECTOR: "Director", 
            UserRole.DIRECTOR: "Leadership",
            UserRole.LEADERSHIP: None
        }
        
        return {
            "reports_to": reporting_map.get(user.role),
            "direct_reports": await self._count_direct_reports(user),
            "department": "Unknown"  # TODO: Get from user profile
        }
    
    async def _get_team_members(self, user: AuthUser) -> List[str]:
        """Get team member information"""
        
        # TODO: Implement actual team lookup
        return []
    
    async def _get_department_context(self, user: AuthUser) -> Dict[str, Any]:
        """Get department-specific context"""
        
        # TODO: Implement department context from user profile
        return {
            "department": "Unknown",
            "budget_access": user.role.value >= 3,
            "project_access": True,
            "team_size": 0
        }
    
    async def _get_security_warnings(self, user: AuthUser) -> List[str]:
        """Get security warnings for user context"""
        
        warnings = []
        
        if user.role.value >= 4:  # Leadership
            warnings.append("High-privilege account - all actions audited")
        
        if not user.last_login:
            warnings.append("First-time user - provide additional guidance")
        
        # TODO: Add more security checks
        return warnings
    
    async def _get_approval_requirements(self, user: AuthUser) -> List[str]:
        """Get operations requiring approval"""
        
        requirements = []
        
        if user.role.value < 3:  # Below Director
            requirements.extend([
                "Data export operations",
                "User management changes",
                "System configuration access"
            ])
        
        if user.role.value < 4:  # Below Leadership
            requirements.extend([
                "Role assignments",
                "Security configuration",
                "Audit log access"
            ])
        
        return requirements
    
    async def _get_ai_use_cases(self, user: AuthUser) -> List[str]:
        """Get suggested AI use cases for user role"""
        
        use_cases = {
            UserRole.SALESPERSON: [
                "Customer inquiry assistance",
                "Sales proposal generation",
                "Market research summaries",
                "Lead qualification support"
            ],
            UserRole.CREATIVE_DIRECTOR: [
                "Project planning assistance",
                "Creative brief analysis",
                "Resource allocation optimization",
                "Timeline and milestone tracking"
            ],
            UserRole.DIRECTOR: [
                "Strategic planning support",
                "Performance analysis",
                "Team management insights",
                "Budget optimization recommendations"
            ],
            UserRole.LEADERSHIP: [
                "Executive decision support",
                "Company-wide analytics",
                "Strategic forecasting",
                "Compliance monitoring"
            ]
        }
        
        return use_cases.get(user.role, [])
    
    async def _count_direct_reports(self, user: AuthUser) -> int:
        """Count direct reports for user"""
        
        # TODO: Implement actual count from database
        return 0
    
    async def _get_minimal_context(self, user: AuthUser) -> Dict[str, Any]:
        """Get minimal context on error"""
        
        return {
            "user_identity": {
                "user_id": user.id,
                "role": user.role.name,
                "email": user.email
            },
            "permissions": {
                "basic_access": True,
                "data_access_level": user.permissions.data_access_level.name
            },
            "metadata": {
                "context_id": str(uuid4()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0-minimal",
                "error": "Full context generation failed"
            }
        }
    
    async def _log_ai_context_access(
        self,
        user: AuthUser,
        session_id: Optional[str],
        request_info: Optional[Dict[str, Any]]
    ):
        """Log AI context access for audit"""
        
        if not self.audit_service:
            return
        
        try:
            await self.audit_service.log_event(
                AuditLogEntry(
                    user_id=user.id,
                    session_id=session_id,
                    action=AuditAction.DATA_READ,
                    resource="/ai/context",
                    success=True,
                    details={
                        "ai_context_requested": True,
                        "user_role": user.role.name,
                        "data_access_level": user.permissions.data_access_level.name,
                        "request_info": request_info or {}
                    }
                )
            )
        except Exception as e:
            logger.error(f"Failed to log AI context access: {e}")


# Global context provider instance
_ai_context_provider: Optional[AIContextProvider] = None


def get_ai_context_provider(audit_service: Optional[AuditService] = None) -> AIContextProvider:
    """Get singleton AI context provider instance"""
    
    global _ai_context_provider
    
    if _ai_context_provider is None:
        _ai_context_provider = AIContextProvider(audit_service)
    
    return _ai_context_provider