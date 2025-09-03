import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { DashboardContext } from '@/lib/api/types';

// API imports
import { projectsApi } from '@/lib/api/projects';
import { talentApi } from '@/lib/api/talent';
import { intelligenceApi } from '@/lib/api/intelligence';
import { conversationsApi } from '@/lib/api/conversations';

// Types
import {
  Project,
  Person,
  Client,
  CaseStudy,
  AnalyticsMetrics,
  TopPerformer,
  Conversation
} from '@/lib/api/types';

interface ViewDataState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface HomeViewData {
  metrics: AnalyticsMetrics | null;
  topPerformers: TopPerformer[];
  recentProjects: Project[];
  featuredCaseStudies: CaseStudy[];
}

interface BidProposalViewData {
  projects: Project[];
  templates: Project[];
  recentProjects: Project[];
}

interface PreCallBriefViewData {
  clients: Client[];
  recentClients: Client[];
}

interface CaseStudyViewData {
  caseStudies: CaseStudy[];
  featuredCaseStudies: CaseStudy[];
  portfolioMetrics: any;
}

interface TalentDiscoveryViewData {
  people: Person[];
  topPerformers: Person[];
  availableTalent: Person[];
  skillCategories: string[];
}

// Home view hook
export function useHomeViewData(): ViewDataState<HomeViewData> {
  const { isAuthenticated } = useAuth();
  const [state, setState] = useState<ViewDataState<HomeViewData>>({
    data: null,
    isLoading: false,
    error: null,
    refetch: async () => {},
  });

  const fetchData = async () => {
    if (!isAuthenticated) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const [metricsRes, performersRes, projectsRes, caseStudiesRes] = await Promise.all([
        projectsApi.getAnalyticsMetrics(),
        projectsApi.getTopPerformers(3),
        projectsApi.getProjects({ limit: 5, sort_by: 'updated_at', sort_order: 'desc' }),
        intelligenceApi.getFeaturedCaseStudies(3),
      ]);

      setState(prev => ({
        ...prev,
        data: {
          metrics: metricsRes.data,
          topPerformers: performersRes.data,
          recentProjects: projectsRes.data.items,
          featuredCaseStudies: caseStudiesRes.data,
        },
        isLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false,
      }));
    }
  };

  useEffect(() => {
    fetchData();
  }, [isAuthenticated]);

  return {
    ...state,
    refetch: fetchData,
  };
}

// Bid Proposal view hook
export function useBidProposalViewData(): ViewDataState<BidProposalViewData> {
  const { isAuthenticated } = useAuth();
  const [state, setState] = useState<ViewDataState<BidProposalViewData>>({
    data: null,
    isLoading: false,
    error: null,
    refetch: async () => {},
  });

  const fetchData = async () => {
    if (!isAuthenticated) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const [projectsRes, templatesRes, recentRes] = await Promise.all([
        projectsApi.getProjects({ limit: 20 }),
        projectsApi.getProjectTemplates(),
        projectsApi.getProjects({ limit: 5, sort_by: 'updated_at', sort_order: 'desc' }),
      ]);

      setState(prev => ({
        ...prev,
        data: {
          projects: projectsRes.data.items,
          templates: templatesRes.data,
          recentProjects: recentRes.data.items,
        },
        isLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false,
      }));
    }
  };

  useEffect(() => {
    fetchData();
  }, [isAuthenticated]);

  return {
    ...state,
    refetch: fetchData,
  };
}

