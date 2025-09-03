# Conversation History System

A comprehensive conversation history system with agent context tracking for the OneVice AI-powered business intelligence platform.

## Overview

The Conversation History System provides:

- **Agent-Aware History Storage**: Track which agents participated in conversations with detailed metadata
- **Conversation Threads**: Group messages by conversation with agent participation tracking
- **Agent Continuity**: Show which agents were involved in previous conversations
- **Context Preservation**: Maintain agent-specific conversation context across sessions
- **Search and Filter**: Filter conversations by agent type, capability, date, rating, and more
- **Visual History**: Rich UI showing agent participation in conversation threads
- **Timeline Views**: Chronological visualization of conversation events and agent handoffs
- **Export Capabilities**: Export conversations in JSON, Markdown, or CSV formats

## Architecture

### Core Components

#### 1. Main Interface
- `ConversationHistoryMain` - Primary interface component with all views and controls
- `ConversationHistorySidebar` - Filtering and search sidebar with statistics
- `ConversationThreadCard` - Individual conversation display with agent information

#### 2. Agent-Specific Components
- `AgentParticipationBadge` - Shows agent usage statistics in conversations
- `AgentHandoffIndicator` - Visualizes agent transitions during conversations
- `AgentHandoffSummary` - Summary view of all handoffs in a conversation

#### 3. Timeline and Visualization
- `ConversationTimeline` - Chronological view of conversation events
- `DatePicker` - Date range selection for filtering

#### 4. Enhanced Message Display
- Enhanced `AgentMessage` component with handoff visualization support

### Data Layer

#### Core Types
```typescript
interface ConversationThread {
  id: string;
  title: string;
  context: DashboardContext;
  participating_agents: AgentType[];
  primary_agent?: AgentType;
  agent_handoffs: AgentHandoff[];
  agent_usage_stats: AgentUsageStats;
  conversation_tags: string[];
  user_rating?: number;
  is_pinned: boolean;
  is_archived: boolean;
}
```

#### Agent Tracking
```typescript
interface AgentHandoff {
  id: string;
  from_agent?: AgentType;
  to_agent: AgentType;
  timestamp: string;
  reason?: string;
  message_id: string;
  context_shift?: DashboardContext;
}

interface AgentUsageStats {
  total_messages: number;
  agent_breakdown: Record<AgentType, number>;
  processing_time_avg: Record<AgentType, number>;
  confidence_avg: Record<AgentType, number>;
  last_agent_used?: AgentType;
}
```

### State Management

#### Main Hook: `useConversationHistory`
```typescript
const {
  conversations,
  loading,
  error,
  searchConversations,
  sortConversations,
  togglePin,
  toggleArchive,
  rateConversation,
  updateViewMode,
  stats
} = useConversationHistory();
```

#### Export Hook: `useConversationExport`
```typescript
const { exportConversation, exportMultipleConversations } = useConversationExport();
```

## Features

### 1. Agent-Aware History
- Track which agents participated in each conversation
- Show agent contribution percentages
- Display agent confidence and processing times
- Identify primary agent for each conversation

### 2. Agent Handoffs
- Visual indicators when conversations switch between agents
- Handoff reasons and context
- Timeline of agent transitions
- Statistics on handoff frequency

### 3. Smart Filtering and Search
- Filter by participating agents
- Filter by conversation context
- Date range filtering
- Rating-based filtering
- Tag-based search
- Pinned/archived status

### 4. Multiple View Modes
- **List View**: Compact conversation list
- **Grid View**: Card-based layout with rich visuals
- **Timeline View**: Chronological event visualization

### 5. Conversation Management
- Pin important conversations
- Archive completed conversations
- Rate conversations (1-5 stars)
- Tag conversations for organization

### 6. Export and Sharing
- Export individual conversations
- Bulk export multiple conversations
- Multiple formats: JSON, Markdown, CSV
- Configurable export options

### 7. Performance Optimization
- Client-side caching with localStorage
- Lazy loading of conversation details
- Efficient search and filtering
- Optimistic UI updates

## Integration Points

### WebSocket Integration
The system integrates with the existing WebSocket infrastructure:

```typescript
// WebSocket messages include agent metadata
interface WebSocketMessage {
  agent?: AgentType;
  agent_metadata?: AgentMetadata;
  conversation_id?: string;
}
```

### Agent Preferences Integration
Works with the existing `AgentPreferencesContext`:

```typescript
// Agent preferences influence conversation routing
const { preferences, getContextSuggestions } = useAgentPreferences();
```

### Backend API Integration
Extends the existing conversations API:

```typescript
// Enhanced conversation data with agent information
const response = await conversationsApi.getConversations({
  agent_filter: [AgentType.SALES, AgentType.ANALYTICS],
  has_handoffs: true
});
```

## Usage Examples

### Basic Usage
```tsx
import { ConversationHistoryMain } from '@/components/conversation-history';

function ConversationHistoryPage() {
  const handleSelectConversation = (conversation) => {
    // Navigate to conversation or load in chat interface
    console.log('Selected:', conversation);
  };

  return (
    <ConversationHistoryMain
      onSelectConversation={handleSelectConversation}
      onNewConversation={() => router.push('/chat')}
    />
  );
}
```

