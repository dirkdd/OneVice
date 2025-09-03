import React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { AgentType, AgentMetadata } from "@/lib/api/types";
import { 
  TrendingUp, 
  Users, 
  BarChart3, 
  Clock, 
  CheckCircle2,
  AlertTriangle,
  XCircle
} from "lucide-react";

interface AgentBadgeProps {
  agent: AgentType;
  metadata?: AgentMetadata;
  size?: 'sm' | 'default' | 'lg';
  showConfidence?: boolean;
  showProcessingTime?: boolean;
  className?: string;
}

const agentConfig = {
  [AgentType.SALES]: {
    label: 'Sales Intelligence',
    icon: TrendingUp,
    colors: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      text: 'text-blue-400',
      glow: 'shadow-blue-500/20'
    }
  },
  [AgentType.TALENT]: {
    label: 'Talent Discovery',
    icon: Users,
    colors: {
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/30',
      text: 'text-purple-400',
      glow: 'shadow-purple-500/20'
    }
  },
  [AgentType.ANALYTICS]: {
    label: 'Leadership Analytics',
    icon: BarChart3,
    colors: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      text: 'text-emerald-400',
      glow: 'shadow-emerald-500/20'
    }
  }
} as const;

const confidenceConfig = {
  high: {
    icon: CheckCircle2,
    color: 'text-green-400',
    label: 'High Confidence'
  },
  medium: {
    icon: AlertTriangle,
    color: 'text-yellow-400',
    label: 'Medium Confidence'
  },
  low: {
    icon: XCircle,
    color: 'text-red-400',
    label: 'Low Confidence'
  }
} as const;

export const AgentBadge = React.forwardRef<
  HTMLDivElement,
  AgentBadgeProps
>(({
  agent,
  metadata,
  size = 'default',
  showConfidence = false,
  showProcessingTime = false,
  className,
  ...props
}, ref) => {
  const config = agentConfig[agent];
  const Icon = config.icon;
  
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

  return (
    <div 
      ref={ref}
      className={cn(
        'inline-flex items-center rounded-lg backdrop-blur-sm shadow-lg',
        'transition-all duration-300 hover:scale-105',
        config.colors.bg,
        config.colors.border,
        config.colors.text,
        config.colors.glow,
        'border',
        sizeClasses[size],
        className
      )}
      {...props}
    >
      <Icon className={cn(iconSizes[size], 'flex-shrink-0')} />
      
      <span className="font-medium whitespace-nowrap">
        {config.label}
      </span>
      
      {showConfidence && metadata?.confidence && (
        <>
          <div className="w-px h-4 bg-current/30 mx-1" />
          <div className="flex items-center gap-1">
            {React.createElement(
              confidenceConfig[metadata.confidence].icon,
              {
                className: cn(
                  iconSizes[size],
                  confidenceConfig[metadata.confidence].color
                )
              }
            )}
            {size !== 'sm' && (
              <span className={cn(
                'text-xs opacity-75',
                confidenceConfig[metadata.confidence].color
              )}>
                {metadata.confidence}
              </span>
            )}
          </div>
        </>
      )}
      
      {showProcessingTime && metadata?.processing_time && (
        <>
          <div className="w-px h-4 bg-current/30 mx-1" />
          <div className="flex items-center gap-1 opacity-75">
            <Clock className={cn(iconSizes[size])} />
            {size !== 'sm' && (
              <span className="text-xs">
                {metadata.processing_time}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
});

AgentBadge.displayName = "AgentBadge";

// Individual agent badge variants for convenience
export const SalesAgentBadge = (props: Omit<AgentBadgeProps, 'agent'>) => (
  <AgentBadge agent={AgentType.SALES} {...props} />
);

export const TalentAgentBadge = (props: Omit<AgentBadgeProps, 'agent'>) => (
  <AgentBadge agent={AgentType.TALENT} {...props} />
);

export const AnalyticsAgentBadge = (props: Omit<AgentBadgeProps, 'agent'>) => (
  <AgentBadge agent={AgentType.ANALYTICS} {...props} />
);

// Utility function to get agent color scheme
export const getAgentColorScheme = (agent: AgentType) => {
  return agentConfig[agent]?.colors || agentConfig[AgentType.SALES].colors;
};