// Pre-Call Brief view hook
export function usePreCallBriefViewData(): ViewDataState<PreCallBriefViewData> {
  const { isAuthenticated } = useAuth();
  const [state, setState] = useState<ViewDataState<PreCallBriefViewData>>({
    data: null,
    isLoading: false,
    error: null,
    refetch: async () => {},
  });

  const fetchData = async () => {
    if (!isAuthenticated) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const [clientsRes, recentRes] = await Promise.all([
        intelligenceApi.getClients({ limit: 20 }),
        intelligenceApi.getClients({ limit: 5, sort_by: 'last_interaction', sort_order: 'desc' }),
      ]);

      setState(prev => ({
        ...prev,
        data: {
          clients: clientsRes.data.items,
          recentClients: recentRes.data.items,
        },
        isLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false,
      }));
    }
  };

  useEffect(() => {
    fetchData();
  }, [isAuthenticated]);

  return {
    ...state,
    refetch: fetchData,
  };
}

// Case Study view hook
export function useCaseStudyViewData(): ViewDataState<CaseStudyViewData> {
  const { isAuthenticated } = useAuth();
  const [state, setState] = useState<ViewDataState<CaseStudyViewData>>({
    data: null,
    isLoading: false,
    error: null,
    refetch: async () => {},
  });

  const fetchData = async () => {
    if (!isAuthenticated) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const [caseStudiesRes, featuredRes, metricsRes] = await Promise.all([
        intelligenceApi.getCaseStudies({ limit: 20 }),
        intelligenceApi.getFeaturedCaseStudies(6),
        intelligenceApi.getPortfolioMetrics(),
      ]);

      setState(prev => ({
        ...prev,
        data: {
          caseStudies: caseStudiesRes.data.items,
          featuredCaseStudies: featuredRes.data,
          portfolioMetrics: metricsRes.data,
        },
        isLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false,
      }));
    }
  };

  useEffect(() => {
    fetchData();
  }, [isAuthenticated]);

  return {
    ...state,
    refetch: fetchData,
  };
}

// Talent Discovery view hook
export function useTalentDiscoveryViewData(): ViewDataState<TalentDiscoveryViewData> {
  const { isAuthenticated } = useAuth();
  const [state, setState] = useState<ViewDataState<TalentDiscoveryViewData>>({
    data: null,
    isLoading: false,
    error: null,
    refetch: async () => {},
  });

  const fetchData = async () => {
    if (!isAuthenticated) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const [peopleRes, topPerformersRes, availableRes, categoriesRes] = await Promise.all([
        talentApi.getPeople({ limit: 20 }),
        talentApi.getTopPerformers(),
        talentApi.getAvailablePeople(),
        talentApi.getSkillCategories(),
      ]);

      setState(prev => ({
        ...prev,
        data: {
          people: peopleRes.data.items,
          topPerformers: topPerformersRes.data,
          availableTalent: availableRes.data,
          skillCategories: categoriesRes.data,
        },
        isLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false,
      }));
    }
  };

  useEffect(() => {
    fetchData();
  }, [isAuthenticated]);

  return {
    ...state,
    refetch: fetchData,
  };
}

// Recent conversations hook (used by Sidebar)
export function useRecentConversations(): ViewDataState<Conversation[]> {
  const { isAuthenticated } = useAuth();
  const [state, setState] = useState<ViewDataState<Conversation[]>>({
    data: null,
    isLoading: false,
    error: null,
    refetch: async () => {},
  });

  const fetchData = async () => {
    if (!isAuthenticated) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await conversationsApi.getRecentConversations(5);
      setState(prev => ({
        ...prev,
        data: response.data,
        isLoading: false,
      }));
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false,
      }));
    }
  };

  useEffect(() => {
    fetchData();
  }, [isAuthenticated]);

  return {
    ...state,
    refetch: fetchData,
  };
}

// Generic view data hook that switches based on context
export function useViewData(context: DashboardContext) {
  switch (context) {
    case 'home':
      return useHomeViewData();
    case 'bid-proposal':
      return useBidProposalViewData();
    case 'pre-call-brief':
      return usePreCallBriefViewData();
    case 'case-study':
      return useCaseStudyViewData();
    case 'talent-discovery':
      return useTalentDiscoveryViewData();
    default:
      return useHomeViewData();
  }
}