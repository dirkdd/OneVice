import React from "react";
import { cn } from "@/lib/utils";
import { AgentType, AgentMetadata, WebSocketMessage } from "@/lib/api/types";
import { MessageWithAgent, AgentHandoff } from "@/types/conversation-history";
import { AgentBadge, getAgentColorScheme } from "./agent-badge";
import { AgentHandoffIndicator } from "./agent-handoff-indicator";
import { Card } from "./card";
import { Button } from "./button";
import { Clock, ExternalLink, Lightbulb, ChevronDown, ChevronUp, Maximize2 } from "lucide-react";

// Import specialized components
import {
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
} from "./sales-agent-components";

import {
  CrewMemberProfileCard,
  SkillAssessmentCard,
  AvailabilityCalendarCard,
  RoleMatchingCard,
  PortfolioShowcaseCard,
  UnionStatusCard,
  type CrewMemberProfile,
  type SkillAssessment,
  type AvailabilityStatus,
  type RoleMatchingData,
  type PortfolioItem,
  type UnionInfo
} from "./talent-agent-components";

import {
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
} from "./analytics-agent-components";

// Enhanced types for structured agent responses
export interface StructuredAgentResponse extends WebSocketMessage {
  structured_data?: {
    type: 'sales' | 'talent' | 'analytics';
    components: Array<{
      component_type: string;
      data: any;
      title?: string;
      priority?: 'high' | 'medium' | 'low';
    }>;
  };
  response_type?: 'text' | 'structured' | 'mixed';
  interactive_elements?: Array<{
    type: 'action_button' | 'drill_down' | 'export' | 'contact';
    label: string;
    action: string;
    data?: any;
  }>;
}

interface EnhancedAgentMessageProps {
  message: StructuredAgentResponse | MessageWithAgent;
  showHandoff?: boolean;
  expandable?: boolean;
  defaultExpanded?: boolean;
  onInteractionClick?: (action: string, data?: any) => void;
  className?: string;
}

interface MessageContentProps {
  content: string;
  metadata?: AgentMetadata;
  className?: string;
}

