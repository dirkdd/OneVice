// Main conversation history system
export { ConversationHistoryMain } from '@/components/ui/conversation-history-main';
export { ConversationHistorySidebar } from '@/components/ui/conversation-history-sidebar';
export { useConversationHistory } from '@/hooks/useConversationHistory';

// Individual components
export { ConversationThreadCard } from '@/components/ui/conversation-thread-card';
export { ConversationTimeline } from '@/components/ui/conversation-timeline';
export { AgentParticipationBadge } from '@/components/ui/agent-participation-badge';
export { AgentHandoffIndicator, AgentHandoffSummary } from '@/components/ui/agent-handoff-indicator';

// Enhanced agent message with handoff support
export { AgentMessage } from '@/components/ui/agent-message';

// Types
export type {
  ConversationThread,
  ConversationHistoryState,
  ConversationSearchParams,
  ConversationSort,
  ConversationStats,
  MessageWithAgent,
  AgentHandoff,
  AgentUsageStats,
  AgentParticipationData,
  ConversationTimelineEvent,
  ConversationInsights,
} from '@/types/conversation-history';