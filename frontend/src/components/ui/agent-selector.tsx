import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { AgentType } from "@/lib/api/types";
import { 
  TrendingUp, 
  Users, 
  BarChart3, 
  Settings,
  Zap,
  Brain,
  CheckCircle2,
  Circle
} from "lucide-react";

export type RoutingMode = 'single' | 'multi' | 'auto';

export interface AgentPreferences {
  routingMode: RoutingMode;
  selectedAgents: AgentType[];
  autoRouteEnabled: boolean;
  contextAware: boolean;
}

interface AgentSelectorProps {
  preferences: AgentPreferences;
  onChange: (preferences: AgentPreferences) => void;
  className?: string;
}

interface AgentInfo {
  type: AgentType;
  label: string;
  description: string;
  capabilities: string[];
  icon: React.ComponentType<any>;
  colors: {
    bg: string;
    border: string;
    text: string;
    glow: string;
    accent: string;
  };
}

const agentInfo: Record<AgentType, AgentInfo> = {
  [AgentType.SALES]: {
    type: AgentType.SALES,
    label: 'Sales Intelligence',
    description: 'Market analysis, client research, budget optimization, and strategic sales insights',
    capabilities: [
      'Market Analysis',
      'Lead Qualification', 
      'Client Research',
      'Budget Optimization',
      'Proposal Strategy',
      'Revenue Forecasting'
    ],
    icon: TrendingUp,
    colors: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      text: 'text-blue-400',
      glow: 'shadow-blue-500/20',
      accent: 'bg-blue-500'
    }
  },
  [AgentType.TALENT]: {
    type: AgentType.TALENT,
    label: 'Talent Discovery',
    description: 'Crew matching, skill assessment, team optimization, and resource allocation',
    capabilities: [
      'Crew Matching',
      'Skill Assessment',
      'Availability Tracking',
      'Team Optimization',
      'Resource Planning',
      'Performance Analysis'
    ],
    icon: Users,
    colors: {
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/30', 
      text: 'text-purple-400',
      glow: 'shadow-purple-500/20',
      accent: 'bg-purple-500'
    }
  },
  [AgentType.ANALYTICS]: {
    type: AgentType.ANALYTICS,
    label: 'Leadership Analytics',
    description: 'Performance metrics, strategic forecasting, portfolio analysis, and executive insights',
    capabilities: [
      'Performance Metrics',
      'Strategic Forecasting',
      'Portfolio Analysis', 
      'Executive Dashboards',
      'ROI Analysis',
      'Decision Support'
    ],
    icon: BarChart3,
    colors: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      text: 'text-emerald-400',
      glow: 'shadow-emerald-500/20',
      accent: 'bg-emerald-500'
    }
  }
};

const routingModeInfo = {
  single: {
    label: 'Single Agent',
    description: 'Route all queries to one specific agent',
    icon: Circle,
    benefit: 'Specialized expertise'
  },
  multi: {
    label: 'Multi-Agent',
    description: 'Use multiple agents and synthesize responses',
    icon: Brain,
    benefit: 'Comprehensive insights'
  },
  auto: {
    label: 'Auto-Route',
    description: 'Let AI choose the best agent for each query',
    icon: Zap,
    benefit: 'Intelligent optimization'
  }
};

interface AgentCardProps {
  agent: AgentInfo;
  isSelected: boolean;
  isDisabled: boolean;
  onToggle: (agentType: AgentType) => void;
}

