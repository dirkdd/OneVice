import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { ConversationThread } from "@/types/conversation-history";
import { AgentParticipationBadge } from "./agent-participation-badge";
import { 
  Pin, 
  Archive, 
  Star, 
  MessageSquare, 
  Clock, 
  ArrowRightLeft,
  MoreVertical,
  Calendar,
  User,
  Hash,
  Download
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { AgentType } from "@/lib/api/types";

interface ConversationThreadCardProps {
  conversation: ConversationThread;
  onSelect?: (conversation: ConversationThread) => void;
  onPin?: (id: string) => void;
  onArchive?: (id: string) => void;
  onRate?: (id: string, rating: number) => void;
  onExport?: (id: string) => void;
  onDelete?: (id: string) => void;
  selected?: boolean;
  className?: string;
}

const contextLabels = {
  'home': 'Home Dashboard',
  'pre-call-brief': 'Pre-Call Brief',
  'case-study': 'Case Study',
  'talent-discovery': 'Talent Discovery',
  'bid-proposal': 'Bid Proposal',
};

const StarRating = ({ 
  rating, 
  onRate, 
  size = 'sm' 
}: { 
  rating?: number; 
  onRate?: (rating: number) => void;
  size?: 'sm' | 'md';
}) => {
  const stars = Array.from({ length: 5 }, (_, i) => i + 1);
  const iconSize = size === 'sm' ? 'w-3 h-3' : 'w-4 h-4';
  
  return (
    <div className="flex items-center gap-1">
      {stars.map((star) => (
        <Button
          key={star}
          variant="ghost"
          size="sm"
          className={cn(
            "p-0 h-auto hover:scale-110 transition-transform",
            onRate && "cursor-pointer"
          )}
          onClick={() => onRate?.(star)}
          disabled={!onRate}
        >
          <Star 
            className={cn(
              iconSize,
              star <= (rating || 0) 
                ? "fill-yellow-400 text-yellow-400" 
                : "text-muted-foreground/40"
            )}
          />
        </Button>
      ))}
    </div>
  );
};

export const ConversationThreadCard = React.forwardRef<
  HTMLDivElement,
  ConversationThreadCardProps
>(({
  conversation,
  onSelect,
  onPin,
  onArchive,
  onRate,
  onExport,
  onDelete,
  selected = false,
  className,
  ...props
}, ref) => {
  const {
    id,
    title,
    subtitle,
    context,
    created_at,
    updated_at,
    message_count,
    last_message_preview,
    participating_agents,
    primary_agent,
    agent_handoffs,
    agent_usage_stats,
    conversation_tags,
    user_rating,
    is_pinned,
    is_archived,
  } = conversation;

  // Calculate agent participation data
  const agentParticipationData = participating_agents.map(agent => {
    const messageCount = agent_usage_stats.agent_breakdown[agent] || 0;
    const percentage = (messageCount / message_count) * 100;
    
    // Count handoffs for this agent
    const handoffsInitiated = agent_handoffs.filter(h => h.from_agent === agent).length;
    const handoffsReceived = agent_handoffs.filter(h => h.to_agent === agent).length;
    
    return {
      agent,
      message_count: messageCount,
      percentage,
      avg_confidence: agent_usage_stats.confidence_avg[agent] || 0,
      avg_processing_time: agent_usage_stats.processing_time_avg[agent] || 0,
      first_appearance: created_at, // Simplified - could be more precise
      last_appearance: updated_at, // Simplified - could be more precise
      handoffs_initiated: handoffsInitiated,
      handoffs_received: handoffsReceived,
    };
  }).sort((a, b) => b.message_count - a.message_count);

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(conversation);
    }
  };

  const handleRating = (rating: number) => {
    if (onRate) {
      onRate(id, rating);
    }
  };

  const timeAgo = formatDistanceToNow(new Date(updated_at), { addSuffix: true });

  return (
    <TooltipProvider>
      <Card
        ref={ref}
        className={cn(
          "group relative transition-all duration-200 cursor-pointer",
          "hover:shadow-lg hover:shadow-primary/10 hover:-translate-y-1",
          "border-border/50 backdrop-blur-sm",
          selected && "ring-2 ring-primary shadow-lg shadow-primary/20",
          is_pinned && "border-yellow-500/50 shadow-yellow-500/10",
          is_archived && "opacity-70 grayscale",
          className
        )}
        onClick={handleCardClick}
        {...props}
      >
        {/* Pin indicator */}
        {is_pinned && (
          <div className="absolute -top-2 -right-2 z-10">
            <div className="w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center">
              <Pin className="w-2 h-2 text-yellow-900" />
            </div>
          </div>
        )}

        {/* Archive overlay */}
        {is_archived && (
          <div className="absolute inset-0 bg-muted/50 rounded-lg flex items-center justify-center z-20">
            <Badge variant="secondary" className="opacity-90">
              <Archive className="w-3 h-3 mr-1" />
              Archived
            </Badge>
          </div>
        )}

        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-base line-clamp-2 group-hover:text-primary transition-colors">
                {title}
              </h3>
              {subtitle && (
                <p className="text-sm text-muted-foreground mt-1 line-clamp-1">
                  {subtitle}
                </p>
              )}
            </div>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 p-0"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onPin?.(id); }}>
                  <Pin className="w-4 h-4 mr-2" />
                  {is_pinned ? 'Unpin' : 'Pin'}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onArchive?.(id); }}>
                  <Archive className="w-4 h-4 mr-2" />
                  {is_archived ? 'Unarchive' : 'Archive'}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onExport?.(id); }}>
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  className="text-destructive focus:text-destructive"
                  onClick={(e) => { e.stopPropagation(); onDelete?.(id); }}
                >
                  <User className="w-4 h-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Metadata row */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>{timeAgo}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <div className="text-xs">
                  <div>Created: {new Date(created_at).toLocaleString()}</div>
                  <div>Updated: {new Date(updated_at).toLocaleString()}</div>
                </div>
              </TooltipContent>
            </Tooltip>
            
            <div className="flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              <span>{message_count}</span>
            </div>
            
            {agent_handoffs.length > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-1">
                    <ArrowRightLeft className="w-3 h-3" />
                    <span>{agent_handoffs.length}</span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <span>Agent handoffs in this conversation</span>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-0 space-y-4">
          {/* Context and tags */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-xs">
              {contextLabels[context]}
            </Badge>
            
            {conversation_tags.slice(0, 2).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                <Hash className="w-2 h-2 mr-1" />
                {tag}
              </Badge>
            ))}
            
            {conversation_tags.length > 2 && (
              <Badge variant="secondary" className="text-xs">
                +{conversation_tags.length - 2}
              </Badge>
            )}
          </div>

          {/* Agent participation */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground font-medium">
                Agent Participation
              </span>
              {primary_agent && (
                <Badge variant="outline" className="text-xs">
                  Primary: {primary_agent}
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-2 flex-wrap">
              {agentParticipationData.slice(0, 3).map(({ agent, ...data }) => (
                <AgentParticipationBadge
                  key={agent}
                  agent={agent}
                  data={{ agent, ...data }}
                  size="sm"
                  showPercentage={true}
                  showConfidence={false}
                />
              ))}
              
              {participating_agents.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{participating_agents.length - 3}
                </Badge>
              )}
            </div>
          </div>

          {/* Last message preview */}
          {last_message_preview && (
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground font-medium">
                Latest Message
              </span>
              <p className="text-sm text-muted-foreground line-clamp-2 bg-muted/30 rounded px-2 py-1">
                {last_message_preview}
              </p>
            </div>
          )}

          {/* Rating */}
          {(user_rating || onRate) && (
            <div className="flex items-center justify-between pt-2 border-t border-border/50">
              <span className="text-xs text-muted-foreground">Rating:</span>
              <StarRating 
                rating={user_rating} 
                onRate={onRate ? handleRating : undefined}
                size="sm"
              />
            </div>
          )}
        </CardContent>
      </Card>
    </TooltipProvider>
  );
});

ConversationThreadCard.displayName = "ConversationThreadCard";