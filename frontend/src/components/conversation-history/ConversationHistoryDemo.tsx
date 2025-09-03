import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ConversationHistoryMain } from "./index";
import { ConversationThread } from "@/types/conversation-history";
import { AgentType } from "@/lib/api/types";
import { 
  MessageSquare, 
  History, 
  Users, 
  TrendingUp,
  Clock,
  ArrowRightLeft
} from "lucide-react";

// Mock data for demonstration
const mockConversations: ConversationThread[] = [
  {
    id: "conv-1",
    title: "Market Research for Netflix Documentary",
    subtitle: "Exploring audience preferences for documentary content",
    context: "case-study",
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-15T11:45:00Z",
    message_count: 24,
    last_message_preview: "Based on the market analysis, I recommend targeting the 25-54 demographic with this documentary series...",
    participating_agents: [AgentType.SALES, AgentType.ANALYTICS],
    primary_agent: AgentType.ANALYTICS,
    agent_handoffs: [
      {
        id: "handoff-1",
        from_agent: AgentType.SALES,
        to_agent: AgentType.ANALYTICS,
        timestamp: "2024-01-15T11:15:00Z",
        reason: "Switching to analytics for detailed market research",
        message_id: "msg-15",
      }
    ],
    agent_usage_stats: {
      total_messages: 24,
      agent_breakdown: {
        [AgentType.SALES]: 8,
        [AgentType.ANALYTICS]: 16,
        [AgentType.TALENT]: 0,
      },
      processing_time_avg: {
        [AgentType.SALES]: 1200,
        [AgentType.ANALYTICS]: 2100,
        [AgentType.TALENT]: 0,
      },
      confidence_avg: {
        [AgentType.SALES]: 2.8,
        [AgentType.ANALYTICS]: 3.0,
        [AgentType.TALENT]: 0,
      },
      last_agent_used: AgentType.ANALYTICS,
    },
    conversation_tags: ["market-research", "netflix", "documentary"],
    user_rating: 5,
    is_pinned: true,
    is_archived: false,
  },
  {
    id: "conv-2",
    title: "Talent Search for Period Drama",
    subtitle: "Finding the perfect cast for 18th century costume drama",
    context: "talent-discovery",
    created_at: "2024-01-14T14:20:00Z",
    updated_at: "2024-01-14T16:30:00Z",
    message_count: 18,
    last_message_preview: "I've identified 5 potential leads who have experience with period pieces and match your criteria...",
    participating_agents: [AgentType.TALENT, AgentType.ANALYTICS, AgentType.SALES],
    primary_agent: AgentType.TALENT,
    agent_handoffs: [
      {
        id: "handoff-2",
        from_agent: AgentType.TALENT,
        to_agent: AgentType.ANALYTICS,
        timestamp: "2024-01-14T15:45:00Z",
        reason: "Need budget analysis for talent costs",
        message_id: "msg-12",
      },
      {
        id: "handoff-3",
        from_agent: AgentType.ANALYTICS,
        to_agent: AgentType.SALES,
        timestamp: "2024-01-14T16:10:00Z",
        reason: "Discussing contract negotiations",
        message_id: "msg-16",
      }
    ],
    agent_usage_stats: {
      total_messages: 18,
      agent_breakdown: {
        [AgentType.TALENT]: 10,
        [AgentType.ANALYTICS]: 5,
        [AgentType.SALES]: 3,
      },
      processing_time_avg: {
        [AgentType.TALENT]: 1800,
        [AgentType.ANALYTICS]: 2400,
        [AgentType.SALES]: 1100,
      },
      confidence_avg: {
        [AgentType.TALENT]: 2.9,
        [AgentType.ANALYTICS]: 2.7,
        [AgentType.SALES]: 2.5,
      },
      last_agent_used: AgentType.SALES,
    },
    conversation_tags: ["casting", "period-drama", "talent"],
    user_rating: 4,
    is_pinned: false,
    is_archived: false,
  },
  {
    id: "conv-3", 
    title: "Budget Optimization Strategy",
    subtitle: "Reducing production costs while maintaining quality",
    context: "pre-call-brief",
    created_at: "2024-01-13T09:15:00Z",
    updated_at: "2024-01-13T10:45:00Z",
    message_count: 12,
    last_message_preview: "The proposed budget cuts in post-production could save 15% without significantly impacting quality...",
    participating_agents: [AgentType.ANALYTICS, AgentType.SALES],
    primary_agent: AgentType.ANALYTICS,
    agent_handoffs: [],
    agent_usage_stats: {
      total_messages: 12,
      agent_breakdown: {
        [AgentType.ANALYTICS]: 8,
        [AgentType.SALES]: 4,
        [AgentType.TALENT]: 0,
      },
      processing_time_avg: {
        [AgentType.ANALYTICS]: 1950,
        [AgentType.SALES]: 1350,
        [AgentType.TALENT]: 0,
      },
      confidence_avg: {
        [AgentType.ANALYTICS]: 2.8,
        [AgentType.SALES]: 2.6,
        [AgentType.TALENT]: 0,
      },
      last_agent_used: AgentType.ANALYTICS,
    },
    conversation_tags: ["budget", "optimization", "cost-reduction"],
    user_rating: 3,
    is_pinned: false,
    is_archived: false,
  }
];

