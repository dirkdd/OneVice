import { useCallback } from 'react';
import { ConversationThread, MessageWithAgent } from '@/types/conversation-history';
import { conversationsApi } from '@/lib/api/conversations';

export interface ExportOptions {
  format: 'json' | 'markdown' | 'csv';
  includeMetadata: boolean;
  includeAgentInfo: boolean;
  includeHandoffs: boolean;
  dateRange?: {
    start: Date;
    end: Date;
  };
}

export function useConversationExport() {
  const exportConversation = useCallback(async (
    conversation: ConversationThread,
    options: ExportOptions = {
      format: 'json',
      includeMetadata: true,
      includeAgentInfo: true,
      includeHandoffs: true,
    }
  ) => {
    try {
      // Get full conversation messages
      const messagesResponse = await conversationsApi.getConversationMessages(conversation.id);
      const messages = messagesResponse.data?.items || [];
      
      let exportData: any = {};
      let filename = `conversation-${conversation.id}`;
      let mimeType = 'application/json';
      
      switch (options.format) {
        case 'json':
          exportData = formatAsJSON(conversation, messages, options);
          filename += '.json';
          mimeType = 'application/json';
          break;
          
        case 'markdown':
          exportData = formatAsMarkdown(conversation, messages, options);
          filename += '.md';
          mimeType = 'text/markdown';
          break;
          
        case 'csv':
          exportData = formatAsCSV(conversation, messages, options);
          filename += '.csv';
          mimeType = 'text/csv';
          break;
      }
      
      // Create and download file
      const blob = new Blob([exportData], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      return { success: true, filename };
    } catch (error: any) {
      console.error('Export failed:', error);
      return { success: false, error: error.message };
    }
  }, []);

  const exportMultipleConversations = useCallback(async (
    conversations: ConversationThread[],
    options: ExportOptions
  ) => {
    try {
      const exportData = [];
      
      for (const conversation of conversations) {
        const messagesResponse = await conversationsApi.getConversationMessages(conversation.id);
        const messages = messagesResponse.data?.items || [];
        
        exportData.push({
          conversation,
          messages: messages.map(msg => ({
            ...msg,
            exported_at: new Date().toISOString(),
          })),
          export_metadata: {
            exported_at: new Date().toISOString(),
            include_metadata: options.includeMetadata,
            include_agent_info: options.includeAgentInfo,
            include_handoffs: options.includeHandoffs,
          }
        });
      }
      
      const filename = `conversations-export-${new Date().toISOString().split('T')[0]}.json`;
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      return { success: true, filename, count: conversations.length };
    } catch (error: any) {
      console.error('Bulk export failed:', error);
      return { success: false, error: error.message };
    }
  }, []);

  return {
    exportConversation,
    exportMultipleConversations,
  };
}

function formatAsJSON(
  conversation: ConversationThread,
  messages: MessageWithAgent[],
  options: ExportOptions
) {
  const exportData: any = {
    conversation: {
      id: conversation.id,
      title: conversation.title,
      subtitle: conversation.subtitle,
      context: conversation.context,
      created_at: conversation.created_at,
      updated_at: conversation.updated_at,
      message_count: conversation.message_count,
      user_rating: conversation.user_rating,
      conversation_tags: conversation.conversation_tags,
    },
    messages: messages.map(msg => {
      const messageData: any = {
        id: msg.id,
        role: msg.role,
        content: msg.content,
        created_at: msg.created_at,
      };
      
      if (options.includeAgentInfo && msg.agent) {
        messageData.agent = msg.agent;
        messageData.agent_metadata = msg.agent_metadata;
      }
      
      if (options.includeMetadata && msg.metadata) {
        messageData.metadata = msg.metadata;
      }
      
      return messageData;
    }),
    export_metadata: {
      exported_at: new Date().toISOString(),
      format: 'json',
      options,
    },
  };
  
  if (options.includeAgentInfo) {
    exportData.conversation.participating_agents = conversation.participating_agents;
    exportData.conversation.primary_agent = conversation.primary_agent;
    exportData.conversation.agent_usage_stats = conversation.agent_usage_stats;
  }
  
  if (options.includeHandoffs) {
    exportData.conversation.agent_handoffs = conversation.agent_handoffs;
  }
  
  return JSON.stringify(exportData, null, 2);
}

function formatAsMarkdown(
  conversation: ConversationThread,
  messages: MessageWithAgent[],
  options: ExportOptions
) {
  let markdown = `# ${conversation.title}\n\n`;
  
  if (conversation.subtitle) {
    markdown += `*${conversation.subtitle}*\n\n`;
  }
  
  markdown += `**Context:** ${conversation.context}\n`;
  markdown += `**Created:** ${new Date(conversation.created_at).toLocaleString()}\n`;
  markdown += `**Messages:** ${conversation.message_count}\n`;
  
  if (conversation.user_rating) {
    markdown += `**Rating:** ${'⭐'.repeat(conversation.user_rating)}\n`;
  }
  
  if (conversation.conversation_tags.length > 0) {
    markdown += `**Tags:** ${conversation.conversation_tags.map(tag => `\`${tag}\``).join(', ')}\n`;
  }
  
  if (options.includeAgentInfo && conversation.participating_agents.length > 0) {
    markdown += `**Participating Agents:** ${conversation.participating_agents.join(', ')}\n`;
    if (conversation.primary_agent) {
      markdown += `**Primary Agent:** ${conversation.primary_agent}\n`;
    }
  }
  
  if (options.includeHandoffs && conversation.agent_handoffs.length > 0) {
    markdown += `**Agent Handoffs:** ${conversation.agent_handoffs.length}\n`;
  }
  
  markdown += '\n---\n\n';
  
  // Messages
  messages.forEach((message, index) => {
    const timestamp = new Date(message.created_at).toLocaleString();
    const role = message.role === 'user' ? 'User' : 
                 message.role === 'assistant' && message.agent ? 
                 `${message.agent.charAt(0).toUpperCase() + message.agent.slice(1)} Agent` : 
                 'Assistant';
    
    markdown += `## Message ${index + 1} - ${role}\n`;
    markdown += `*${timestamp}*\n\n`;
    markdown += `${message.content}\n\n`;
    
    if (options.includeAgentInfo && message.agent_metadata) {
      if (message.agent_metadata.confidence) {
        markdown += `**Confidence:** ${message.agent_metadata.confidence}\n`;
      }
      if (message.agent_metadata.processing_time) {
        markdown += `**Processing Time:** ${message.agent_metadata.processing_time}\n`;
      }
      if (message.agent_metadata.sources?.length) {
        markdown += `**Sources:** ${message.agent_metadata.sources.join(', ')}\n`;
      }
      markdown += '\n';
    }
    
    markdown += '---\n\n';
  });
  
  markdown += `\n*Exported on ${new Date().toLocaleString()}*\n`;
  
  return markdown;
}

function formatAsCSV(
  conversation: ConversationThread,
  messages: MessageWithAgent[],
  options: ExportOptions
) {
  const headers = [
    'Message ID',
    'Timestamp',
    'Role',
    'Content',
    'Agent',
    'Confidence',
    'Processing Time',
    'Handoff'
  ];
  
  let csv = headers.join(',') + '\n';
  
  messages.forEach(message => {
    const row = [
      message.id,
      message.created_at,
      message.role,
      `"${message.content.replace(/"/g, '""')}"`,
      message.agent || '',
      message.agent_metadata?.confidence || '',
      message.agent_metadata?.processing_time || '',
      message.is_handoff ? 'Yes' : 'No'
    ];
    
    csv += row.join(',') + '\n';
  });
  
  return csv;
}