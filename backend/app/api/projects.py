"""
OneVice Projects API

Handles project management, analytics, and performance tracking.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import uuid

# Import auth dependencies
from auth.dependencies import get_current_user
from auth.models import AuthUser, DataSensitivity

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Enums and models
class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProjectType(str, Enum):
    COMMERCIAL = "commercial"
    DOCUMENTARY = "documentary"
    MUSIC_VIDEO = "music_video"
    CORPORATE = "corporate"
    SHORT_FILM = "short_film"
    FEATURE_FILM = "feature_film"

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    client_name: str
    project_type: ProjectType
    status: ProjectStatus
    budget: float
    spent: float = 0
    start_date: datetime
    end_date: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    team_size: int = 0
    completion_percentage: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProjectAnalytics(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    total_budget: float
    total_spent: float
    average_completion_time: Optional[float] = None  # days
    success_rate: float
    revenue_this_month: float
    profit_margin: float

class Person(BaseModel):
    id: str
    name: str
    specialties: List[str]
    contact_info: Optional[Dict[str, Any]] = None
    bio: Optional[str] = None

class PerformerMetrics(BaseModel):
    projects_completed: int
    budget_efficiency: str
    performance_score: float
    specialty: str

class TopPerformer(BaseModel):
    person: Person
    metrics: PerformerMetrics

# Mock data
MOCK_PROJECTS = [
    Project(
        id="proj_1",
        title="Luxury Watch Commercial",
        client_name="Timepiece Studios",
        project_type=ProjectType.COMMERCIAL,
        status=ProjectStatus.ACTIVE,
        budget=150000,
        spent=89000,
        start_date=datetime(2025, 1, 10, tzinfo=timezone.utc),
        estimated_completion=datetime(2025, 2, 15, tzinfo=timezone.utc),
        description="60-second luxury watch commercial with premium production values",
        tags=["luxury", "commercial", "product"],
        team_size=12,
        completion_percentage=75,
        metadata={
            "director": "Sarah Johnson",
            "location": "Los Angeles",
            "shoot_days": 3,
            "post_production_weeks": 4
        }
    ),
    Project(
        id="proj_2",
        title="Tech Startup Documentary",
        client_name="Innovation Docs",
        project_type=ProjectType.DOCUMENTARY,
        status=ProjectStatus.COMPLETED,
        budget=80000,
        spent=78500,
        start_date=datetime(2024, 12, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 1, 20, tzinfo=timezone.utc),
        description="Feature-length documentary about tech startup culture",
        tags=["documentary", "tech", "startup"],
        team_size=8,
        completion_percentage=100,
        metadata={
            "director": "Mike Chen",
            "runtime": "90 minutes",
            "interviews": 25,
            "locations": 5
        }
    ),
    Project(
        id="proj_3",
        title="Fashion Brand Music Video",
        client_name="Avant Fashion",
        project_type=ProjectType.MUSIC_VIDEO,
        status=ProjectStatus.PLANNING,
        budget=120000,
        spent=5000,
        start_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
        estimated_completion=datetime(2025, 3, 10, tzinfo=timezone.utc),
        description="High-concept music video for fashion brand collaboration",
        tags=["music video", "fashion", "concept"],
        team_size=15,
        completion_percentage=10,
        metadata={
            "artist": "Luna Echo",
            "concept": "Futuristic runway",
            "vfx_heavy": True,
            "choreographer": "Emma Davis"
        }
    ),
    Project(
        id="proj_4",
        title="Corporate Training Series",
        client_name="MegaCorp Industries",
        project_type=ProjectType.CORPORATE,
        status=ProjectStatus.ACTIVE,
        budget=95000,
        spent=45000,
        start_date=datetime(2025, 1, 5, tzinfo=timezone.utc),
        estimated_completion=datetime(2025, 2, 28, tzinfo=timezone.utc),
        description="Series of corporate training videos for employee onboarding",
        tags=["corporate", "training", "series"],
        team_size=6,
        completion_percentage=50,
        metadata={
            "episodes": 12,
            "target_length": "15 minutes each",
            "languages": ["English", "Spanish"],
            "delivery_format": "Online platform"
        }
    ),
    Project(
        id="proj_5",
        title="Independent Short Film",
        client_name="Indie Collective",
        project_type=ProjectType.SHORT_FILM,
        status=ProjectStatus.ON_HOLD,
        budget=45000,
        spent=12000,
        start_date=datetime(2024, 11, 15, tzinfo=timezone.utc),
        description="Award-submission short film with strong narrative focus",
        tags=["short film", "indie", "narrative"],
        team_size=10,
        completion_percentage=25,
        metadata={
            "genre": "Drama",
            "runtime": "20 minutes",
            "festival_targets": ["Sundance", "SXSW", "Cannes"],
            "hold_reason": "Funding review"
        }
    )
]

@router.get("", response_model=List[Project])
async def get_projects(
    status: Optional[ProjectStatus] = None,
    project_type: Optional[ProjectType] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get projects with optional filtering"""
    try:
        # Apply filters
        filtered_projects = MOCK_PROJECTS
        
        if status:
            filtered_projects = [p for p in filtered_projects if p.status == status]
            
        if project_type:
            filtered_projects = [p for p in filtered_projects if p.project_type == project_type]
        
        # Apply pagination
        paginated_projects = filtered_projects[offset:offset + limit]
        
        return paginated_projects
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve projects: {str(e)}"
        )

