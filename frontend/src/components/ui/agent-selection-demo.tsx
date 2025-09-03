import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AgentSelector } from "./agent-selector";
import { AgentSettingsPanel } from "./agent-settings-panel";
import { AgentBadge } from "./agent-badge";
import { useAgentPreferences, useContextAgents } from "@/contexts/AgentPreferencesContext";
import { AgentType, DashboardContext } from "@/lib/api/types";
import { Settings, Zap, Users, BarChart3 } from "lucide-react";

interface AgentSelectionDemoProps {
  className?: string;
}

export const AgentSelectionDemo: React.FC<AgentSelectionDemoProps> = ({ className }) => {
  const { preferences, updatePreferences, reset } = useAgentPreferences();
  
  // Simulate different dashboard contexts
  const contexts: DashboardContext[] = ['home', 'pre-call-brief', 'case-study', 'talent-discovery', 'bid-proposal'];
  const [currentContext, setCurrentContext] = React.useState<DashboardContext>('home');
  
  const { suggestedAgents, preferredAgent, routingMode } = useContextAgents(currentContext);

  return (
    <div className={`max-w-7xl mx-auto p-6 space-y-8 ${className}`}>
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-white">Agent Selection System Demo</h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Experience OneVice's intelligent agent routing system. Configure how AI agents handle your queries 
          and see how context-aware suggestions adapt to different dashboard views.
        </p>
      </div>

      {/* Context Selector */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Dashboard Context Simulation
          </CardTitle>
          <CardDescription>
            Switch between different dashboard contexts to see how agent suggestions adapt
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {contexts.map((context) => (
              <Button
                key={context}
                variant={currentContext === context ? "default" : "outline"}
                size="sm"
                onClick={() => setCurrentContext(context)}
                className={currentContext === context ? "bg-blue-600 hover:bg-blue-700" : ""}
              >
                {context.replace('-', ' ')}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Current Status Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Configuration */}
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white text-lg">Current Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="text-sm text-gray-400">Routing Mode</div>
              <div className="flex items-center gap-2">
                {preferences.routingMode === 'auto' ? (
                  <Zap className="w-4 h-4 text-emerald-400" />
                ) : preferences.routingMode === 'multi' ? (
                  <Users className="w-4 h-4 text-purple-400" />
                ) : (
                  <BarChart3 className="w-4 h-4 text-blue-400" />
                )}
                <span className="text-white capitalize">{preferences.routingMode}</span>
                {preferences.contextAware && (
                  <Badge variant="outline" className="text-green-400 border-green-400/30">
                    Context-Aware
                  </Badge>
                )}
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm text-gray-400">Selected Agents ({preferences.selectedAgents.length})</div>
              <div className="flex flex-wrap gap-2">
                {preferences.selectedAgents.map((agent) => (
                  <AgentBadge key={agent} agent={agent} size="sm" />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Context Suggestions */}
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white text-lg">Context Suggestions</CardTitle>
            <CardDescription>For "{currentContext}" context</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="text-sm text-gray-400">Suggested Agents</div>
              <div className="flex flex-wrap gap-2">
                {suggestedAgents.map((agent, index) => (
                  <div key={agent} className="flex items-center gap-1">
                    <AgentBadge agent={agent} size="sm" className="opacity-75" />
                    {index === 0 && <Badge variant="secondary" className="text-xs">Primary</Badge>}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm text-gray-400">Preferred Agent</div>
              <AgentBadge agent={preferredAgent} size="default" />
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <AgentSettingsPanel currentContext={currentContext} className="w-full" />
            
            <Button 
              variant="outline" 
              className="w-full"
              onClick={() => updatePreferences({
                ...preferences,
                routingMode: 'auto',
                selectedAgents: Object.values(AgentType),
                autoRouteEnabled: true,
                contextAware: true,
              })}
            >
              <Zap className="w-4 h-4 mr-2" />
              Enable Auto Mode
            </Button>
            
            <Button 
              variant="outline" 
              className="w-full"
              onClick={reset}
            >
              Reset to Defaults
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Agent Configuration Panel */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white">Agent Configuration</CardTitle>
          <CardDescription>
            Configure your agent preferences. Changes are automatically saved to localStorage.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AgentSelector preferences={preferences} onChange={updatePreferences} />
        </CardContent>
      </Card>

      {/* Implementation Info */}
      <Card className="bg-gray-900/50 border-gray-600/30">
        <CardHeader>
          <CardTitle className="text-white">Implementation Features</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-medium text-gray-300">✅ Completed Features</h4>
              <ul className="space-y-1 text-gray-400">
                <li>• Interactive agent selection cards</li>
                <li>• Three routing modes (single/multi/auto)</li>
                <li>• Context-aware agent suggestions</li>
                <li>• User preference persistence (localStorage)</li>
                <li>• WebSocket integration with metadata</li>
                <li>• Responsive design with OneVice styling</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium text-gray-300">🔧 Integration Points</h4>
              <ul className="space-y-1 text-gray-400">
                <li>• ChatInterface shows current agent status</li>
                <li>• Settings panel accessible from chat</li>
                <li>• Agent preferences sent with WebSocket messages</li>
                <li>• Context-aware placeholder text</li>
                <li>• Real-time preference updates</li>
                <li>• Mobile-responsive agent settings</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};