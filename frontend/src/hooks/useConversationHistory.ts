import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { conversationsApi } from '@/lib/api/conversations';
import { 
  ConversationThread, 
  ConversationHistoryState,
  ConversationSearchParams,
  ConversationSort,
  ConversationStats,
  ConversationHistoryCache,
  MessageWithAgent,
  AgentHandoff,
  AgentUsageStats
} from '@/types/conversation-history';
import { AgentType, DashboardContext } from '@/lib/api/types';

const CACHE_KEY = 'onevice-conversation-history';
const CACHE_VERSION = 1;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

const defaultSearchParams: ConversationSearchParams = {};
const defaultSort: ConversationSort = { field: 'updated_at', order: 'desc' };

export function useConversationHistory() {
  const { user } = useAuth();
  const [state, setState] = useState<ConversationHistoryState>({
    conversations: [],
    loading: true,
    error: null,
    search_params: defaultSearchParams,
    sort: defaultSort,
    pagination: {
      page: 1,
      limit: 20,
      total: 0,
      has_next: false,
    },
    view_mode: 'list',
    sidebar_open: false,
  });

  // Load from cache on mount
  useEffect(() => {
    loadFromCache();
  }, []);

  // Cache conversations when they change
  useEffect(() => {
    if (state.conversations.length > 0) {
      cacheConversations(state.conversations);
    }
  }, [state.conversations]);

  const loadFromCache = useCallback(() => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const cacheData: ConversationHistoryCache = JSON.parse(cached);
        
        // Check cache validity
        const cacheAge = Date.now() - new Date(cacheData.last_sync).getTime();
        if (cacheAge < CACHE_DURATION && cacheData.cache_version === CACHE_VERSION) {
          setState(prev => ({
            ...prev,
            conversations: cacheData.conversations,
            loading: false,
            pagination: {
              ...prev.pagination,
              total: cacheData.total_conversations,
            },
          }));
          return true; // Cache was used
        }
      }
    } catch (error) {
      console.error('Failed to load conversation history from cache:', error);
    }
    return false; // Cache was not used
  }, []);

  const cacheConversations = useCallback((conversations: ConversationThread[]) => {
    try {
      const cacheData: ConversationHistoryCache = {
        conversations,
        last_sync: new Date().toISOString(),
        cache_version: CACHE_VERSION,
        total_conversations: conversations.length,
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
    } catch (error) {
      console.error('Failed to cache conversation history:', error);
    }
  }, []);

  const clearCache = useCallback(() => {
    try {
      localStorage.removeItem(CACHE_KEY);
    } catch (error) {
      console.error('Failed to clear conversation history cache:', error);
    }
  }, []);

  // Transform API conversations to include agent data
  const transformConversation = useCallback(async (apiConversation: any): Promise<ConversationThread> => {
    // Get messages for agent analysis
    const messagesResponse = await conversationsApi.getConversationMessages(apiConversation.id);
    const messages: MessageWithAgent[] = messagesResponse.data?.items || [];
    
    // Analyze agent participation
    const participatingAgents: AgentType[] = [];
    const agentHandoffs: AgentHandoff[] = [];
    const agentMessageCount: Record<AgentType, number> = {} as Record<AgentType, number>;
    const agentProcessingTimes: Record<AgentType, number[]> = {} as Record<AgentType, number[]>;
    const agentConfidenceScores: Record<AgentType, number[]> = {} as Record<AgentType, number[]>;
    
    let currentAgent: AgentType | undefined;
    
    messages.forEach((message, index) => {
      if (message.agent_metadata?.agent_type) {
        const agent = message.agent_metadata.agent_type;
        
        // Track participating agents
        if (!participatingAgents.includes(agent)) {
          participatingAgents.push(agent);
        }
        
        // Count messages per agent
        agentMessageCount[agent] = (agentMessageCount[agent] || 0) + 1;
        
        // Track processing times
        if (message.agent_metadata.processing_time) {
          const timeMs = parseFloat(message.agent_metadata.processing_time.replace(/[^0-9.]/g, ''));
          if (!isNaN(timeMs)) {
            if (!agentProcessingTimes[agent]) agentProcessingTimes[agent] = [];
            agentProcessingTimes[agent].push(timeMs);
          }
        }
        
        // Track confidence scores
        if (message.agent_metadata.confidence) {
          const confidenceMap = { low: 1, medium: 2, high: 3 };
          const score = confidenceMap[message.agent_metadata.confidence];
          if (!agentConfidenceScores[agent]) agentConfidenceScores[agent] = [];
          agentConfidenceScores[agent].push(score);
        }
        
        // Detect agent handoffs
        if (currentAgent && currentAgent !== agent) {
          agentHandoffs.push({
            id: `handoff_${index}`,
            from_agent: currentAgent,
            to_agent: agent,
            timestamp: message.created_at,
            message_id: message.id,
          });
        }
        
        currentAgent = agent;
      }
    });
    
    // Calculate usage stats
    const totalMessages = messages.length;
    const agentUsageStats: AgentUsageStats = {
      total_messages: totalMessages,
      agent_breakdown: agentMessageCount,
      processing_time_avg: {} as Record<AgentType, number>,
      confidence_avg: {} as Record<AgentType, number>,
      last_agent_used: currentAgent,
    };
    
    // Calculate averages
    Object.keys(agentProcessingTimes).forEach(agent => {
      const times = agentProcessingTimes[agent as AgentType];
      agentUsageStats.processing_time_avg[agent as AgentType] = 
        times.reduce((sum, time) => sum + time, 0) / times.length;
    });
    
    Object.keys(agentConfidenceScores).forEach(agent => {
      const scores = agentConfidenceScores[agent as AgentType];
      agentUsageStats.confidence_avg[agent as AgentType] = 
        scores.reduce((sum, score) => sum + score, 0) / scores.length;
    });
    
    // Determine primary agent (most messages)
    const primaryAgent = Object.entries(agentMessageCount)
      .sort(([,a], [,b]) => b - a)[0]?.[0] as AgentType;
    
    return {
      ...apiConversation,
      participating_agents: participatingAgents,
      primary_agent: primaryAgent,
      agent_handoffs: agentHandoffs,
      agent_usage_stats: agentUsageStats,
      conversation_tags: [], // TODO: Extract from content
      is_pinned: false,
      is_archived: false,
    };
  }, []);

  const loadConversations = useCallback(async (force = false) => {
    if (!force && !loadFromCache()) {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      try {
        const response = await conversationsApi.getConversations({
          page: state.pagination.page,
          limit: state.pagination.limit,
          sort_by: state.sort.field,
          sort_order: state.sort.order,
        });
        
        if (response.success && response.data) {
          // Transform conversations to include agent data
          const transformedConversations = await Promise.all(
            response.data.items.map(transformConversation)
          );
          
          setState(prev => ({
            ...prev,
            conversations: transformedConversations,
            loading: false,
            pagination: {
              ...prev.pagination,
              total: response.data!.total,
              has_next: response.data!.has_next,
            },
          }));
        } else {
          setState(prev => ({
            ...prev,
            loading: false,
            error: response.error || 'Failed to load conversations',
          }));
        }
      } catch (error: any) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error.message || 'Failed to load conversations',
        }));
      }
    }
  }, [state.pagination.page, state.pagination.limit, state.sort, loadFromCache, transformConversation]);

  const searchConversations = useCallback(async (params: ConversationSearchParams) => {
    setState(prev => ({ 
      ...prev, 
      loading: true, 
      search_params: params,
      pagination: { ...prev.pagination, page: 1 }
    }));

    try {
      // Apply local filtering for agent and context filters
      let filtered = state.conversations;
      
      if (params.query) {
        const query = params.query.toLowerCase();
        filtered = filtered.filter(conv => 
          conv.title.toLowerCase().includes(query) ||
          conv.last_message_preview?.toLowerCase().includes(query) ||
          conv.conversation_tags.some(tag => tag.toLowerCase().includes(query))
        );
      }
      
      if (params.agent_filter?.length) {
        filtered = filtered.filter(conv =>
          params.agent_filter!.some(agent => conv.participating_agents.includes(agent))
        );
      }
      
      if (params.context_filter?.length) {
        filtered = filtered.filter(conv =>
          params.context_filter!.includes(conv.context)
        );
      }
      
      if (params.has_handoffs) {
        filtered = filtered.filter(conv => conv.agent_handoffs.length > 0);
      }
      
      if (params.is_pinned !== undefined) {
        filtered = filtered.filter(conv => conv.is_pinned === params.is_pinned);
      }
      
      if (params.is_archived !== undefined) {
        filtered = filtered.filter(conv => conv.is_archived === params.is_archived);
      }
      
      if (params.min_rating) {
        filtered = filtered.filter(conv => 
          conv.user_rating !== undefined && conv.user_rating >= params.min_rating!
        );
      }
      
      if (params.date_range) {
        const start = new Date(params.date_range.start);
        const end = new Date(params.date_range.end);
        filtered = filtered.filter(conv => {
          const created = new Date(conv.created_at);
          return created >= start && created <= end;
        });
      }

      setState(prev => ({
        ...prev,
        conversations: filtered,
        loading: false,
        pagination: {
          ...prev.pagination,
          total: filtered.length,
          has_next: false,
        },
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Search failed',
      }));
    }
  }, [state.conversations]);

  const sortConversations = useCallback((sort: ConversationSort) => {
    setState(prev => {
      const sorted = [...prev.conversations].sort((a, b) => {
        let aVal: any, bVal: any;
        
        switch (sort.field) {
          case 'created_at':
          case 'updated_at':
            aVal = new Date(a[sort.field]).getTime();
            bVal = new Date(b[sort.field]).getTime();
            break;
          case 'message_count':
            aVal = a.message_count;
            bVal = b.message_count;
            break;
          case 'agent_count':
            aVal = a.participating_agents.length;
            bVal = b.participating_agents.length;
            break;
          case 'user_rating':
            aVal = a.user_rating || 0;
            bVal = b.user_rating || 0;
            break;
          default:
            return 0;
        }
        
        return sort.order === 'asc' ? aVal - bVal : bVal - aVal;
      });
      
      return {
        ...prev,
        conversations: sorted,
        sort,
      };
    });
  }, []);

  // Calculate conversation statistics
  const stats: ConversationStats = useMemo(() => {
    const conversations = state.conversations;
    const total = conversations.length;
    
    if (total === 0) {
      return {
        total_conversations: 0,
        active_conversations: 0,
        archived_conversations: 0,
        most_used_agent: AgentType.SALES,
        most_used_context: 'home',
        total_messages: 0,
        avg_messages_per_conversation: 0,
        agent_usage_distribution: {} as Record<AgentType, number>,
        context_distribution: {} as Record<DashboardContext, number>,
        handoff_frequency: 0,
      };
    }
    
    const active = conversations.filter(c => !c.is_archived).length;
    const archived = conversations.filter(c => c.is_archived).length;
    const totalMessages = conversations.reduce((sum, c) => sum + c.message_count, 0);
    const totalHandoffs = conversations.reduce((sum, c) => sum + c.agent_handoffs.length, 0);
    
    // Agent usage distribution
    const agentUsage: Record<AgentType, number> = {} as Record<AgentType, number>;
    conversations.forEach(conv => {
      Object.entries(conv.agent_usage_stats.agent_breakdown).forEach(([agent, count]) => {
        agentUsage[agent as AgentType] = (agentUsage[agent as AgentType] || 0) + count;
      });
    });
    
    // Context distribution
    const contextUsage: Record<DashboardContext, number> = {} as Record<DashboardContext, number>;
    conversations.forEach(conv => {
      contextUsage[conv.context] = (contextUsage[conv.context] || 0) + 1;
    });
    
    // Most used agent and context
    const mostUsedAgent = Object.entries(agentUsage)
      .sort(([,a], [,b]) => b - a)[0]?.[0] as AgentType || AgentType.SALES;
    const mostUsedContext = Object.entries(contextUsage)
      .sort(([,a], [,b]) => b - a)[0]?.[0] as DashboardContext || 'home';
    
    return {
      total_conversations: total,
      active_conversations: active,
      archived_conversations: archived,
      most_used_agent: mostUsedAgent,
      most_used_context: mostUsedContext,
      total_messages: totalMessages,
      avg_messages_per_conversation: totalMessages / total,
      agent_usage_distribution: agentUsage,
      context_distribution: contextUsage,
      handoff_frequency: totalHandoffs / total,
    };
  }, [state.conversations]);

  // Load conversations on mount and user change
  useEffect(() => {
    if (user) {
      loadConversations();
    }
  }, [user, loadConversations]);

  const togglePin = useCallback((conversationId: string) => {
    setState(prev => ({
      ...prev,
      conversations: prev.conversations.map(conv =>
        conv.id === conversationId ? { ...conv, is_pinned: !conv.is_pinned } : conv
      ),
    }));
  }, []);

  const toggleArchive = useCallback((conversationId: string) => {
    setState(prev => ({
      ...prev,
      conversations: prev.conversations.map(conv =>
        conv.id === conversationId ? { ...conv, is_archived: !conv.is_archived } : conv
      ),
    }));
  }, []);

  const rateConversation = useCallback((conversationId: string, rating: number) => {
    setState(prev => ({
      ...prev,
      conversations: prev.conversations.map(conv =>
        conv.id === conversationId ? { ...conv, user_rating: rating } : conv
      ),
    }));
  }, []);

  const updateViewMode = useCallback((mode: 'list' | 'grid' | 'timeline') => {
    setState(prev => ({ ...prev, view_mode: mode }));
  }, []);

  const toggleSidebar = useCallback(() => {
    setState(prev => ({ ...prev, sidebar_open: !prev.sidebar_open }));
  }, []);

  const selectConversation = useCallback((conversationId?: string) => {
    setState(prev => ({ ...prev, selected_conversation: conversationId }));
  }, []);

  return {
    // State
    ...state,
    stats,
    
    // Actions
    loadConversations,
    searchConversations,
    sortConversations,
    togglePin,
    toggleArchive,
    rateConversation,
    updateViewMode,
    toggleSidebar,
    selectConversation,
    clearCache,
    
    // Utilities
    isLoading: state.loading,
    hasError: !!state.error,
    isEmpty: state.conversations.length === 0,
    hasFilters: Object.keys(state.search_params).length > 0,
  };
}