@router.get("/analytics", response_model=ProjectAnalytics)
async def get_project_analytics(
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Get comprehensive project analytics"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Check data access permissions
        if not current_user.can_access_data(DataSensitivity.CONFIDENTIAL):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for analytics data"
            )
        
        # Calculate analytics from mock data
        total_projects = len(MOCK_PROJECTS)
        active_projects = len([p for p in MOCK_PROJECTS if p.status == ProjectStatus.ACTIVE])
        completed_projects = len([p for p in MOCK_PROJECTS if p.status == ProjectStatus.COMPLETED])
        
        total_budget = sum(p.budget for p in MOCK_PROJECTS)
        total_spent = sum(p.spent for p in MOCK_PROJECTS)
        
        # Mock calculations for demonstration
        success_rate = completed_projects / total_projects if total_projects > 0 else 0
        revenue_this_month = 245000  # Mock data
        profit_margin = (revenue_this_month - 180000) / revenue_this_month if revenue_this_month > 0 else 0
        
        analytics = ProjectAnalytics(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            total_budget=total_budget,
            total_spent=total_spent,
            average_completion_time=45.5,  # Mock average
            success_rate=success_rate,
            revenue_this_month=revenue_this_month,
            profit_margin=profit_margin
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics: {str(e)}"
        )

