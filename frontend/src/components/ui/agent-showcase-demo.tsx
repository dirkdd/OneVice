import React from "react";
import { Card } from "./card";
import { Button } from "./button";
import { Badge } from "./badge";
import { cn } from "@/lib/utils";
import { AgentType } from "@/lib/api/types";
import { 
  EnhancedSalesMessage,
  EnhancedTalentMessage,
  EnhancedAnalyticsMessage
} from "./enhanced-agent-message";
import { TrendingUp, Users, BarChart3, Play, RefreshCw } from "lucide-react";

// Mock data for demonstrations
const mockSalesData = {
  lead_scoring: {
    score: 85,
    factors: [
      { factor: "Budget Authority", impact: "high" as const, value: "Decision Maker", points: 25 },
      { factor: "Timeline", impact: "medium" as const, value: "Q1 2025", points: 15 },
      { factor: "Company Size", impact: "high" as const, value: "500+ employees", points: 20 },
      { factor: "Previous Projects", impact: "medium" as const, value: "3 similar projects", points: 15 },
      { factor: "Engagement Level", impact: "low" as const, value: "High interest", points: 10 }
    ],
    recommendation: "Prioritize this lead - high conversion probability with strong budget authority and timeline alignment.",
    confidence: "high" as const
  },
  client_analysis: {
    client: {
      id: "client-001",
      name: "Netflix Originals",
      type: "Streaming Platform",
      logo: ""
    },
    relationship_score: 92,
    total_projects: 12,
    total_revenue: 2450000,
    last_interaction: "2024-01-15T10:30:00Z",
    next_opportunity: {
      project: "Limited Series Documentary",
      value: 850000,
      probability: 75,
      timeline: "Q2 2025"
    },
    health_status: "excellent" as const
  },
  revenue_projection: [
    {
      period: "Q1 2025",
      projected: 650000,
      actual: 620000,
      confidence_interval: { min: 580000, max: 720000 },
      factors: ["Streaming demand", "Documentary trend", "Budget cycles"]
    },
    {
      period: "Q2 2025", 
      projected: 750000,
      confidence_interval: { min: 680000, max: 820000 },
      factors: ["Netflix contract", "Award season", "New talent pool"]
    }
  ],
  market_opportunity: {
    id: "opp-001",
    title: "True Crime Documentary Series",
    market_size: 15000000,
    competition_level: "medium" as const,
    timeline: "6 months",
    requirements: [
      "Investigative journalism experience",
      "Documentary production capabilities", 
      "Legal clearance expertise",
      "Distribution relationships"
    ],
    success_probability: 72,
    estimated_revenue: 1200000
  }
};

const mockTalentData = {
  crew_profile: {
    id: "crew-001",
    name: "Sarah Chen",
    avatar: "",
    title: "Director of Photography",
    bio: "Award-winning cinematographer with 15+ years in documentary and narrative film production. Specializes in intimate storytelling and natural lighting techniques.",
    experience_years: 15,
    location: "Los Angeles, CA",
    skills: [
      { id: "1", name: "Cinematography", category: "technical" as const, proficiency: 9, years_experience: 15 },
      { id: "2", name: "Lighting Design", category: "technical" as const, proficiency: 8, years_experience: 12 },
      { id: "3", name: "Team Leadership", category: "leadership" as const, proficiency: 8, years_experience: 10 }
    ],
    availability: {
      status: "available" as const,
      next_available: "2025-02-01T00:00:00Z",
      hourly_capacity: 40
    },
    rate: {
      min: 1500,
      max: 2500,
      currency: "USD",
      per: "day" as const,
      negotiable: true
    },
    performance_score: 94,
    projects_completed: 45,
    specialties: ["Documentary", "Narrative Film", "Commercial"],
    contact: {
      email: "sarah.chen@example.com",
      phone: "+1-555-0123"
    },
    portfolio: [
      {
        id: "p1",
        title: "Ocean's Last Song",
        type: "video" as const,
        thumbnail: "",
        role: "Director of Photography",
        year: 2023,
        awards: ["Sundance Cinematography Award"]
      }
    ],
    union_status: {
      unions: ["IATSE Local 600", "ASC"],
      member_since: "2015-01-01T00:00:00Z",
      status: "active" as const
    }
  },
  skill_assessments: [
    {
      skill: "Cinematography",
      level: 9,
      assessment_type: "project_based" as const,
      evidence: [
        "Sundance Award for 'Ocean's Last Song'",
        "Netflix series 'Dark Waters' - Lead DP",
        "15+ feature films as DP"
      ],
      last_updated: "2024-01-15T00:00:00Z",
      trend: "improving" as const
    },
    {
      skill: "Drone Operations",
      level: 7,
      assessment_type: "verified" as const,
      evidence: [
        "FAA Part 107 Commercial License",
        "Advanced drone cinematography course",
        "10+ productions with aerial footage"
      ],
      last_updated: "2024-01-10T00:00:00Z", 
      trend: "stable" as const
    }
  ],
  role_matching: {
    role: "Documentary Director of Photography",
    requirements: [
      "10+ years cinematography experience",
      "Documentary production experience",
      "Team leadership capabilities",
      "Equipment proficiency"
    ],
    candidates: [
      {
        profile: mockTalentData.crew_profile,
        match_score: 94,
        strengths: ["Award-winning work", "Documentary expertise", "Strong portfolio"],
        concerns: ["Premium rate tier"],
        recommendation: "highly_recommended" as const
      }
    ]
  }
};

