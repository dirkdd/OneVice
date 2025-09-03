import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Paperclip, Mic, AlertCircle, Loader2, Bot, Settings } from "lucide-react";
import { DashboardContext } from "../Dashboard";
import { useWebSocket } from "@/hooks/useWebSocket";
import { WebSocketMessage, AgentType } from "@/lib/api/types";
import { AgentMessage } from "@/components/ui/agent-message";
import { AgentProcessingIndicator } from "@/components/ui/agent-processing-indicator";
import { AgentSettingsPanel } from "@/components/ui/agent-settings-panel";
import { useAgentPreferences, useContextAgents } from "@/contexts/AgentPreferencesContext";
import xIcon from "@assets/x1.png";

interface ChatInterfaceProps {
  context: DashboardContext;
}

export const ChatInterface = ({ context }: ChatInterfaceProps): JSX.Element => {
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [activeAgent, setActiveAgent] = useState<AgentType | null>(null);
  const [processingStage, setProcessingStage] = useState<string>('processing');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Agent preferences
  const { preferences, updatePreferences } = useAgentPreferences();
  const { suggestedAgents, preferredAgent, routingMode } = useContextAgents(context);

  const {
    isConnected,
    isConnecting,
    error,
    messages,
    sendMessage,
    clearError,
    reconnect,
  } = useWebSocket({
    agentPreferences: preferences,
    onMessage: (message) => {
      if (message.type === 'ai_response' || message.type === 'agent_response') {
        setIsTyping(false);
        setActiveAgent(null);
      } else if (message.type === 'typing') {
        setIsTyping(true);
        // Detect agent type from message content, response, or use preferred agent
        const detectedAgent = message.agent || getAgentFromContext(context, message.content);
        setActiveAgent(detectedAgent);
      }
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      setIsTyping(false);
      setActiveAgent(null);
    },
  });

  // Utility function to determine which agent should handle the context
  const getAgentFromContext = (context: DashboardContext, content?: string): AgentType => {
    // If auto-routing is disabled, use the preferred agent from user preferences
    if (preferences.routingMode !== 'auto') {
      return preferredAgent;
    }

    // Check message content for agent-specific keywords
    if (content) {
      const lowerContent = content.toLowerCase();
      if (lowerContent.includes('talent') || lowerContent.includes('team') || lowerContent.includes('resource')) {
        return AgentType.TALENT;
      }
      if (lowerContent.includes('budget') || lowerContent.includes('revenue') || lowerContent.includes('sales')) {
        return AgentType.SALES;
      }
      if (lowerContent.includes('analytics') || lowerContent.includes('performance') || lowerContent.includes('metrics')) {
        return AgentType.ANALYTICS;
      }
    }

    // Use suggested agents from context or fall back to preferred
    return suggestedAgents[0] || preferredAgent;
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  

  const getPlaceholderText = () => {
    if (!isConnected) {
      return isConnecting ? "Connecting to AI assistant..." : "Disconnected - Click to reconnect";
    }
    
    if (preferences.routingMode === 'auto') {
      return "Ask anything - AI will route to the best agent automatically...";
    }
    
    if (preferences.routingMode === 'multi') {
      return "Ask anything - multiple agents will provide comprehensive insights...";
    }
    
    // Single agent mode - customize based on selected agent
    const selectedAgent = preferences.selectedAgents[0] || preferredAgent;
    switch (selectedAgent) {
      case AgentType.SALES:
        return "Ask Sales Intelligence about clients, budgets, proposals, or market insights...";
      case AgentType.TALENT:
        return "Ask Talent Discovery about team matching, skills, availability, or resources...";
      case AgentType.ANALYTICS:
        return "Ask Leadership Analytics about performance, forecasting, or strategic analysis...";
      default:
        return "Ask our AI agents about projects, talent, finances, or strategic opportunities...";
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const message = inputValue.trim();
    if (!message || !isConnected) return;

    sendMessage(message, context, {
      timestamp: new Date().toISOString(),
      user_context: context,
    });

    setInputValue("");
    setIsTyping(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleReconnect = () => {
    clearError();
    reconnect();
  };

  const renderMessage = (message: WebSocketMessage, index: number) => {
    const isSystem = message.type === 'system';
    
    if (isSystem) return null;

    return (
      <AgentMessage
        key={index}
        message={message}
        className="mx-auto max-w-6xl"
      />
    );
  };

  return (
    <div className="border-t lg:border-t-0 lg:border-l border-gray-800 flex flex-col h-full">
      {/* Messages Area - Always present to take up space */}
      <div className="flex-1 overflow-y-auto">
        {messages.length > 0 && (
          <div className="p-6 pb-2">
          <div className="max-w-6xl mx-auto">
            {messages.map(renderMessage)}
            
            {/* Agent Processing Indicator */}
            {isTyping && (
              <div className="mx-auto max-w-6xl">
                <AgentProcessingIndicator
                  agent={activeAgent || undefined}
                  stage={processingStage as any}
                  metadata={{
                    agent_type: activeAgent || AgentType.SALES,
                    query_complexity: 'moderate'
                  }}
                />
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-900/20 border-b border-red-500/30 p-3">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span className="text-red-400 text-sm">{error}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReconnect}
              className="text-red-400 hover:text-red-300"
            >
              Reconnect
            </Button>
          </div>
        </div>
      )}

      {/* Input Area - Always at bottom */}
      <div className="mt-auto p-6 bg-[#0a0a0b] border-t border-gray-800/50">
        <div className="max-w-6xl mx-auto">
          {/* Agent Settings Row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Bot className="w-5 h-5 text-gray-400" />
              <span className="text-sm text-gray-400">
                {preferences.routingMode === 'auto' 
                  ? 'Auto-routing enabled' 
                  : preferences.routingMode === 'multi'
                  ? `${preferences.selectedAgents.length} agents active`
                  : `Using ${preferences.selectedAgents.length} agent`
                }
              </span>
              {preferences.contextAware && (
                <div className="text-xs text-green-400 opacity-75">
                  • Context-aware
                </div>
              )}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={getPlaceholderText()}
                className="bg-gray-800/50 border-gray-700 text-white placeholder-gray-400 pr-32 py-3"
                disabled={!isConnected && !error}
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                <AgentSettingsPanel 
                  currentContext={context}
                  trigger={
                    <Button 
                      type="button"
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8"
                      disabled={!isConnected}
                      title="Agent Settings"
                    >
                      <Settings className="w-4 h-4" />
                    </Button>
                  }
                />
                <Button 
                  type="button"
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8"
                  disabled={!isConnected}
                >
                  <Paperclip className="w-4 h-4" />
                </Button>
                <Button 
                  type="button"
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8"
                  disabled={!isConnected}
                >
                  <Mic className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            <button 
              type="submit"
              disabled={!inputValue.trim() || !isConnected || isTyping}
              className="flex items-center justify-center hover:opacity-80 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isConnecting ? (
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              ) : (
                <img 
                  src={xIcon} 
                  alt="Send" 
                  className="h-10 w-auto"
                />
              )}
            </button>
          </form>
          
          <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span>Press Enter to Submit • ⌘+Enter for new line</span>
              <div className="flex items-center gap-1">
                <div 
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <span>
                  {isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}
                </span>
              </div>
            </div>
            <span>AI-powered by OneVice Intelligence</span>
          </div>
        </div>
      </div>
    </div>
  );
};