const DemoStats = () => {
  const totalConversations = mockConversations.length;
  const totalMessages = mockConversations.reduce((sum, conv) => sum + conv.message_count, 0);
  const totalHandoffs = mockConversations.reduce((sum, conv) => sum + conv.agent_handoffs.length, 0);
  const avgRating = mockConversations.reduce((sum, conv) => sum + (conv.user_rating || 0), 0) / totalConversations;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card className="bg-card/50 border-border/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <MessageSquare className="w-4 h-4 text-blue-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Conversations</p>
              <p className="text-lg font-semibold">{totalConversations}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card/50 border-border/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/10 rounded-lg">
              <Users className="w-4 h-4 text-green-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Messages</p>
              <p className="text-lg font-semibold">{totalMessages}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card/50 border-border/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <ArrowRightLeft className="w-4 h-4 text-purple-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Agent Handoffs</p>
              <p className="text-lg font-semibold">{totalHandoffs}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card/50 border-border/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-500/10 rounded-lg">
              <TrendingUp className="w-4 h-4 text-yellow-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Avg Rating</p>
              <p className="text-lg font-semibold">{avgRating.toFixed(1)}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const FeatureHighlights = () => {
  const features = [
    {
      icon: History,
      title: "Agent-Aware History",
      description: "Track which agents participated in each conversation with detailed metadata"
    },
    {
      icon: ArrowRightLeft,
      title: "Agent Handoffs",
      description: "Visualize when conversations switched between different AI agents"
    },
    {
      icon: Users,
      title: "Participation Analytics",
      description: "See agent usage statistics, confidence levels, and performance metrics"
    },
    {
      icon: MessageSquare,
      title: "Rich Conversation Cards",
      description: "View conversation details with tags, ratings, and agent participation"
    },
    {
      icon: Clock,
      title: "Timeline View",
      description: "Explore conversation flow with chronological timeline of events"
    },
    {
      icon: TrendingUp,
      title: "Smart Filtering",
      description: "Filter by agents, context, handoffs, ratings, and date ranges"
    }
  ];

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Key Features
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map(({ icon: Icon, title, description }) => (
            <div key={title} className="flex gap-3 p-3 rounded-lg bg-muted/30">
              <div className="p-2 bg-primary/10 rounded-lg flex-shrink-0">
                <Icon className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h4 className="font-medium text-sm mb-1">{title}</h4>
                <p className="text-xs text-muted-foreground">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export const ConversationHistoryDemo: React.FC = () => {
  const [selectedConversation, setSelectedConversation] = React.useState<ConversationThread | null>(null);

  const handleSelectConversation = (conversation: ConversationThread) => {
    setSelectedConversation(conversation);
    console.log('Selected conversation:', conversation);
  };

  const handleNewConversation = () => {
    console.log('Start new conversation');
  };

  return (
    <div className="w-full h-screen bg-background">
      <div className="p-6 border-b">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold">Conversation History System</h1>
              <p className="text-muted-foreground">
                AI agent-aware conversation management with context preservation
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary">Demo Mode</Badge>
              <Badge variant="outline">
                {mockConversations.length} Sample Conversations
              </Badge>
            </div>
          </div>

          <DemoStats />
          <FeatureHighlights />
        </div>
      </div>

      <div className="flex-1">
        <ConversationHistoryMain
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          className="h-[calc(100vh-400px)]"
        />
      </div>

      {selectedConversation && (
        <div className="fixed bottom-4 right-4 max-w-sm">
          <Card className="bg-card/95 backdrop-blur-sm border shadow-lg">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Selected Conversation</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setSelectedConversation(null)}
                >
                  ×
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2 text-xs">
              <div><strong>Title:</strong> {selectedConversation.title}</div>
              <div><strong>Context:</strong> {selectedConversation.context}</div>
              <div><strong>Messages:</strong> {selectedConversation.message_count}</div>
              <div><strong>Agents:</strong> {selectedConversation.participating_agents.join(', ')}</div>
              <div><strong>Handoffs:</strong> {selectedConversation.agent_handoffs.length}</div>
              {selectedConversation.user_rating && (
                <div><strong>Rating:</strong> {selectedConversation.user_rating}/5 ⭐</div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};