const mockAnalyticsData = {
  performance_dashboard: {
    period: "Q4 2024",
    overview: {
      total_projects: 28,
      active_projects: 8,
      completed_projects: 20,
      total_revenue: 3200000,
      revenue_growth: 15.5,
      team_utilization: 87,
      client_satisfaction: 8.9
    },
    trends: [
      { metric: "Project Success Rate", current_value: 94, previous_value: 89, trend: "up" as const, percentage_change: 5.6 },
      { metric: "Client Retention", current_value: 92, previous_value: 88, trend: "up" as const, percentage_change: 4.5 },
      { metric: "Budget Efficiency", current_value: 98, previous_value: 102, trend: "down" as const, percentage_change: -3.9 }
    ],
    alerts: [
      { level: "warning" as const, message: "Q1 2025 booking rate below target", action: "Increase sales outreach" },
      { level: "info" as const, message: "New talent pool available for documentary projects" }
    ]
  },
  kpi_metrics: [
    {
      id: "kpi-001",
      name: "Revenue Growth",
      category: "financial" as const,
      current_value: 3200000,
      target_value: 3500000,
      unit: "",
      trend: { direction: "up" as const, percentage: 15.5, period: "quarterly" },
      status: "on_track" as const,
      last_updated: "2024-01-15T00:00:00Z"
    },
    {
      id: "kpi-002", 
      name: "Team Utilization",
      category: "operational" as const,
      current_value: 87,
      target_value: 85,
      unit: "%",
      trend: { direction: "up" as const, percentage: 3.2, period: "monthly" },
      status: "exceeding" as const,
      last_updated: "2024-01-15T00:00:00Z"
    }
  ],
  strategic_insights: [
    {
      id: "insight-001",
      title: "Documentary Market Expansion Opportunity",
      category: "opportunity" as const,
      priority: "high" as const,
      impact_score: 85,
      confidence: 78,
      description: "Emerging demand in true crime documentaries presents significant revenue opportunity with existing talent capabilities.",
      supporting_data: [
        { metric: "Market Growth", value: "32% YoY" },
        { metric: "Client Inquiries", value: "+45%" },
        { metric: "Talent Availability", value: "High" }
      ],
      recommended_actions: [
        "Develop true crime documentary pitch deck",
        "Expand investigative journalist network",
        "Partner with legal clearance specialists"
      ],
      timeline: "3-6 months",
      stakeholders: ["Sales Team", "Creative Director", "Legal"]
    }
  ],
  executive_summary: {
    period: "Q4 2024",
    key_achievements: [
      "Exceeded revenue target by 15.5%",
      "Completed 20 projects with 94% success rate",
      "Expanded team by 6 specialized crew members",
      "Secured 3 major streaming platform partnerships"
    ],
    critical_metrics: [
      { metric: "Revenue", value: "$3.2M", status: "positive" as const },
      { metric: "Client Satisfaction", value: "8.9/10", status: "positive" as const },
      { metric: "Team Utilization", value: "87%", status: "positive" as const }
    ],
    strategic_priorities: [
      { priority: "Documentary market expansion", status: "on_track" as const, progress: 75 },
      { priority: "International co-production", status: "delayed" as const, progress: 45 },
      { priority: "Technology infrastructure upgrade", status: "completed" as const, progress: 100 }
    ],
    risks_and_opportunities: [
      { type: "opportunity" as const, description: "True crime documentary demand surge", impact: "high" as const },
      { type: "risk" as const, description: "Key talent retention in competitive market", impact: "medium" as const }
    ],
    next_quarter_focus: [
      "Launch true crime documentary division",
      "Finalize international partnership agreements", 
      "Implement advanced project management tools"
    ]
  }
};

