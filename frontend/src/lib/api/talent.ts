import { apiClient, ApiResponse } from './client';
import { 
  Person, 
  Skill,
  SkillCategory,
  PaginatedResponse,
  PaginationParams,
  SearchParams
} from './types';

export class TalentApi {
  async getPeople(
    params: PaginationParams & SearchParams = {}
  ): Promise<ApiResponse<PaginatedResponse<Person>>> {
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

      const url = `/api/talent/people${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return await apiClient.get<PaginatedResponse<Person>>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch people');
    }
  }

  async getPerson(personId: string): Promise<ApiResponse<Person>> {
    try {
      return await apiClient.get<Person>(`/api/talent/people/${personId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch person');
    }
  }

  async searchPeople(
    query: string,
    filters?: {
      skills?: string[];
      availability?: 'available' | 'booked' | 'limited';
      location?: string;
      experience_years_min?: number;
      experience_years_max?: number;
      performance_rating_min?: number;
    }
  ): Promise<ApiResponse<Person[]>> {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('q', query);
      
      if (filters) {
        if (filters.skills?.length) {
          filters.skills.forEach(skill => queryParams.append('skills', skill));
        }
        if (filters.availability) queryParams.append('availability', filters.availability);
        if (filters.location) queryParams.append('location', filters.location);
        if (filters.experience_years_min) queryParams.append('experience_years_min', filters.experience_years_min.toString());
        if (filters.experience_years_max) queryParams.append('experience_years_max', filters.experience_years_max.toString());
        if (filters.performance_rating_min) queryParams.append('performance_rating_min', filters.performance_rating_min.toString());
      }

      const url = `/api/talent/people/search?${queryParams.toString()}`;
      return await apiClient.get<Person[]>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to search people');
    }
  }

  async getPersonsBySkill(skillName: string): Promise<ApiResponse<Person[]>> {
    try {
      return await apiClient.get<Person[]>(`/api/talent/people/by-skill/${encodeURIComponent(skillName)}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch people by skill');
    }
  }

  async getAvailablePeople(
    startDate?: string,
    endDate?: string,
    skillCategories?: SkillCategory[]
  ): Promise<ApiResponse<Person[]>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (startDate) queryParams.append('start_date', startDate);
      if (endDate) queryParams.append('end_date', endDate);
      if (skillCategories?.length) {
        skillCategories.forEach(category => queryParams.append('skill_categories', category));
      }

      const url = `/api/talent/people/available${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return await apiClient.get<Person[]>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch available people');
    }
  }

  async getSkills(): Promise<ApiResponse<Skill[]>> {
    try {
      return await apiClient.get<Skill[]>('/api/talent/skills');
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch skills');
    }
  }

  async getSkillsByCategory(category: SkillCategory): Promise<ApiResponse<Skill[]>> {
    try {
      return await apiClient.get<Skill[]>(`/api/talent/skills/by-category/${category}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch skills by category');
    }
  }

  async getSkillCategories(): Promise<ApiResponse<SkillCategory[]>> {
    try {
      return await apiClient.get<SkillCategory[]>('/api/talent/skills/categories');
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch skill categories');
    }
  }

  async createPerson(data: Omit<Person, 'id' | 'created_at'>): Promise<ApiResponse<Person>> {
    try {
      return await apiClient.post<Person>('/api/talent/people', data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create person');
    }
  }

  async updatePerson(
    personId: string,
    data: Partial<Omit<Person, 'id' | 'created_at'>>
  ): Promise<ApiResponse<Person>> {
    try {
      return await apiClient.patch<Person>(`/api/talent/people/${personId}`, data);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update person');
    }
  }

  async deletePerson(personId: string): Promise<ApiResponse<{ message: string }>> {
    try {
      return await apiClient.delete<{ message: string }>(`/api/talent/people/${personId}`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete person');
    }
  }

  async getPersonProjects(personId: string): Promise<ApiResponse<any[]>> {
    try {
      return await apiClient.get<any[]>(`/api/talent/people/${personId}/projects`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch person projects');
    }
  }

  async getPersonCollaborators(personId: string): Promise<ApiResponse<Person[]>> {
    try {
      return await apiClient.get<Person[]>(`/api/talent/people/${personId}/collaborators`);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch person collaborators');
    }
  }

  async getRecommendedTalent(
    projectRequirements: {
      skills_needed: string[];
      project_type: string;
      budget_range?: { min: number; max: number };
      timeline?: string;
      location?: string;
    }
  ): Promise<ApiResponse<Person[]>> {
    try {
      return await apiClient.post<Person[]>('/api/talent/recommendations', projectRequirements);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get talent recommendations');
    }
  }

  async getTopPerformers(
    category?: SkillCategory,
    limit: number = 10
  ): Promise<ApiResponse<Person[]>> {
    try {
      const queryParams = new URLSearchParams();
      if (category) queryParams.append('category', category);
      queryParams.append('limit', limit.toString());

      const url = `/api/talent/people/top-performers?${queryParams.toString()}`;
      return await apiClient.get<Person[]>(url);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to fetch top performers');
    }
  }
}

// Export singleton instance
export const talentApi = new TalentApi();
export default talentApi;