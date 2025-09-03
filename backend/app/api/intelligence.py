"""
OneVice Intelligence API

Handles business intelligence, case studies, insights, and analytics.
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

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])

# Enums and models
class IndustryType(str, Enum):
    AUTOMOTIVE = "automotive"
    FASHION = "fashion" 
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ENTERTAINMENT = "entertainment"
    FOOD_BEVERAGE = "food_beverage"
    RETAIL = "retail"

class CaseStudyStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    FEATURED = "featured"
    ARCHIVED = "archived"

class ClientType(str, Enum):
    STREAMING_PLATFORM = "streaming_platform"
    BROADCASTER = "broadcaster" 
    PRODUCTION_COMPANY = "production_company"
    STUDIO = "studio"
    AGENCY = "agency"
    DIRECT_CLIENT = "direct_client"

class CaseStudy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    client_name: str
    industry: IndustryType
    status: CaseStudyStatus
    project_type: str
    budget: float
    revenue: float
    roi_percentage: float
    duration_days: int
    success_metrics: Dict[str, float]
    description: str
    key_insights: List[str]
    challenges_overcome: List[str]
    tags: List[str] = Field(default_factory=list)
    featured_image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_satisfaction: float = Field(default=4.5, ge=1, le=5)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BusinessInsight(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    category: str
    priority: str  # "high", "medium", "low"
    insight_text: str
    data_points: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float = Field(ge=0, le=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: ClientType
    industry: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    relationship_strength: int = Field(default=5, ge=1, le=10)
    projects_count: int = 0
    total_budget: float = 0
    last_interaction: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PortfolioMetrics(BaseModel):
    total_case_studies: int
    success_rate: float
    average_roi: float
    client_satisfaction: float
    featured_projects: int
    industries_served: List[str]
    top_performing_categories: List[str]

class IntelligenceMetrics(BaseModel):
    total_case_studies: int
    success_rate: float
    average_roi: float
    client_satisfaction_avg: float
    top_performing_industry: str
    recent_insights_count: int
    trending_keywords: List[str]
    monthly_revenue_trend: List[float]

# Mock clients data
MOCK_CLIENTS = [
    Client(
        id="client_1",
        name="Netflix",
        type=ClientType.STREAMING_PLATFORM,
        industry="Entertainment Streaming",
        contact_person="Sarah Mitchell",
        email="sarah.mitchell@netflix.com",
        phone="+1-555-0101",
        relationship_strength=9,
        projects_count=12,
        total_budget=2850000,
        last_interaction=datetime(2025, 8, 28, tzinfo=timezone.utc),
        notes="Premium client, focus on high-quality documentary content"
    ),
    Client(
        id="client_2", 
        name="BBC Studios",
        type=ClientType.BROADCASTER,
        industry="Broadcasting",
        contact_person="James Thompson",
        email="j.thompson@bbcstudios.com", 
        phone="+44-20-8123-4567",
        relationship_strength=8,
        projects_count=8,
        total_budget=1650000,
        last_interaction=datetime(2025, 8, 25, tzinfo=timezone.utc),
        notes="Long-term partnership, interested in nature documentaries"
    ),
    Client(
        id="client_3",
        name="Universal Pictures", 
        type=ClientType.STUDIO,
        industry="Film Production",
        contact_person="Maria Rodriguez",
        email="m.rodriguez@universalpictures.com",
        phone="+1-818-555-0123",
        relationship_strength=7,
        projects_count=5,
        total_budget=4200000,
        last_interaction=datetime(2025, 8, 22, tzinfo=timezone.utc),
        notes="Big budget projects, focus on commercial viability"
    ),
    Client(
        id="client_4",
        name="Wieden+Kennedy",
        type=ClientType.AGENCY,
        industry="Advertising",
        contact_person="Alex Chen",
        email="alex.chen@wk.com",
        phone="+1-503-555-0199", 
        relationship_strength=8,
        projects_count=15,
        total_budget=1850000,
        last_interaction=datetime(2025, 8, 30, tzinfo=timezone.utc),
        notes="Creative agency, values innovative storytelling approaches"
    ),
    Client(
        id="client_5",
        name="A24 Films",
        type=ClientType.PRODUCTION_COMPANY,
        industry="Independent Film",
        contact_person="Emma Davis",
        email="emma.davis@a24films.com",
        phone="+1-212-555-0165",
        relationship_strength=9,
        projects_count=7,
        total_budget=3100000,
        last_interaction=datetime(2025, 9, 1, tzinfo=timezone.utc),
        notes="Indie film production, values artistic integrity over commercial appeal"
    )
]

# Mock case studies data
MOCK_CASE_STUDIES = [
    CaseStudy(
        id="cs_1",
        title="Luxury Automotive Campaign Success",
        client_name="PremiumCars Inc",
        industry=IndustryType.AUTOMOTIVE,
        status=CaseStudyStatus.FEATURED,
        project_type="Commercial Campaign",
        budget=250000,
        revenue=485000,
        roi_percentage=194.0,
        duration_days=65,
        success_metrics={
            "brand_awareness_increase": 42.5,
            "lead_generation": 156.8,
            "conversion_rate": 23.4,
            "social_engagement": 89.2
        },
        description="A comprehensive luxury automotive campaign that exceeded all performance targets through strategic storytelling and premium production values.",
        key_insights=[
            "High-quality cinematography significantly impacts luxury brand perception",
            "Emotional storytelling drives 3x higher engagement than feature-focused content",
            "Premium location choices correlate with 65% higher conversion rates"
        ],
        challenges_overcome=[
            "Weather-dependent outdoor shoots requiring flexible scheduling",
            "Complex vehicle coordination across multiple locations",
            "Balancing artistic vision with strict brand guidelines"
        ],
        tags=["luxury", "automotive", "commercial", "premium"],
        client_satisfaction=4.9,
        metadata={
            "director": "Alexandra Rivera",
            "shoot_locations": ["Monaco", "Swiss Alps"],
            "awards": ["Cannes Lions Bronze", "Automotive Marketing Excellence"]
        }
    ),
    CaseStudy(
        id="cs_2",
        title="Fashion Brand Digital Transformation",
        client_name="Avant Style",
        industry=IndustryType.FASHION,
        status=CaseStudyStatus.FEATURED,
        project_type="Digital Campaign",
        budget=180000,
        revenue=394000,
        roi_percentage=218.9,
        duration_days=90,
        success_metrics={
            "online_sales_increase": 78.3,
            "instagram_followers": 245.7,
            "engagement_rate": 12.4,
            "brand_mention_sentiment": 94.1
        },
        description="Complete digital transformation for emerging fashion brand, focusing on Gen Z audience through innovative content strategy.",
        key_insights=[
            "User-generated content drives 4x higher authenticity scores",
            "Behind-the-scenes content performs 2.5x better than polished campaigns",
            "Micro-influencer partnerships yield 40% better ROI than celebrity endorsements"
        ],
        challenges_overcome=[
            "Limited initial social media presence",
            "Tight timeline for seasonal launch alignment",
            "Budget constraints requiring creative resource allocation"
        ],
        tags=["fashion", "digital", "social media", "gen-z"],
        client_satisfaction=4.8,
        metadata={
            "campaign_duration": "3 months",
            "platforms": ["Instagram", "TikTok", "YouTube"],
            "content_pieces": 156
        }
    ),
    CaseStudy(
        id="cs_3",
        title="Tech Startup Product Launch",
        client_name="InnovateTech Solutions",
        industry=IndustryType.TECHNOLOGY,
        status=CaseStudyStatus.PUBLISHED,
        project_type="Product Launch",
        budget=320000,
        revenue=598000,
        roi_percentage=186.9,
        duration_days=120,
        success_metrics={
            "product_awareness": 67.4,
            "demo_requests": 189.5,
            "conversion_to_trial": 34.7,
            "media_coverage_reach": 2840000
        },
        description="Strategic product launch campaign for B2B software solution, focusing on thought leadership and technical credibility.",
        key_insights=[
            "Technical demos drive 5x higher qualified lead generation",
            "Industry expert testimonials increase credibility by 78%",
            "Educational content performs 3.2x better than direct sales messaging"
        ],
        challenges_overcome=[
            "Complex technical product requiring simplified messaging",
            "Competitive market with established players",
            "Limited brand recognition in target market"
        ],
        tags=["technology", "B2B", "product launch", "software"],
        client_satisfaction=4.6,
        metadata={
            "target_audience": "CTOs and Technical Directors",
            "primary_channels": ["LinkedIn", "Industry Publications", "Conferences"],
            "lead_quality_score": 8.7
        }
    ),
    CaseStudy(
        id="cs_4",
        title="Healthcare Awareness Campaign",
        client_name="MedCare Foundation",
        industry=IndustryType.HEALTHCARE,
        status=CaseStudyStatus.PUBLISHED,
        project_type="Awareness Campaign",
        budget=145000,
        revenue=289000,
        roi_percentage=199.3,
        duration_days=75,
        success_metrics={
            "awareness_increase": 89.2,
            "appointment_bookings": 156.8,
            "website_traffic": 234.5,
            "community_engagement": 67.9
        },
        description="Public health awareness campaign focusing on preventive care, with emphasis on accessibility and community trust.",
        key_insights=[
            "Community testimonials increase trust by 85%",
            "Local language adaptation improves engagement by 67%",
            "Healthcare professionals as spokespersons drive 3x credibility"
        ],
        challenges_overcome=[
            "Sensitive health topics requiring careful messaging",
            "Diverse community demographics and languages",
            "Regulatory compliance across multiple jurisdictions"
        ],
        tags=["healthcare", "awareness", "community", "public health"],
        client_satisfaction=4.7,
        metadata={
            "languages": ["English", "Spanish", "Mandarin"],
            "community_partners": 15,
            "compliance_approvals": 8
        }
    )
]

# Mock business insights
MOCK_INSIGHTS = [
    BusinessInsight(
        id="insight_1",
        title="Q1 ROI Performance Exceeds Industry Standards",
        category="Performance",
        priority="high",
        insight_text="Our Q1 campaigns achieved an average ROI of 187%, significantly outperforming the industry average of 124%. The luxury and technology sectors showed particularly strong performance.",
        data_points=[
            {"metric": "Average ROI", "value": 187.0, "comparison": 124.0, "period": "Q1 2025"},
            {"metric": "Top Sector", "value": "Luxury Automotive", "roi": 194.0},
            {"metric": "Growth vs Previous Quarter", "value": 23.5, "unit": "percent"}
        ],
        recommendations=[
            "Increase investment in luxury automotive sector campaigns",
            "Replicate successful storytelling frameworks across other sectors",
            "Expand team capacity to handle increased demand"
        ],
        confidence_score=0.92
    ),
    BusinessInsight(
        id="insight_2",
        title="Emerging Trend: Sustainability-Focused Campaigns",
        category="Market Trends",
        priority="medium",
        insight_text="Clients are increasingly requesting sustainability-focused messaging. Campaigns with environmental themes show 34% higher engagement rates.",
        data_points=[
            {"metric": "Engagement Increase", "value": 34.0, "unit": "percent"},
            {"metric": "Client Requests", "value": 67.0, "unit": "percent increase"},
            {"metric": "Sustainability Mentions", "value": 156, "period": "Last 3 months"}
        ],
        recommendations=[
            "Develop sustainability messaging framework",
            "Partner with environmental consultants",
            "Create carbon-neutral production guidelines"
        ],
        confidence_score=0.78
    ),
    BusinessInsight(
        id="insight_3",
        title="Technology Sector Shows Strong Growth Potential",
        category="Sector Analysis",
        priority="high",
        insight_text="Technology sector projects demonstrate consistent high performance with average project values increasing by 45% year-over-year.",
        data_points=[
            {"metric": "Project Value Growth", "value": 45.0, "unit": "percent YoY"},
            {"metric": "Sector Revenue Share", "value": 28.5, "unit": "percent"},
            {"metric": "Client Retention", "value": 89.0, "unit": "percent"}
        ],
        recommendations=[
            "Expand technology sector sales team",
            "Develop tech-specific service offerings",
            "Invest in emerging technology capabilities (AR/VR)"
        ],
        confidence_score=0.85
    )
]

@router.get("/case-studies/featured", response_model=List[CaseStudy])
async def get_featured_case_studies(
    limit: int = Query(default=3, ge=1, le=10),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get featured case studies"""
    try:
        # Filter for featured case studies
        featured_studies = [
            cs for cs in MOCK_CASE_STUDIES 
            if cs.status == CaseStudyStatus.FEATURED
        ]
        
        # Sort by ROI and limit results
        sorted_studies = sorted(
            featured_studies, 
            key=lambda x: x.roi_percentage, 
            reverse=True
        )[:limit]
        
        return sorted_studies
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve featured case studies: {str(e)}"
        )

