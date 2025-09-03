// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: UserRole;
  sensitivity_level: DataSensitivityLevel;
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

export interface UserRole {
  id: string;
  name: string;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  description: string;
}

export enum DataSensitivityLevel {
  PUBLIC = 1,
  INTERNAL = 2,
  CONFIDENTIAL = 3,
  RESTRICTED = 4,
  HIGHLY_CONFIDENTIAL = 5,
  TOP_SECRET = 6,
}

// Conversation Types
export interface Conversation {
  id: string;
  title: string;
  subtitle?: string;
  context: DashboardContext;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export type DashboardContext = 'home' | 'pre-call-brief' | 'case-study' | 'talent-discovery' | 'bid-proposal';

// Project Types
export interface Project {
  id: string;
  title: string;
  type: ProjectType;
  status: ProjectStatus;
  budget: number;
  currency: string;
  timeline: ProjectTimeline;
  team: TeamMember[];
  client?: Client;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectTimeline {
  pre_production: number; // weeks
  production: number; // weeks
  post_production: number; // weeks
  total: number; // weeks
}

export interface TeamMember {
  id: string;
  person_id: string;
  role: string;
  rate_per_episode?: number;
  availability_status: 'available' | 'booked' | 'limited';
  specialty?: string;
}

export enum ProjectType {
  DOCUMENTARY = 'documentary',
  DRAMA = 'drama',
  FILM = 'film',
  COMMERCIAL = 'commercial',
  SERIES = 'series',
}

export enum ProjectStatus {
  PLANNING = 'planning',
  PRE_PRODUCTION = 'pre-production',
  PRODUCTION = 'production',
  POST_PRODUCTION = 'post-production',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

// Client Types
export interface Client {
  id: string;
  name: string;
  type: ClientType;
  industry: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  relationship_strength: number; // 1-10
  projects_count: number;
  total_budget: number;
  last_interaction?: string;
  notes?: string;
  created_at: string;
}

export enum ClientType {
  STREAMING_PLATFORM = 'streaming_platform',
  BROADCASTER = 'broadcaster',
  PRODUCTION_COMPANY = 'production_company',
  STUDIO = 'studio',
  AGENCY = 'agency',
  DIRECT_CLIENT = 'direct_client',
}

// Talent Types
export interface Person {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  bio?: string;
  skills: Skill[];
  availability_status: 'available' | 'booked' | 'limited';
  rate_range?: RateRange;
  experience_years: number;
  projects_completed: number;
  performance_rating: number; // 1-100
  specialties: string[];
  location?: string;
  created_at: string;
}

export interface Skill {
  id: string;
  name: string;
  category: SkillCategory;
  proficiency_level: number; // 1-10
  years_experience: number;
}

export enum SkillCategory {
  DIRECTING = 'directing',
  PRODUCING = 'producing',
  CINEMATOGRAPHY = 'cinematography',
  EDITING = 'editing',
  SOUND = 'sound',
  WRITING = 'writing',
  PERFORMANCE = 'performance',
  TECHNICAL = 'technical',
}

export interface RateRange {
  min: number;
  max: number;
  currency: string;
  per: 'day' | 'week' | 'episode' | 'project';
}

// Analytics Types
export interface AnalyticsMetrics {
  total_projects: number;
  active_projects: number;
  total_budget: number;
  budget_utilization: number; // percentage
  team_efficiency: number; // percentage
  client_satisfaction: number; // 1-10
  revenue_growth: number; // percentage
  period: string;
  generated_at: string;
}

export interface TopPerformer {
  person: Person;
  metrics: {
    projects_completed: number;
    budget_efficiency: string;
    performance_score: number;
    specialty: string;
  };
}

// Case Study Types
export interface CaseStudy {
  id: string;
  project_id: string;
  title: string;
  description: string;
  challenge: string;
  solution: string;
  outcome: string;
  metrics: CaseStudyMetrics;
  media: CaseStudyMedia[];
  tags: string[];
  is_featured: boolean;
  created_at: string;
}

export interface CaseStudyMetrics {
  budget_variance: number; // percentage
  timeline_variance: number; // percentage
  quality_score: number; // 1-100
  client_satisfaction: number; // 1-10
  team_satisfaction: number; // 1-10
  roi: number; // percentage
}

export interface CaseStudyMedia {
  type: 'image' | 'video' | 'document';
  url: string;
  caption?: string;
  thumbnail_url?: string;
}

// Agent Types
export enum AgentType {
  SALES = 'sales',
  TALENT = 'talent', 
  ANALYTICS = 'analytics'
}

export interface AgentMetadata {
  agent_type: AgentType;
  processing_time?: string;
  confidence?: 'low' | 'medium' | 'high';
  sources?: string[];
  query_complexity?: 'simple' | 'moderate' | 'complex';
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'user_message' | 'ai_response' | 'agent_response' | 'system' | 'typing' | 'error';
  content: string;
  conversation_id?: string;
  context?: DashboardContext;
  agent?: AgentType;
  agent_metadata?: AgentMetadata;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface WebSocketResponse {
  type: string;
  data: any;
  error?: string;
  conversation_id?: string;
  timestamp?: string;
}

// Backend WebSocket Response Structures
export interface BackendAIResponse {
  conversation_id: string;
  user_message: {
    content: string;
    sender_name: string;
    timestamp: string;
  };
  ai_message: {
    content: string;
    sender_name: string;
    agent_info?: {
      type: string;
      primary_agent?: string;
    };
  };
}

// API Error Types
export interface ApiErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, any>;
  timestamp: string;
}

// Pagination Types
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Search/Filter Types
export interface SearchParams {
  query?: string;
  filters?: Record<string, any>;
  context?: DashboardContext;
}