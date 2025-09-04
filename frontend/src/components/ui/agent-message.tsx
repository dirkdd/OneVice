import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { AgentType, AgentMetadata, WebSocketMessage } from "@/lib/api/types";
import { MessageWithAgent, AgentHandoff } from "@/types/conversation-history";
import { AgentBadge, getAgentColorScheme } from "./agent-badge";
import { AgentHandoffIndicator } from "./agent-handoff-indicator";
import { MessageJSONModal } from "./message-json-modal";
import { Card } from "./card";
import { Button } from "./button";
import { Clock, ExternalLink, Lightbulb, Code2 } from "lucide-react";

interface AgentMessageProps {
  message: WebSocketMessage | MessageWithAgent;
  showHandoff?: boolean;
  className?: string;
}

interface MessageContentProps {
  content: string;
  metadata?: AgentMetadata;
  className?: string;
}

const MessageContent: React.FC<MessageContentProps> = ({ 
  content, 
  metadata, 
  className 
}) => {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="prose prose-invert prose-sm max-w-none">
        <div className="whitespace-pre-line break-words leading-relaxed text-gray-200">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Custom styling for code blocks
              code: ({ node, inline, className, children, ...props }: any) => {
                const match = /language-(\w+)/.exec(className || '');
                const language = match ? match[1] : '';
                
                return (
                  <code
                    className={cn(
                      inline 
                        ? "bg-gray-800/60 text-gray-200 px-1.5 py-0.5 rounded text-sm font-mono"
                        : "block bg-gray-900/60 text-gray-200 p-3 rounded-lg overflow-x-auto text-sm font-mono whitespace-pre",
                      className
                    )}
                    {...props}
                  >
                    {language && !inline && (
                      <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider">
                        {language}
                      </div>
                    )}
                    {children}
                  </code>
                );
              },
            // Custom styling for blockquotes
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-gray-600 pl-4 italic text-gray-300 my-2">
                {children}
              </blockquote>
            ),
            // Custom styling for links
            a: ({ children, href }) => (
              <a 
                href={href} 
                className="text-blue-400 hover:text-blue-300 underline transition-colors"
                target="_blank"
                rel="noopener noreferrer"
              >
                {children}
              </a>
            ),
            // Custom styling for lists
            ul: ({ children }) => (
              <ul className="list-disc list-inside space-y-0.5 text-gray-200 mb-3">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-inside space-y-0.5 text-gray-200 mb-3">
                {children}
              </ol>
            ),
            // Custom styling for paragraphs
            p: ({ children }) => (
              <p className="mb-2 text-gray-200">
                {children}
              </p>
            ),
            // Custom styling for headers
            h1: ({ children }) => (
              <h1 className="text-xl font-bold text-white mb-2 mt-4">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-lg font-bold text-white mb-2 mt-3">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-md font-semibold text-white mb-1 mt-2">
                {children}
              </h3>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
        </div>
      </div>
      
      {metadata?.sources && metadata.sources.length > 0 && (
        <div className="border-t border-gray-700/50 pt-3 mt-3">
          <div className="flex items-center gap-2 mb-2">
            <ExternalLink className="w-3 h-3 text-gray-400" />
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
              Sources
            </span>
          </div>
          <div className="flex flex-wrap gap-1">
            {metadata.sources.map((source, index) => (
              <div
                key={index}
                className="px-2 py-1 bg-gray-800/50 text-xs text-gray-300 rounded border border-gray-700/50"
              >
                {source}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {metadata?.query_complexity && (
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Lightbulb className="w-3 h-3" />
          <span>Query complexity: {metadata.query_complexity}</span>
        </div>
      )}
    </div>
  );
};

export const AgentMessage: React.FC<AgentMessageProps> = ({ 
  message, 
  showHandoff = true,
  className 
}) => {
  const [showJSONModal, setShowJSONModal] = useState(false);
  
  const wsMessage = message as WebSocketMessage;
  const messageWithAgent = message as MessageWithAgent;
  
  const isUser = wsMessage.type === 'user_message';
  const isAgent = wsMessage.type === 'agent_response' && wsMessage.agent;
  const isAI = wsMessage.type === 'ai_response';
  const hasHandoff = showHandoff && messageWithAgent.is_handoff && messageWithAgent.handoff_data;
  
  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get agent color scheme for styling
  const colorScheme = isAgent && wsMessage.agent 
    ? getAgentColorScheme(wsMessage.agent)
    : null;

  if (isUser) {
    return (
      <>
        <div className={cn("flex justify-end mb-4", className)}>
          <div className="max-w-[70%] group">
            <Card className="bg-white/10 border-white/20 backdrop-blur-sm p-4">
              <MessageContent 
                content={wsMessage.content}
                className="text-white"
              />
              <div className="flex justify-between items-center mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="flex items-center gap-2 text-xs text-gray-300">
                  <Clock className="w-3 h-3" />
                  <span>{formatTime(wsMessage.timestamp)}</span>
                </div>
                
                {/* JSON Modal Trigger for User Messages */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowJSONModal(true)}
                  className="h-6 px-2 hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                  title="View message JSON"
                >
                  <Code2 className="w-3 h-3" />
                </Button>
              </div>
            </Card>
          </div>
        </div>
        
        {/* JSON Modal */}
        <MessageJSONModal
          message={message}
          open={showJSONModal}
          onOpenChange={setShowJSONModal}
        />
      </>
    );
  }

  return (
    <div className={cn("flex justify-start mb-4", className)}>
      <div className="max-w-[85%] group">
        <div className="space-y-2">
          {/* Agent Handoff Indicator */}
          {hasHandoff && messageWithAgent.handoff_data && (
            <div className="mb-3">
              <AgentHandoffIndicator 
                handoff={messageWithAgent.handoff_data}
                variant="detailed"
                size="default"
              />
            </div>
          )}

          {/* Agent Badge Header */}
          {isAgent && wsMessage.agent && (
            <div className="flex items-center gap-2">
              <AgentBadge 
                agent={wsMessage.agent}
                metadata={wsMessage.agent_metadata}
                showConfidence={true}
                showProcessingTime={true}
                size="default"
              />
            </div>
          )}
          
          {/* Message Card */}
          <Card 
            className={cn(
              "p-4 backdrop-blur-sm transition-all duration-300",
              isAgent && colorScheme ? [
                // Agent-specific styling
                colorScheme.bg,
                colorScheme.border,
                'border',
                `hover:${colorScheme.glow}`,
                'hover:shadow-lg'
              ] : [
                // Default AI response styling
                'bg-gray-800/70',
                'border-gray-700',
                'hover:bg-gray-800/90'
              ]
            )}
          >
            <MessageContent 
              content={wsMessage.content}
              metadata={wsMessage.agent_metadata}
              className="text-white"
            />
            
            {/* Message Footer */}
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-current/10 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="flex items-center gap-4 text-xs text-current/70">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{formatTime(wsMessage.timestamp)}</span>
                </div>
                
                {wsMessage.agent_metadata?.processing_time && (
                  <div className="flex items-center gap-1">
                    <span>Processed in {wsMessage.agent_metadata.processing_time}</span>
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                {/* JSON Modal Trigger */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowJSONModal(true)}
                  className="h-6 px-2 hover:bg-current/10 text-current/60 hover:text-current/90 transition-colors"
                  title="View message JSON"
                >
                  <Code2 className="w-3 h-3" />
                </Button>
                
                {isAgent && (
                  <div className="text-xs opacity-75">
                    AI Agent Response
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>
        
        {/* JSON Modal */}
        <MessageJSONModal
          message={message}
          open={showJSONModal}
          onOpenChange={setShowJSONModal}
        />
      </div>
    </div>
  );
};

// Specialized components for each agent type
export const SalesMessage: React.FC<Omit<AgentMessageProps, 'message'> & { content: string; timestamp?: string; metadata?: AgentMetadata }> = ({ 
  content, 
  timestamp = new Date().toISOString(), 
  metadata,
  ...props 
}) => {
  const message: WebSocketMessage = {
    type: 'agent_response',
    content,
    agent: AgentType.SALES,
    agent_metadata: metadata,
    timestamp,
  };
  
  return <AgentMessage message={message} {...props} />;
};

export const TalentMessage: React.FC<Omit<AgentMessageProps, 'message'> & { content: string; timestamp?: string; metadata?: AgentMetadata }> = ({ 
  content, 
  timestamp = new Date().toISOString(), 
  metadata,
  ...props 
}) => {
  const message: WebSocketMessage = {
    type: 'agent_response',
    content,
    agent: AgentType.TALENT,
    agent_metadata: metadata,
    timestamp,
  };
  
  return <AgentMessage message={message} {...props} />;
};

export const AnalyticsMessage: React.FC<Omit<AgentMessageProps, 'message'> & { content: string; timestamp?: string; metadata?: AgentMetadata }> = ({ 
  content, 
  timestamp = new Date().toISOString(), 
  metadata,
  ...props 
}) => {
  const message: WebSocketMessage = {
    type: 'agent_response',
    content,
    agent: AgentType.ANALYTICS,
    agent_metadata: metadata,
    timestamp,
  };
  
  return <AgentMessage message={message} {...props} />;
};