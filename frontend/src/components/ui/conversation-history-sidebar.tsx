import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import { ConversationSearchParams, ConversationStats } from "@/types/conversation-history";
import { AgentType, DashboardContext } from "@/lib/api/types";
import { AgentBadge } from "./agent-badge";
import { 
  Search,
  Filter,
  Calendar,
  Star,
  Pin,
  Archive,
  ChevronDown,
  ChevronUp,
  BarChart3,
  MessageSquare,
  TrendingUp,
  Users,
  ArrowRightLeft,
  X,
  RefreshCw
} from "lucide-react";
import { DatePicker } from "./date-picker";

interface ConversationHistorySidebarProps {
  searchParams: ConversationSearchParams;
  stats: ConversationStats;
  onSearch: (params: ConversationSearchParams) => void;
  onClear: () => void;
  onRefresh: () => void;
  isOpen: boolean;
  onToggle: () => void;
  className?: string;
}

const contextOptions: { value: DashboardContext; label: string }[] = [
  { value: 'home', label: 'Home Dashboard' },
  { value: 'pre-call-brief', label: 'Pre-Call Brief' },
  { value: 'case-study', label: 'Case Study' },
  { value: 'talent-discovery', label: 'Talent Discovery' },
  { value: 'bid-proposal', label: 'Bid Proposal' },
];

export const ConversationHistorySidebar = React.forwardRef<
  HTMLDivElement,
  ConversationHistorySidebarProps
