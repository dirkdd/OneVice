import { apiClient, ApiResponse } from './client';
import { 
  Conversation, 
  Message,
  DashboardContext,
  PaginatedResponse,
  PaginationParams 
} from './types';

export class ConversationsApi {
  async getConversations(
    params: PaginationParams & { context?: DashboardContext } = {}
  ): Promise<ApiResponse<PaginatedResponse<Conversation>>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());
      if (params.sort_by) queryParams.append('sort_by', params.sort_by);
      if (params.sort_order) queryParams.append('sort_order', params.sort_order);
      if (params.context) queryParams.append('context', params.context);

      const url = `/api/conversations${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return await apiClient.get<PaginatedResponse<Conversation>>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch conversations');
    }
  }

  async getConversation(conversationId: string): Promise<ApiResponse<Conversation>> {
    try {
      return await apiClient.get<Conversation>(`/api/conversations/${conversationId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch conversation');
    }
  }

  async getConversationMessages(
    conversationId: string,
    params: PaginationParams = {}
  ): Promise<ApiResponse<PaginatedResponse<Message>>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());
      
      const url = `/api/conversations/${conversationId}/messages${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return await apiClient.get<PaginatedResponse<Message>>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch conversation messages');
    }
  }

  async createConversation(data: {
    title: string;
    context: DashboardContext;
    initial_message?: string;
  }): Promise<ApiResponse<Conversation>> {
    try {
      return await apiClient.post<Conversation>('/api/conversations', data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create conversation');
    }
  }

  async updateConversation(
    conversationId: string,
    data: { title?: string; context?: DashboardContext }
  ): Promise<ApiResponse<Conversation>> {
    try {
      return await apiClient.patch<Conversation>(`/api/conversations/${conversationId}`, data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update conversation');
    }
  }

  async deleteConversation(conversationId: string): Promise<ApiResponse<{ message: string }>> {
    try {
      return await apiClient.delete<{ message: string }>(`/api/conversations/${conversationId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete conversation');
    }
  }

  async addMessage(
    conversationId: string,
    content: string,
    metadata?: Record<string, any>
  ): Promise<ApiResponse<Message>> {
    try {
      return await apiClient.post<Message>(`/api/conversations/${conversationId}/messages`, {
        content,
        metadata,
      });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to add message');
    }
  }

  async getRecentConversations(limit: number = 5): Promise<ApiResponse<Conversation[]>> {
    try {
      return await apiClient.get<Conversation[]>(`/api/conversations/recent?limit=${limit}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch recent conversations');
    }
  }

  async searchConversations(query: string): Promise<ApiResponse<Conversation[]>> {
    try {
      return await apiClient.get<Conversation[]>(`/api/conversations/search?q=${encodeURIComponent(query)}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to search conversations');
    }
  }
}

// Export singleton instance
export const conversationsApi = new ConversationsApi();
export default conversationsApi;