import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { AgentType, AgentMetadata } from "@/lib/api/types";
import { AgentBadge, getAgentColorScheme } from "./agent-badge";
import { Card } from "./card";
import { Loader2, Brain, Zap, Search, Database } from "lucide-react";

interface AgentProcessingIndicatorProps {
  agent?: AgentType;
  message?: string;
  stage?: ProcessingStage;
  metadata?: AgentMetadata;
  className?: string;
}

type ProcessingStage = 
  | 'initializing'
  | 'analyzing'
  | 'searching'
  | 'processing' 
  | 'generating'
  | 'finalizing';

const processingStages: Record<ProcessingStage, { 
  label: string; 
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}> = {
  initializing: {
    label: 'Initializing',
    icon: Loader2,
    description: 'Starting up agent systems...'
  },
  analyzing: {
    label: 'Analyzing',
    icon: Brain,
    description: 'Understanding your query...'
  },
  searching: {
    label: 'Searching',
    icon: Search,
    description: 'Finding relevant data...'
  },
  processing: {
    label: 'Processing',
    icon: Database,
    description: 'Processing information...'
  },
  generating: {
    label: 'Generating',
    icon: Zap,
    description: 'Crafting response...'
  },
  finalizing: {
    label: 'Finalizing',
    icon: Loader2,
    description: 'Finishing up...'
  }
};

const agentMessages = {
  [AgentType.SALES]: [
    'Analyzing client opportunities...',
    'Reviewing revenue potential...',
    'Examining market trends...',
    'Calculating budget scenarios...',
    'Identifying strategic advantages...'
  ],
  [AgentType.TALENT]: [
    'Searching talent database...',
    'Analyzing team compositions...',
    'Evaluating skill matches...',
    'Reviewing availability windows...',
    'Optimizing resource allocation...'
  ],
  [AgentType.ANALYTICS]: [
    'Crunching performance metrics...',
    'Analyzing trend patterns...',
    'Calculating efficiency ratios...',
    'Processing KPI data...',
    'Generating insights...'
  ]
};

export const AgentProcessingIndicator: React.FC<AgentProcessingIndicatorProps> = ({
  agent,
  message,
  stage = 'processing',
  metadata,
  className
}) => {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [displayMessage, setDisplayMessage] = useState(message);

  const stageConfig = processingStages[stage];
  const StageIcon = stageConfig.icon;
  
  const colorScheme = agent ? getAgentColorScheme(agent) : null;
  
  // Cycle through agent-specific messages if no custom message provided
  useEffect(() => {
    if (!message && agent) {
      const messages = agentMessages[agent];
      const interval = setInterval(() => {
        setCurrentMessageIndex(prev => (prev + 1) % messages.length);
      }, 2000);
      
      return () => clearInterval(interval);
    }
  }, [message, agent]);

  // Update display message
  useEffect(() => {
    if (message) {
      setDisplayMessage(message);
    } else if (agent) {
      setDisplayMessage(agentMessages[agent][currentMessageIndex]);
    } else {
      setDisplayMessage(stageConfig.description);
    }
  }, [message, agent, currentMessageIndex, stageConfig.description]);

  return (
    <div className={cn("flex justify-start mb-4", className)}>
      <div className="max-w-[70%]">
        <div className="space-y-2">
          {/* Agent Badge if available */}
          {agent && (
            <div className="flex items-center gap-2">
              <AgentBadge 
                agent={agent}
                metadata={metadata}
                size="sm"
                className="animate-pulse"
              />
            </div>
          )}
          
          {/* Processing Card */}
          <Card 
            className={cn(
              "p-4 backdrop-blur-sm border transition-all duration-300",
              colorScheme ? [
                colorScheme.bg,
                colorScheme.border,
                colorScheme.glow,
                'shadow-lg'
              ] : [
                'bg-gray-800/70',
                'border-gray-700'
              ]
            )}
          >
            <div className="flex items-center gap-3">
              {/* Animated Processing Icon */}
              <div className="relative">
                <div 
                  className={cn(
                    "absolute inset-0 rounded-full opacity-20 animate-ping",
                    colorScheme?.bg || 'bg-gray-600'
                  )}
                />
                <div 
                  className={cn(
                    "relative p-2 rounded-full",
                    colorScheme?.bg || 'bg-gray-700'
                  )}
                >
                  <StageIcon 
                    className={cn(
                      "w-4 h-4 animate-spin",
                      colorScheme?.text || 'text-gray-300'
                    )}
                  />
                </div>
              </div>
              
              {/* Processing Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span 
                    className={cn(
                      "text-sm font-medium",
                      colorScheme?.text || 'text-gray-200'
                    )}
                  >
                    {stageConfig.label}
                  </span>
                  
                  {metadata?.query_complexity && (
                    <div className="px-2 py-0.5 bg-black/20 rounded text-xs opacity-75">
                      {metadata.query_complexity} query
                    </div>
                  )}
                </div>
                
                <div 
                  className={cn(
                    "text-xs opacity-75 animate-pulse",
                    colorScheme?.text || 'text-gray-300'
                  )}
                >
                  {displayMessage}
                </div>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="mt-3">
              <div className="h-1 bg-black/20 rounded-full overflow-hidden">
                <div 
                  className={cn(
                    "h-full rounded-full animate-pulse",
                    colorScheme?.text || 'bg-gray-400'
                  )}
                  style={{
                    background: colorScheme 
                      ? `linear-gradient(90deg, ${colorScheme.text.replace('text-', 'rgb(')}, transparent)`
                      : 'linear-gradient(90deg, rgb(156, 163, 175), transparent)',
                    animation: 'progress 2s ease-in-out infinite'
                  }}
                />
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Convenience components for each agent type
export const SalesProcessingIndicator: React.FC<Omit<AgentProcessingIndicatorProps, 'agent'>> = (props) => (
  <AgentProcessingIndicator agent={AgentType.SALES} {...props} />
);

export const TalentProcessingIndicator: React.FC<Omit<AgentProcessingIndicatorProps, 'agent'>> = (props) => (
  <AgentProcessingIndicator agent={AgentType.TALENT} {...props} />
);

export const AnalyticsProcessingIndicator: React.FC<Omit<AgentProcessingIndicatorProps, 'agent'>> = (props) => (
  <AgentProcessingIndicator agent={AgentType.ANALYTICS} {...props} />
);

// Add custom CSS for the progress animation
const style = `
  @keyframes progress {
    0% {
      width: 0%;
      opacity: 1;
    }
    50% {
      width: 60%;
      opacity: 0.8;
    }
    100% {
      width: 100%;
      opacity: 0.6;
    }
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = style;
  document.head.appendChild(styleElement);
}