@router.get("/top-performers", response_model=List[TopPerformer])
async def get_top_performers(
    limit: int = Query(default=5, ge=1, le=10),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Get top performing projects by ROI"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Check data access permissions
        if not current_user.can_access_data(DataSensitivity.CONFIDENTIAL):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for performance data"
            )
        
        # Mock top performers data
        mock_performers = [
            TopPerformer(
                person=Person(
                    id="person_1",
                    name="Sarah Johnson",
                    specialties=["Directing", "Commercial Production"],
                    contact_info={
                        "email": "sarah.j@example.com",
                        "phone": "+1-555-0101"
                    },
                    bio="Award-winning commercial director with 12 years of experience in luxury brand campaigns."
                ),
                metrics=PerformerMetrics(
                    projects_completed=15,
                    budget_efficiency="95%",
                    performance_score=4.9,
                    specialty="Commercial Director"
                )
            ),
            TopPerformer(
                person=Person(
                    id="person_2",
                    name="Mike Chen",
                    specialties=["Documentary", "Cinematography"],
                    contact_info={
                        "email": "mike.chen@example.com",
                        "phone": "+1-555-0102"
                    },
                    bio="Documentary filmmaker specializing in tech and startup stories with a cinematic approach."
                ),
                metrics=PerformerMetrics(
                    projects_completed=8,
                    budget_efficiency="92%",
                    performance_score=4.8,
                    specialty="Documentary Director"
                )
            ),
            TopPerformer(
                person=Person(
                    id="person_3",
                    name="Emma Davis",
                    specialties=["Choreography", "Creative Direction"],
                    contact_info={
                        "email": "emma.davis@example.com",
                        "phone": "+1-555-0103"
                    },
                    bio="Creative choreographer and director known for high-concept music videos and fashion content."
                ),
                metrics=PerformerMetrics(
                    projects_completed=22,
                    budget_efficiency="88%",
                    performance_score=4.7,
                    specialty="Choreographer"
                )
            ),
            TopPerformer(
                person=Person(
                    id="person_4",
                    name="Alex Rivera",
                    specialties=["Production Management", "Corporate Content"],
                    contact_info={
                        "email": "alex.rivera@example.com",
                        "phone": "+1-555-0104"
                    },
                    bio="Efficient production manager with expertise in corporate training content and multi-language productions."
                ),
                metrics=PerformerMetrics(
                    projects_completed=18,
                    budget_efficiency="94%",
                    performance_score=4.6,
                    specialty="Production Manager"
                )
            ),
            TopPerformer(
                person=Person(
                    id="person_5",
                    name="Jordan Kim",
                    specialties=["Post-Production", "VFX Supervision"],
                    contact_info={
                        "email": "jordan.kim@example.com",
                        "phone": "+1-555-0105"
                    },
                    bio="Post-production specialist and VFX supervisor with experience in high-end commercial and music video projects."
                ),
                metrics=PerformerMetrics(
                    projects_completed=12,
                    budget_efficiency="90%",
                    performance_score=4.5,
                    specialty="Post-Production Supervisor"
                )
            )
        ]
        
        # Sort by performance score and limit results
        sorted_performers = sorted(
            mock_performers, 
            key=lambda x: x.metrics.performance_score, 
            reverse=True
        )[:limit]
        
        return sorted_performers
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve top performers: {str(e)}"
        )

@router.get("/templates", response_model=List[Project])
async def get_project_templates(
    current_user: AuthUser = Depends(get_current_user)
):
    """Get project templates for quick project creation"""
    try:
        return MOCK_PROJECT_TEMPLATES
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve project templates: {str(e)}"
        )

@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user)
):
    """Get specific project details"""
    try:
        project = next((p for p in MOCK_PROJECTS if p.id == project_id), None)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve project: {str(e)}"
        )

@router.post("", response_model=Project)
async def create_project(
    project_data: Dict[str, Any],
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Create a new project"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Check permissions for project creation
        if not current_user.has_permission("manage_projects"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to create projects"
            )
        
        # Create new project
        new_project = Project(
            title=project_data.get("title", "New Project"),
            client_name=project_data.get("client_name", "Unknown Client"),
            project_type=ProjectType(project_data.get("project_type", "commercial")),
            status=ProjectStatus(project_data.get("status", "planning")),
            budget=project_data.get("budget", 0),
            start_date=datetime.fromisoformat(project_data.get("start_date", datetime.now().isoformat())),
            description=project_data.get("description", ""),
            tags=project_data.get("tags", []),
            team_size=project_data.get("team_size", 0),
            metadata=project_data.get("metadata", {})
        )
        
        # Add to mock data (in real implementation, save to database)
        MOCK_PROJECTS.append(new_project)
        
        return new_project
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project: {str(e)}"
        )