### Agent-Specific Filtering
```tsx
import { useConversationHistory } from '@/hooks/useConversationHistory';
import { AgentType } from '@/lib/api/types';

function SalesConversations() {
  const { searchConversations } = useConversationHistory();

  useEffect(() => {
    searchConversations({
      agent_filter: [AgentType.SALES],
      context_filter: ['pre-call-brief', 'bid-proposal']
    });
  }, []);

  return <ConversationHistoryMain />;
}
```

### Export Functionality
```tsx
import { useConversationExport } from '@/hooks/useConversationExport';

function ConversationCard({ conversation }) {
  const { exportConversation } = useConversationExport();

  const handleExport = async () => {
    const result = await exportConversation(conversation, {
      format: 'markdown',
      includeMetadata: true,
      includeAgentInfo: true,
      includeHandoffs: true
    });

    if (result.success) {
      toast.success(`Exported as ${result.filename}`);
    }
  };

  return (
    <Button onClick={handleExport}>
      Export Conversation
    </Button>
  );
}
```

## Demo

A comprehensive demo is available at:
```tsx
import { ConversationHistoryDemo } from '@/components/conversation-history/ConversationHistoryDemo';
```

The demo includes:
- Mock conversation data with realistic agent interactions
- All view modes and filtering options
- Agent handoff examples
- Export functionality demonstration
- Performance metrics and statistics

## Backend Requirements

### Database Schema Extensions
The system requires the following database schema extensions:

```sql
-- Conversations table enhancements
ALTER TABLE conversations ADD COLUMN participating_agents JSON;
ALTER TABLE conversations ADD COLUMN primary_agent VARCHAR(50);
ALTER TABLE conversations ADD COLUMN agent_usage_stats JSON;
ALTER TABLE conversations ADD COLUMN user_rating INTEGER;
ALTER TABLE conversations ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN conversation_tags JSON;

-- Agent handoffs table
CREATE TABLE agent_handoffs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id),
  from_agent VARCHAR(50),
  to_agent VARCHAR(50) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  reason TEXT,
  message_id UUID,
  context_shift VARCHAR(50)
);
```

### API Endpoints
```typescript
// Enhanced conversation endpoints
GET /api/conversations?agent_filter=sales&has_handoffs=true
GET /api/conversations/{id}/timeline
POST /api/conversations/{id}/rating
PUT /api/conversations/{id}/pin
PUT /api/conversations/{id}/archive
```

### Redis Integration
```typescript
// Conversation history caching
const cacheKey = `conversation_history:${userId}`;
await redis.setex(cacheKey, 300, JSON.stringify(conversations));
```

## Performance Considerations

### Client-Side Optimizations
- **Lazy Loading**: Load conversation details on demand
- **Virtual Scrolling**: For large conversation lists
- **Debounced Search**: Prevent excessive API calls
- **Caching Strategy**: Cache conversations and search results

### Memory Management
- **Conversation Limits**: Limit loaded conversations (default: 50)
- **Message Pagination**: Load messages in chunks
- **Cache Cleanup**: Automatic cleanup of old cached data
- **Image Optimization**: Lazy load agent avatars and media

### Backend Optimizations
- **Database Indexing**: Index on agent types, timestamps, contexts
- **Query Optimization**: Efficient agent participation queries
- **Caching Layer**: Redis caching for frequently accessed data
- **Connection Pooling**: Optimize database connections

## Security and Privacy

### Data Protection
- **User Isolation**: Conversations scoped to authenticated user
- **Sensitive Data**: Exclude sensitive information from exports
- **Access Control**: Role-based access to conversation features
- **Audit Trail**: Log conversation access and modifications

### Export Security
- **File Size Limits**: Prevent excessive export sizes
- **Rate Limiting**: Limit export frequency per user
- **Content Sanitization**: Clean exported content
- **Temporary Files**: Auto-delete temporary export files

## Future Enhancements

### Planned Features
- **Conversation Merging**: Combine related conversations
- **Advanced Analytics**: Conversation insights and trends
- **AI Summarization**: Auto-generate conversation summaries
- **Collaboration**: Share conversations with team members
- **Voice Integration**: Support for voice conversation history
- **Mobile App**: Native mobile conversation history

### Technical Improvements
- **Real-time Updates**: Live conversation updates via WebSocket
- **Advanced Search**: Full-text search with ranking
- **Bulk Operations**: Bulk archive, delete, export
- **Custom Views**: User-defined conversation views
- **Integration APIs**: Third-party integration endpoints
- **Machine Learning**: Conversation quality scoring

## Contributing

### Development Setup
1. Install dependencies: `npm install`
2. Start development server: `npm run dev`
3. Run tests: `npm run test`
4. Build for production: `npm run build`

### Code Standards
- TypeScript strict mode
- ESLint and Prettier configuration
- Component documentation with JSDoc
- Unit tests for hooks and utilities
- Integration tests for main components

### Testing Strategy
- **Unit Tests**: Individual component and hook testing
- **Integration Tests**: Full user flow testing
- **Performance Tests**: Load testing with large datasets
- **Accessibility Tests**: WCAG compliance validation
- **Visual Tests**: Screenshot regression testing