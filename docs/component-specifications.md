# OneVice Component Design Specifications

**Version:** 1.0  
**Date:** September 1, 2025  
**Status:** Implementation Ready  
**Framework:** Next.js 15.4 + React 19 + TypeScript 5.6

## 1. Overview

This document defines the comprehensive React component specifications for the OneVice platform, including core UI components, page components, state management patterns, and TypeScript interfaces. All components follow the OneVice design system and support glassmorphism effects with dark theming.

## 2. Core UI Components

### 2.1 GlassmorphicCard Component

#### Interface Definition

```typescript
interface GlassmorphicCardProps {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'interactive' | 'modal';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  onClick?: () => void;
  className?: string;
  blurIntensity?: 'light' | 'medium' | 'heavy';
  border?: boolean;
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  'data-testid'?: string;
}

interface GlassmorphicCardVariants {
  default: {
    background: 'rgba(255, 255, 255, 0.05)';
    border: 'rgba(255, 255, 255, 0.1)';
    backdropBlur: '12px';
  };
  elevated: {
    background: 'rgba(255, 255, 255, 0.08)';
    border: 'rgba(255, 255, 255, 0.15)';
    backdropBlur: '16px';
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)';
  };
  interactive: {
    background: 'rgba(255, 255, 255, 0.05)';
    border: 'rgba(255, 255, 255, 0.1)';
    backdropBlur: '12px';
    cursor: 'pointer';
    transition: 'all 0.3s ease';
    hoverBackground: 'rgba(255, 255, 255, 0.08)';
    hoverBorder: 'rgba(255, 255, 255, 0.2)';
    hoverTransform: 'translateY(-2px)';
  };
  modal: {
    background: 'rgba(20, 20, 20, 0.85)';
    border: 'rgba(255, 255, 255, 0.15)';
    backdropBlur: '20px';
    boxShadow: '0 16px 64px rgba(0, 0, 0, 0.5)';
  };
}
```

#### Component Implementation Structure

```typescript
export const GlassmorphicCard: React.FC<GlassmorphicCardProps> = ({
  children,
  variant = 'default',
  size = 'md',
  hover = false,
  onClick,
  className = '',
  blurIntensity = 'medium',
  border = true,
  shadow = 'none',
  'data-testid': testId,
  ...props
}) => {
  const cardVariants = {
    // Variant definitions...
  };

  const sizeClasses = {
    sm: 'p-3 rounded-lg',
    md: 'p-6 rounded-xl',
    lg: 'p-8 rounded-2xl',
    xl: 'p-12 rounded-3xl'
  };

  return (
    <div
      className={cn(
        'glassmorphic-card',
        sizeClasses[size],
        cardVariants[variant],
        hover && 'hover:transform hover:scale-[1.02]',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
      data-testid={testId}
      {...props}
    >
      {children}
    </div>
  );
};
```

### 2.2 ChatInterface Component

#### Interface Definition

```typescript
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  agent?: 'sales_intelligence' | 'case_study' | 'talent_discovery' | 'bidding_support';
  status?: 'sending' | 'sent' | 'delivered' | 'error';
  metadata?: {
    confidence_score?: number;
    processing_time_ms?: number;
    sources?: string[];
    chunk_index?: number;
    total_chunks?: number;
  };
}

interface ChatInterfaceProps {
  threadId: string;
  userId: string;
  userRole: 'Leadership' | 'Director' | 'Salesperson' | 'Creative Director';
  initialMessages?: Message[];
  onMessageSend?: (message: string) => void;
  onAgentSelect?: (agent: string) => void;
  className?: string;
  autoFocus?: boolean;
  placeholder?: string;
  maxHeight?: string;
  enableFileUpload?: boolean;
  enableVoiceInput?: boolean;
  streamingEnabled?: boolean;
}

interface ChatInterfaceState {
  messages: Message[];
  isStreaming: boolean;
  currentStreamingMessage?: Partial<Message>;
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error';
  selectedAgent: string;
  inputValue: string;
  isTyping: boolean;
  error: string | null;
  retryCount: number;
}
```

#### Component Implementation Structure

