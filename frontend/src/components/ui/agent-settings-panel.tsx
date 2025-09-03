import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Settings, ChevronRight, Zap, Users, TrendingUp, BarChart3 } from "lucide-react";
import { AgentSelector, RoutingMode } from "./agent-selector";
import { useAgentPreferences, useContextAgents } from "@/contexts/AgentPreferencesContext";
import { AgentType, DashboardContext } from "@/lib/api/types";
import { AgentBadge } from "./agent-badge";

interface AgentSettingsPanelProps {
  currentContext?: DashboardContext;
  className?: string;
  trigger?: React.ReactNode;
}

const routingModeIcons = {
  single: Users,
  multi: TrendingUp, 
  auto: Zap,
};

const agentTypeIcons = {
  [AgentType.SALES]: TrendingUp,
  [AgentType.TALENT]: Users,
  [AgentType.ANALYTICS]: BarChart3,
};

interface AgentStatusIndicatorProps {
  preferences: ReturnType<typeof useAgentPreferences>['preferences'];
  suggestedAgents: AgentType[];
  preferredAgent: AgentType;
  className?: string;
}

const AgentStatusIndicator: React.FC<AgentStatusIndicatorProps> = ({
  preferences,
  suggestedAgents,
  preferredAgent,
  className
}) => {
  const RoutingIcon = routingModeIcons[preferences.routingMode];
  
  const getStatusText = () => {
    switch (preferences.routingMode) {
      case 'single':
        return `${preferences.selectedAgents.length} agent selected`;
      case 'multi':
        return `${preferences.selectedAgents.length} agents active`;
      case 'auto':
        return 'Auto-routing enabled';
      default:
        return 'Agent routing configured';
    }
  };

  const getStatusColor = () => {
    switch (preferences.routingMode) {
      case 'single':
        return preferences.selectedAgents.length === 1 ? 'text-blue-400' : 'text-yellow-400';
      case 'multi':
        return preferences.selectedAgents.length > 0 ? 'text-purple-400' : 'text-red-400';
      case 'auto':
        return 'text-emerald-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className={cn("flex items-center gap-2 text-sm", className)}>
      <RoutingIcon className={cn("w-4 h-4", getStatusColor())} />
      <span className={getStatusColor()}>{getStatusText()}</span>
      {preferences.contextAware && (
        <Badge variant="outline" className="text-xs border-green-400/30 text-green-400">
          Context-Aware
        </Badge>
      )}
    </div>
  );
};

export const AgentSettingsPanel: React.FC<AgentSettingsPanelProps> = ({
  currentContext,
  className,
  trigger
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { preferences, updatePreferences } = useAgentPreferences();
  const { suggestedAgents, preferredAgent } = useContextAgents(currentContext);

  const handlePreferencesChange = (newPreferences: typeof preferences) => {
    updatePreferences(newPreferences);
  };

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        {trigger ? (
          trigger
        ) : (
          <Button 
            variant="outline" 
            className={cn(
              "flex items-center gap-2 bg-gray-800/50 border-gray-700 hover:bg-gray-800/70",
              "transition-all duration-300 hover:scale-[1.02]",
              className
            )}
          >
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">Agent Settings</span>
            <ChevronRight className="w-3 h-3 opacity-60" />
          </Button>
        )}
      </SheetTrigger>
      
      <SheetContent 
        side="right" 
        className="w-full sm:max-w-xl md:max-w-2xl"
      >
        <SheetHeader>
          <SheetTitle>Agent Configuration</SheetTitle>
          <SheetDescription>
            Configure how OneVice AI agents handle your queries and provide insights.
          </SheetDescription>
        </SheetHeader>
        
        <div className="mt-6 space-y-6 pb-6">
          {/* Current Status */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-300">Current Setup</h3>
            <div className="bg-gray-800/50 rounded-lg p-4 space-y-3">
              <AgentStatusIndicator
                preferences={preferences}
                suggestedAgents={suggestedAgents}
                preferredAgent={preferredAgent}
              />
              
              {/* Active Agents Display */}
              {preferences.selectedAgents.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs text-gray-400 font-medium">Active Agents:</span>
                  <div className="flex flex-wrap gap-2">
                    {preferences.selectedAgents.map((agentType) => (
                      <AgentBadge
                        key={agentType}
                        agent={agentType}
                        size="sm"
                        className="opacity-90"
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Context Suggestions */}
              {currentContext && preferences.contextAware && suggestedAgents.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-gray-700">
                  <span className="text-xs text-gray-400 font-medium">
                    Suggested for "{currentContext}":
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {suggestedAgents.slice(0, 3).map((agentType) => (
                      <AgentBadge
                        key={agentType}
                        agent={agentType}
                        size="sm"
                        className="opacity-75 scale-90"
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Agent Configuration */}
          <div className="space-y-4">
            <AgentSelector
              preferences={preferences}
              onChange={handlePreferencesChange}
            />
          </div>

          {/* Quick Actions */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-300">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                className="bg-gray-800/30 border-gray-700 hover:bg-gray-800/50"
                onClick={() => handlePreferencesChange({
                  ...preferences,
                  routingMode: 'auto',
                  selectedAgents: Object.values(AgentType),
                  autoRouteEnabled: true,
                })}
              >
                <Zap className="w-4 h-4 mr-2" />
                Auto Mode
              </Button>
              <Button
                variant="outline"
                className="bg-gray-800/30 border-gray-700 hover:bg-gray-800/50"
                onClick={() => handlePreferencesChange({
                  ...preferences,
                  routingMode: 'single',
                  selectedAgents: [preferredAgent],
                  autoRouteEnabled: false,
                })}
              >
                <Users className="w-4 h-4 mr-2" />
                Single Agent
              </Button>
            </div>
          </div>

          {/* Footer Info */}
          <div className="text-xs text-gray-500 bg-gray-800/30 rounded-lg p-3">
            <div className="space-y-1">
              <p>• <strong>Auto Mode:</strong> AI automatically selects the best agent for each query</p>
              <p>• <strong>Single Agent:</strong> All queries go to one specialized agent</p>
              <p>• <strong>Multi-Agent:</strong> Multiple agents provide comprehensive insights</p>
              <p>• <strong>Context-Aware:</strong> Agent suggestions adapt to your current dashboard view</p>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

// Compact version for mobile/small spaces
export const AgentSettingsButton: React.FC<AgentSettingsPanelProps> = ({
  currentContext,
  className
}) => {
  const { preferences } = useAgentPreferences();
  const { preferredAgent } = useContextAgents(currentContext);
  
  return (
    <AgentSettingsPanel currentContext={currentContext} className={className}>
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          "flex items-center gap-2 text-gray-400 hover:text-gray-300",
          className
        )}
      >
        <Settings className="w-4 h-4" />
        {preferences.routingMode === 'auto' ? (
          <Zap className="w-4 h-4 text-emerald-400" />
        ) : (
          <AgentBadge agent={preferredAgent} size="sm" />
        )}
      </Button>
    </AgentSettingsPanel>
  );
};