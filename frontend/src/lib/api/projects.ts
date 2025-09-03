import { apiClient, ApiResponse } from './client';
import { 
  Project, 
  ProjectType,
  ProjectStatus,
  PaginatedResponse,
  PaginationParams,
  SearchParams,
  AnalyticsMetrics,
  TopPerformer
} from './types';

export class ProjectsApi {
  async getProjects(
    params: PaginationParams & SearchParams = {}
  ): Promise<ApiResponse<PaginatedResponse<Project>>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());
      if (params.sort_by) queryParams.append('sort_by', params.sort_by);
      if (params.sort_order) queryParams.append('sort_order', params.sort_order);
      if (params.query) queryParams.append('q', params.query);
      
      if (params.filters) {
        Object.entries(params.filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            queryParams.append(key, value.toString());
          }
        });
      }

      const url = `/api/projects${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return await apiClient.get<PaginatedResponse<Project>>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch projects');
    }
  }

  async getProject(projectId: string): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.get<Project>(`/api/projects/${projectId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch project');
    }
  }

  async createProject(data: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.post<Project>('/api/projects', data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create project');
    }
  }

  async updateProject(
    projectId: string,
    data: Partial<Omit<Project, 'id' | 'created_at' | 'updated_at'>>
  ): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.patch<Project>(`/api/projects/${projectId}`, data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update project');
    }
  }

  async deleteProject(projectId: string): Promise<ApiResponse<{ message: string }>> {
    try {
      return await apiClient.delete<{ message: string }>(`/api/projects/${projectId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete project');
    }
  }

  async getProjectsByType(type: ProjectType): Promise<ApiResponse<Project[]>> {
    try {
      return await apiClient.get<Project[]>(`/api/projects/by-type/${type}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch projects by type');
    }
  }

  async getProjectsByStatus(status: ProjectStatus): Promise<ApiResponse<Project[]>> {
    try {
      return await apiClient.get<Project[]>(`/api/projects/by-status/${status}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch projects by status');
    }
  }

  async getProjectTemplates(): Promise<ApiResponse<Project[]>> {
    try {
      return await apiClient.get<Project[]>('/api/projects/templates');
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch project templates');
    }
  }

  async generateBudgetEstimate(projectData: {
    type: ProjectType;
    episodes?: number;
    duration_per_episode?: number;
    complexity?: 'low' | 'medium' | 'high';
    location?: string;
  }): Promise<ApiResponse<{
    total_budget: number;
    breakdown: {
      pre_production: number;
      production: number;
      post_production: number;
      contingency: number;
    };
    timeline: {
      pre_production_weeks: number;
      production_weeks: number;
      post_production_weeks: number;
      total_weeks: number;
    };
  }>> {
    try {
      return await apiClient.post('/api/projects/estimate-budget', projectData);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to generate budget estimate');
    }
  }

  async getAnalyticsMetrics(period?: string): Promise<ApiResponse<AnalyticsMetrics>> {
    try {
      const url = `/api/projects/analytics${period ? `?period=${period}` : ''}`;
      return await apiClient.get<AnalyticsMetrics>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch analytics metrics');
    }
  }

  async getTopPerformers(limit: number = 10): Promise<ApiResponse<TopPerformer[]>> {
    try {
      return await apiClient.get<TopPerformer[]>(`/api/projects/top-performers?limit=${limit}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch top performers');
    }
  }

  async searchProjects(query: string): Promise<ApiResponse<Project[]>> {
    try {
      return await apiClient.get<Project[]>(`/api/projects/search?q=${encodeURIComponent(query)}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to search projects');
    }
  }

  async exportProject(projectId: string, format: 'pdf' | 'json' | 'csv'): Promise<ApiResponse<{ download_url: string }>> {
    try {
      return await apiClient.post<{ download_url: string }>(`/api/projects/${projectId}/export`, { format });
    } catch (error: any) {
      throw new Error(error.message || 'Failed to export project');
    }
  }
}

// Export singleton instance
export const projectsApi = new ProjectsApi();
export default projectsApi;