@router.get("/case-studies", response_model=List[CaseStudy])
async def get_case_studies(
    industry: Optional[IndustryType] = None,
    status: Optional[CaseStudyStatus] = None,
    min_roi: Optional[float] = Query(None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get case studies with optional filtering"""
    try:
        # Apply filters
        filtered_studies = MOCK_CASE_STUDIES
        
        if industry:
            filtered_studies = [cs for cs in filtered_studies if cs.industry == industry]
            
        if status:
            filtered_studies = [cs for cs in filtered_studies if cs.status == status]
            
        if min_roi is not None:
            filtered_studies = [cs for cs in filtered_studies if cs.roi_percentage >= min_roi]
        
        # Apply pagination
        paginated_studies = filtered_studies[offset:offset + limit]
        
        return paginated_studies
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve case studies: {str(e)}"
        )

@router.get("/case-studies/{case_study_id}", response_model=CaseStudy)
async def get_case_study(
    case_study_id: str,
    current_user: AuthUser = Depends(get_current_user)
):
    """Get specific case study details"""
    try:
        case_study = next(
            (cs for cs in MOCK_CASE_STUDIES if cs.id == case_study_id), 
            None
        )
        
        if not case_study:
            raise HTTPException(status_code=404, detail="Case study not found")
        
        return case_study
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve case study: {str(e)}"
        )

@router.get("/insights", response_model=List[BusinessInsight])
async def get_business_insights(
    category: Optional[str] = None,
    priority: Optional[str] = Query(None, regex="^(high|medium|low)$"),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Get business insights with optional filtering"""
    try:
        # Check authentication
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Check data access permissions for insights
        if not current_user.can_access_data(DataSensitivity.CONFIDENTIAL):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for business insights"
            )
        
        # Apply filters
        filtered_insights = MOCK_INSIGHTS
        
        if category:
            filtered_insights = [
                insight for insight in filtered_insights 
                if insight.category.lower() == category.lower()
            ]
            
        if priority:
            filtered_insights = [
                insight for insight in filtered_insights 
                if insight.priority == priority
            ]
        
        # Sort by confidence score and limit
        sorted_insights = sorted(
            filtered_insights, 
            key=lambda x: x.confidence_score, 
            reverse=True
        )[:limit]
        
        return sorted_insights
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve insights: {str(e)}"
        )

