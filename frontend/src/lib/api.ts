import { useAuth } from '@clerk/clerk-react';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// API Client Class
class ApiClient {
  private baseUrl: string;
  private getToken?: () => Promise<string | null>;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  // Set auth token getter (to be called after Clerk is initialized)
  setAuthTokenGetter(getToken: () => Promise<string | null>) {
    this.getToken = getToken;
  }

  // Generic request method
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Get auth token if available
    const token = this.getToken ? await this.getToken() : null;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return response.json();
      }
      
      return response.text() as T;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // HTTP Methods
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // WebSocket connection
  connectWebSocket(
    endpoint: string,
    token?: string
  ): WebSocket {
    const wsUrl = `${WS_BASE_URL}${endpoint}`;
    const ws = new WebSocket(wsUrl);
    
    // Send auth token after connection opens
    ws.addEventListener('open', () => {
      if (token) {
        ws.send(JSON.stringify({ type: 'auth', token }));
      }
    });

    return ws;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get('/health');
  }
}

// Create singleton instance
const apiClient = new ApiClient(API_BASE_URL);

// Hook to use API client with Clerk auth
export function useApiClient() {
  const { getToken } = useAuth();
  
  // Set token getter on first use
  if (!apiClient['getToken']) {
    apiClient.setAuthTokenGetter(() => getToken());
  }
  
  return apiClient;
}

// Export for use outside of React components
export { apiClient };

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// User and Auth Types
export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: 'Leadership' | 'Director' | 'Creative Director' | 'Salesperson';
  permissions: string[];
  createdAt: string;
  updatedAt: string;
}

// Dashboard Types
export interface DashboardStats {
  totalUsers: number;
  activeProjects: number;
  totalQueries: number;
  systemHealth: 'healthy' | 'warning' | 'error';
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
}