import { AgentType, AgentMetadata, DashboardContext, Message } from '@/lib/api/types';

// Extended conversation types for history with agent tracking
export interface ConversationThread {
  id: string;
  title: string;
  subtitle?: string;
  context: DashboardContext;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview?: string;
  
  // Agent-specific data
  participating_agents: AgentType[];
  primary_agent?: AgentType;
  agent_handoffs: AgentHandoff[];
  agent_usage_stats: AgentUsageStats;
  
  // Conversation metadata
  conversation_tags: string[];
  user_rating?: number;
  is_pinned: boolean;
  is_archived: boolean;
  export_data?: ConversationExport;
}

export interface AgentHandoff {
  id: string;
  from_agent?: AgentType;
  to_agent: AgentType;
  timestamp: string;
  reason?: string;
  message_id: string;
  context_shift?: DashboardContext;
}

export interface AgentUsageStats {
  total_messages: number;
  agent_breakdown: Record<AgentType, number>;
  processing_time_avg: Record<AgentType, number>;
  confidence_avg: Record<AgentType, number>;
  last_agent_used?: AgentType;
}

export interface MessageWithAgent extends Message {
  agent?: AgentType;
  agent_metadata?: AgentMetadata;
  is_handoff?: boolean;
  handoff_data?: AgentHandoff;
}

export interface ConversationExport {
  format: 'json' | 'markdown' | 'pdf';
  include_metadata: boolean;
  include_agent_info: boolean;
  created_at: string;
  file_size: number;
}

// Search and filtering types
export interface ConversationSearchParams {
  query?: string;
  agent_filter?: AgentType[];
  context_filter?: DashboardContext[];
  date_range?: {
    start: string;
    end: string;
  };
  has_handoffs?: boolean;
  is_pinned?: boolean;
  is_archived?: boolean;
  min_rating?: number;
  tags?: string[];
}

export interface ConversationSort {
  field: 'created_at' | 'updated_at' | 'message_count' | 'agent_count' | 'user_rating';
  order: 'asc' | 'desc';
}

// History storage types
export interface ConversationHistoryCache {
  conversations: ConversationThread[];
  last_sync: string;
  cache_version: number;
  total_conversations: number;
}

export interface ConversationStats {
  total_conversations: number;
  active_conversations: number;
  archived_conversations: number;
  most_used_agent: AgentType;
  most_used_context: DashboardContext;
  total_messages: number;
  avg_messages_per_conversation: number;
  agent_usage_distribution: Record<AgentType, number>;
  context_distribution: Record<DashboardContext, number>;
  handoff_frequency: number;
}

// Visual timeline types
export interface ConversationTimelineEvent {
  id: string;
  type: 'message' | 'agent_handoff' | 'context_change' | 'rating' | 'export';
  timestamp: string;
  title: string;
  description?: string;
  agent?: AgentType;
  metadata?: Record<string, any>;
}

export interface TimelineGroup {
  date: string;
  events: ConversationTimelineEvent[];
}

// UI state types
export interface ConversationHistoryState {
  conversations: ConversationThread[];
  loading: boolean;
  error: string | null;
  search_params: ConversationSearchParams;
  sort: ConversationSort;
  pagination: {
    page: number;
    limit: number;
    total: number;
    has_next: boolean;
  };
  selected_conversation?: string;
  view_mode: 'list' | 'grid' | 'timeline';
  sidebar_open: boolean;
}

// Agent participation visualization
export interface AgentParticipationData {
  agent: AgentType;
  message_count: number;
  percentage: number;
  avg_confidence: number;
  avg_processing_time: number;
  first_appearance: string;
  last_appearance: string;
  handoffs_initiated: number;
  handoffs_received: number;
}

// Conversation insights
export interface ConversationInsights {
  duration_minutes: number;
  dominant_agent: AgentType;
  context_switches: number;
  agent_switches: number;
  user_engagement_score: number;
  complexity_score: number;
  resolution_quality: 'high' | 'medium' | 'low';
  key_topics: string[];
  sentiment_trend: 'positive' | 'neutral' | 'negative';
}