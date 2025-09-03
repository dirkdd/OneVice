import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { ConversationTimelineEvent, TimelineGroup, ConversationThread } from "@/types/conversation-history";
import { AgentBadge } from "./agent-badge";
import { 
  MessageSquare, 
  ArrowRightLeft, 
  Star, 
  Download, 
  Settings,
  Clock,
  ChevronDown,
  ChevronRight,
  Calendar
} from "lucide-react";
import { formatDistanceToNow, format, isSameDay, startOfDay } from "date-fns";

interface ConversationTimelineProps {
  conversation: ConversationThread;
  events: ConversationTimelineEvent[];
  onEventClick?: (event: ConversationTimelineEvent) => void;
  className?: string;
}

const eventTypeConfig = {
  message: {
    icon: MessageSquare,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
  },
  agent_handoff: {
    icon: ArrowRightLeft,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
  },
  context_change: {
    icon: Settings,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/30',
  },
  rating: {
    icon: Star,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
  },
  export: {
    icon: Download,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
  },
};

const TimelineEvent = React.memo<{
  event: ConversationTimelineEvent;
  onClick?: (event: ConversationTimelineEvent) => void;
  isLast?: boolean;
}>(({ event, onClick, isLast = false }) => {
  const config = eventTypeConfig[event.type];
  const Icon = config.icon;
  
  return (
    <div className="relative flex gap-3 group">
      {/* Timeline line */}
      {!isLast && (
        <div className="absolute left-4 top-10 bottom-0 w-px bg-border/50 group-hover:bg-border transition-colors" />
      )}
      
      {/* Event marker */}
      <div className={cn(
        "relative z-10 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        "border-2 backdrop-blur-sm transition-all duration-200",
        config.bgColor,
        config.borderColor,
        onClick && "cursor-pointer hover:scale-110"
      )}>
        <Icon className={cn("w-4 h-4", config.color)} />
      </div>
      
      {/* Event content */}
      <div 
        className={cn(
          "flex-1 min-w-0 pb-6",
          onClick && "cursor-pointer"
        )}
        onClick={() => onClick?.(event)}
      >
        <div className="flex items-start justify-between gap-2 mb-1">
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm group-hover:text-primary transition-colors line-clamp-1">
              {event.title}
            </h4>
            {event.description && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {event.description}
              </p>
            )}
          </div>
          
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            <span>{format(new Date(event.timestamp), 'HH:mm')}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2 mt-2">
          {event.agent && (
            <AgentBadge agent={event.agent} size="sm" />
          )}
          
          {event.metadata && Object.keys(event.metadata).length > 0 && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="text-xs cursor-help">
                    +{Object.keys(event.metadata).length} more
                  </Badge>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-xs">
                  <div className="space-y-1 text-xs">
                    {Object.entries(event.metadata).map(([key, value]) => (
                      <div key={key} className="flex justify-between gap-2">
                        <span className="opacity-75">{key}:</span>
                        <span className="font-medium truncate">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </div>
    </div>
  );
});

TimelineEvent.displayName = "TimelineEvent";

const TimelineGroup = React.memo<{
  group: TimelineGroup;
  onEventClick?: (event: ConversationTimelineEvent) => void;
  defaultExpanded?: boolean;
}>(({ group, onEventClick, defaultExpanded = true }) => {
  const [isExpanded, setIsExpanded] = React.useState(defaultExpanded);
  const isToday = isSameDay(new Date(group.date), new Date());
  
  return (
    <div className="space-y-2">
      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2 w-full justify-between font-medium"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          <span>
            {isToday ? 'Today' : format(new Date(group.date), 'EEEE, MMMM d, yyyy')}
          </span>
          <Badge variant="secondary" className="h-4 px-1 text-xs">
            {group.events.length}
          </Badge>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </Button>
      
      {isExpanded && (
        <div className="pl-4 space-y-0">
          {group.events.map((event, index) => (
            <TimelineEvent
              key={event.id}
              event={event}
              onClick={onEventClick}
              isLast={index === group.events.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
});

TimelineGroup.displayName = "TimelineGroup";

export const ConversationTimeline = React.forwardRef<
  HTMLDivElement,
  ConversationTimelineProps
>(({ conversation, events, onEventClick, className, ...props }, ref) => {
  // Group events by date
  const groupedEvents = React.useMemo(() => {
    const groups = new Map<string, ConversationTimelineEvent[]>();
    
    events.forEach(event => {
      const dateKey = format(startOfDay(new Date(event.timestamp)), 'yyyy-MM-dd');
      const existing = groups.get(dateKey) || [];
      groups.set(dateKey, [...existing, event]);
    });
    
    // Convert to timeline groups and sort by date (newest first)
    const timelineGroups: TimelineGroup[] = Array.from(groups.entries())
      .map(([date, eventList]) => ({
        date,
        events: eventList.sort((a, b) => 
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        ),
      }))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    
    return timelineGroups;
  }, [events]);

  if (events.length === 0) {
    return (
      <Card className={cn("flex items-center justify-center h-64", className)}>
        <div className="text-center text-muted-foreground">
          <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>No timeline events available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card ref={ref} className={cn("flex flex-col", className)} {...props}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Clock className="w-5 h-5" />
          Conversation Timeline
        </CardTitle>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>{events.length} events</span>
          <span>
            {formatDistanceToNow(new Date(conversation.created_at), { addSuffix: false })} duration
          </span>
        </div>
      </CardHeader>
      
      <Separator />
      
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-full p-4">
          <div className="space-y-6">
            {groupedEvents.map((group, index) => (
              <React.Fragment key={group.date}>
                <TimelineGroup
                  group={group}
                  onEventClick={onEventClick}
                  defaultExpanded={index === 0} // Expand only the first (most recent) group
                />
                {index < groupedEvents.length - 1 && (
                  <Separator className="my-6" />
                )}
              </React.Fragment>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
});

ConversationTimeline.displayName = "ConversationTimeline";