```typescript
export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  threadId,
  userId,
  userRole,
  initialMessages = [],
  onMessageSend,
  onAgentSelect,
  className = '',
  autoFocus = true,
  placeholder = 'Ask about projects, talent, or budgets...',
  maxHeight = '600px',
  enableFileUpload = false,
  enableVoiceInput = false,
  streamingEnabled = true
}) => {
  // Hooks
  const { messages, sendMessage, isStreaming, connectionStatus } = useChat(threadId);
  const { isConnected, connectionError } = useWebSocket();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // State management
  const [state, setState] = useState<ChatInterfaceState>({
    messages: initialMessages,
    isStreaming: false,
    connectionStatus: 'disconnected',
    selectedAgent: 'sales_intelligence',
    inputValue: '',
    isTyping: false,
    error: null,
    retryCount: 0
  });

  // Component structure
  return (
    <div className={cn('chat-interface flex flex-col h-full', className)}>
      {/* Connection Status Bar */}
      <ConnectionStatusBar 
        status={connectionStatus}
        agent={state.selectedAgent}
        onRetry={handleRetryConnection}
      />

      {/* Agent Selection */}
      <AgentSelector
        selectedAgent={state.selectedAgent}
        userRole={userRole}
        onAgentChange={handleAgentChange}
      />

      {/* Messages Container */}
      <div 
        className="flex-1 overflow-y-auto p-4 space-y-4"
        style={{ maxHeight }}
      >
        <AnimatePresence>
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              userRole={userRole}
              showMetadata={userRole === 'Leadership'}
            />
          ))}
        </AnimatePresence>
        
        {isStreaming && <TypingIndicator agent={state.selectedAgent} />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <MessageInput
        ref={inputRef}
        value={state.inputValue}
        onChange={handleInputChange}
        onSubmit={handleMessageSubmit}
        placeholder={placeholder}
        disabled={!isConnected || isStreaming}
        autoFocus={autoFocus}
        enableFileUpload={enableFileUpload}
        enableVoiceInput={enableVoiceInput}
      />
    </div>
  );
};
```

### 2.3 MessageBubble Component

#### Interface Definition

```typescript
interface MessageBubbleProps {
  message: Message;
  userRole: 'Leadership' | 'Director' | 'Salesperson' | 'Creative Director';
  showMetadata?: boolean;
  onRetry?: (messageId: string) => void;
  onCopy?: (content: string) => void;
  onFeedback?: (messageId: string, rating: 'positive' | 'negative') => void;
  className?: string;
}

interface MessageActions {
  copy: boolean;
  retry: boolean;
  feedback: boolean;
  source: boolean;
  bookmark: boolean;
}
```

#### Component Implementation Structure

```typescript
export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  userRole,
  showMetadata = false,
  onRetry,
  onCopy,
  onFeedback,
  className = ''
}) => {
  const isUser = message.role === 'user';
  const [showActions, setShowActions] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      onCopy?.(message.content);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  }, [message.content, onCopy]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      className={cn('message-bubble', className)}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className={cn(
        'flex',
        isUser ? 'justify-end' : 'justify-start'
      )}>
        <div className={cn(
          'max-w-[80%] rounded-2xl px-4 py-3 relative',
          isUser
            ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
            : 'glassmorphic-card text-slate-100'
        )}>
          {/* Agent Badge for Assistant Messages */}
          {!isUser && message.agent && (
            <AgentBadge agent={message.agent} className="mb-2" />
          )}

          {/* Message Content */}
          <div className="message-content">
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  code: CodeBlock,
                  pre: PreBlock,
                  a: LinkComponent
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>

          {/* Message Metadata */}
          {showMetadata && message.metadata && (
            <MessageMetadata metadata={message.metadata} />
          )}

          {/* Message Footer */}
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs opacity-60">
              {formatMessageTime(message.timestamp)}
            </span>
            
            {message.status && (
              <MessageStatus status={message.status} />
            )}
          </div>

          {/* Message Actions */}
          <AnimatePresence>
            {showActions && (
              <MessageActions
                message={message}
                isUser={isUser}
                userRole={userRole}
                onCopy={handleCopy}
                onRetry={onRetry}
                onFeedback={onFeedback}
                copied={copied}
              />
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};
```

### 2.4 RoleBasedContent Component

#### Interface Definition

```typescript
interface RoleBasedContentProps {
  children: React.ReactNode;
  allowedRoles: ('Leadership' | 'Director' | 'Salesperson' | 'Creative Director')[];
  userRole: string;
  fallback?: React.ReactNode;
  sensitivityLevel?: 1 | 2 | 3 | 4 | 5 | 6;
  showPlaceholder?: boolean;
  className?: string;
}

interface ContentFilter {
  role: string;
  sensitivityLevel: number;
  allowed: boolean;
  reason?: string;
}
```

