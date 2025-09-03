import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useConversationHistory } from "@/hooks/useConversationHistory";
import { ConversationHistorySidebar } from "./conversation-history-sidebar";
import { ConversationThreadCard } from "./conversation-thread-card";
import { ConversationTimeline } from "./conversation-timeline";
import { ConversationThread, ConversationTimelineEvent } from "@/types/conversation-history";
import { 
  Grid,
  List,
  Timeline,
  Search,
  Filter,
  RefreshCw,
  Download,
  Settings,
  MessageSquare,
  BarChart3,
  SortAsc,
  SortDesc,
  Plus
} from "lucide-react";

interface ConversationHistoryMainProps {
  onSelectConversation?: (conversation: ConversationThread) => void;
  onNewConversation?: () => void;
  className?: string;
}

const ViewModeToggle = ({ 
  mode, 
  onChange 
}: { 
  mode: 'list' | 'grid' | 'timeline';
  onChange: (mode: 'list' | 'grid' | 'timeline') => void;
}) => {
  const modes = [
    { value: 'list' as const, icon: List, label: 'List View' },
    { value: 'grid' as const, icon: Grid, label: 'Grid View' },
    { value: 'timeline' as const, icon: Timeline, label: 'Timeline View' },
  ];

  return (
    <div className="flex items-center bg-muted/30 rounded-lg p-1">
      {modes.map(({ value, icon: Icon, label }) => (
        <Button
          key={value}
          variant={mode === value ? "secondary" : "ghost"}
          size="sm"
          onClick={() => onChange(value)}
          className="h-8 px-3"
          title={label}
        >
          <Icon className="w-4 h-4" />
        </Button>
      ))}
    </div>
  );
};