@router.get("/metrics", response_model=IntelligenceMetrics)
async def get_intelligence_metrics(
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Get comprehensive intelligence metrics"""
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
                detail="Insufficient permissions for intelligence metrics"
            )
        
        # Calculate metrics from mock data
        total_case_studies = len(MOCK_CASE_STUDIES)
        success_rate = len([cs for cs in MOCK_CASE_STUDIES if cs.roi_percentage > 150]) / total_case_studies
        average_roi = sum(cs.roi_percentage for cs in MOCK_CASE_STUDIES) / total_case_studies
        client_satisfaction_avg = sum(cs.client_satisfaction for cs in MOCK_CASE_STUDIES) / total_case_studies
        
        # Find top performing industry
        industry_performance = {}
        for cs in MOCK_CASE_STUDIES:
            if cs.industry not in industry_performance:
                industry_performance[cs.industry] = []
            industry_performance[cs.industry].append(cs.roi_percentage)
        
        top_industry = max(
            industry_performance.items(), 
            key=lambda x: sum(x[1]) / len(x[1])
        )[0].value
        
        metrics = IntelligenceMetrics(
            total_case_studies=total_case_studies,
            success_rate=success_rate,
            average_roi=average_roi,
            client_satisfaction_avg=client_satisfaction_avg,
            top_performing_industry=top_industry,
            recent_insights_count=len(MOCK_INSIGHTS),
            trending_keywords=["sustainability", "digital transformation", "AI integration", "luxury branding"],
            monthly_revenue_trend=[1200000, 1350000, 1420000, 1580000, 1650000, 1720000]
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate intelligence metrics: {str(e)}"
        )

@router.get("/clients", response_model=List[Client])
async def get_clients(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: Optional[str] = Query(default="name"),
    sort_order: Optional[str] = Query(default="asc", regex="^(asc|desc)$"),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get clients with optional filtering and sorting"""
    try:
        # Apply sorting
        clients = MOCK_CLIENTS.copy()
        
        if sort_by == "last_interaction":
            clients.sort(
                key=lambda x: x.last_interaction or datetime.min.replace(tzinfo=timezone.utc),
                reverse=(sort_order == "desc")
            )
        elif sort_by == "name":
            clients.sort(key=lambda x: x.name, reverse=(sort_order == "desc"))
        elif sort_by == "projects_count":
            clients.sort(key=lambda x: x.projects_count, reverse=(sort_order == "desc"))
        elif sort_by == "total_budget":
            clients.sort(key=lambda x: x.total_budget, reverse=(sort_order == "desc"))
        
        # Apply pagination
        paginated_clients = clients[offset:offset + limit]
        
        return paginated_clients
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve clients: {str(e)}"
        )