>(({
  searchParams,
  stats,
  onSearch,
  onClear,
  onRefresh,
  isOpen,
  onToggle,
  className,
  ...props
}, ref) => {
  const [localParams, setLocalParams] = React.useState<ConversationSearchParams>(searchParams);
  const [expandedSections, setExpandedSections] = React.useState({
    filters: true,
    agents: true,
    context: false,
    date: false,
    stats: false,
  });

  // Update local params when search params change
  React.useEffect(() => {
    setLocalParams(searchParams);
  }, [searchParams]);

  const handleParamChange = (key: keyof ConversationSearchParams, value: any) => {
    const newParams = { ...localParams, [key]: value };
    setLocalParams(newParams);
    onSearch(newParams);
  };

  const handleAgentToggle = (agent: AgentType, checked: boolean) => {
    const currentAgents = localParams.agent_filter || [];
    const newAgents = checked
      ? [...currentAgents, agent]
      : currentAgents.filter(a => a !== agent);
    
    handleParamChange('agent_filter', newAgents.length > 0 ? newAgents : undefined);
  };

  const handleContextToggle = (context: DashboardContext, checked: boolean) => {
    const currentContexts = localParams.context_filter || [];
    const newContexts = checked
      ? [...currentContexts, context]
      : currentContexts.filter(c => c !== context);
    
    handleParamChange('context_filter', newContexts.length > 0 ? newContexts : undefined);
  };

  const handleDateRangeChange = (field: 'start' | 'end', date?: Date) => {
    const currentRange = localParams.date_range || { start: '', end: '' };
    const newRange = {
      ...currentRange,
      [field]: date ? date.toISOString() : '',
    };
    
    // Only set date_range if both start and end are provided or clear if both are empty
    const hasValidRange = newRange.start && newRange.end;
    handleParamChange('date_range', hasValidRange ? newRange : undefined);
  };

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const hasActiveFilters = Object.keys(localParams).length > 0;

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatPercentage = (num: number) => {
    return `${Math.round(num * 100)}%`;
  };

  if (!isOpen) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={onToggle}
        className={cn("fixed left-4 top-20 z-50 shadow-lg", className)}
      >
        <Filter className="w-4 h-4 mr-2" />
        Filters
        {hasActiveFilters && (
          <Badge variant="secondary" className="ml-2 h-4 px-1 text-xs">
            {Object.keys(localParams).length}
          </Badge>
        )}
      </Button>
    );
  }

  return (
    <div
      ref={ref}
      className={cn(
        "w-80 border-r bg-card/50 backdrop-blur-sm flex flex-col",
        className
      )}
      {...props}
    >
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Conversation History</h3>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={onRefresh}>
              <RefreshCw className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onToggle}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        {hasActiveFilters && (
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary" className="text-xs">
              {Object.keys(localParams).length} filter{Object.keys(localParams).length !== 1 ? 's' : ''} active
            </Badge>
            <Button variant="ghost" size="sm" onClick={onClear} className="h-6 px-2 text-xs">
              Clear all
            </Button>
          </div>
        )}
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* Search */}
          <div className="space-y-2">
            <Label htmlFor="search">Search conversations</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="search"
                placeholder="Search titles, content, tags..."
                value={localParams.query || ''}
                onChange={(e) => handleParamChange('query', e.target.value || undefined)}
                className="pl-10"
              />
            </div>
          </div>

          <Separator />

          {/* Basic Filters */}
          <Collapsible open={expandedSections.filters} onOpenChange={() => toggleSection('filters')}>
            <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted/50 rounded">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4" />
                <span className="font-medium">Quick Filters</span>
              </div>
              {expandedSections.filters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-3 mt-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="pinned"
                  checked={localParams.is_pinned === true}
                  onCheckedChange={(checked) => 
                    handleParamChange('is_pinned', checked ? true : undefined)
                  }
                />
                <Label htmlFor="pinned" className="flex items-center gap-2 cursor-pointer">
                  <Pin className="w-3 h-3" />
                  Pinned conversations
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="archived"
                  checked={localParams.is_archived === true}
                  onCheckedChange={(checked) => 
                    handleParamChange('is_archived', checked ? true : undefined)
                  }
                />
                <Label htmlFor="archived" className="flex items-center gap-2 cursor-pointer">
                  <Archive className="w-3 h-3" />
                  Archived conversations
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="handoffs"
                  checked={localParams.has_handoffs === true}
                  onCheckedChange={(checked) => 
                    handleParamChange('has_handoffs', checked ? true : undefined)
                  }
                />
                <Label htmlFor="handoffs" className="flex items-center gap-2 cursor-pointer">
                  <ArrowRightLeft className="w-3 h-3" />
                  Has agent handoffs
                </Label>
              </div>

              <div className="space-y-2">
                <Label>Minimum rating</Label>
                <Select 
                  value={localParams.min_rating?.toString() || ''} 
                  onValueChange={(value) => 
                    handleParamChange('min_rating', value ? parseInt(value) : undefined)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Any rating" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Any rating</SelectItem>
                    <SelectItem value="1">1+ stars</SelectItem>
                    <SelectItem value="2">2+ stars</SelectItem>
                    <SelectItem value="3">3+ stars</SelectItem>
                    <SelectItem value="4">4+ stars</SelectItem>
                    <SelectItem value="5">5 stars only</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CollapsibleContent>
          </Collapsible>

          <Separator />

          {/* Agent Filter */}
          <Collapsible open={expandedSections.agents} onOpenChange={() => toggleSection('agents')}>
            <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted/50 rounded">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                <span className="font-medium">Filter by Agents</span>
                {localParams.agent_filter?.length && (
                  <Badge variant="secondary" className="h-4 px-1 text-xs">
                    {localParams.agent_filter.length}
                  </Badge>
                )}
              </div>
              {expandedSections.agents ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-2 mt-2">
              {Object.values(AgentType).map((agent) => (
                <div key={agent} className="flex items-center space-x-2">
                  <Checkbox
                    id={`agent-${agent}`}
                    checked={localParams.agent_filter?.includes(agent) || false}
                    onCheckedChange={(checked) => handleAgentToggle(agent, !!checked)}
                  />
                  <Label htmlFor={`agent-${agent}`} className="flex items-center gap-2 cursor-pointer">
                    <AgentBadge agent={agent} size="sm" />
                    <span className="text-sm">
                      ({stats.agent_usage_distribution[agent] || 0})
                    </span>
                  </Label>
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>

          <Separator />

          {/* Context Filter */}
          <Collapsible open={expandedSections.context} onOpenChange={() => toggleSection('context')}>
            <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted/50 rounded">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                <span className="font-medium">Filter by Context</span>
                {localParams.context_filter?.length && (
                  <Badge variant="secondary" className="h-4 px-1 text-xs">
                    {localParams.context_filter.length}
                  </Badge>
                )}
              </div>
              {expandedSections.context ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-2 mt-2">
              {contextOptions.map(({ value, label }) => (
                <div key={value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`context-${value}`}
                    checked={localParams.context_filter?.includes(value) || false}
                    onCheckedChange={(checked) => handleContextToggle(value, !!checked)}
                  />
                  <Label htmlFor={`context-${value}`} className="cursor-pointer flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{label}</span>
                      <span className="text-xs text-muted-foreground">
                        ({stats.context_distribution[value] || 0})
                      </span>
                    </div>
                  </Label>
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>

          <Separator />

          {/* Date Range Filter */}
          <Collapsible open={expandedSections.date} onOpenChange={() => toggleSection('date')}>
            <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted/50 rounded">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span className="font-medium">Date Range</span>
                {localParams.date_range && (
                  <Badge variant="secondary" className="h-4 px-1 text-xs">
                    Set
                  </Badge>
                )}
              </div>
              {expandedSections.date ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-3 mt-2">
              <div className="space-y-2">
                <Label>From date</Label>
                <DatePicker
                  date={localParams.date_range?.start ? new Date(localParams.date_range.start) : undefined}
                  onSelect={(date) => handleDateRangeChange('start', date)}
                />
              </div>
              <div className="space-y-2">
                <Label>To date</Label>
                <DatePicker
                  date={localParams.date_range?.end ? new Date(localParams.date_range.end) : undefined}
                  onSelect={(date) => handleDateRangeChange('end', date)}
                />
              </div>
            </CollapsibleContent>
          </Collapsible>

          <Separator />

          {/* Statistics */}
          <Collapsible open={expandedSections.stats} onOpenChange={() => toggleSection('stats')}>
            <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted/50 rounded">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                <span className="font-medium">Statistics</span>
              </div>
              {expandedSections.stats ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-3 mt-2">
              <Card className="bg-muted/30 border-0">
                <CardContent className="p-3 space-y-2">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <div className="text-muted-foreground">Total</div>
                      <div className="font-semibold">{formatNumber(stats.total_conversations)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Active</div>
                      <div className="font-semibold">{formatNumber(stats.active_conversations)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Messages</div>
                      <div className="font-semibold">{formatNumber(stats.total_messages)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Avg/Conv</div>
                      <div className="font-semibold">{Math.round(stats.avg_messages_per_conversation)}</div>
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground">Most used agent</div>
                    <AgentBadge agent={stats.most_used_agent} size="sm" />
                  </div>
                  
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground">Handoffs per conversation</div>
                    <div className="text-sm font-semibold">
                      {stats.handoff_frequency.toFixed(1)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </ScrollArea>
    </div>
  );
});

ConversationHistorySidebar.displayName = "ConversationHistorySidebar";