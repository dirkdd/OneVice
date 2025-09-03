import React from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { AgentType } from "@/lib/api/types";
import { AgentParticipationData } from "@/types/conversation-history";
import { getAgentColorScheme } from "@/components/ui/agent-badge";
import { 
  Clock, 
  MessageSquare, 
  TrendingUp, 
  ArrowRightLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle 
} from "lucide-react";

interface AgentParticipationBadgeProps {
  agent: AgentType;
  data: AgentParticipationData;
  size?: 'sm' | 'default' | 'lg';
  showDetails?: boolean;
  showPercentage?: boolean;
  showConfidence?: boolean;
  className?: string;
}

const confidenceConfig = {
  high: { icon: CheckCircle2, color: 'text-green-400', threshold: 2.5 },
  medium: { icon: AlertTriangle, color: 'text-yellow-400', threshold: 1.5 },
  low: { icon: XCircle, color: 'text-red-400', threshold: 0 },
} as const;

const getConfidenceLevel = (score: number): keyof typeof confidenceConfig => {
  if (score >= confidenceConfig.high.threshold) return 'high';
  if (score >= confidenceConfig.medium.threshold) return 'medium';
  return 'low';
};

export const AgentParticipationBadge = React.forwardRef<
  HTMLDivElement,
  AgentParticipationBadgeProps
>(({
  agent,
  data,
  size = 'default',
  showDetails = false,
  showPercentage = true,
  showConfidence = false,
  className,
  ...props
}, ref) => {
  const colorScheme = getAgentColorScheme(agent);
  const confidenceLevel = getConfidenceLevel(data.avg_confidence);
  const confidenceInfo = confidenceConfig[confidenceLevel];
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs gap-1',
    default: 'px-3 py-1.5 text-sm gap-1.5',
    lg: 'px-4 py-2 text-base gap-2'
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    default: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatPercentage = (percentage: number) => {
    return `${Math.round(percentage)}%`;
  };

  const badge = (
    <div 
      ref={ref}
      className={cn(
        'inline-flex items-center rounded-lg backdrop-blur-sm shadow-lg',
        'transition-all duration-300 hover:scale-105',
        colorScheme.bg,
        colorScheme.border,
        colorScheme.text,
        colorScheme.glow,
        'border',
        sizeClasses[size],
        className
      )}
      {...props}
    >
      <MessageSquare className={cn(iconSizes[size], 'flex-shrink-0')} />
      
      <span className="font-medium">
        {data.message_count}
      </span>
      
      {showPercentage && (
        <>
          <div className="w-px h-4 bg-current/30 mx-1" />
          <span className="text-xs opacity-75">
            {formatPercentage(data.percentage)}
          </span>
        </>
      )}
      
      {showConfidence && (
        <>
          <div className="w-px h-4 bg-current/30 mx-1" />
          <div className="flex items-center gap-1">
            {React.createElement(confidenceInfo.icon, {
              className: cn(iconSizes[size], confidenceInfo.color)
            })}
          </div>
        </>
      )}
      
      {showDetails && size !== 'sm' && (
        <>
          <div className="w-px h-4 bg-current/30 mx-1" />
          <div className="flex items-center gap-2 text-xs opacity-75">
            <div className="flex items-center gap-1">
              <Clock className={iconSizes[size]} />
              <span>{formatTime(data.avg_processing_time)}</span>
            </div>
            
            {data.handoffs_initiated > 0 && (
              <div className="flex items-center gap-1">
                <ArrowRightLeft className={iconSizes[size]} />
                <span>{data.handoffs_initiated}</span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );

  // Wrap in tooltip for additional details
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {badge}
        </TooltipTrigger>
        <TooltipContent 
          side="bottom" 
          className={cn(
            "max-w-xs p-3 space-y-2",
            colorScheme.bg,
            colorScheme.border,
            colorScheme.text
          )}
        >
          <div className="font-medium text-sm">
            {agent.charAt(0).toUpperCase() + agent.slice(1)} Agent Activity
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="opacity-75">Messages:</span>
              <span className="font-medium ml-1">{data.message_count}</span>
            </div>
            <div>
              <span className="opacity-75">Share:</span>
              <span className="font-medium ml-1">{formatPercentage(data.percentage)}</span>
            </div>
            <div>
              <span className="opacity-75">Avg Time:</span>
              <span className="font-medium ml-1">{formatTime(data.avg_processing_time)}</span>
            </div>
            <div>
              <span className="opacity-75">Confidence:</span>
              <span className={cn("font-medium ml-1", confidenceInfo.color)}>
                {confidenceLevel}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="opacity-75">First Used:</span>
              <span className="font-medium ml-1 block">
                {new Date(data.first_appearance).toLocaleDateString()}
              </span>
            </div>
            <div>
              <span className="opacity-75">Last Used:</span>
              <span className="font-medium ml-1 block">
                {new Date(data.last_appearance).toLocaleDateString()}
              </span>
            </div>
          </div>
          
          {(data.handoffs_initiated > 0 || data.handoffs_received > 0) && (
            <div className="border-t border-current/20 pt-2">
              <div className="text-xs opacity-75 mb-1">Agent Handoffs:</div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <TrendingUp className="w-3 h-3 inline mr-1" />
                  <span>Initiated: {data.handoffs_initiated}</span>
                </div>
                <div>
                  <TrendingUp className="w-3 h-3 inline mr-1 rotate-180" />
                  <span>Received: {data.handoffs_received}</span>
                </div>
              </div>
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
});

AgentParticipationBadge.displayName = "AgentParticipationBadge";