@router.get("/clients/{client_id}", response_model=Client)
async def get_client(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user)
):
    """Get specific client details"""
    try:
        client = next((c for c in MOCK_CLIENTS if c.id == client_id), None)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return client
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve client: {str(e)}"
        )

@router.get("/portfolio/metrics", response_model=PortfolioMetrics) 
async def get_portfolio_metrics(
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """Get portfolio analytics and metrics"""
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
                detail="Insufficient permissions for portfolio metrics"
            )
        
        # Calculate metrics from mock data
        total_case_studies = len(MOCK_CASE_STUDIES)
        completed_case_studies = len([cs for cs in MOCK_CASE_STUDIES if cs.status == CaseStudyStatus.PUBLISHED or cs.status == CaseStudyStatus.FEATURED])
        success_rate = (completed_case_studies / total_case_studies) * 100 if total_case_studies > 0 else 0
        
        total_roi = sum(cs.roi_percentage for cs in MOCK_CASE_STUDIES)
        average_roi = total_roi / total_case_studies if total_case_studies > 0 else 0
        
        total_satisfaction = sum(cs.client_satisfaction for cs in MOCK_CASE_STUDIES)
        client_satisfaction = total_satisfaction / total_case_studies if total_case_studies > 0 else 0
        
        featured_projects = len([cs for cs in MOCK_CASE_STUDIES if cs.status == CaseStudyStatus.FEATURED])
        
        industries_served = list(set(cs.industry.value for cs in MOCK_CASE_STUDIES))
        
        # Group by project type to find top performing categories
        category_performance = {}
        for cs in MOCK_CASE_STUDIES:
            if cs.project_type not in category_performance:
                category_performance[cs.project_type] = []
            category_performance[cs.project_type].append(cs.roi_percentage)
        
        top_performing_categories = sorted(
            category_performance.keys(), 
            key=lambda x: sum(category_performance[x]) / len(category_performance[x]), 
            reverse=True
        )[:3]
        
        metrics = PortfolioMetrics(
            total_case_studies=total_case_studies,
            success_rate=success_rate,
            average_roi=average_roi,
            client_satisfaction=client_satisfaction,
            featured_projects=featured_projects,
            industries_served=industries_served,
            top_performing_categories=top_performing_categories
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate portfolio metrics: {str(e)}"
        )