import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { WebSocketMessage, WebSocketResponse, DashboardContext, BackendAIResponse, AgentType } from '@/lib/api/types';
import { getAgentRoutingMetadata } from '@/contexts/AgentPreferencesContext';
import { AgentPreferences } from '@/components/ui/agent-selector';

export interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  messages: WebSocketMessage[];
  lastMessage: WebSocketMessage | null;
}

export interface WebSocketActions {
  sendMessage: (content: string, context?: DashboardContext, metadata?: Record<string, any>) => void;
  clearMessages: () => void;
  clearError: () => void;
  reconnect: () => void;
}

export interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  agentPreferences?: AgentPreferences;
}

// Helper function to map agent types from backend
function mapAgentType(agentType?: string): AgentType | undefined {
  if (!agentType) return undefined;
  
  const typeMap: Record<string, AgentType> = {
    'sales': AgentType.SALES,
    'sales_agent': AgentType.SALES,
    'talent': AgentType.TALENT,
    'talent_agent': AgentType.TALENT,
    'analytics': AgentType.ANALYTICS,
    'analytics_agent': AgentType.ANALYTICS,
  };
  
  return typeMap[agentType.toLowerCase()];
}

export function useWebSocket(options: UseWebSocketOptions = {}): WebSocketState & WebSocketActions {
  const {
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 3000,
    agentPreferences,
  } = options;

  const { getToken } = useAuth();
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    messages: [],
    lastMessage: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const optionsRef = useRef(options);
  
  // Update options ref when options change
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  // Stable WebSocket URL
  const wsUrl = useMemo(() => {
    return import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const clearMessages = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      messages: [],
      lastMessage: null 
    }));
  }, []);

  const addMessage = useCallback((message: WebSocketMessage) => {
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
      lastMessage: message,
    }));
    
    // Call onMessage from current options
    if (optionsRef.current.onMessage) {
      optionsRef.current.onMessage(message);
    }
  }, []);

  const handleError = useCallback((error: string) => {
    setState(prev => ({ ...prev, error }));
    if (optionsRef.current.onError) {
      optionsRef.current.onError(error);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    setState(prev => ({ 
      ...prev, 
      isConnecting: true,
      error: null 
    }));

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = async () => {
        console.log('WebSocket connected');
        reconnectAttemptsRef.current = 0;
        
        // Send authentication message after connection with proper async handling
        try {
          const token = await getToken();
          if (token) {
            ws.send(JSON.stringify({
              type: 'auth',
              token: token
            }));
            console.log('WebSocket authentication message sent');
          } else {
            console.warn('No authentication token available for WebSocket');
          }
        } catch (error) {
          console.error('Failed to get authentication token for WebSocket:', error);
        }
        
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
        }));
        
        if (optionsRef.current.onConnect) {
          optionsRef.current.onConnect();
        }
      };

      ws.onmessage = (event) => {
        try {
          const response: WebSocketResponse = JSON.parse(event.data);
          
          // Handle different message types
          if (response.type === 'connection') {
            console.log('WebSocket connection established');
            return;
          }
          
          if (response.type === 'auth_success') {
            console.log('WebSocket authenticated successfully');
            return;
          }
          
          if (response.type === 'auth_error') {
            console.error('WebSocket authentication failed:', response.data);
            handleError('Authentication failed');
            return;
          }
          
          // Handle AI response from backend
          if ((response.type === 'chat_response' || response.type === 'ai_response') && response.data) {
            try {
              const backendResponse = response.data as BackendAIResponse;
              
              // Extract the AI message content properly
              const message: WebSocketMessage = {
                type: 'ai_response',
                content: backendResponse.ai_message?.content || 'No content available',
                conversation_id: response.conversation_id || backendResponse.conversation_id,
                agent: mapAgentType(backendResponse.ai_message?.agent_info?.primary_agent),
                agent_metadata: backendResponse.ai_message?.agent_info && mapAgentType(backendResponse.ai_message.agent_info.primary_agent) ? {
                  agent_type: mapAgentType(backendResponse.ai_message.agent_info.primary_agent)!,
                  processing_time: undefined,
                  confidence: 'medium' as const,
                } : undefined,
                metadata: {
                  ...backendResponse,
                  sender_name: backendResponse.ai_message?.sender_name || 'OneVice AI',
                },
                timestamp: response.timestamp || new Date().toISOString(),
              };

              addMessage(message);
              return;
            } catch (parseError) {
              console.error('Error parsing backend AI response:', parseError);
              // Fallback to original parsing
            }
          }
          
          // Convert response to message format for regular messages (fallback)
          const message: WebSocketMessage = {
            type: response.type as any,
            content: typeof response.data === 'string' ? response.data : 
                    response.data?.message || JSON.stringify(response.data),
            conversation_id: response.conversation_id,
            metadata: response.data && typeof response.data === 'object' ? response.data : {},
            timestamp: response.timestamp || new Date().toISOString(),
          };

          addMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          handleError('Failed to parse server message');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        handleError('Connection error occurred');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }));

        if (optionsRef.current.onDisconnect) {
          optionsRef.current.onDisconnect();
        }

        // Auto-reconnect logic
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts && event.code !== 1000) {
          reconnectAttemptsRef.current += 1;
          const delay = reconnectInterval * Math.pow(1.5, reconnectAttemptsRef.current - 1);
          
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          handleError('Max reconnection attempts reached');
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setState(prev => ({ 
        ...prev, 
        isConnecting: false,
        error: 'Failed to create connection' 
      }));
    }
  }, [wsUrl, getToken, addMessage, handleError, autoReconnect, maxReconnectAttempts, reconnectInterval]);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    connect();
  }, [disconnect, connect]);

  const sendMessage = useCallback((
    content: string, 
    context?: DashboardContext,
    metadata?: Record<string, any>
  ) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      handleError('WebSocket is not connected');
      return;
    }

    try {
      // Include agent preferences in message metadata
      const agentRoutingData = agentPreferences 
        ? getAgentRoutingMetadata(agentPreferences, context)
        : {};

      const message = {
        type: 'user_message',
        content,
        context,
        metadata: {
          ...metadata,
          timestamp: new Date().toISOString(),
          agent_preferences: agentRoutingData,
        },
      };

      wsRef.current.send(JSON.stringify(message));
      
      // Add user message to local state
      const userMessage: WebSocketMessage = {
        type: 'user_message',
        content,
        context,
        metadata: message.metadata,
        timestamp: new Date().toISOString(),
      };
      
      addMessage(userMessage);
    } catch (error) {
      console.error('Error sending message:', error);
      handleError('Failed to send message');
    }
  }, [addMessage, handleError, agentPreferences]);

  // Connect when component mounts - no authentication dependency
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);


  return {
    ...state,
    sendMessage,
    clearMessages,
    clearError,
    reconnect,
  };
}