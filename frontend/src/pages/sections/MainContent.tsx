import React from "react";
import { Button } from "@/components/ui/button";
import { User, Loader2, AlertCircle, RefreshCw, ChevronUp } from "lucide-react";
import { DashboardContext } from "../Dashboard";
import { 
  useHomeViewData, 
  useBidProposalViewData, 
  usePreCallBriefViewData, 
  useCaseStudyViewData, 
  useTalentDiscoveryViewData 
} from "@/hooks/useViewData";

interface MainContentProps {
  context: DashboardContext;
  onShowProjectPanel: () => void;
  onCollapse?: () => void;
}

export const MainContent = ({ context, onShowProjectPanel, onCollapse }: MainContentProps): JSX.Element => {
  const intelligenceCards = [
    {
      title: "Strategic Intelligence",
      description: "Market analysis, competitive insights, growth opportunities",
      color: "bg-blue-500/20 border-blue-500/30"
    },
    {
      title: "Financial Analytics", 
      description: "Revenue analysis, budget optimization, ROI tracking",
      color: "bg-green-500/20 border-green-500/30"
    },
    {
      title: "Talent Intelligence",
      description: "Team performance, recruitment insights",
      color: "bg-purple-500/20 border-purple-500/30"
    },
    {
      title: "Project Oversight",
      description: "Portfolio management, resource allocation, timeline optimization",
      color: "bg-orange-500/20 border-orange-500/30"
    }
  ];

  const topPerformers = [
    {
      name: "Sarah Chen",
      role: "Senior Creative Director", 
      projects: 8,
      budget: "+12% efficiency",
      status: "Available",
      progress: 95,
      specialty: "Film Productions"
    },
    {
      name: "Marcus Rodriguez", 
      role: "Creative Director",
      projects: 6,
      budget: "Drama Series",
      status: "Booked until March",
      progress: 92,
      specialty: "Television"
    },
    {
      name: "Alex Thompson",
      role: "Creative Director", 
      projects: 7,
      budget: "3 Emmy noms",
      status: "Available (2-week notice)",
      progress: 90,
      specialty: "Documentary"
    }
  ];

  const renderContextContent = () => {
    switch (context) {
      case "bid-proposal":
        return <BidProposalView onShowProjectPanel={onShowProjectPanel} />;
      case "pre-call-brief":
        return <PreCallBriefView onShowProjectPanel={onShowProjectPanel} />;
      case "case-study":
        return <CaseStudyView onShowProjectPanel={onShowProjectPanel} />;
      case "talent-discovery":
        return <TalentDiscoveryView onShowProjectPanel={onShowProjectPanel} />;
      default:
        return <HomeView onShowProjectPanel={onShowProjectPanel} />;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto relative">
      {/* Context-Specific Content */}
      {renderContextContent()}
      
      {/* Collapse Control Button */}
      {onCollapse && (
        <button
          onClick={onCollapse}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-[calc(100%-8px)]
                     w-6 h-16 bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 border-r-0
                     rounded-l-lg flex items-center justify-center group z-10
                     opacity-40 hover:opacity-100 hover:translate-x-[calc(100%-12px)]
                     transition-all duration-300 hover:bg-gray-800/80 hover:shadow-[-4px_0_24px_rgba(0,0,0,0.4)]"
          title="Collapse content (⌘\)"
          aria-label="Collapse main content"
        >
          <ChevronUp className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors duration-300" />
        </button>
      )}
    </div>
  );
};

// Home View Component
const HomeView = ({ onShowProjectPanel }: { onShowProjectPanel: () => void }) => {
  const { data, isLoading, error, refetch } = useHomeViewData();

  const intelligenceCards = [
    {
      title: "Strategic Intelligence",
      description: "Market analysis, competitive insights, growth opportunities",
      color: "bg-blue-500/20 border-blue-500/30"
    },
    {
      title: "Financial Analytics", 
      description: "Revenue analysis, budget optimization, ROI tracking",
      color: "bg-green-500/20 border-green-500/30"
    },
    {
      title: "Talent Intelligence",
      description: "Team performance, recruitment insights",
      color: "bg-purple-500/20 border-purple-500/30"
    },
    {
      title: "Project Oversight",
      description: "Portfolio management, resource allocation, timeline optimization",
      color: "bg-orange-500/20 border-orange-500/30"
    }
  ];

  // Show loading state
  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-white mx-auto mb-4" />
              <p className="text-gray-400">Loading dashboard data...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-4" />
              <p className="text-red-400 mb-4">Error loading dashboard data</p>
              <p className="text-gray-400 text-sm mb-4">{error}</p>
              <Button
                variant="glass"
                size="sm"
                onClick={refetch}
                className="flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-2xl font-light text-white mb-2">Welcome to One Vice AI Intelligence Hub</h1>
          <p className="text-gray-400 max-w-3xl">
            As a Leadership user, you have full access to our comprehensive business intelligence platform. I can help you with strategic insights, financial analysis, talent discovery, project management, and competitive intelligence across all company operations.
          </p>
        </div>

        {/* Metrics Overview */}
        {data?.metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-2">Total Projects</h3>
              <div className="text-2xl font-bold text-white">{data.metrics.total_projects}</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-2">Active Projects</h3>
              <div className="text-2xl font-bold text-white">{data.metrics.active_projects}</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-2">Team Efficiency</h3>
              <div className="text-2xl font-bold text-green-400">{data.metrics.team_efficiency}%</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-2">Budget Utilization</h3>
              <div className="text-2xl font-bold text-blue-400">{data.metrics.budget_utilization}%</div>
            </div>
          </div>
        )}

        {/* Intelligence Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {intelligenceCards.map((card, index) => (
            <div
              key={index}
              className={`p-6 rounded-lg border ${card.color} cursor-pointer hover:bg-opacity-30 transition-all`}
            >
              <h3 className="text-lg font-medium text-white mb-2">{card.title}</h3>
              <p className="text-sm text-gray-400">{card.description}</p>
            </div>
          ))}
        </div>

        {/* Query Suggestion */}
        <div className="bg-gray-800/30 rounded-lg p-6 mb-8">
          <p className="text-gray-300 italic">
            Ask me anything about projects, people, finances, or strategic opportunities. I have access to the complete company knowledge base and real-time data.
          </p>
        </div>

        {/* Top Performers Section */}
        <div className="bg-gray-800/50 rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-medium text-white">Top Performing Talent</h2>
            <Button variant="glass" size="sm" onClick={onShowProjectPanel}>View All</Button>
          </div>
          
          {data?.topPerformers && data.topPerformers.length > 0 ? (
            <div className="space-y-4">
              {data.topPerformers.map((performer, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-gray-300" />
                    </div>
                    <div>
                      <h3 className="font-medium text-white">{performer.person.name}</h3>
                      <p className="text-sm text-gray-400">{performer.person.specialties?.[0] || 'Professional'}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-8 text-sm">
                    <div>
                      <span className="text-gray-400">Projects: </span>
                      <span className="text-white">{performer.metrics.projects_completed} completed</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Performance: </span>
                      <span className="text-white">{performer.metrics.performance_score}%</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Status: </span>
                      <span className={`${performer.person.availability_status === 'available' ? 'text-green-400' : 'text-yellow-400'}`}>
                        {performer.person.availability_status}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-medium">{performer.metrics.specialty}</div>
                      <div className="text-xs text-gray-400">
                        {performer.person.experience_years} years experience
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <User className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No top performers data available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Bid Proposal View Component
const BidProposalView = ({ onShowProjectPanel }: { onShowProjectPanel: () => void }) => {
  const { data, isLoading, error, refetch } = useBidProposalViewData();

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="text-gray-400">Loading bid proposal data...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <h2 className="text-xl font-medium text-white mb-2">Error Loading Data</h2>
              <p className="text-gray-400 mb-4">{error}</p>
              <Button onClick={refetch} variant="glass" className="gap-2">
                <RefreshCw className="w-4 h-4" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-light text-white mb-2">Bidding Proposal Generator</h1>
            <p className="text-gray-400">AI-powered proposal creation and optimization</p>
          </div>
          <Button onClick={onShowProjectPanel} variant="glass">
            View Project Context
          </Button>
        </div>

        {/* Recent Projects */}
        <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-white">Recent Projects</h3>
            <span className="text-sm text-gray-400">
              {data?.recentProjects?.length || 0} active proposals
            </span>
          </div>
          
          {data?.recentProjects && data.recentProjects.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.recentProjects.map((project) => (
                <div key={project.id} className="bg-gray-900/50 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">{project.title}</h4>
                  <p className="text-sm text-gray-400 mb-2">{project.description}</p>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">{project.type}</span>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        project.status === 'active' ? 'bg-green-500/20 text-green-400' :
                        project.status === 'draft' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                  </div>
                  {project.budget && (
                    <div className="mt-2 text-sm">
                      <span className="text-gray-400">Budget: </span>
                      <span className="text-white">${project.budget.total?.toLocaleString()}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-400">No recent projects available</p>
              <Button className="mt-4" variant="gold">Create New Proposal</Button>
            </div>
          )}
        </div>

        {/* Templates */}
        {data?.templates && data.templates.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">Project Templates</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {data.templates.map((template) => (
                <div key={template.id} className="bg-gray-900/50 rounded-lg p-4 cursor-pointer hover:bg-gray-900/70 transition-colors">
                  <h4 className="font-medium text-white mb-2">{template.title}</h4>
                  <p className="text-xs text-gray-400 mb-2">{template.type}</p>
                  <div className="text-xs text-gray-500">
                    {template.budget && `Budget: $${template.budget.total?.toLocaleString()}`}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Projects */}
        {data?.projects && data.projects.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">All Projects</h3>
            <div className="space-y-3">
              {data.projects.slice(0, 5).map((project) => (
                <div key={project.id} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-white">{project.title}</h4>
                    <p className="text-sm text-gray-400">{project.type} • {project.description}</p>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={`px-2 py-1 rounded text-xs ${
                      project.status === 'active' ? 'bg-green-500/20 text-green-400' :
                      project.status === 'draft' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {project.status}
                    </span>
                    {project.budget && (
                      <span className="text-white">${project.budget.total?.toLocaleString()}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <Button variant="gold">Create New Proposal</Button>
          <Button variant="glass">Import Template</Button>
          <Button variant="glass">Export Proposals</Button>
          <Button variant="ghost" onClick={refetch}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Data
          </Button>
        </div>
      </div>
    </div>
  );
};

// Pre-Call Brief View Component
const PreCallBriefView = ({ onShowProjectPanel }: { onShowProjectPanel: () => void }) => {
  const { data, isLoading, error, refetch } = usePreCallBriefViewData();

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="text-gray-400">Loading client intelligence...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <h2 className="text-xl font-medium text-white mb-2">Error Loading Data</h2>
              <p className="text-gray-400 mb-4">{error}</p>
              <Button onClick={refetch} variant="glass" className="gap-2">
                <RefreshCw className="w-4 h-4" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-light text-white mb-2">Pre-Call Brief Generator</h1>
            <p className="text-gray-400">Generate client intelligence</p>
          </div>
          <Button onClick={onShowProjectPanel} variant="glass">
            View Client Context
          </Button>
        </div>
        
        {/* Recent Clients */}
        <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-white">Recent Clients</h3>
            <span className="text-sm text-gray-400">
              {data?.recentClients?.length || 0} recent interactions
            </span>
          </div>
          
          {data?.recentClients && data.recentClients.length > 0 ? (
            <div className="space-y-3">
              {data.recentClients.map((client) => (
                <div key={client.id} className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-gray-300" />
                    </div>
                    <div>
                      <h4 className="font-medium text-white">{client.name}</h4>
                      <p className="text-sm text-gray-400">{client.type} • {client.industry}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-8 text-sm">
                    <div>
                      <span className="text-gray-400">Last Contact: </span>
                      <span className="text-white">
                        {new Date(client.last_interaction).toLocaleDateString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Projects: </span>
                      <span className="text-white">{client.total_projects || 0}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Relationship: </span>
                      <span className={`${
                        client.relationship_strength === 'strong' ? 'text-green-400' :
                        client.relationship_strength === 'moderate' ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {client.relationship_strength || 'New'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <User className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No recent client interactions</p>
            </div>
          )}
        </div>

        {/* All Clients */}
        {data?.clients && data.clients.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">All Clients</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.clients.slice(0, 9).map((client) => (
                <div key={client.id} className="bg-gray-900/50 rounded-lg p-4 cursor-pointer hover:bg-gray-900/70 transition-colors">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-gray-300" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-white text-sm">{client.name}</h4>
                      <p className="text-xs text-gray-400">{client.type}</p>
                    </div>
                  </div>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Industry:</span>
                      <span className="text-white">{client.industry}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Projects:</span>
                      <span className="text-white">{client.total_projects || 0}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <Button variant="gold">Generate Pre-Call Brief</Button>
          <Button variant="glass">Add New Client</Button>
          <Button variant="glass">Export Client Data</Button>
          <Button variant="ghost" onClick={refetch}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Data
          </Button>
        </div>
      </div>
    </div>
  );
};

// Case Study View Component
const CaseStudyView = ({ onShowProjectPanel }: { onShowProjectPanel: () => void }) => {
  const { data, isLoading, error, refetch } = useCaseStudyViewData();

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="text-gray-400">Loading portfolio data...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <h2 className="text-xl font-medium text-white mb-2">Error Loading Data</h2>
              <p className="text-gray-400 mb-4">{error}</p>
              <Button onClick={refetch} variant="glass" className="gap-2">
                <RefreshCw className="w-4 h-4" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-light text-white mb-2">Case Study Portfolio</h1>
            <p className="text-gray-400">Compile project portfolio</p>
          </div>
          <Button onClick={onShowProjectPanel} variant="glass">
            View Portfolio Context
          </Button>
        </div>
        
        {/* Portfolio Metrics */}
        {data?.portfolioMetrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-gray-800/50 rounded-lg p-6">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Total Case Studies</h3>
              <p className="text-2xl font-light text-white">{data.portfolioMetrics.total_case_studies || 0}</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-6">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Success Rate</h3>
              <p className="text-2xl font-light text-white">{data.portfolioMetrics.success_rate || 0}%</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-6">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Average ROI</h3>
              <p className="text-2xl font-light text-white">{data.portfolioMetrics.average_roi || 0}%</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-6">
              <h3 className="text-sm font-medium text-gray-400 mb-2">Client Satisfaction</h3>
              <p className="text-2xl font-light text-white">{data.portfolioMetrics.client_satisfaction || 0}%</p>
            </div>
          </div>
        )}
        
        {/* Featured Case Studies */}
        <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-white">Featured Case Studies</h3>
            <span className="text-sm text-gray-400">
              {data?.featuredCaseStudies?.length || 0} featured projects
            </span>
          </div>
          
          {data?.featuredCaseStudies && data.featuredCaseStudies.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.featuredCaseStudies.map((caseStudy) => (
                <div key={caseStudy.id} className="bg-gray-900/50 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2">{caseStudy.title}</h4>
                  <p className="text-sm text-gray-400 mb-3">{caseStudy.description}</p>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Client:</span>
                      <span className="text-white">{caseStudy.client_name || 'Confidential'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Industry:</span>
                      <span className="text-white">{caseStudy.industry || 'Entertainment'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Budget:</span>
                      <span className="text-white">
                        {caseStudy.project_budget 
                          ? `$${caseStudy.project_budget.toLocaleString()}` 
                          : 'Confidential'
                        }
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">ROI:</span>
                      <span className="text-green-400">+{caseStudy.roi_percentage || 0}%</span>
                    </div>
                  </div>
                  
                  {caseStudy.tags && caseStudy.tags.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {caseStudy.tags.slice(0, 3).map((tag, index) => (
                        <span key={index} className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-400">No featured case studies available</p>
              <Button className="mt-4" variant="gold">Create Case Study</Button>
            </div>
          )}
        </div>

        {/* All Case Studies */}
        {data?.caseStudies && data.caseStudies.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">All Case Studies</h3>
            <div className="space-y-3">
              {data.caseStudies.slice(0, 5).map((caseStudy) => (
                <div key={caseStudy.id} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-white">{caseStudy.title}</h4>
                    <p className="text-sm text-gray-400">{caseStudy.industry} • {caseStudy.description}</p>
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <div>
                      <span className="text-gray-400">ROI: </span>
                      <span className="text-green-400">+{caseStudy.roi_percentage || 0}%</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Budget: </span>
                      <span className="text-white">
                        {caseStudy.project_budget 
                          ? `$${caseStudy.project_budget.toLocaleString()}` 
                          : 'Confidential'
                        }
                      </span>
                    </div>
                    <div>
                      <span className={`text-xs px-2 py-1 rounded ${
                        caseStudy.featured ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {caseStudy.featured ? 'Featured' : 'Standard'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <Button variant="gold">Create New Case Study</Button>
          <Button variant="glass">Export Portfolio</Button>
          <Button variant="glass">Generate Report</Button>
          <Button variant="ghost" onClick={refetch}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Data
          </Button>
        </div>
      </div>
    </div>
  );
};

// Talent Discovery View Component
const TalentDiscoveryView = ({ onShowProjectPanel }: { onShowProjectPanel: () => void }) => {
  const { data, isLoading, error, refetch } = useTalentDiscoveryViewData();

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="text-gray-400">Loading talent data...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <h2 className="text-xl font-medium text-white mb-2">Error Loading Data</h2>
              <p className="text-gray-400 mb-4">{error}</p>
              <Button onClick={refetch} variant="glass" className="gap-2">
                <RefreshCw className="w-4 h-4" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-light text-white mb-2">Talent Discovery</h1>
            <p className="text-gray-400">Discovery Portfolio</p>
          </div>
          <Button onClick={onShowProjectPanel} variant="glass">
            View Talent Context
          </Button>
        </div>
        
        {/* Skill Categories */}
        {data?.skillCategories && data.skillCategories.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">Skill Categories</h3>
            <div className="flex flex-wrap gap-2">
              {data.skillCategories.map((category, index) => (
                <span key={index} className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm">
                  {category}
                </span>
              ))}
            </div>
          </div>
        )}
        
        {/* Top Performers */}
        <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-white">Top Performers</h3>
            <span className="text-sm text-gray-400">
              {data?.topPerformers?.length || 0} top talent
            </span>
          </div>
          
          {data?.topPerformers && data.topPerformers.length > 0 ? (
            <div className="space-y-3">
              {data.topPerformers.map((person) => (
                <div key={person.id} className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-gray-300" />
                    </div>
                    <div>
                      <h4 className="font-medium text-white">{person.name}</h4>
                      <p className="text-sm text-gray-400">
                        {person.specialties?.[0] || person.primary_skill || 'Professional'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-8 text-sm">
                    <div>
                      <span className="text-gray-400">Experience: </span>
                      <span className="text-white">{person.experience_years || 0} years</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Rating: </span>
                      <span className="text-white">{person.performance_rating || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Status: </span>
                      <span className={`${
                        person.availability_status === 'available' ? 'text-green-400' :
                        person.availability_status === 'limited' ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {person.availability_status || 'Unknown'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Location: </span>
                      <span className="text-white">{person.location || 'Remote'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <User className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No top performers data available</p>
            </div>
          )}
        </div>

        {/* Available Talent */}
        {data?.availableTalent && data.availableTalent.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">Available Now</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.availableTalent.slice(0, 6).map((person) => (
                <div key={person.id} className="bg-gray-900/50 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-gray-300" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-white text-sm">{person.name}</h4>
                      <p className="text-xs text-gray-400">
                        {person.specialties?.[0] || person.primary_skill || 'Professional'}
                      </p>
                    </div>
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  </div>
                  
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Experience:</span>
                      <span className="text-white">{person.experience_years || 0}y</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Rating:</span>
                      <span className="text-white">{person.performance_rating || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Location:</span>
                      <span className="text-white">{person.location || 'Remote'}</span>
                    </div>
                  </div>
                  
                  {person.skills && person.skills.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {person.skills.slice(0, 2).map((skill, index) => (
                        <span key={index} className="text-xs px-2 py-1 bg-gray-600/50 text-gray-300 rounded">
                          {skill.name || skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Talent */}
        {data?.people && data.people.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">All Talent</h3>
            <div className="space-y-2">
              {data.people.slice(0, 8).map((person) => (
                <div key={person.id} className="flex items-center justify-between p-3 bg-gray-900/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-gray-300" />
                    </div>
                    <div>
                      <h4 className="font-medium text-white text-sm">{person.name}</h4>
                      <p className="text-xs text-gray-400">
                        {person.specialties?.[0] || person.primary_skill || 'Professional'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-gray-400">{person.experience_years || 0}y exp</span>
                    <span className={`px-2 py-1 rounded ${
                      person.availability_status === 'available' ? 'bg-green-500/20 text-green-400' :
                      person.availability_status === 'limited' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {person.availability_status || 'Unknown'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <Button variant="gold">Search Talent</Button>
          <Button variant="glass">Add New Talent</Button>
          <Button variant="glass">Export Talent Database</Button>
          <Button variant="ghost" onClick={refetch}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Data
          </Button>
        </div>
      </div>
    </div>
  );
};