#### Component Implementation Structure

```typescript
export const RoleBasedContent: React.FC<RoleBasedContentProps> = ({
  children,
  allowedRoles,
  userRole,
  fallback,
  sensitivityLevel,
  showPlaceholder = true,
  className = ''
}) => {
  const isAllowed = useMemo(() => {
    // Base role check
    if (!allowedRoles.includes(userRole as any)) {
      return false;
    }

    // Sensitivity level check
    if (sensitivityLevel) {
      return checkDataSensitivityAccess(userRole, sensitivityLevel);
    }

    return true;
  }, [allowedRoles, userRole, sensitivityLevel]);

  if (!isAllowed) {
    if (fallback) {
      return <>{fallback}</>;
    }

    if (showPlaceholder) {
      return (
        <div className={cn('role-restricted-content p-4 rounded-lg border border-dashed border-gray-600', className)}>
          <div className="flex items-center space-x-2 text-gray-400">
            <LockIcon className="w-4 h-4" />
            <span className="text-sm">
              Content restricted for your role ({userRole})
            </span>
          </div>
        </div>
      );
    }

    return null;
  }

  return <div className={className}>{children}</div>;
};

// Helper function for data sensitivity checking
function checkDataSensitivityAccess(role: string, level: number): boolean {
  const accessMatrix = {
    'Leadership': [1, 2, 3, 4, 5, 6],
    'Director': [2, 3, 4, 5, 6], // No budget access (level 1)
    'Salesperson': [4, 5, 6],     // Limited access
    'Creative Director': [4, 5, 6] // Same as Salesperson
  };

  return accessMatrix[role]?.includes(level) ?? false;
}
```

### 2.5 AgentSelector Component

#### Interface Definition

```typescript
interface AgentOption {
  id: 'sales_intelligence' | 'case_study' | 'talent_discovery' | 'bidding_support';
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  color: string;
  specialties: string[];
  estimatedResponseTime: string;
  accessibleToRoles: ('Leadership' | 'Director' | 'Salesperson' | 'Creative Director')[];
}

interface AgentSelectorProps {
  selectedAgent: string;
  userRole: 'Leadership' | 'Director' | 'Salesperson' | 'Creative Director';
  onAgentChange: (agentId: string) => void;
  layout?: 'horizontal' | 'vertical' | 'dropdown';
  showDescriptions?: boolean;
  className?: string;
}
```

#### Component Implementation Structure

```typescript
const AGENT_OPTIONS: AgentOption[] = [
  {
    id: 'sales_intelligence',
    name: 'Sales Intelligence',
    description: 'Research contacts, companies, and industry relationships',
    icon: SearchIcon,
    color: 'from-blue-500 to-cyan-500',
    specialties: ['Contact Research', 'Company Analysis', 'Relationship Mapping'],
    estimatedResponseTime: '2-3 seconds',
    accessibleToRoles: ['Leadership', 'Director', 'Salesperson', 'Creative Director']
  },
  {
    id: 'case_study',
    name: 'Case Study',
    description: 'Find similar projects and generate compelling case studies',
    icon: DocumentIcon,
    color: 'from-green-500 to-emerald-500',
    specialties: ['Project Matching', 'Template Generation', 'Portfolio Assembly'],
    estimatedResponseTime: '3-5 seconds',
    accessibleToRoles: ['Leadership', 'Director', 'Salesperson', 'Creative Director']
  },
  {
    id: 'talent_discovery',
    name: 'Talent Discovery',
    description: 'Advanced search for production talent and resources',
    icon: UsersIcon,
    color: 'from-purple-500 to-pink-500',
    specialties: ['Multi-faceted Search', 'Availability Prediction', 'Skill Matching'],
    estimatedResponseTime: '2-4 seconds',
    accessibleToRoles: ['Leadership', 'Director', 'Salesperson', 'Creative Director']
  },
  {
    id: 'bidding_support',
    name: 'Bidding Support',
    description: 'Budget analysis and union rule integration',
    icon: CalculatorIcon,
    color: 'from-orange-500 to-red-500',
    specialties: ['Budget Analysis', 'Union Rules', 'Risk Assessment'],
    estimatedResponseTime: '4-8 seconds',
    accessibleToRoles: ['Leadership', 'Director']
  }
];

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  selectedAgent,
  userRole,
  onAgentChange,
  layout = 'horizontal',
  showDescriptions = true,
  className = ''
}) => {
  const availableAgents = useMemo(() => {
    return AGENT_OPTIONS.filter(agent => 
      agent.accessibleToRoles.includes(userRole)
    );
  }, [userRole]);

  if (layout === 'dropdown') {
    return (
      <Select value={selectedAgent} onValueChange={onAgentChange}>
        <SelectTrigger className={cn('agent-selector-trigger', className)}>
          <SelectValue>
            <AgentOption agent={availableAgents.find(a => a.id === selectedAgent)!} />
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {availableAgents.map(agent => (
            <SelectItem key={agent.id} value={agent.id}>
              <AgentOption agent={agent} showDescription={false} />
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  }

  return (
    <div className={cn(
      'agent-selector',
      layout === 'horizontal' ? 'flex flex-wrap gap-3' : 'space-y-2',
      className
    )}>
      {availableAgents.map(agent => (
        <AgentCard
          key={agent.id}
          agent={agent}
          isSelected={selectedAgent === agent.id}
          onClick={() => onAgentChange(agent.id)}
          showDescription={showDescriptions}
          layout={layout}
        />
      ))}
    </div>
  );
};
```

