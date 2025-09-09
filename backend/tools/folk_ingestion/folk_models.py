"""
Folk.app Data Models

Pydantic models for validating and transforming Folk.app data to Neo4j schema.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator, model_validator


class DealStatus(str, Enum):
    """Folk deal status enumeration"""
    LEAD = "lead"
    CONTACTED = "contacted" 
    MEETING_SCHEDULED = "meeting_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    ON_HOLD = "on_hold"


class PersonType(str, Enum):
    """Person type classification"""
    CONTACT = "contact"
    INTERNAL = "internal"
    PROSPECT = "prospect"
    CLIENT = "client"


class OrganizationType(str, Enum):
    """Organization type classification"""
    CLIENT = "client"
    AGENCY = "agency"
    VENDOR = "vendor"
    PARTNER = "partner"
    PROSPECT = "prospect"


class FolkPerson(BaseModel):
    """
    Folk Person/Contact model with validation and Neo4j transformation
    """
    folk_id: str = Field(..., description="Folk unique identifier")
    email: Optional[EmailStr] = Field(None, description="Primary email address")
    name: str = Field(..., min_length=1, description="Full name")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    phone: Optional[str] = Field(None, description="Phone number")
    bio: Optional[str] = Field(None, description="Biography or notes")
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn profile URL")
    website: Optional[HttpUrl] = Field(None, description="Personal/company website")
    location: Optional[str] = Field(None, description="Location/city")
    tags: List[str] = Field(default_factory=list, description="Tags associated with person")
    groups: List[str] = Field(default_factory=list, description="Group memberships")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field data")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_internal: bool = Field(default=False, description="Internal team member flag")
    folk_user_id: Optional[str] = Field(None, description="Folk user ID if internal")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and '@' not in str(v):
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('linkedin_url', 'website')
    @classmethod
    def validate_url(cls, v):
        """Add https:// prefix to incomplete URLs"""
        if v and isinstance(v, str):
            # If URL doesn't start with protocol, add https://
            if not v.startswith(('http://', 'https://')):
                v = f'https://{v}'
        return v
    
    @model_validator(mode='after')
    def validate_internal_user(self):
        if self.is_internal and not self.folk_user_id:
            raise ValueError('Internal users must have folk_user_id')
        return self
    
    def to_neo4j_node(self, data_owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Transform to Neo4j Person node properties"""
        
        # Generate unique person ID
        person_id = str(uuid.uuid4())
        
        node_props = {
            "personId": person_id,
            "folkId": self.folk_id,
            "name": self.name,
            "email": self.email,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "title": self.title,
            "phone": self.phone,
            "bio": self.bio,
            "location": self.location,
            "linkedinUrl": str(self.linkedin_url) if self.linkedin_url else None,
            "website": str(self.website) if self.website else None,
            "tags": self.tags,
            "isInternal": self.is_internal,
            "folkUserId": self.folk_user_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "lastSyncedAt": datetime.utcnow().isoformat(),
            "dataSource": "folk",
            "dataOwnerId": data_owner_id
        }
        
        # Add custom fields with prefix
        for key, value in self.custom_fields.items():
            node_props[f"folk_{key}"] = value
        
        # Remove None values
        return {k: v for k, v in node_props.items() if v is not None}
    
    @classmethod
    def from_folk_api(cls, data: Dict[str, Any], data_owner_id: Optional[str] = None) -> "FolkPerson":
        """Create instance from Folk API response"""
        
        # Extract email from emails array (Folk API structure)
        emails = data.get("emails", [])
        primary_email = emails[0] if emails else None
        
        # Extract phone from phones array
        phones = data.get("phones", [])
        primary_phone = phones[0] if phones else None
        
        # Extract URLs
        urls = data.get("urls", [])
        linkedin_url = None
        website = None
        
        for url in urls:
            if "linkedin" in url.lower():
                linkedin_url = url
            elif not website:  # Use first non-LinkedIn URL as website
                website = url
        
        # Get company name from companies array
        companies = data.get("companies", [])
        company_name = companies[0].get("name") if companies else None
        
        return cls(
            folk_id=data.get("id", ""),
            email=primary_email,
            name=data.get("fullName") or "Unknown",
            first_name=data.get("firstName"),
            last_name=data.get("lastName"), 
            title=data.get("jobTitle"),
            company=company_name,
            phone=primary_phone,
            bio=data.get("description"),
            linkedin_url=linkedin_url,
            website=website,
            location=None,  # Not in Folk API response
            tags=[],  # Not directly available
            groups=[group.get("id", "") for group in data.get("groups", [])],
            custom_fields=data.get("customFieldValues", {}),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")) if data.get("createdAt") else None,
            updated_at=None,  # Not in Folk API response
            is_internal=data_owner_id is not None,
            folk_user_id=data_owner_id
        )


class FolkCompany(BaseModel):
    """
    Folk Company/Organization model with validation and Neo4j transformation
    """
    folk_id: str = Field(..., description="Folk unique identifier")
    name: str = Field(..., min_length=1, description="Company name")
    domain: Optional[str] = Field(None, description="Company domain")
    website: Optional[HttpUrl] = Field(None, description="Company website")
    industry: Optional[str] = Field(None, description="Industry sector")
    size: Optional[str] = Field(None, description="Company size")
    location: Optional[str] = Field(None, description="Company location")
    description: Optional[str] = Field(None, description="Company description")
    tags: List[str] = Field(default_factory=list, description="Tags associated with company")
    groups: List[str] = Field(default_factory=list, description="Group memberships")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field data")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        return v.strip()
    
    def to_neo4j_node(self, data_owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Transform to Neo4j Organization node properties"""
        
        # Generate unique organization ID
        org_id = str(uuid.uuid4())
        
        node_props = {
            "organizationId": org_id,
            "folkId": self.folk_id,
            "name": self.name,
            "domain": self.domain,
            "website": str(self.website) if self.website else None,
            "industry": self.industry,
            "size": self.size,
            "location": self.location,
            "description": self.description,
            "tags": self.tags,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "lastSyncedAt": datetime.utcnow().isoformat(),
            "dataSource": "folk",
            "dataOwnerId": data_owner_id
        }
        
        # Add custom fields with prefix
        for key, value in self.custom_fields.items():
            node_props[f"folk_{key}"] = value
        
        # Remove None values
        return {k: v for k, v in node_props.items() if v is not None}
    
    @classmethod
    def from_folk_api(cls, data: Dict[str, Any]) -> "FolkCompany":
        """Create instance from Folk API response"""
        
        # Extract website from URLs array (Folk API structure)
        urls = data.get("urls", [])
        website = urls[0] if urls else None
        
        # Ensure website has protocol
        if website and not website.startswith(("http://", "https://")):
            website = f"https://{website}"
        
        return cls(
            folk_id=data.get("id", ""),
            name=data.get("name", "Unknown Company"),
            domain=None,  # Not directly available in Folk API
            website=website,
            industry=None,  # Not in Folk API response
            size=None,  # Not in Folk API response
            location=None,  # Not in Folk API response
            description=data.get("description", ""),
            tags=[],  # Not directly available
            groups=[group.get("id", "") for group in data.get("groups", [])],
            custom_fields=data.get("customFieldValues", {}),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")) if data.get("createdAt") else None,
            updated_at=None  # Not in Folk API response
        )


class FolkGroup(BaseModel):
    """
    Folk Group/Segment model with validation and Neo4j transformation
    """
    folk_id: str = Field(..., description="Folk unique identifier")
    name: str = Field(..., min_length=1, description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    color: Optional[str] = Field(None, description="Group color")
    member_count: int = Field(default=0, description="Number of members")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Group name cannot be empty')
        return v.strip()
    
    def to_neo4j_node(self, data_owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Transform to Neo4j Group node properties"""
        
        node_props = {
            "folkId": self.folk_id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "memberCount": self.member_count,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "lastSyncedAt": datetime.utcnow().isoformat(),
            "dataSource": "folk",
            "dataOwnerId": data_owner_id
        }
        
        # Remove None values
        return {k: v for k, v in node_props.items() if v is not None}
    
    @classmethod
    def from_folk_api(cls, data: Dict[str, Any]) -> "FolkGroup":
        """Create instance from Folk API response"""
        
        return cls(
            folk_id=data.get("id", ""),
            name=data.get("name", "Unknown Group"),
            description=None,  # Not in Folk API response
            color=None,  # Not in Folk API response
            member_count=0,  # Not in Folk API response
            created_at=None,  # Not in Folk API response
            updated_at=None  # Not in Folk API response
        )


class FolkCustomObject(BaseModel):
    """
    Generic Folk Custom Object model (deals, projects, opportunities, etc.)
    """
    folk_id: str = Field(..., description="Folk unique identifier")
    entity_type: str = Field(..., description="Type of custom object (Deals, Projects, etc.)")
    name: str = Field(..., min_length=1, description="Object name")
    status: Optional[str] = Field(None, description="Object status")
    value: Optional[float] = Field(None, ge=0, description="Object value")
    currency: Optional[str] = Field(None, description="Currency code")
    probability: Optional[float] = Field(None, ge=0, le=1, description="Win probability")
    expected_close_date: Optional[datetime] = Field(None, description="Expected close date")
    actual_close_date: Optional[datetime] = Field(None, description="Actual close date")
    description: Optional[str] = Field(None, description="Object description")
    stage: Optional[str] = Field(None, description="Object stage")
    source: Optional[str] = Field(None, description="Object source")
    tags: List[str] = Field(default_factory=list, description="Tags associated with object")
    contact_ids: List[str] = Field(default_factory=list, description="Associated contact IDs")
    company_ids: List[str] = Field(default_factory=list, description="Associated company IDs")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field data")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Object name cannot be empty')
        return v.strip()
    
    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        if not v or not v.strip():
            raise ValueError('Entity type cannot be empty')
        return v.strip()
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('Currency code must be 3 characters (e.g., USD, EUR)')
        return v.upper() if v else v
    
    def to_neo4j_node(self, data_owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Transform to Neo4j custom object node properties"""
        
        # Generate unique object ID
        object_id = str(uuid.uuid4())
        
        node_props = {
            "objectId": object_id,
            "folkId": self.folk_id,
            "entityType": self.entity_type,
            "name": self.name,
            "status": self.status,
            "value": self.value,
            "currency": self.currency,
            "probability": self.probability,
            "expectedCloseDate": self.expected_close_date.isoformat() if self.expected_close_date else None,
            "actualCloseDate": self.actual_close_date.isoformat() if self.actual_close_date else None,
            "description": self.description,
            "stage": self.stage,
            "source": self.source,
            "tags": self.tags,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "lastSyncedAt": datetime.utcnow().isoformat(),
            "dataSource": "folk",
            "dataOwnerId": data_owner_id
        }
        
        # Add custom fields with prefix
        for key, value in self.custom_fields.items():
            node_props[f"folk_{key}"] = value
        
        # Remove None values
        return {k: v for k, v in node_props.items() if v is not None}
    
    @classmethod
    def from_folk_api(cls, data: Dict[str, Any], entity_type: str) -> "FolkCustomObject":
        """Create instance from Folk API response"""
        
        # Parse custom field values for object details
        custom_fields = data.get("customFieldValues", {})
        
        # Extract budget/value and convert to float if available
        budget_str = custom_fields.get("Budget")
        budget_value = None
        if budget_str and budget_str.strip():
            try:
                budget_value = float(budget_str)
            except (ValueError, TypeError):
                budget_value = None
        
        # Extract status information
        folk_stage = custom_fields.get("Stage", "")
        folk_state = custom_fields.get("State", "")
        
        # Use state if available, otherwise use stage
        status = folk_state if folk_state else folk_stage
        
        return cls(
            folk_id=data.get("id", ""),
            entity_type=entity_type,
            name=data.get("name", f"Unknown {entity_type}"),
            status=status,
            value=budget_value,
            currency="USD",  # Assume USD for budget fields
            probability=None,  # Not directly in Folk API
            expected_close_date=None,  # Could parse Input Date if needed
            actual_close_date=None,  # Not directly available
            description=custom_fields.get("Notes"),
            stage=custom_fields.get("Stage"),
            source=custom_fields.get("Sales Territory"),
            tags=[],  # Not directly available
            contact_ids=[person.get("id", "") for person in data.get("people", [])],
            company_ids=[company.get("id", "") for company in data.get("companies", [])],
            custom_fields=custom_fields,
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")) if data.get("createdAt") else None,
            updated_at=None  # Not in Folk API response
        )


# Keep the old FolkDeal class for backward compatibility, inheriting from FolkCustomObject
class FolkDeal(FolkCustomObject):
    """
    Backward compatibility wrapper for FolkCustomObject specialized for deals
    """
    
    def __init__(self, **data):
        # Ensure entity_type is set to "Deals" for backward compatibility
        if 'entity_type' not in data:
            data['entity_type'] = 'Deals'
        super().__init__(**data)
    
    @classmethod
    def from_folk_api(cls, data: Dict[str, Any]) -> "FolkDeal":
        """Create deal instance from Folk API response"""
        custom_object = FolkCustomObject.from_folk_api(data, "Deals")
        return cls(**custom_object.model_dump())