"""
OneVice Talent API

Handles talent discovery, management, and performance analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum
import uuid

# Import auth dependencies
from auth.dependencies import get_current_user
from auth.models import AuthUser, DataSensitivity

router = APIRouter(prefix="/api/talent", tags=["talent"])

# Enums and models
class SkillCategory(str, Enum):
    DIRECTING = "directing"
    PRODUCING = "producing"
    CINEMATOGRAPHY = "cinematography"
    EDITING = "editing"
    SOUND = "sound"
    WRITING = "writing"
    PERFORMANCE = "performance"
    TECHNICAL = "technical"

class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    LIMITED = "limited"

class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: SkillCategory
    proficiency_level: int = Field(ge=1, le=10)
    years_experience: int = Field(ge=0)

class RateRange(BaseModel):
    min: float
    max: float
    currency: str = "USD"
    per: str = "day"  # day, week, episode, project

class Person(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    skills: List[Skill] = Field(default_factory=list)
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    rate_range: Optional[RateRange] = None
    experience_years: int = Field(default=0, ge=0)
    projects_completed: int = Field(default=0, ge=0)
    performance_rating: float = Field(default=75.0, ge=0, le=100)
    specialties: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    contact_info: Optional[Dict[str, Any]] = None

# Mock data
MOCK_PEOPLE = [
    Person(
        id="person_1",
        name="Sarah Johnson",
        email="sarah.j@example.com",
        phone="+1-555-0101",
        bio="Award-winning commercial director with 12 years of experience in luxury brand campaigns.",
        skills=[
            Skill(name="Commercial Directing", category=SkillCategory.DIRECTING, proficiency_level=9, years_experience=12),
            Skill(name="Brand Strategy", category=SkillCategory.PRODUCING, proficiency_level=8, years_experience=10),
            Skill(name="Creative Vision", category=SkillCategory.DIRECTING, proficiency_level=9, years_experience=12)
        ],
        availability_status=AvailabilityStatus.LIMITED,
        rate_range=RateRange(min=3500, max=5000, per="day"),
        experience_years=12,
        projects_completed=15,
        performance_rating=95.0,
        specialties=["Directing", "Commercial Production"],
        location="Los Angeles, CA",
        contact_info={"linkedin": "sarah-johnson-director", "website": "sarahjohnsonfilms.com"}
    ),
    Person(
        id="person_2", 
        name="Mike Chen",
        email="mike.chen@example.com",
        phone="+1-555-0102",
        bio="Documentary filmmaker specializing in tech and startup stories with a cinematic approach.",
        skills=[
            Skill(name="Documentary Direction", category=SkillCategory.DIRECTING, proficiency_level=8, years_experience=8),
            Skill(name="Cinematography", category=SkillCategory.CINEMATOGRAPHY, proficiency_level=9, years_experience=10),
            Skill(name="Storytelling", category=SkillCategory.WRITING, proficiency_level=8, years_experience=8)
        ],
        availability_status=AvailabilityStatus.AVAILABLE,
        rate_range=RateRange(min=2800, max=4200, per="day"),
        experience_years=8,
        projects_completed=8,
        performance_rating=92.0,
        specialties=["Documentary", "Cinematography"],
        location="San Francisco, CA",
        contact_info={"imdb": "mike-chen-filmmaker", "website": "mikechen.documentaries"}
    ),
    Person(
        id="person_3",
        name="Emma Davis", 
        email="emma.davis@example.com",
        phone="+1-555-0103",
        bio="Creative choreographer and director known for high-concept music videos and fashion content.",
        skills=[
            Skill(name="Choreography", category=SkillCategory.PERFORMANCE, proficiency_level=9, years_experience=15),
            Skill(name="Music Video Direction", category=SkillCategory.DIRECTING, proficiency_level=8, years_experience=10),
            Skill(name="Creative Direction", category=SkillCategory.DIRECTING, proficiency_level=8, years_experience=12)
        ],
        availability_status=AvailabilityStatus.BOOKED,
        rate_range=RateRange(min=4000, max=6000, per="project"),
        experience_years=15,
        projects_completed=22,
        performance_rating=88.0,
        specialties=["Choreography", "Creative Direction"],
        location="New York, NY",
        contact_info={"instagram": "@emmadavischoreography", "website": "emmadavis.studio"}
    ),
    Person(
        id="person_4",
        name="Alex Rivera",
        email="alex.rivera@example.com", 
        phone="+1-555-0104",
        bio="Efficient production manager with expertise in corporate training content and multi-language productions.",
        skills=[
            Skill(name="Production Management", category=SkillCategory.PRODUCING, proficiency_level=9, years_experience=12),
            Skill(name="Budget Management", category=SkillCategory.PRODUCING, proficiency_level=8, years_experience=12),
            Skill(name="Team Coordination", category=SkillCategory.PRODUCING, proficiency_level=9, years_experience=12)
        ],
        availability_status=AvailabilityStatus.AVAILABLE,
        rate_range=RateRange(min=2500, max=3500, per="day"),
        experience_years=12,
        projects_completed=18,
        performance_rating=94.0,
        specialties=["Production Management", "Corporate Content"],
        location="Austin, TX",
        contact_info={"linkedin": "alex-rivera-producer", "email": "alex@riveraproductions.com"}
    ),
    Person(
        id="person_5",
        name="Jordan Kim",
        email="jordan.kim@example.com",
        phone="+1-555-0105",
        bio="Post-production specialist and VFX supervisor with experience in high-end commercial and music video projects.",
        skills=[
            Skill(name="Post Production", category=SkillCategory.EDITING, proficiency_level=9, years_experience=10),
            Skill(name="VFX Supervision", category=SkillCategory.TECHNICAL, proficiency_level=8, years_experience=8),
            Skill(name="Color Grading", category=SkillCategory.TECHNICAL, proficiency_level=7, years_experience=6)
        ],
        availability_status=AvailabilityStatus.AVAILABLE,
        rate_range=RateRange(min=3000, max=4500, per="day"),
        experience_years=10,
        projects_completed=12,
        performance_rating=90.0,
        specialties=["Post-Production", "VFX Supervision"],
        location="Atlanta, GA",
        contact_info={"reel": "jordankim.showreel", "website": "jordankim.post"}
    ),
    Person(
        id="person_6",
        name="Isabella Torres",
        email="isabella.torres@example.com",
        phone="+1-555-0106", 
        bio="Sound engineer and composer with expertise in original scoring and advanced audio post-production.",
        skills=[
            Skill(name="Sound Engineering", category=SkillCategory.SOUND, proficiency_level=9, years_experience=14),
            Skill(name="Music Composition", category=SkillCategory.SOUND, proficiency_level=8, years_experience=12),
            Skill(name="Audio Post Production", category=SkillCategory.SOUND, proficiency_level=9, years_experience=14)
        ],
        availability_status=AvailabilityStatus.LIMITED,
        rate_range=RateRange(min=2200, max=3800, per="day"),
        experience_years=14,
        projects_completed=28,
        performance_rating=93.0,
        specialties=["Sound Engineering", "Music Composition"],
        location="Nashville, TN",
        contact_info={"soundcloud": "isabella-torres-audio", "website": "isabellatorres.audio"}
    ),
    Person(
        id="person_7",
        name="Marcus Williams",
        email="marcus.williams@example.com",
        phone="+1-555-0107",
        bio="Versatile writer and creative producer specializing in branded content and narrative storytelling.",
        skills=[
            Skill(name="Scriptwriting", category=SkillCategory.WRITING, proficiency_level=9, years_experience=11),
            Skill(name="Creative Production", category=SkillCategory.PRODUCING, proficiency_level=8, years_experience=9),
            Skill(name="Brand Storytelling", category=SkillCategory.WRITING, proficiency_level=8, years_experience=11)
        ],
        availability_status=AvailabilityStatus.AVAILABLE,
        rate_range=RateRange(min=1800, max=2800, per="day"),
        experience_years=11,
        projects_completed=32,
        performance_rating=87.0,
        specialties=["Writing", "Creative Production"],
        location="Chicago, IL",
        contact_info={"portfolio": "marcuswilliams.writer", "linkedin": "marcus-williams-writer"}
    ),
    Person(
        id="person_8",
        name="Zara Okafor",
        email="zara.okafor@example.com",
        phone="+1-555-0108",
        bio="Technical director and camera operator with expertise in advanced cinematography and technical innovation.",
        skills=[
            Skill(name="Camera Operation", category=SkillCategory.CINEMATOGRAPHY, proficiency_level=9, years_experience=13),
            Skill(name="Technical Direction", category=SkillCategory.TECHNICAL, proficiency_level=8, years_experience=10),
            Skill(name="Lighting Design", category=SkillCategory.CINEMATOGRAPHY, proficiency_level=8, years_experience=13)
        ],
        availability_status=AvailabilityStatus.AVAILABLE,
        rate_range=RateRange(min=3200, max=4800, per="day"),
        experience_years=13,
        projects_completed=19,
        performance_rating=91.0,
        specialties=["Cinematography", "Technical Innovation"],
        location="Vancouver, BC",
        contact_info={"reel": "zara-okafor-dp", "instagram": "@zara_cinematography"}
    )
]

@router.get("/people", response_model=List[Person])
async def get_people(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: Optional[str] = Query(default="name"),
    sort_order: Optional[str] = Query(default="asc", regex="^(asc|desc)$"),
    availability: Optional[AvailabilityStatus] = None,
    skill_category: Optional[SkillCategory] = None,
    current_user: AuthUser = Depends(get_current_user)
):
    """Get people with optional filtering and sorting"""
    try:
        # Apply filters
        filtered_people = MOCK_PEOPLE.copy()
        
        if availability:
            filtered_people = [p for p in filtered_people if p.availability_status == availability]
        
        if skill_category:
            filtered_people = [
                p for p in filtered_people 
                if any(skill.category == skill_category for skill in p.skills)
            ]
        
        # Apply sorting
        if sort_by == "name":
            filtered_people.sort(key=lambda x: x.name, reverse=(sort_order == "desc"))
        elif sort_by == "performance_rating":
            filtered_people.sort(key=lambda x: x.performance_rating, reverse=(sort_order == "desc"))
        elif sort_by == "projects_completed":
            filtered_people.sort(key=lambda x: x.projects_completed, reverse=(sort_order == "desc"))
        elif sort_by == "experience_years":
            filtered_people.sort(key=lambda x: x.experience_years, reverse=(sort_order == "desc"))
        
        # Apply pagination
        paginated_people = filtered_people[offset:offset + limit]
        
        return paginated_people
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve people: {str(e)}"
        )

@router.get("/people/available", response_model=List[Person])
async def get_available_people(
    skill_categories: Optional[List[SkillCategory]] = Query(None),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get available people optionally filtered by skill categories"""
    try:
        # Filter for available people
        available_people = [p for p in MOCK_PEOPLE if p.availability_status == AvailabilityStatus.AVAILABLE]
        
        # Filter by skill categories if provided
        if skill_categories:
            available_people = [
                p for p in available_people
                if any(skill.category in skill_categories for skill in p.skills)
            ]
        
        # Sort by performance rating descending
        available_people.sort(key=lambda x: x.performance_rating, reverse=True)
        
        return available_people
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve available people: {str(e)}"
        )

@router.get("/people/top-performers", response_model=List[Person])
async def get_top_performers(
    category: Optional[SkillCategory] = None,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get top performing people by performance rating and project success"""
    try:
        people = MOCK_PEOPLE.copy()
        
        # Filter by skill category if provided
        if category:
            people = [
                p for p in people
                if any(skill.category == category for skill in p.skills)
            ]
        
        # Sort by composite score: performance rating + projects completed factor
        people.sort(
            key=lambda x: (x.performance_rating * 0.7) + (min(x.projects_completed, 30) * 0.3),
            reverse=True
        )
        
        return people[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve top performers: {str(e)}"
        )

@router.get("/people/{person_id}", response_model=Person)
async def get_person(
    person_id: str,
    current_user: AuthUser = Depends(get_current_user)
):
    """Get specific person details"""
    try:
        person = next((p for p in MOCK_PEOPLE if p.id == person_id), None)
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        return person
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve person: {str(e)}"
        )

@router.get("/skills/categories", response_model=List[SkillCategory])
async def get_skill_categories(
    current_user: AuthUser = Depends(get_current_user)
):
    """Get all available skill categories"""
    try:
        return list(SkillCategory)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve skill categories: {str(e)}"
        )