const SortControls = ({
  sort,
  onChange,
}: {
  sort: { field: string; order: 'asc' | 'desc' };
  onChange: (sort: { field: string; order: 'asc' | 'desc' }) => void;
}) => {
  const sortOptions = [
    { value: 'updated_at', label: 'Last Updated' },
    { value: 'created_at', label: 'Created Date' },
    { value: 'message_count', label: 'Message Count' },
    { value: 'agent_count', label: 'Agent Count' },
    { value: 'user_rating', label: 'User Rating' },
  ];

  return (
    <div className="flex items-center gap-2">
      <Select 
        value={sort.field} 
        onValueChange={(field) => onChange({ ...sort, field })}
      >
        <SelectTrigger className="w-36">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {sortOptions.map(({ value, label }) => (
            <SelectItem key={value} value={value}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      <Button
        variant="outline"
        size="sm"
        onClick={() => onChange({ ...sort, order: sort.order === 'asc' ? 'desc' : 'asc' })}
        className="px-3"
      >
        {sort.order === 'asc' ? (
          <SortAsc className="w-4 h-4" />
        ) : (
          <SortDesc className="w-4 h-4" />
        )}
      </Button>
    </div>
  );
};

const ConversationGrid = ({ 
  conversations, 
  onSelect,
  onPin,
  onArchive,
  onRate,
  onExport,
  selectedId
}: {
  conversations: ConversationThread[];
  onSelect?: (conversation: ConversationThread) => void;
  onPin?: (id: string) => void;
  onArchive?: (id: string) => void;
  onRate?: (id: string, rating: number) => void;
  onExport?: (id: string) => void;
  selectedId?: string;
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {conversations.map((conversation) => (
        <ConversationThreadCard
          key={conversation.id}
          conversation={conversation}
          onSelect={onSelect}
          onPin={onPin}
          onArchive={onArchive}
          onRate={onRate}
          onExport={onExport}
          selected={conversation.id === selectedId}
        />
      ))}
    </div>
  );
};

const ConversationList = ({ 
  conversations, 
  onSelect,
  onPin,
  onArchive,
  onRate,
  onExport,
  selectedId
}: {
  conversations: ConversationThread[];
  onSelect?: (conversation: ConversationThread) => void;
  onPin?: (id: string) => void;
  onArchive?: (id: string) => void;
  onRate?: (id: string, rating: number) => void;
  onExport?: (id: string) => void;
  selectedId?: string;
}) => {
  return (
    <div className="space-y-3">
      {conversations.map((conversation) => (
        <ConversationThreadCard
          key={conversation.id}
          conversation={conversation}
          onSelect={onSelect}
          onPin={onPin}
          onArchive={onArchive}
          onRate={onRate}
          onExport={onExport}
          selected={conversation.id === selectedId}
          className="w-full"
        />
      ))}
    </div>
  );
};

const LoadingSkeleton = ({ mode }: { mode: 'list' | 'grid' | 'timeline' }) => {
  const skeletonCount = mode === 'grid' ? 6 : mode === 'list' ? 4 : 1;
  
  return (
    <div className={cn(
      mode === 'grid' && "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4",
      mode === 'list' && "space-y-3",
      mode === 'timeline' && "space-y-6"
    )}>
      {Array.from({ length: skeletonCount }).map((_, i) => (
        <Card key={i} className="p-4">
          <div className="space-y-3">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <div className="flex gap-2">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-16" />
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};

export const ConversationHistoryMain = React.forwardRef<
  HTMLDivElement,
  ConversationHistoryMainProps
>(({ onSelectConversation, onNewConversation, className, ...props }, ref) => {
  const {
    conversations,
    loading,
    error,
    search_params,
    sort,
    view_mode,
    sidebar_open,
    selected_conversation,
    stats,
    searchConversations,
    sortConversations,
    togglePin,
    toggleArchive,
    rateConversation,
    updateViewMode,
    toggleSidebar,
    selectConversation,
    loadConversations,
    clearCache,
    hasFilters,
  } = useConversationHistory();

  // Generate timeline events for selected conversation
  const timelineEvents = React.useMemo((): ConversationTimelineEvent[] => {
    const selectedConv = conversations.find(c => c.id === selected_conversation);
    if (!selectedConv || view_mode !== 'timeline') return [];

    const events: ConversationTimelineEvent[] = [];

    // Add message events (simplified)
    events.push({
      id: `msg-${selectedConv.id}`,
      type: 'message',
      timestamp: selectedConv.created_at,
      title: 'Conversation Started',
      description: `Started in ${selectedConv.context} context`,
      metadata: { context: selectedConv.context },
    });

    // Add agent handoff events
    selectedConv.agent_handoffs.forEach(handoff => {
      events.push({
        id: handoff.id,
        type: 'agent_handoff',
        timestamp: handoff.timestamp,
        title: `Agent Handoff: ${handoff.from_agent || 'User'} → ${handoff.to_agent}`,
        description: handoff.reason || 'Agent switched during conversation',
        agent: handoff.to_agent,
        metadata: { 
          from_agent: handoff.from_agent,
          to_agent: handoff.to_agent,
          reason: handoff.reason,
        },
      });
    });

    // Add rating event if exists
    if (selectedConv.user_rating) {
      events.push({
        id: `rating-${selectedConv.id}`,
        type: 'rating',
        timestamp: selectedConv.updated_at,
        title: `Rated ${selectedConv.user_rating} stars`,
        description: 'User provided feedback for this conversation',
        metadata: { rating: selectedConv.user_rating },
      });
    }

    return events.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [conversations, selected_conversation, view_mode]);

  const handleConversationSelect = (conversation: ConversationThread) => {
    selectConversation(conversation.id);
    onSelectConversation?.(conversation);
  };

  const handleExportConversation = (id: string) => {
    // TODO: Implement export functionality
    console.log('Export conversation:', id);
  };

  const handleClearFilters = () => {
    searchConversations({});
  };

  const handleRefresh = () => {
    clearCache();
    loadConversations(true);
  };

  return (
    <div ref={ref} className={cn("flex h-full", className)} {...props}>
      {/* Sidebar */}
      <ConversationHistorySidebar
        searchParams={search_params}
        stats={stats}
        onSearch={searchConversations}
        onClear={handleClearFilters}
        onRefresh={handleRefresh}
        isOpen={sidebar_open}
        onToggle={toggleSidebar}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="border-b bg-card/50 backdrop-blur-sm p-4">
          <div className="flex items-center justify-between gap-4 mb-3">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold">Conversation History</h2>
              {loading && (
                <RefreshCw className="w-4 h-4 animate-spin text-muted-foreground" />
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {onNewConversation && (
                <Button onClick={onNewConversation} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  New Chat
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={handleRefresh}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              {!sidebar_open && (
                <Button variant="outline" size="sm" onClick={toggleSidebar}>
                  <Filter className="w-4 h-4 mr-2" />
                  Filters
                  {hasFilters && (
                    <Badge variant="secondary" className="ml-2 h-4 px-1 text-xs">
                      {Object.keys(search_params).length}
                    </Badge>
                  )}
                </Button>
              )}
              
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MessageSquare className="w-4 h-4" />
                <span>{conversations.length} conversation{conversations.length !== 1 ? 's' : ''}</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <SortControls sort={sort} onChange={sortConversations} />
              <ViewModeToggle mode={view_mode} onChange={updateViewMode} />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-4">
          {error ? (
            <Card className="flex items-center justify-center h-64">
              <div className="text-center text-destructive">
                <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="font-medium">Failed to load conversations</p>
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
                <Button variant="outline" size="sm" onClick={handleRefresh} className="mt-3">
                  Try Again
                </Button>
              </div>
            </Card>
          ) : loading ? (
            <LoadingSkeleton mode={view_mode} />
          ) : conversations.length === 0 ? (
            <Card className="flex items-center justify-center h-64">
              <div className="text-center text-muted-foreground">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="font-medium">
                  {hasFilters ? 'No conversations match your filters' : 'No conversations yet'}
                </p>
                <p className="text-sm mt-1">
                  {hasFilters 
                    ? 'Try adjusting your search criteria' 
                    : 'Start a conversation to see it here'
                  }
                </p>
                {hasFilters ? (
                  <Button variant="outline" size="sm" onClick={handleClearFilters} className="mt-3">
                    Clear Filters
                  </Button>
                ) : onNewConversation && (
                  <Button onClick={onNewConversation} size="sm" className="mt-3">
                    <Plus className="w-4 h-4 mr-2" />
                    Start New Chat
                  </Button>
                )}
              </div>
            </Card>
          ) : (
            <ScrollArea className="h-full">
              {view_mode === 'timeline' ? (
                selected_conversation ? (
                  <ConversationTimeline
                    conversation={conversations.find(c => c.id === selected_conversation)!}
                    events={timelineEvents}
                    onEventClick={(event) => console.log('Timeline event clicked:', event)}
                  />
                ) : (
                  <Card className="flex items-center justify-center h-64">
                    <div className="text-center text-muted-foreground">
                      <Timeline className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Select a conversation to view its timeline</p>
                    </div>
                  </Card>
                )
              ) : view_mode === 'grid' ? (
                <ConversationGrid
                  conversations={conversations}
                  onSelect={handleConversationSelect}
                  onPin={togglePin}
                  onArchive={toggleArchive}
                  onRate={rateConversation}
                  onExport={handleExportConversation}
                  selectedId={selected_conversation}
                />
              ) : (
                <ConversationList
                  conversations={conversations}
                  onSelect={handleConversationSelect}
                  onPin={togglePin}
                  onArchive={toggleArchive}
                  onRate={rateConversation}
                  onExport={handleExportConversation}
                  selectedId={selected_conversation}
                />
              )}
            </ScrollArea>
          )}
        </div>
      </div>
    </div>
  );
});

ConversationHistoryMain.displayName = "ConversationHistoryMain";