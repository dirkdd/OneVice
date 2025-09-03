import React from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { AgentHandoff } from "@/types/conversation-history";
import { AgentBadge, getAgentColorScheme } from "./agent-badge";
import { 
  ArrowRightLeft,
  ArrowRight,
  Clock,
  MessageSquare,
  AlertCircle
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface AgentHandoffIndicatorProps {
  handoff: AgentHandoff;
  showTimestamp?: boolean;
  showReason?: boolean;
  size?: 'sm' | 'default' | 'lg';
  variant?: 'compact' | 'detailed' | 'inline';
  className?: string;
}

export const AgentHandoffIndicator = React.forwardRef<
  HTMLDivElement,
  AgentHandoffIndicatorProps
>(({
  handoff,
  showTimestamp = true,
  showReason = true,
  size = 'default',
  variant = 'detailed',
  className,
  ...props
}, ref) => {
  const { from_agent, to_agent, timestamp, reason, context_shift } = handoff;
  
  const fromColorScheme = from_agent ? getAgentColorScheme(from_agent) : null;
  const toColorScheme = getAgentColorScheme(to_agent);
  
  const sizeClasses = {
    sm: 'gap-1 text-xs',
    default: 'gap-2 text-sm',
    lg: 'gap-3 text-base'
  };
  
  const iconSizes = {
    sm: 'w-3 h-3',
    default: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  const timeAgo = formatDistanceToNow(new Date(timestamp), { addSuffix: true });

  // Compact variant - just an arrow with badges
  if (variant === 'compact') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div 
              ref={ref}
              className={cn(
                "inline-flex items-center",
                sizeClasses[size],
                className
              )}
              {...props}
            >
              {from_agent && <AgentBadge agent={from_agent} size={size} />}
              <ArrowRight className={cn(iconSizes[size], "text-muted-foreground")} />
              <AgentBadge agent={to_agent} size={size} />
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1 text-xs">
              <div className="font-medium">Agent Handoff</div>
              <div>{from_agent || 'User'} → {to_agent}</div>
              {reason && <div className="opacity-75">{reason}</div>}
              <div className="opacity-75">{timeAgo}</div>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Inline variant - minimal space usage
  if (variant === 'inline') {
    return (
      <Badge
        ref={ref}
        variant="outline"
        className={cn(
          "inline-flex items-center gap-1",
          toColorScheme.text,
          toColorScheme.border,
          className
        )}
        {...props}
      >
        <ArrowRightLeft className={iconSizes[size]} />
        <span>
          {from_agent ? `${from_agent} → ${to_agent}` : `→ ${to_agent}`}
        </span>
      </Badge>
    );
  }

  // Detailed variant - full information display
  return (
    <div
      ref={ref}
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg border bg-card/50 backdrop-blur-sm",
        "transition-all duration-200 hover:bg-card/80",
        toColorScheme.border,
        className
      )}
      {...props}
    >
      {/* Handoff icon */}
      <div className={cn(
        "flex-shrink-0 p-2 rounded-full",
        toColorScheme.bg,
        toColorScheme.border,
        "border"
      )}>
        <ArrowRightLeft className={cn(iconSizes[size], toColorScheme.text)} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-medium text-sm">Agent Handoff</span>
          {context_shift && (
            <Badge variant="secondary" className="text-xs">
              Context: {context_shift}
            </Badge>
          )}
        </div>

        {/* Agent transition */}
        <div className="flex items-center gap-3 mb-2">
          {from_agent ? (
            <AgentBadge agent={from_agent} size={size} />
          ) : (
            <Badge variant="outline" className="text-xs">
              User
            </Badge>
          )}
          
          <div className="flex items-center gap-1 text-muted-foreground">
            <ArrowRight className={iconSizes[size]} />
          </div>
          
          <AgentBadge agent={to_agent} size={size} />
        </div>

        {/* Additional details */}
        <div className="space-y-1">
          {showReason && reason && (
            <div className="flex items-start gap-2 text-xs text-muted-foreground">
              <AlertCircle className="w-3 h-3 flex-shrink-0 mt-0.5" />
              <span className="line-clamp-2">{reason}</span>
            </div>
          )}
          
          {showTimestamp && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>{timeAgo}</span>
              <span className="opacity-50">•</span>
              <span>{new Date(timestamp).toLocaleTimeString()}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

AgentHandoffIndicator.displayName = "AgentHandoffIndicator";

// Multiple handoffs summary component
interface AgentHandoffSummaryProps {
  handoffs: AgentHandoff[];
  maxVisible?: number;
  className?: string;
}

export const AgentHandoffSummary = React.forwardRef<
  HTMLDivElement,
  AgentHandoffSummaryProps
>(({ handoffs, maxVisible = 3, className, ...props }, ref) => {
  const visibleHandoffs = handoffs.slice(0, maxVisible);
  const remainingCount = handoffs.length - maxVisible;

  if (handoffs.length === 0) {
    return null;
  }

  return (
    <div
      ref={ref}
      className={cn("space-y-2", className)}
      {...props}
    >
      <div className="flex items-center gap-2 mb-2">
        <ArrowRightLeft className="w-4 h-4 text-muted-foreground" />
        <span className="text-sm font-medium">
          Agent Handoffs ({handoffs.length})
        </span>
      </div>

      <div className="space-y-2">
        {visibleHandoffs.map((handoff) => (
          <AgentHandoffIndicator
            key={handoff.id}
            handoff={handoff}
            variant="compact"
            size="sm"
          />
        ))}
        
        {remainingCount > 0 && (
          <Badge variant="secondary" className="text-xs">
            +{remainingCount} more handoff{remainingCount !== 1 ? 's' : ''}
          </Badge>
        )}
      </div>
    </div>
  );
});

AgentHandoffSummary.displayName = "AgentHandoffSummary";