const AgentCard: React.FC<AgentCardProps> = ({ 
  agent, 
  isSelected, 
  isDisabled,
  onToggle 
}) => {
  const Icon = agent.icon;
  
  return (
    <Card 
      className={cn(
        "relative overflow-hidden cursor-pointer transition-all duration-300",
        "hover:scale-[1.02] hover:shadow-xl",
        isSelected ? [
          agent.colors.bg,
          agent.colors.border,
          'border-2',
          `hover:${agent.colors.glow}`,
          'shadow-lg'
        ] : [
          'bg-gray-800/30',
          'border-gray-700/50',
          'hover:bg-gray-800/50',
          'hover:border-gray-600'
        ],
        isDisabled && 'opacity-50 cursor-not-allowed'
      )}
      onClick={() => !isDisabled && onToggle(agent.type)}
    >
      {/* Selection Indicator */}
      <div className={cn(
        "absolute top-3 right-3 transition-all duration-300",
        isSelected ? agent.colors.text : 'text-gray-500'
      )}>
        {isSelected ? (
          <CheckCircle2 className="w-5 h-5" />
        ) : (
          <Circle className="w-5 h-5" />
        )}
      </div>

      {/* Gradient Overlay */}
      {isSelected && (
        <div className="absolute inset-0 bg-gradient-to-br from-current/5 to-transparent pointer-events-none" />
      )}

      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-start gap-3">
            <div className={cn(
              "p-2 rounded-lg",
              isSelected ? agent.colors.accent : 'bg-gray-700'
            )}>
              <Icon className={cn(
                "w-5 h-5",
                isSelected ? 'text-white' : 'text-gray-300'
              )} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className={cn(
                "font-semibold text-lg",
                isSelected ? agent.colors.text : 'text-gray-200'
              )}>
                {agent.label}
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                {agent.description}
              </p>
            </div>
          </div>

          {/* Capabilities */}
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wide">
              Key Capabilities
            </h4>
            <div className="flex flex-wrap gap-1">
              {agent.capabilities.slice(0, 4).map((capability) => (
                <Badge
                  key={capability}
                  variant="secondary"
                  className={cn(
                    "text-xs px-2 py-1",
                    isSelected ? [
                      agent.colors.bg,
                      agent.colors.text,
                      'border',
                      agent.colors.border
                    ] : [
                      'bg-gray-700/50',
                      'text-gray-300',
                      'border-gray-600'
                    ]
                  )}
                >
                  {capability}
                </Badge>
              ))}
              {agent.capabilities.length > 4 && (
                <Badge
                  variant="secondary"
                  className="text-xs px-2 py-1 bg-gray-700/50 text-gray-400"
                >
                  +{agent.capabilities.length - 4} more
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  preferences,
  onChange,
  className
}) => {
  const handleRoutingModeChange = (mode: RoutingMode) => {
    const newPreferences: AgentPreferences = {
      ...preferences,
      routingMode: mode,
      // Set autoRouteEnabled based on routing mode
      autoRouteEnabled: mode === 'auto',
    };

    // Adjust selected agents based on routing mode
    if (mode === 'single' && preferences.selectedAgents.length > 1) {
      newPreferences.selectedAgents = [preferences.selectedAgents[0]];
    } else if (mode === 'auto') {
      newPreferences.selectedAgents = Object.values(AgentType);
    }

    onChange(newPreferences);
  };

  const handleAgentToggle = (agentType: AgentType) => {
    let newSelectedAgents: AgentType[];

    if (preferences.routingMode === 'single') {
      // Single mode: only one agent can be selected
      newSelectedAgents = [agentType];
    } else {
      // Multi mode: toggle agent in array
      if (preferences.selectedAgents.includes(agentType)) {
        newSelectedAgents = preferences.selectedAgents.filter(a => a !== agentType);
      } else {
        newSelectedAgents = [...preferences.selectedAgents, agentType];
      }
    }

    onChange({
      ...preferences,
      selectedAgents: newSelectedAgents,
      // Ensure autoRouteEnabled stays consistent with routing mode
      autoRouteEnabled: preferences.routingMode === 'auto'
    });
  };

  const handleContextAwareToggle = (enabled: boolean) => {
    onChange({
      ...preferences,
      contextAware: enabled,
      // Ensure autoRouteEnabled stays consistent with routing mode
      autoRouteEnabled: preferences.routingMode === 'auto'
    });
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="flex items-center justify-center gap-2">
          <Settings className="w-5 h-5 text-gray-400" />
          <h2 className="text-xl font-semibold text-white">Agent Selection</h2>
        </div>
        <p className="text-gray-400 text-sm max-w-md mx-auto">
          Choose how you want to interact with OneVice AI agents. You can use single agents for specialized tasks or multiple agents for comprehensive insights.
        </p>
      </div>

      {/* Routing Mode Selection */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-white">Routing Mode</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(routingModeInfo).map(([mode, info]) => {
            const Icon = info.icon;
            const isSelected = preferences.routingMode === mode;
            
            return (
              <Card
                key={mode}
                className={cn(
                  "cursor-pointer transition-all duration-300",
                  "hover:scale-[1.02]",
                  isSelected ? [
                    'bg-white/10',
                    'border-white/30',
                    'shadow-lg'
                  ] : [
                    'bg-gray-800/30',
                    'border-gray-700/50',
                    'hover:bg-gray-800/50'
                  ]
                )}
                onClick={() => handleRoutingModeChange(mode as RoutingMode)}
              >
                <CardContent className="p-4 text-center space-y-3">
                  <div className={cn(
                    "mx-auto w-12 h-12 rounded-lg flex items-center justify-center",
                    isSelected ? 'bg-white/20' : 'bg-gray-700'
                  )}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h4 className="font-medium text-white">{info.label}</h4>
                    <p className="text-xs text-gray-400 mt-1">{info.description}</p>
                    <Badge 
                      variant="secondary" 
                      className="mt-2 text-xs bg-gray-700/50 text-gray-300"
                    >
                      {info.benefit}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Agent Selection Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-white">Available Agents</h3>
          {preferences.routingMode !== 'auto' && (
            <Badge variant="outline" className="text-gray-300">
              {preferences.routingMode === 'single' 
                ? 'Select 1 agent' 
                : `${preferences.selectedAgents.length} selected`}
            </Badge>
          )}
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {Object.values(agentInfo).map((agent) => (
            <AgentCard
              key={agent.type}
              agent={agent}
              isSelected={preferences.selectedAgents.includes(agent.type)}
              isDisabled={preferences.routingMode === 'auto'}
              onToggle={handleAgentToggle}
            />
          ))}
        </div>
      </div>

      {/* Context Awareness Setting */}
      <Card className="bg-gray-800/30 border-gray-700/50">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label className="text-white font-medium">Context-Aware Suggestions</Label>
              <p className="text-sm text-gray-400">
                Automatically suggest relevant agents based on your current dashboard context
              </p>
            </div>
            <Switch
              checked={preferences.contextAware}
              onCheckedChange={handleContextAwareToggle}
            />
          </div>
        </CardContent>
      </Card>

      {/* Selection Summary */}
      <Card className="bg-gray-900/50 border-gray-700/30">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-300">
              Current Setup:
            </span>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-gray-300">
                {routingModeInfo[preferences.routingMode].label}
              </Badge>
              {preferences.routingMode !== 'auto' && (
                <Badge variant="outline" className="text-gray-300">
                  {preferences.selectedAgents.length} agent{preferences.selectedAgents.length !== 1 ? 's' : ''}
                </Badge>
              )}
              {preferences.contextAware && (
                <Badge variant="outline" className="text-green-400 border-green-400/30">
                  Context-Aware
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};