## 3. Page Components

### 3.1 HomePage Component

#### Interface Definition

```typescript
interface HomePageProps {
  user?: {
    id: string;
    role: string;
    name: string;
  };
  className?: string;
}

interface HeroSectionProps {
  user?: {
    name: string;
    role: string;
  };
  onGetStarted: () => void;
}

interface FeatureSectionProps {
  features: FeatureItem[];
  variant?: 'grid' | 'carousel' | 'list';
}

interface FeatureItem {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  href?: string;
  comingSoon?: boolean;
}
```

#### Component Structure

```typescript
export const HomePage: React.FC<HomePageProps> = ({
  user,
  className = ''
}) => {
  const router = useRouter();
  
  const handleGetStarted = useCallback(() => {
    if (user) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [user, router]);

  return (
    <div className={cn('homepage', className)}>
      {/* Hero Section - 600px */}
      <HeroSection
        user={user}
        onGetStarted={handleGetStarted}
        className="h-[600px]"
      />

      {/* Feature Overview Section - 590px */}
      <FeatureOverviewSection className="h-[590px]" />

      {/* AI Agents Showcase - 902px */}
      <AgentsShowcaseSection 
        agents={AGENT_OPTIONS}
        className="h-[902px]"
      />

      {/* Success Stories - 807px */}
      <SuccessStoriesSection className="h-[807px]" />

      {/* Platform Benefits - 764px */}
      <PlatformBenefitsSection className="h-[764px]" />

      {/* CTA Section - 605px */}
      <CTASection 
        onGetStarted={handleGetStarted}
        className="h-[605px]"
      />
    </div>
  );
};
```

### 3.2 LeadershipDashboard Component

#### Interface Definition

```typescript
interface LeadershipDashboardProps {
  user: {
    id: string;
    role: 'Leadership';
    permissions: string[];
  };
  timeframe?: '7d' | '30d' | '90d' | '1y';
  refreshInterval?: number;
}

interface DashboardMetrics {
  overview: {
    totalProjects: number;
    activeProjects: number;
    completedThisMonth: number;
    pipelineValue: string;
    teamUtilization: number;
  };
  agentUsage: {
    [key: string]: {
      queries: number;
      avgResponseTime: string;
      successRate: number;
      topQueries: string[];
    };
  };
  performance: {
    systemHealth: 'healthy' | 'degraded' | 'error';
    uptime: string;
    avgResponseTime: string;
    errorRate: number;
  };
  recentActivity: ActivityItem[];
}

interface ActivityItem {
  id: string;
  type: 'query' | 'project_update' | 'system_event';
  user: string;
  action: string;
  timestamp: string;
  metadata?: Record<string, any>;
}
```

### 3.3 TalentDiscoveryPage Component

#### Interface Definition