interface AgentShowcaseDemoProps {
  className?: string;
}

export const AgentShowcaseDemo: React.FC<AgentShowcaseDemoProps> = ({ className }) => {
  const [activeDemo, setActiveDemo] = React.useState<'sales' | 'talent' | 'analytics' | null>(null);
  const [isPlaying, setIsPlaying] = React.useState(false);

  const handleInteraction = (action: string, data?: any) => {
    console.log("Interaction:", action, data);
    // Handle agent interactions here
  };

  const playDemo = (type: 'sales' | 'talent' | 'analytics') => {
    setActiveDemo(type);
    setIsPlaying(true);
    
    // Simulate demo playing
    setTimeout(() => {
      setIsPlaying(false);
    }, 2000);
  };

  return (
    <div className={cn("space-y-6", className)}>
      <Card className="p-6 bg-gradient-to-br from-purple-500/10 to-blue-500/10 border border-purple-500/30">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold text-white">
            OneVice AI Agent Showcase
          </h2>
          <p className="text-gray-300 max-w-2xl mx-auto">
            Experience the power of specialized AI agents with rich, domain-specific visualizations 
            and interactive components designed for entertainment industry professionals.
          </p>
          
          <div className="flex items-center justify-center gap-4 mt-6">
            <Button
              onClick={() => playDemo('sales')}
              disabled={isPlaying}
              className="bg-blue-500/20 border-blue-500/30 text-blue-400 hover:bg-blue-500/30"
            >
              {isPlaying && activeDemo === 'sales' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <TrendingUp className="w-4 h-4 mr-2" />
              )}
              Sales Intelligence
            </Button>
            
            <Button
              onClick={() => playDemo('talent')}
              disabled={isPlaying}
              className="bg-purple-500/20 border-purple-500/30 text-purple-400 hover:bg-purple-500/30"
            >
              {isPlaying && activeDemo === 'talent' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Users className="w-4 h-4 mr-2" />
              )}
              Talent Discovery
            </Button>
            
            <Button
              onClick={() => playDemo('analytics')}
              disabled={isPlaying}
              className="bg-emerald-500/20 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/30"
            >
              {isPlaying && activeDemo === 'analytics' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <BarChart3 className="w-4 h-4 mr-2" />
              )}
              Leadership Analytics
            </Button>
          </div>
        </div>
      </Card>

      {/* Demo Messages */}
      <div className="space-y-6">
        {(activeDemo === 'sales' || !activeDemo) && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                Sales Intelligence Agent
              </Badge>
              <span className="text-sm text-gray-400">Revenue optimization and client insights</span>
            </div>
            
            <EnhancedSalesMessage
              content="I've analyzed your Netflix opportunity and current market conditions. Based on the lead scoring analysis, this represents a high-priority opportunity with strong conversion potential."
              metadata={{
                agent_type: AgentType.SALES,
                processing_time: "2.3s",
                confidence: "high",
                sources: ["CRM Database", "Market Research", "Historical Projects"],
                query_complexity: "complex"
              }}
              structuredData={{
                type: 'sales',
                components: [
                  {
                    component_type: 'lead_scoring',
                    data: mockSalesData.lead_scoring,
                    title: 'Lead Scoring Analysis',
                    priority: 'high'
                  },
                  {
                    component_type: 'client_analysis', 
                    data: mockSalesData.client_analysis,
                    title: 'Client Relationship Analysis',
                    priority: 'high'
                  },
                  {
                    component_type: 'revenue_projection',
                    data: mockSalesData.revenue_projection,
                    title: 'Revenue Projections',
                    priority: 'medium'
                  },
                  {
                    component_type: 'market_opportunity',
                    data: mockSalesData.market_opportunity,
                    title: 'Market Opportunity Assessment', 
                    priority: 'medium'
                  }
                ]
              }}
              interactiveElements={[
                { type: 'action_button', label: 'Schedule Meeting', action: 'schedule_meeting', data: { client_id: 'client-001' } },
                { type: 'export', label: 'Export Analysis', action: 'export_analysis' },
                { type: 'drill_down', label: 'View Full Report', action: 'view_report' }
              ]}
              onInteractionClick={handleInteraction}
              expandable={true}
              defaultExpanded={activeDemo === 'sales'}
            />
          </div>
        )}

        {(activeDemo === 'talent' || !activeDemo) && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                Talent Discovery Agent
              </Badge>
              <span className="text-sm text-gray-400">Crew matching and talent analytics</span>
            </div>
            
            <EnhancedTalentMessage
              content="I've identified several excellent candidates for your documentary project. Sarah Chen stands out as a top match with 94% compatibility and award-winning documentary experience."
              metadata={{
                agent_type: AgentType.TALENT,
                processing_time: "1.8s", 
                confidence: "high",
                sources: ["Talent Database", "Portfolio Analysis", "Project History"],
                query_complexity: "moderate"
              }}
              structuredData={{
                type: 'talent',
                components: [
                  {
                    component_type: 'role_matching',
                    data: mockTalentData.role_matching,
                    title: 'Role Matching Analysis',
                    priority: 'high'
                  },
                  {
                    component_type: 'crew_profile',
                    data: mockTalentData.crew_profile,
                    title: 'Top Candidate Profile',
                    priority: 'high' 
                  },
                  {
                    component_type: 'skill_assessment',
                    data: mockTalentData.skill_assessments,
                    title: 'Skill Verification',
                    priority: 'medium'
                  }
                ]
              }}
              interactiveElements={[
                { type: 'contact', label: 'Contact Sarah', action: 'contact_talent', data: { talent_id: 'crew-001' } },
                { type: 'action_button', label: 'View Portfolio', action: 'view_portfolio' },
                { type: 'drill_down', label: 'See More Candidates', action: 'view_candidates' }
              ]}
              onInteractionClick={handleInteraction}
              expandable={true}
              defaultExpanded={activeDemo === 'talent'}
            />
          </div>
        )}

        {(activeDemo === 'analytics' || !activeDemo) && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                Leadership Analytics Agent
              </Badge>
              <span className="text-sm text-gray-400">Performance insights and strategic analysis</span>
            </div>
            
            <EnhancedAnalyticsMessage
              content="Your Q4 performance exceeded targets with strong indicators for continued growth. I've identified a significant market opportunity in true crime documentaries that aligns with your current capabilities."
              metadata={{
                agent_type: AgentType.ANALYTICS,
                processing_time: "3.1s",
                confidence: "high", 
                sources: ["Financial Data", "Market Analysis", "Performance Metrics"],
                query_complexity: "complex"
              }}
              structuredData={{
                type: 'analytics',
                components: [
                  {
                    component_type: 'performance_dashboard',
                    data: mockAnalyticsData.performance_dashboard,
                    title: 'Q4 Performance Overview',
                    priority: 'high'
                  },
                  {
                    component_type: 'kpi_metrics',
                    data: mockAnalyticsData.kpi_metrics,
                    title: 'Key Performance Indicators',
                    priority: 'high'
                  },
                  {
                    component_type: 'strategic_insights',
                    data: mockAnalyticsData.strategic_insights,
                    title: 'AI-Generated Strategic Insights', 
                    priority: 'high'
                  },
                  {
                    component_type: 'executive_summary',
                    data: mockAnalyticsData.executive_summary,
                    title: 'Executive Summary',
                    priority: 'medium'
                  }
                ]
              }}
              interactiveElements={[
                { type: 'export', label: 'Export Dashboard', action: 'export_dashboard' },
                { type: 'drill_down', label: 'Detailed Analysis', action: 'detailed_analysis' },
                { type: 'action_button', label: 'Strategic Planning', action: 'strategic_planning' }
              ]}
              onInteractionClick={handleInteraction}
              expandable={true}
              defaultExpanded={activeDemo === 'analytics'}
            />
          </div>
        )}
      </div>
    </div>
  );
};