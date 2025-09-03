import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { AgentType, DashboardContext } from '@/lib/api/types';
import { RoutingMode, AgentPreferences } from '@/components/ui/agent-selector';

interface AgentPreferencesContextType {
  preferences: AgentPreferences;
  updatePreferences: (preferences: AgentPreferences) => void;
  getContextSuggestions: (context: DashboardContext) => AgentType[];
  isAgentRelevant: (agent: AgentType, context: DashboardContext) => boolean;
  reset: () => void;
}

const AgentPreferencesContext = createContext<AgentPreferencesContextType | undefined>(
  undefined
);

// Default preferences
const defaultPreferences: AgentPreferences = {
  routingMode: 'auto',
  selectedAgents: Object.values(AgentType),
  autoRouteEnabled: true, // Only true when routingMode is 'auto'
  contextAware: true,
};

// Context-to-agent mapping for intelligent suggestions
const contextAgentMapping: Record<DashboardContext, AgentType[]> = {
  'home': [AgentType.ANALYTICS, AgentType.SALES, AgentType.TALENT],
  'pre-call-brief': [AgentType.SALES, AgentType.ANALYTICS],
  'case-study': [AgentType.ANALYTICS, AgentType.SALES],
  'talent-discovery': [AgentType.TALENT, AgentType.ANALYTICS],
  'bid-proposal': [AgentType.SALES, AgentType.TALENT, AgentType.ANALYTICS],
};

// Agent relevance scoring for different contexts
const agentRelevanceMatrix: Record<DashboardContext, Record<AgentType, number>> = {
  'home': {
    [AgentType.ANALYTICS]: 0.9,
    [AgentType.SALES]: 0.7,
    [AgentType.TALENT]: 0.6,
  },
  'pre-call-brief': {
    [AgentType.SALES]: 0.95,
    [AgentType.ANALYTICS]: 0.8,
    [AgentType.TALENT]: 0.3,
  },
  'case-study': {
    [AgentType.ANALYTICS]: 0.95,
    [AgentType.SALES]: 0.6,
    [AgentType.TALENT]: 0.4,
  },
  'talent-discovery': {
    [AgentType.TALENT]: 0.95,
    [AgentType.ANALYTICS]: 0.7,
    [AgentType.SALES]: 0.3,
  },
  'bid-proposal': {
    [AgentType.SALES]: 0.9,
    [AgentType.TALENT]: 0.8,
    [AgentType.ANALYTICS]: 0.8,
  },
};

// Storage key for preferences
const STORAGE_KEY = 'onevice-agent-preferences';

interface AgentPreferencesProviderProps {
  children: React.ReactNode;
}

export const AgentPreferencesProvider: React.FC<AgentPreferencesProviderProps> = ({
  children
}) => {
  const [preferences, setPreferences] = useState<AgentPreferences>(defaultPreferences);

  // Load preferences from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        
        // Validate stored preferences
        if (
          parsed &&
          typeof parsed === 'object' &&
          parsed.routingMode &&
          Array.isArray(parsed.selectedAgents)
        ) {
          setPreferences({
            ...defaultPreferences,
            ...parsed,
            // Ensure selected agents are valid
            selectedAgents: parsed.selectedAgents.filter((agent: string) =>
              Object.values(AgentType).includes(agent as AgentType)
            ),
          });
        }
      }
    } catch (error) {
      console.error('Failed to load agent preferences:', error);
      // Fall back to defaults
      setPreferences(defaultPreferences);
    }
  }, []);

  // Save preferences to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    } catch (error) {
      console.error('Failed to save agent preferences:', error);
    }
  }, [preferences]);

  const updatePreferences = useCallback((newPreferences: AgentPreferences) => {
    setPreferences(newPreferences);
  }, []);

  const getContextSuggestions = useCallback((context: DashboardContext): AgentType[] => {
    const suggestions = contextAgentMapping[context] || [];
    
    // Sort by relevance score
    return suggestions.sort((a, b) => {
      const scoreA = agentRelevanceMatrix[context]?.[a] || 0;
      const scoreB = agentRelevanceMatrix[context]?.[b] || 0;
      return scoreB - scoreA;
    });
  }, []);

  const isAgentRelevant = useCallback(
    (agent: AgentType, context: DashboardContext): boolean => {
      const relevanceScore = agentRelevanceMatrix[context]?.[agent] || 0;
      return relevanceScore >= 0.5; // Threshold for relevance
    },
    []
  );

  const reset = useCallback(() => {
    setPreferences(defaultPreferences);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear agent preferences:', error);
    }
  }, []);

  const contextValue: AgentPreferencesContextType = {
    preferences,
    updatePreferences,
    getContextSuggestions,
    isAgentRelevant,
    reset,
  };

  return (
    <AgentPreferencesContext.Provider value={contextValue}>
      {children}
    </AgentPreferencesContext.Provider>
  );
};

export const useAgentPreferences = (): AgentPreferencesContextType => {
  const context = useContext(AgentPreferencesContext);
  if (context === undefined) {
    throw new Error('useAgentPreferences must be used within an AgentPreferencesProvider');
  }
  return context;
};

// Utility hook for getting suggested agents based on current context
export const useContextAgents = (currentContext?: DashboardContext) => {
  const { preferences, getContextSuggestions, isAgentRelevant } = useAgentPreferences();

  const getSuggestedAgents = useCallback(() => {
    if (!currentContext || !preferences.contextAware) {
      return preferences.selectedAgents;
    }

    const suggestions = getContextSuggestions(currentContext);
    
    // If auto routing is enabled, return suggestions
    if (preferences.routingMode === 'auto') {
      return suggestions;
    }

    // Filter selected agents by relevance to context
    return preferences.selectedAgents.filter(agent =>
      isAgentRelevant(agent, currentContext)
    );
  }, [currentContext, preferences, getContextSuggestions, isAgentRelevant]);

  const getPreferredAgent = useCallback(() => {
    if (!currentContext) {
      return preferences.selectedAgents[0] || AgentType.SALES;
    }

    const suggestions = getContextSuggestions(currentContext);
    
    // Return the most relevant agent that's also selected
    for (const suggested of suggestions) {
      if (preferences.selectedAgents.includes(suggested)) {
        return suggested;
      }
    }

    // Fall back to first selected agent
    return preferences.selectedAgents[0] || AgentType.SALES;
  }, [currentContext, preferences, getContextSuggestions]);

  return {
    suggestedAgents: getSuggestedAgents(),
    preferredAgent: getPreferredAgent(),
    isContextAware: preferences.contextAware,
    routingMode: preferences.routingMode,
  };
};

// Utility function to get agent routing metadata for WebSocket messages
export const getAgentRoutingMetadata = (
  preferences: AgentPreferences,
  context?: DashboardContext
) => {
  const contextSuggestions = context ? contextAgentMapping[context] || [] : [];
  
  return {
    routing_mode: preferences.routingMode,
    selected_agents: preferences.selectedAgents,
    auto_route_enabled: preferences.autoRouteEnabled,
    context_aware: preferences.contextAware,
    context_suggestions: contextSuggestions,
    ...(context && {
      current_context: context,
      context_relevance: Object.fromEntries(
        Object.values(AgentType).map(agent => [
          agent,
          agentRelevanceMatrix[context]?.[agent] || 0
        ])
      ),
    }),
  };
};