```typescript
interface TalentDiscoveryPageProps {
  user: {
    id: string;
    role: string;
  };
  initialFilters?: TalentFilters;
}

interface TalentFilters {
  role?: string[];
  unionStatus?: 'Union' | 'Non-Union' | 'Either';
  specialization?: string[];
  budgetRange?: {
    min: number;
    max: number;
  };
  availability?: {
    startDate: string;
    endDate: string;
  };
  location?: string[];
  experienceLevel?: 'Entry' | 'Mid' | 'Senior' | 'Expert';
}

interface TalentSearchResults {
  results: TalentProfile[];
  totalCount: number;
  page: number;
  pageSize: number;
  facets: {
    roles: { value: string; count: number }[];
    specializations: { value: string; count: number }[];
    locations: { value: string; count: number }[];
  };
}

interface TalentProfile {
  id: string;
  name: string;
  role: string;
  unionStatus: string;
  specializations: string[];
  budgetRange: string;
  location: string;
  availability: {
    status: 'available' | 'busy' | 'unknown';
    nextAvailable?: string;
  };
  portfolio: PortfolioItem[];
  matchScore?: number;
  lastUpdated: string;
}
```

### 3.4 BiddingPage Component

#### Interface Definition

```typescript
interface BiddingPageProps {
  user: {
    id: string;
    role: string;
  };
  projectId?: string;
  initialData?: BiddingFormData;
}

interface BiddingFormData {
  projectDetails: {
    name: string;
    type: 'Music Video' | 'Commercial' | 'Brand Film';
    duration: number; // in days
    location: string;
    unionStatus: 'Union' | 'Non-Union' | 'Mixed';
    crewSize: 'Small' | 'Medium' | 'Large';
    equipmentLevel: 'Basic' | 'Standard' | 'Premium';
  };
  budgetRequirements: {
    totalBudget?: number;
    flexibilityPercentage: number;
    currency: 'USD' | 'CAD' | 'GBP' | 'EUR';
    contingencyPercentage: number;
  };
  timeline: {
    prepStart: string;
    shootStart: string;
    shootEnd: string;
    deliveryDate: string;
    flexibleDates: boolean;
  };
  specialRequirements?: {
    unionSpecific: string[];
    equipmentSpecific: string[];
    locationSpecific: string[];
    talentSpecific: string[];
  };
}

interface BiddingAnalysis {
  budgetBreakdown: {
    aboveLine: number;
    belowLine: number;
    postProduction: number;
    contingency: number;
    total: number;
  };
  unionCompliance: {
    requirements: UnionRequirement[];
    estimatedCosts: { [union: string]: number };
    riskFactors: string[];
  };
  competitiveAnalysis: {
    marketRange: { min: number; max: number };
    recommendedBid: number;
    winProbability: number;
    differentiators: string[];
  };
  riskAssessment: {
    overall: 'Low' | 'Medium' | 'High';
    factors: RiskFactor[];
    mitigationStrategies: string[];
  };
}
```

## 4. State Management Specifications

### 4.1 Zustand Store Structures

#### Chat Store

```typescript
interface ChatState {
  conversations: Map<string, Message[]>;
  activeThread: string | null;
  isStreaming: boolean;
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error';
  selectedAgent: string;
  
  // Actions
  addMessage: (threadId: string, message: Message) => void;
  updateMessage: (threadId: string, messageId: string, update: Partial<Message>) => void;
  setActiveThread: (threadId: string) => void;
  setStreaming: (isStreaming: boolean) => void;
  setConnectionStatus: (status: ChatState['connectionStatus']) => void;
  setSelectedAgent: (agent: string) => void;
  clearConversation: (threadId: string) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: new Map(),
      activeThread: null,
      isStreaming: false,
      connectionStatus: 'disconnected',
      selectedAgent: 'sales_intelligence',

      addMessage: (threadId, message) => {
        set((state) => {
          const conversations = new Map(state.conversations);
          const messages = conversations.get(threadId) || [];
          conversations.set(threadId, [...messages, message]);
          return { conversations };
        });
      },

      updateMessage: (threadId, messageId, update) => {
        set((state) => {
          const conversations = new Map(state.conversations);
          const messages = conversations.get(threadId) || [];
          const updatedMessages = messages.map(msg =>
            msg.id === messageId ? { ...msg, ...update } : msg
          );
          conversations.set(threadId, updatedMessages);
          return { conversations };
        });
      },

      setActiveThread: (threadId) => set({ activeThread: threadId }),
      setStreaming: (isStreaming) => set({ isStreaming }),
      setConnectionStatus: (connectionStatus) => set({ connectionStatus }),
      setSelectedAgent: (selectedAgent) => set({ selectedAgent }),
      
      clearConversation: (threadId) => {
        set((state) => {
          const conversations = new Map(state.conversations);
          conversations.delete(threadId);
          return { conversations };
        });
      }
    }),
    {
      name: 'onevice-chat-storage',
      partialize: (state) => ({
        conversations: Array.from(state.conversations.entries()),
        activeThread: state.activeThread,
        selectedAgent: state.selectedAgent
      }),
      onRehydrateStorage: () => (state) => {
        if (state && Array.isArray(state.conversations)) {
          state.conversations = new Map(state.conversations);
        }
      }
    }
  )
);
```