const MessageContent: React.FC<MessageContentProps> = ({ 
  content, 
  metadata, 
  className 
}) => {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="prose prose-invert prose-sm max-w-none">
        <div 
          className="whitespace-pre-wrap break-words leading-relaxed text-gray-200"
          dangerouslySetInnerHTML={{ 
            __html: content.replace(/\n/g, '<br />') 
          }}
        />
      </div>
      
      {metadata?.sources && metadata.sources.length > 0 && (
        <div className="border-t border-gray-700/50 pt-3 mt-3">
          <div className="flex items-center gap-2 mb-2">
            <ExternalLink className="w-3 h-3 text-gray-400" />
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
              Sources
            </span>
          </div>
          <div className="flex flex-wrap gap-1">
            {metadata.sources.map((source, index) => (
              <div
                key={index}
                className="px-2 py-1 bg-gray-800/50 text-xs text-gray-300 rounded border border-gray-700/50"
              >
                {source}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {metadata?.query_complexity && (
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Lightbulb className="w-3 h-3" />
          <span>Query complexity: {metadata.query_complexity}</span>
        </div>
      )}
    </div>
  );
};

// Component renderer for structured data
const StructuredComponentRenderer: React.FC<{
  component_type: string;
  data: any;
  title?: string;
  agent: AgentType;
}> = ({ component_type, data, title, agent }) => {
  const commonProps = { className: "mb-4" };

  switch (agent) {
    case AgentType.SALES:
      switch (component_type) {
        case 'lead_scoring':
          return <LeadScoringCard data={data as LeadScoringData} {...commonProps} />;
        case 'revenue_projection':
          return <RevenueProjectionCard projections={data as RevenueProjection[]} {...commonProps} />;
        case 'client_analysis':
          return <ClientAnalysisCard data={data as ClientAnalysis} {...commonProps} />;
        case 'market_opportunity':
          return <MarketOpportunityCard opportunity={data as MarketOpportunity} {...commonProps} />;
        case 'budget_breakdown':
          return <BudgetBreakdownCard data={data as BudgetBreakdown} {...commonProps} />;
        case 'roi_calculator':
          return <ROICalculatorCard data={data as ROICalculation} {...commonProps} />;
        default:
          return null;
      }

    case AgentType.TALENT:
      switch (component_type) {
        case 'crew_profile':
          return <CrewMemberProfileCard profile={data as CrewMemberProfile} {...commonProps} />;
        case 'crew_profile_compact':
          return <CrewMemberProfileCard profile={data as CrewMemberProfile} compact={true} {...commonProps} />;
        case 'skill_assessment':
          return <SkillAssessmentCard assessments={data as SkillAssessment[]} {...commonProps} />;
        case 'availability_calendar':
          return <AvailabilityCalendarCard availability={data as AvailabilityStatus} {...commonProps} />;
        case 'role_matching':
          return <RoleMatchingCard data={data as RoleMatchingData} {...commonProps} />;
        case 'portfolio_showcase':
          return <PortfolioShowcaseCard portfolio={data as PortfolioItem[]} {...commonProps} />;
        case 'union_status':
          return <UnionStatusCard unionInfo={data as UnionInfo} {...commonProps} />;
        default:
          return null;
      }

    case AgentType.ANALYTICS:
      switch (component_type) {
        case 'performance_dashboard':
          return <PerformanceDashboardCard data={data as PerformanceDashboard} {...commonProps} />;
        case 'kpi_metrics':
          return <KPIMetricCard metrics={data as KPIMetric[]} {...commonProps} />;
        case 'trend_analysis':
          return <TrendAnalysisCard data={data as TrendAnalysis} {...commonProps} />;
        case 'strategic_insights':
          return <StrategicInsightCard insights={data as StrategicInsight[]} {...commonProps} />;
        case 'executive_summary':
          return <ExecutiveSummaryCard summary={data as ExecutiveSummary} {...commonProps} />;
        case 'forecasting_visualization':
          return <ForecastingVisualizationCard data={data as ForecastingVisualization} {...commonProps} />;
        default:
          return null;
      }

    default:
      return null;
  }
};

// Interactive elements renderer
const InteractiveElementsRenderer: React.FC<{
  elements: Array<{
    type: 'action_button' | 'drill_down' | 'export' | 'contact';
    label: string;
    action: string;
    data?: any;
  }>;
  onInteractionClick?: (action: string, data?: any) => void;
}> = ({ elements, onInteractionClick }) => {
  if (!elements || elements.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 pt-3 border-t border-gray-700/50">
      {elements.map((element, index) => (
        <Button
          key={index}
          size="sm"
          variant="outline"
          onClick={() => onInteractionClick?.(element.action, element.data)}
          className="text-xs"
        >
          {element.label}
        </Button>
      ))}
    </div>
  );
};

export const EnhancedAgentMessage: React.FC<EnhancedAgentMessageProps> = ({ 
  message, 
  showHandoff = true,
  expandable = false,
  defaultExpanded = true,
  onInteractionClick,
  className 
}) => {
  const [isExpanded, setIsExpanded] = React.useState(defaultExpanded);
  const [isFullscreen, setIsFullscreen] = React.useState(false);
  
  const isUser = message.type === 'user_message';
  const isAgent = message.type === 'agent_response' && message.agent;
  const isAI = message.type === 'ai_response';
  const messageWithAgent = message as MessageWithAgent;
  const structuredMessage = message as StructuredAgentResponse;
  const hasHandoff = showHandoff && messageWithAgent.is_handoff && messageWithAgent.handoff_data;
  const hasStructuredData = structuredMessage.structured_data && structuredMessage.structured_data.components.length > 0;
  
  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get agent color scheme for styling
  const colorScheme = isAgent && message.agent 
    ? getAgentColorScheme(message.agent)
    : null;

  if (isUser) {
    return (
      <div className={cn("flex justify-end mb-4", className)}>
        <div className="max-w-[70%] group">
          <Card className="bg-white/10 border-white/20 backdrop-blur-sm p-4">
            <MessageContent 
              content={message.content}
              className="text-white"
            />
            <div className="flex justify-end mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="flex items-center gap-2 text-xs text-gray-300">
                <Clock className="w-3 h-3" />
                <span>{formatTime(message.timestamp)}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      "flex justify-start mb-4",
      isFullscreen && "fixed inset-4 z-50 bg-black/90 backdrop-blur-sm overflow-auto p-6",
      className
    )}>
      <div className={cn(
        "group",
        isFullscreen ? "w-full" : "max-w-[90%]"
      )}>
        <div className="space-y-2">
          {/* Agent Handoff Indicator */}
          {hasHandoff && messageWithAgent.handoff_data && (
            <div className="mb-3">
              <AgentHandoffIndicator 
                handoff={messageWithAgent.handoff_data}
                variant="detailed"
                size="default"
              />
            </div>
          )}

          {/* Agent Badge Header */}
          {isAgent && message.agent && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AgentBadge 
                  agent={message.agent}
                  metadata={message.agent_metadata}
                  showConfidence={true}
                  showProcessingTime={true}
                  size="default"
                />
              </div>
              
              <div className="flex items-center gap-2">
                {hasStructuredData && expandable && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setIsExpanded(!isExpanded)}
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </Button>
                )}
                {hasStructuredData && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                  >
                    <Maximize2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          )}
          
          {/* Message Card */}
          <Card 
            className={cn(
              "p-4 backdrop-blur-sm transition-all duration-300",
              isAgent && colorScheme ? [
                // Agent-specific styling
                colorScheme.bg,
                colorScheme.border,
                'border',
                `hover:${colorScheme.glow}`,
                'hover:shadow-lg'
              ] : [
                // Default AI response styling
                'bg-gray-800/70',
                'border-gray-700',
                'hover:bg-gray-800/90'
              ]
            )}
          >
            {/* Text Content */}
            <MessageContent 
              content={message.content}
              metadata={message.agent_metadata}
              className="text-white"
            />
            
            {/* Structured Components */}
            {hasStructuredData && isExpanded && isAgent && (
              <div className="mt-4 space-y-4">
                <div className="border-t border-current/10 pt-4">
                  <div className="text-sm font-medium text-current/70 mb-3">
                    Specialized Analysis & Insights
                  </div>
                  
                  <div className="grid gap-4">
                    {structuredMessage.structured_data!.components.map((component, index) => (
                      <div key={index}>
                        {component.title && (
                          <h4 className="text-sm font-medium text-white mb-2">
                            {component.title}
                          </h4>
                        )}
                        <StructuredComponentRenderer
                          component_type={component.component_type}
                          data={component.data}
                          title={component.title}
                          agent={message.agent!}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {/* Interactive Elements */}
            {structuredMessage.interactive_elements && (
              <InteractiveElementsRenderer
                elements={structuredMessage.interactive_elements}
                onInteractionClick={onInteractionClick}
              />
            )}
            
            {/* Message Footer */}
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-current/10 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="flex items-center gap-4 text-xs text-current/70">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{formatTime(message.timestamp)}</span>
                </div>
                
                {message.agent_metadata?.processing_time && (
                  <div className="flex items-center gap-1">
                    <span>Processed in {message.agent_metadata.processing_time}</span>
                  </div>
                )}
              </div>
              
              {isAgent && (
                <div className="text-xs opacity-75">
                  AI Agent Response
                  {hasStructuredData && (
                    <span className="ml-1">
                      • {structuredMessage.structured_data!.components.length} insights
                    </span>
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
      
      {/* Fullscreen overlay close */}
      {isFullscreen && (
        <Button
          className="fixed top-4 right-4 z-10"
          size="sm"
          variant="outline"
          onClick={() => setIsFullscreen(false)}
        >
          Close
        </Button>
      )}
    </div>
  );
};

// Enhanced specialized message components with structured data support
export const EnhancedSalesMessage: React.FC<{
  content: string;
  timestamp?: string;
  metadata?: AgentMetadata;
  structuredData?: any;
  interactiveElements?: any[];
  onInteractionClick?: (action: string, data?: any) => void;
  className?: string;
}> = ({ 
  content, 
  timestamp = new Date().toISOString(), 
  metadata,
  structuredData,
  interactiveElements,
  onInteractionClick,
  ...props 
}) => {
  const message: StructuredAgentResponse = {
    type: 'agent_response',
    content,
    agent: AgentType.SALES,
    agent_metadata: metadata,
    timestamp,
    structured_data: structuredData,
    interactive_elements: interactiveElements
  };
  
  return (
    <EnhancedAgentMessage 
      message={message} 
      onInteractionClick={onInteractionClick}
      {...props} 
    />
  );
};

export const EnhancedTalentMessage: React.FC<{
  content: string;
  timestamp?: string;
  metadata?: AgentMetadata;
  structuredData?: any;
  interactiveElements?: any[];
  onInteractionClick?: (action: string, data?: any) => void;
  className?: string;
}> = ({ 
  content, 
  timestamp = new Date().toISOString(), 
  metadata,
  structuredData,
  interactiveElements,
  onInteractionClick,
  ...props 
}) => {
  const message: StructuredAgentResponse = {
    type: 'agent_response',
    content,
    agent: AgentType.TALENT,
    agent_metadata: metadata,
    timestamp,
    structured_data: structuredData,
    interactive_elements: interactiveElements
  };
  
  return (
    <EnhancedAgentMessage 
      message={message}
      onInteractionClick={onInteractionClick}
      {...props} 
    />
  );
};

export const EnhancedAnalyticsMessage: React.FC<{
  content: string;
  timestamp?: string;
  metadata?: AgentMetadata;
  structuredData?: any;
  interactiveElements?: any[];
  onInteractionClick?: (action: string, data?: any) => void;
  className?: string;
}> = ({ 
  content, 
  timestamp = new Date().toISOString(), 
  metadata,
  structuredData,
  interactiveElements,
  onInteractionClick,
  ...props 
}) => {
  const message: StructuredAgentResponse = {
    type: 'agent_response',
    content,
    agent: AgentType.ANALYTICS,
    agent_metadata: metadata,
    timestamp,
    structured_data: structuredData,
    interactive_elements: interactiveElements
  };
  
  return (
    <EnhancedAgentMessage 
      message={message}
      onInteractionClick={onInteractionClick}
      {...props} 
    />
  );
};