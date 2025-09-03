import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

class ApiClient {
  private instance: AxiosInstance;
  private getClerkToken: (() => Promise<string | null>) | null = null;

  constructor() {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  // Method to set Clerk's getToken function
  setClerkAuth(getToken: () => Promise<string | null>) {
    this.getClerkToken = getToken;
  }

  private setupInterceptors() {
    // Request interceptor - add auth token from Clerk
    this.instance.interceptors.request.use(
      async (config) => {
        if (this.getClerkToken) {
          try {
            const token = await this.getClerkToken();
            if (token) {
              config.headers.Authorization = `Bearer ${token}`;
            }
          } catch (error) {
            console.warn('Failed to get Clerk token:', error);
          }
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors (Clerk handles token refresh automatically)
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error: AxiosError) => {
        // Transform error to ApiError format
        const apiError: ApiError = {
          message: error.response?.data?.message || error.message || 'An error occurred',
          status: error.response?.status,
          code: error.response?.data?.code,
        };

        // For 401 errors, let the calling component handle the redirect
        // Clerk will automatically handle token refresh
        return Promise.reject(apiError);
      }
    );
  }

  // Legacy methods kept for compatibility - now no-ops since Clerk handles tokens
  setToken(token: string) {
    // No-op: Clerk handles token management
  }

  getToken(): string | null {
    // No-op: Use Clerk's getToken instead
    return null;
  }

  clearToken() {
    // No-op: Clerk handles token cleanup
  }

  logout() {
    // No-op: Use Clerk's signOut instead
  }

  // HTTP methods
  async get<T>(url: string, config?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.get(url, config);
    return {
      data: response.data,
      status: response.status,
    };
  }

  async post<T>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.post(url, data, config);
    return {
      data: response.data,
      status: response.status,
    };
  }

  async put<T>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.put(url, data, config);
    return {
      data: response.data,
      status: response.status,
    };
  }

  async delete<T>(url: string, config?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.delete(url, config);
    return {
      data: response.data,
      status: response.status,
    };
  }

  async patch<T>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.patch(url, data, config);
    return {
      data: response.data,
      status: response.status,
    };
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;