#### User Store

```typescript
interface UserState {
  user: {
    id: string;
    email: string;
    role: 'Leadership' | 'Director' | 'Salesperson' | 'Creative Director';
    permissions: string[];
    dataSensitivityLevel: number;
    preferences: UserPreferences;
  } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  setUser: (user: UserState['user']) => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  logout: () => void;
}

interface UserPreferences {
  theme: 'dark' | 'light';
  defaultAgent: string;
  notifications: boolean;
  autoSave: boolean;
  language: 'en' | 'es' | 'fr';
  timezone: string;
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  
  updatePreferences: (preferences) => set((state) => ({
    user: state.user ? {
      ...state.user,
      preferences: { ...state.user.preferences, ...preferences }
    } : null
  })),
  
  logout: () => set({ user: null, isAuthenticated: false })
}));
```

#### WebSocket Store

```typescript
interface WebSocketState {
  connections: Map<string, WebSocketConnection>;
  activeConnections: Set<string>;
  connectionHealth: 'healthy' | 'degraded' | 'error';
  messageQueue: QueuedMessage[];
  reconnectAttempts: number;
  
  // Actions
  addConnection: (id: string, connection: WebSocketConnection) => void;
  removeConnection: (id: string) => void;
  updateConnectionHealth: (health: WebSocketState['connectionHealth']) => void;
  queueMessage: (message: QueuedMessage) => void;
  processMessageQueue: () => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
}

interface WebSocketConnection {
  socket: WebSocket;
  url: string;
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastPing: number;
  reconnectCount: number;
}

interface QueuedMessage {
  id: string;
  connectionId: string;
  data: any;
  timestamp: number;
  retries: number;
}
```

## 5. Custom Hooks

### 5.1 useWebSocket Hook

```typescript
interface UseWebSocketConfig {
  url: string;
  protocols?: string[];
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onMessage?: (event: MessageEvent) => void;
  onError?: (event: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
}

interface UseWebSocketReturn {
  socket: WebSocket | null;
  isConnected: boolean;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastMessage: MessageEvent | null;
  send: (data: string | ArrayBufferLike | Blob | ArrayBufferView) => void;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
}

export function useWebSocket(config: UseWebSocketConfig): UseWebSocketReturn {
  // Implementation details...
}
```

### 5.2 useChat Hook

```typescript
interface UseChatConfig {
  threadId: string;
  userId: string;
  userRole: string;
  apiBaseUrl?: string;
  wsBaseUrl?: string;
  autoConnect?: boolean;
}

interface UseChatReturn {
  messages: Message[];
  isStreaming: boolean;
  isConnected: boolean;
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error';
  error: string | null;
  
  sendMessage: (content: string, agent?: string) => Promise<void>;
  retryMessage: (messageId: string) => Promise<void>;
  clearHistory: () => void;
  reconnect: () => void;
}

export function useChat(config: UseChatConfig): UseChatReturn {
  // Implementation details...
}
```

### 5.3 useRBAC Hook

```typescript
interface UseRBACConfig {
  userRole: string;
  permissions: string[];
}

interface UseRBACReturn {
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  canAccessDataLevel: (sensitivityLevel: number) => boolean;
  filterContent: <T>(content: T, sensitivityLevel: number) => T | null;
}

export function useRBAC(config: UseRBACConfig): UseRBACReturn {
  // Implementation details...
}
```

## 6. TypeScript Type Definitions

### 6.1 Core Types

