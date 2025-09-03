import { apiClient, ApiResponse } from './client';
import { 
  Client, 
  ClientType,
  CaseStudy,
  CaseStudyMetrics,
  PaginatedResponse,
  PaginationParams,
  SearchParams
} from './types';

export class IntelligenceApi {
  async getClients(
    params: PaginationParams & SearchParams = {}
  ): Promise<ApiResponse<PaginatedResponse<Client>>> {
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

      const url = `/api/intelligence/clients${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return await apiClient.get<PaginatedResponse<Client>>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch clients');
    }
  }

  async getClient(clientId: string): Promise<ApiResponse<Client>> {
    try {
      return await apiClient.get<Client>(`/api/intelligence/clients/${clientId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch client');
    }
  }

  async searchClients(query: string): Promise<ApiResponse<Client[]>> {
    try {
      return await apiClient.get<Client[]>(`/api/intelligence/clients/search?q=${encodeURIComponent(query)}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to search clients');
    }
  }

  async getClientsByType(type: ClientType): Promise<ApiResponse<Client[]>> {
    try {
      return await apiClient.get<Client[]>(`/api/intelligence/clients/by-type/${type}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch clients by type');
    }
  }

  async getClientIntelligence(clientId: string): Promise<ApiResponse<{
    client: Client;
    relationship_history: any[];
    recent_interactions: any[];
    project_history: any[];
    market_insights: any[];
    recommendations: string[];
  }>> {
    try {
      return await apiClient.get(`/api/intelligence/clients/${clientId}/intelligence`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch client intelligence');
    }
  }

  async generatePreCallBrief(clientId: string, meetingContext?: string): Promise<ApiResponse<{
    client_summary: string;
    key_talking_points: string[];
    recent_developments: string[];
    strategic_opportunities: string[];
    potential_challenges: string[];
    recommended_approach: string[];
  }>> {
    try {
      const data = meetingContext ? { meeting_context: meetingContext } : {};
      return await apiClient.post(`/api/intelligence/clients/${clientId}/pre-call-brief`, data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to generate pre-call brief');
    }
  }

  async getCaseStudies(
    params: PaginationParams & { 
      featured_only?: boolean;
      tags?: string[];
      project_type?: string;
    } = {}
  ): Promise<ApiResponse<PaginatedResponse<CaseStudy>>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());
      if (params.sort_by) queryParams.append('sort_by', params.sort_by);
      if (params.sort_order) queryParams.append('sort_order', params.sort_order);
      if (params.featured_only) queryParams.append('featured_only', 'true');
      if (params.project_type) queryParams.append('project_type', params.project_type);
      
      if (params.tags?.length) {
        params.tags.forEach(tag => queryParams.append('tags', tag));
      }

      const url = `/api/intelligence/case-studies${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return await apiClient.get<PaginatedResponse<CaseStudy>>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch case studies');
    }
  }

  async getCaseStudy(caseStudyId: string): Promise<ApiResponse<CaseStudy>> {
    try {
      return await apiClient.get<CaseStudy>(`/api/intelligence/case-studies/${caseStudyId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch case study');
    }
  }

  async searchCaseStudies(query: string): Promise<ApiResponse<CaseStudy[]>> {
    try {
      return await apiClient.get<CaseStudy[]>(`/api/intelligence/case-studies/search?q=${encodeURIComponent(query)}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to search case studies');
    }
  }

  async createCaseStudy(data: Omit<CaseStudy, 'id' | 'created_at'>): Promise<ApiResponse<CaseStudy>> {
    try {
      return await apiClient.post<CaseStudy>('/api/intelligence/case-studies', data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create case study');
    }
  }

  async updateCaseStudy(
    caseStudyId: string,
    data: Partial<Omit<CaseStudy, 'id' | 'created_at'>>
  ): Promise<ApiResponse<CaseStudy>> {
    try {
      return await apiClient.patch<CaseStudy>(`/api/intelligence/case-studies/${caseStudyId}`, data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update case study');
    }
  }

  async deleteCaseStudy(caseStudyId: string): Promise<ApiResponse<{ message: string }>> {
    try {
      return await apiClient.delete<{ message: string }>(`/api/intelligence/case-studies/${caseStudyId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete case study');
    }
  }

  async getFeaturedCaseStudies(limit: number = 6): Promise<ApiResponse<CaseStudy[]>> {
    try {
      return await apiClient.get<CaseStudy[]>(`/api/intelligence/case-studies/featured?limit=${limit}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch featured case studies');
    }
  }

  async getPortfolioMetrics(): Promise<ApiResponse<{
    total_case_studies: number;
    success_rate: number;
    average_roi: number;
    client_satisfaction: number;
    featured_projects: number;
    industries_served: string[];
    top_performing_categories: string[];
  }>> {
    try {
      return await apiClient.get('/api/intelligence/portfolio/metrics');
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch portfolio metrics');
    }
  }

  async getMarketInsights(industry?: string): Promise<ApiResponse<{
    industry_trends: string[];
    competitive_landscape: any[];
    opportunity_analysis: string[];
    risk_factors: string[];
    market_size: any;
    growth_projections: any;
  }>> {
    try {
      const url = `/api/intelligence/market-insights${industry ? `?industry=${encodeURIComponent(industry)}` : ''}`;
      return await apiClient.get(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch market insights');
    }
  }

  async generateIntelligenceReport(data: {
    type: 'client' | 'market' | 'competitive' | 'portfolio';
    target_id?: string;
    parameters?: Record<string, any>;
  }): Promise<ApiResponse<{
    report_id: string;
    status: 'generating' | 'completed' | 'failed';
    download_url?: string;
    summary: string;
  }>> {
    try {
      return await apiClient.post('/api/intelligence/reports/generate', data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to generate intelligence report');
    }
  }

  async getIntelligenceReport(reportId: string): Promise<ApiResponse<{
    report_id: string;
    status: 'generating' | 'completed' | 'failed';
    download_url?: string;
    content?: any;
    generated_at: string;
  }>> {
    try {
      return await apiClient.get(`/api/intelligence/reports/${reportId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch intelligence report');
    }
  }
}

// Export singleton instance
export const intelligenceApi = new IntelligenceApi();
export default intelligenceApi;