// Agent Visualization Components - Shared UI components for all agents
export {
  MetricCard,
  ProgressBar,
  StatusIndicator,
  DataList,
  QuickStats,
  type MetricCardProps,
  type ProgressBarProps,
  type StatusIndicatorProps,
  type DataListProps,
  type QuickStatsProps
} from './agent-visualizations';

// Sales Intelligence Agent Components
export {
  LeadScoringCard,
  RevenueProjectionCard,
  ClientAnalysisCard,
  MarketOpportunityCard,
  BudgetBreakdownCard,
  ROICalculatorCard,
  type LeadScoringData,
  type RevenueProjection,
  type ClientAnalysis,
  type MarketOpportunity,
  type BudgetBreakdown,
  type ROICalculation
} from './sales-agent-components';

// Talent Discovery Agent Components  
export {
  CrewMemberProfileCard,
  SkillAssessmentCard,
  AvailabilityCalendarCard,
  RoleMatchingCard,
  PortfolioShowcaseCard,
  UnionStatusCard,
  type CrewMemberProfile,
  type TalentSkill,
  type AvailabilityStatus,
  type RateInfo,
  type PortfolioItem,
  type Review,
  type UnionInfo,
  type RoleMatchingData,
  type SkillAssessment
} from './talent-agent-components';

// Leadership Analytics Agent Components
export {
  PerformanceDashboardCard,
  KPIMetricCard,
  TrendAnalysisCard,
  StrategicInsightCard,
  ExecutiveSummaryCard,
  ForecastingVisualizationCard,
  type PerformanceDashboard,
  type KPIMetric,
  type TrendAnalysis,
  type StrategicInsight,
  type ExecutiveSummary,
  type ForecastingVisualization
} from './analytics-agent-components';

// Enhanced Agent Message Components
export {
  EnhancedAgentMessage,
  EnhancedSalesMessage,
  EnhancedTalentMessage,
  EnhancedAnalyticsMessage,
  type StructuredAgentResponse
} from './enhanced-agent-message';

// Demo and Showcase Components
export {
  AgentShowcaseDemo
} from './agent-showcase-demo';

// Legacy Agent Message Components (for backwards compatibility)
export {
  AgentMessage,
  SalesMessage,
  TalentMessage,
  AnalyticsMessage
} from './agent-message';