```typescript
// User and Authentication Types
export interface User {
  id: string;
  email: string;
  role: 'Leadership' | 'Director' | 'Salesperson' | 'Creative Director';
  permissions: Permission[];
  dataSensitivityLevel: 1 | 2 | 3 | 4 | 5 | 6;
  preferences: UserPreferences;
  createdAt: string;
  lastLogin: string;
}

export interface Permission {
  resource: string;
  actions: ('create' | 'read' | 'update' | 'delete')[];
  conditions?: Record<string, any>;
}

// Project and Entity Types
export interface Project {
  id: string;
  name: string;
  type: 'Music Video' | 'Commercial' | 'Brand Film';
  status: 'Planning' | 'In Production' | 'Post Production' | 'Completed' | 'Cancelled';
  budget: {
    total: number;
    breakdown: BudgetBreakdown;
    currency: 'USD' | 'CAD' | 'GBP' | 'EUR';
  };
  team: ProjectTeam;
  timeline: ProjectTimeline;
  client: Organization;
  unionStatus: 'Union' | 'Non-Union' | 'Mixed';
  sensitivityLevel: 1 | 2 | 3 | 4 | 5 | 6;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface Person {
  id: string;
  name: string;
  roleType: 'Director' | 'Creative Director' | 'Talent' | 'Client' | 'Producer';
  unionStatus: 'Union' | 'Non-Union' | 'Unknown';
  specializations: string[];
  contactInfo: ContactInfo;
  bio: string;
  portfolio: PortfolioItem[];
  availability: AvailabilityInfo;
}

// API Response Types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
  timestamp: string;
  requestId: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  requestId: string;
  documentationUrl?: string;
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  'data-testid'?: string;
  children?: React.ReactNode;
}

export interface InteractiveComponentProps extends BaseComponentProps {
  disabled?: boolean;
  loading?: boolean;
  onClick?: (event: React.MouseEvent) => void;
}
```

### 6.2 Agent and AI Types

```typescript
export interface AgentQuery {
  id: string;
  agent: 'sales_intelligence' | 'case_study' | 'talent_discovery' | 'bidding_support';
  query: string;
  context?: Record<string, any>;
  options?: QueryOptions;
  userId: string;
  threadId: string;
  timestamp: string;
}

export interface AgentResponse {
  queryId: string;
  agent: string;
  result: any;
  confidenceScore: number;
  sources: string[];
  processingTimeMs: number;
  metadata: ResponseMetadata;
}

export interface StreamingChunk {
  chunkIndex: number;
  totalChunks?: number;
  content: string;
  metadata: ChunkMetadata;
  isComplete: boolean;
}

export interface QueryOptions {
  maxResults?: number;
  includeMetadata?: boolean;
  streamResponse?: boolean;
  timeoutMs?: number;
  filters?: Record<string, any>;
}
```

## 7. Testing Specifications

### 7.1 Component Testing Structure

```typescript
// Example test structure for GlassmorphicCard
describe('GlassmorphicCard', () => {
  const defaultProps: GlassmorphicCardProps = {
    children: 'Test content'
  };

  it('renders children correctly', () => {
    render(<GlassmorphicCard {...defaultProps} />);
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('applies correct variant styles', () => {
    render(<GlassmorphicCard {...defaultProps} variant="elevated" />);
    const card = screen.getByRole('generic');
    expect(card).toHaveClass('glassmorphic-card-elevated');
  });

  it('handles click events when interactive', () => {
    const handleClick = jest.fn();
    render(<GlassmorphicCard {...defaultProps} onClick={handleClick} />);
    
    const card = screen.getByRole('button');
    fireEvent.click(card);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('respects accessibility attributes', () => {
    render(<GlassmorphicCard {...defaultProps} data-testid="test-card" />);
    expect(screen.getByTestId('test-card')).toBeInTheDocument();
  });
});
```

### 7.2 Hook Testing Structure

```typescript
// Example test structure for useChat hook
describe('useChat', () => {
  const mockConfig: UseChatConfig = {
    threadId: 'test-thread',
    userId: 'test-user',
    userRole: 'Salesperson'
  };

  beforeEach(() => {
    // Setup mock WebSocket
    jest.clearAllMocks();
  });

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useChat(mockConfig));
    
    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.isConnected).toBe(false);
  });

  it('sends messages correctly', async () => {
    const { result } = renderHook(() => useChat(mockConfig));
    
    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe('Test message');
  });

  it('handles streaming responses', async () => {
    const { result } = renderHook(() => useChat(mockConfig));
    
    // Mock streaming response
    await act(async () => {
      // Simulate streaming chunks
    });

    expect(result.current.isStreaming).toBe(false);
  });
});
```

---

**Document Status**: Ready for Implementation  
**Last Updated**: September 1, 2025  
**Next Review**: Upon completion of component implementation