# Project Templates Data
MOCK_PROJECT_TEMPLATES = [
    Project(
        id="template_1",
        title="Commercial Project Template",
        client_name="[Client Name]",
        project_type=ProjectType.COMMERCIAL,
        status=ProjectStatus.PLANNING,
        budget=150000.0,
        spent=0.0,
        start_date=datetime.now(timezone.utc),
        estimated_completion=datetime.now(timezone.utc) + timedelta(days=30),
        description="Template for commercial projects including brand campaigns, product launches, and advertising content.",
        tags=["commercial", "advertising", "brand", "template"],
        team_size=8,
        completion_percentage=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        metadata={
            "template": True,
            "typical_duration_days": 30,
            "recommended_team": ["Director", "Producer", "Cinematographer", "Editor", "Sound Engineer"],
            "deliverables": ["30s spot", "15s cut", "social media versions"]
        }
    ),
    Project(
        id="template_2",
        title="Documentary Project Template",
        client_name="[Client Name]",
        project_type=ProjectType.DOCUMENTARY,
        status=ProjectStatus.PLANNING,
        budget=300000.0,
        spent=0.0,
        start_date=datetime.now(timezone.utc),
        estimated_completion=datetime.now(timezone.utc) + timedelta(days=90),
        description="Template for documentary projects including feature documentaries, series episodes, and investigative pieces.",
        tags=["documentary", "storytelling", "research", "template"],
        team_size=6,
        completion_percentage=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        metadata={
            "template": True,
            "typical_duration_days": 90,
            "recommended_team": ["Director", "Producer", "Cinematographer", "Editor", "Researcher", "Sound Engineer"],
            "deliverables": ["Feature documentary", "Trailer", "Social media clips"]
        }
    ),
    Project(
        id="template_3",
        title="Music Video Template",
        client_name="[Artist/Label Name]",
        project_type=ProjectType.MUSIC_VIDEO,
        status=ProjectStatus.PLANNING,
        budget=75000.0,
        spent=0.0,
        start_date=datetime.now(timezone.utc),
        estimated_completion=datetime.now(timezone.utc) + timedelta(days=7),
        description="Template for music video projects including performance videos, narrative concepts, and artistic visuals.",
        tags=["music", "video", "performance", "creative", "template"],
        team_size=10,
        completion_percentage=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        metadata={
            "template": True,
            "typical_duration_days": 7,
            "recommended_team": ["Director", "Producer", "Cinematographer", "Gaffer", "Choreographer", "Editor"],
            "deliverables": ["Main video", "Behind-the-scenes", "Lyric video"]
        }
    ),
    Project(
        id="template_4",
        title="Corporate Content Template",
        client_name="[Company Name]",
        project_type=ProjectType.CORPORATE,
        status=ProjectStatus.PLANNING,
        budget=50000.0,
        spent=0.0,
        start_date=datetime.now(timezone.utc),
        estimated_completion=datetime.now(timezone.utc) + timedelta(days=45),
        description="Template for corporate content including training videos, company profiles, and internal communications.",
        tags=["corporate", "training", "business", "professional", "template"],
        team_size=5,
        completion_percentage=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        metadata={
            "template": True,
            "typical_duration_days": 45,
            "recommended_team": ["Director", "Producer", "Cinematographer", "Editor", "Scriptwriter"],
            "deliverables": ["Training modules", "Company overview", "Executive interviews"]
        }
    ),
    Project(
        id="template_5",
        title="Short Film Template",
        client_name="[Production Company]",
        project_type=ProjectType.SHORT_FILM,
        status=ProjectStatus.PLANNING,
        budget=25000.0,
        spent=0.0,
        start_date=datetime.now(timezone.utc),
        estimated_completion=datetime.now(timezone.utc) + timedelta(days=60),
        description="Template for short film projects including narrative shorts, experimental films, and festival submissions.",
        tags=["short film", "narrative", "indie", "festival", "template"],
        team_size=7,
        completion_percentage=0.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        metadata={
            "template": True,
            "typical_duration_days": 60,
            "recommended_team": ["Director", "Producer", "Cinematographer", "Editor", "Sound Designer", "Actor"],
            "deliverables": ["Short film", "Festival cut", "Promotional materials"]
        }
    )
]

