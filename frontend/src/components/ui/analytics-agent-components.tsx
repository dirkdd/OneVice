import React from "react";
import { cn } from "@/lib/utils";
import { Card } from "./card";
import { Badge } from "./badge";
import { Button } from "./button";
import { 
  MetricCard, 
  ProgressBar, 
  StatusIndicator, 
  DataList, 
  QuickStats 
} from "./agent-visualizations";
import {
  BarChart3,
  PieChart,
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  Users,
  DollarSign,
  Clock,
  Calendar,
  AlertTriangle,
  CheckCircle,
  Zap,
  Award,
  Building,
  Briefcase,
  Star,
  ArrowUp,
  ArrowDown,
  Minus,
  Eye,
  Brain,
  Gauge,
  LineChart,
  Filter,
  Download,
  RefreshCw,
  Globe,
  Shield
} from "lucide-react";

// Analytics-specific Types
export interface PerformanceDashboard {
  period: string;
  overview: {
    total_projects: number;
    active_projects: number;
    completed_projects: number;
    total_revenue: number;
    revenue_growth: number;
    team_utilization: number;
    client_satisfaction: number;
  };
  trends: Array<{
    metric: string;
    current_value: number;
    previous_value: number;
    trend: 'up' | 'down' | 'stable';
    percentage_change: number;
  }>;
  alerts: Array<{
    level: 'critical' | 'warning' | 'info';
    message: string;
    action?: string;
  }>;
}

export interface KPIMetric {
  id: string;
  name: string;
  category: 'financial' | 'operational' | 'strategic' | 'team';
  current_value: number;
  target_value: number;
  unit: string;
  trend: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
    period: string;
  };
  status: 'on_track' | 'at_risk' | 'off_track' | 'exceeding';
  last_updated: string;
}

export interface TrendAnalysis {
  metric: string;
  time_period: string;
  data_points: Array<{
    period: string;
    value: number;
    target?: number;
  }>;
  insights: string[];
  prediction: {
    next_period: number;
    confidence: number;
    factors: string[];
  };
  recommendations: string[];
}

export interface StrategicInsight {
  id: string;
  title: string;
  category: 'opportunity' | 'risk' | 'optimization' | 'innovation';
  priority: 'high' | 'medium' | 'low';
  impact_score: number;
  confidence: number;
  description: string;
  supporting_data: Array<{
    metric: string;
    value: string;
  }>;
  recommended_actions: string[];
  timeline: string;
  stakeholders: string[];
}

export interface ExecutiveSummary {
  period: string;
  key_achievements: string[];
  critical_metrics: Array<{
    metric: string;
    value: string;
    status: 'positive' | 'negative' | 'neutral';
  }>;
  strategic_priorities: Array<{
    priority: string;
    status: 'on_track' | 'delayed' | 'completed';
    progress: number;
  }>;
  risks_and_opportunities: Array<{
    type: 'risk' | 'opportunity';
    description: string;
    impact: 'high' | 'medium' | 'low';
  }>;
  next_quarter_focus: string[];
}

export interface ForecastingVisualization {
  metric: string;
  historical_data: Array<{
    period: string;
    actual: number;
  }>;
  forecast_data: Array<{
    period: string;
    predicted: number;
    confidence_lower: number;
    confidence_upper: number;
  }>;
  model_accuracy: number;
  assumptions: string[];
  scenarios: Array<{
    name: string;
    probability: number;
    impact: number;
  }>;
}

// Analytics Agent Components

// Performance Dashboard
export const PerformanceDashboardCard: React.FC<{
  data: PerformanceDashboard;
  className?: string;
}> = ({ data, className }) => {
  return (
    <Card className={cn(
      "p-6 bg-emerald-500/10 border-emerald-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/20 rounded-lg border border-emerald-500/30">
            <BarChart3 className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Performance Dashboard</h3>
            <p className="text-sm text-gray-400">{data.period}</p>
          </div>
        </div>

        <QuickStats
          variant="analytics"
          columns={4}
          stats={[
            {
              label: "Total Projects",
              value: data.overview.total_projects,
              icon: Briefcase,
              trend: { direction: 'up', value: '+5%' }
            },
            {
              label: "Revenue",
              value: `$${data.overview.total_revenue.toLocaleString()}`,
              icon: DollarSign,
              trend: { 
                direction: data.overview.revenue_growth > 0 ? 'up' : 'down', 
                value: `${data.overview.revenue_growth}%` 
              }
            },
            {
              label: "Team Utilization",
              value: `${data.overview.team_utilization}%`,
              icon: Users
            },
            {
              label: "Client Satisfaction",
              value: `${data.overview.client_satisfaction}/10`,
              icon: Star
            }
          ]}
        />

        <div className="grid grid-cols-2 gap-4">
          <MetricCard
            title="Active Projects"
            value={data.overview.active_projects}
            subtitle={`${data.overview.completed_projects} completed this period`}
            variant="analytics"
            size="sm"
            icon={Activity}
          />
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-300">Key Trends</h4>
            <div className="space-y-2">
              {data.trends.slice(0, 3).map((trend, index) => {
                const TrendIcon = trend.trend === 'up' ? ArrowUp : 
                                trend.trend === 'down' ? ArrowDown : Minus;
                const trendColor = trend.trend === 'up' ? 'text-green-400' :
                                 trend.trend === 'down' ? 'text-red-400' : 'text-gray-400';
                
                return (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                    <span className="text-sm text-gray-300">{trend.metric}</span>
                    <div className="flex items-center gap-1">
                      <TrendIcon className={cn("w-3 h-3", trendColor)} />
                      <span className={cn("text-xs", trendColor)}>
                        {trend.percentage_change}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {data.alerts.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Alerts ({data.alerts.length})
            </h4>
            {data.alerts.slice(0, 3).map((alert, index) => (
              <StatusIndicator
                key={index}
                status={alert.level === 'critical' ? 'error' : 
                       alert.level === 'warning' ? 'warning' : 'info'}
                label={alert.message}
                size="sm"
              />
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};

// KPI Metric Display
export const KPIMetricCard: React.FC<{
  metrics: KPIMetric[];
  className?: string;
}> = ({ metrics, className }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on_track': return 'text-green-400 bg-green-500/20 border-green-400/30';
      case 'exceeding': return 'text-blue-400 bg-blue-500/20 border-blue-400/30';
      case 'at_risk': return 'text-yellow-400 bg-yellow-500/20 border-yellow-400/30';
      case 'off_track': return 'text-red-400 bg-red-500/20 border-red-400/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'financial': return DollarSign;
      case 'operational': return Gauge;
      case 'strategic': return Target;
      case 'team': return Users;
      default: return BarChart3;
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-emerald-500/10 border-emerald-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/20 rounded-lg border border-emerald-500/30">
            <Target className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">KPI Metrics</h3>
            <p className="text-sm text-gray-400">{metrics.length} key performance indicators</p>
          </div>
        </div>

        <div className="space-y-4">
          {metrics.map((metric, index) => {
            const Icon = getCategoryIcon(metric.category);
            const progress = (metric.current_value / metric.target_value) * 100;
            const TrendIcon = metric.trend.direction === 'up' ? TrendingUp :
                            metric.trend.direction === 'down' ? TrendingDown : Minus;

            return (
              <div key={index} className="p-4 bg-gray-800/50 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-500/20 rounded-lg">
                      <Icon className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div>
                      <h4 className="font-medium text-white">{metric.name}</h4>
                      <p className="text-xs text-gray-400 capitalize">{metric.category}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(metric.status)}>
                      {metric.status.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-2xl font-bold text-emerald-400">
                    {metric.current_value.toLocaleString()}{metric.unit}
                  </div>
                  <div className="text-right text-sm">
                    <div className="text-gray-300">
                      Target: {metric.target_value.toLocaleString()}{metric.unit}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-gray-400">
                      <TrendIcon className="w-3 h-3" />
                      <span>{metric.trend.percentage}% {metric.trend.period}</span>
                    </div>
                  </div>
                </div>

                <ProgressBar
                  value={Math.min(progress, 100)}
                  variant="analytics"
                  label={`${Math.round(progress)}% of target`}
                  size="sm"
                />

                <div className="text-xs text-gray-500">
                  Last updated: {new Date(metric.last_updated).toLocaleDateString()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
};

// Trend Analysis Chart
export const TrendAnalysisCard: React.FC<{
  data: TrendAnalysis;
  className?: string;
}> = ({ data, className }) => {
  return (
    <Card className={cn(
      "p-6 bg-emerald-500/10 border-emerald-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/20 rounded-lg border border-emerald-500/30">
            <LineChart className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">{data.metric} Trends</h3>
            <p className="text-sm text-gray-400">{data.time_period}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-emerald-500/10 rounded-lg text-center">
            <div className="text-2xl font-bold text-emerald-400 mb-1">
              {data.prediction.next_period.toLocaleString()}
            </div>
            <div className="text-sm text-gray-400">Next Period Forecast</div>
            <div className="text-xs text-gray-500 mt-1">
              {data.prediction.confidence}% confidence
            </div>
          </div>
          <div className="space-y-2">
            <h5 className="text-sm font-medium text-gray-300">Key Factors</h5>
            {data.prediction.factors.slice(0, 3).map((factor, index) => (
              <div key={index} className="text-xs text-gray-400 flex items-start gap-1">
                <div className="w-1 h-1 bg-emerald-400 rounded-full mt-1.5 flex-shrink-0" />
                <span>{factor}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300">Recent Data Points</h4>
          <div className="space-y-2">
            {data.data_points.slice(-5).map((point, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                <span className="text-sm text-gray-300">{point.period}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-emerald-400 font-medium">
                    {point.value.toLocaleString()}
                  </span>
                  {point.target && (
                    <span className="text-xs text-gray-500">
                      (Target: {point.target.toLocaleString()})
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Key Insights</h4>
          {data.insights.slice(0, 3).map((insight, index) => (
            <div key={index} className="flex items-start gap-2 p-2 bg-emerald-500/10 rounded">
              <Brain className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-gray-300">{insight}</span>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Recommendations</h4>
          {data.recommendations.slice(0, 3).map((rec, index) => (
            <div key={index} className="flex items-start gap-2 text-sm">
              <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0 mt-0.5" />
              <span className="text-gray-300">{rec}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

// Strategic Insight Panel
export const StrategicInsightCard: React.FC<{
  insights: StrategicInsight[];
  className?: string;
}> = ({ insights, className }) => {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'opportunity': return Zap;
      case 'risk': return Shield;
      case 'optimization': return Target;
      case 'innovation': return Brain;
      default: return Eye;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-400 bg-red-500/20 border-red-400/30';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-400/30';
      case 'low': return 'text-green-400 bg-green-500/20 border-green-400/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-emerald-500/10 border-emerald-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/20 rounded-lg border border-emerald-500/30">
            <Brain className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Strategic Insights</h3>
            <p className="text-sm text-gray-400">{insights.length} AI-generated insights</p>
          </div>
        </div>

        <div className="space-y-4">
          {insights.slice(0, 3).map((insight, index) => {
            const Icon = getCategoryIcon(insight.category);
            
            return (
              <div key={index} className="p-4 bg-gray-800/50 rounded-lg space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="p-2 bg-emerald-500/20 rounded-lg">
                      <Icon className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-white">{insight.title}</h4>
                      <p className="text-sm text-gray-400 mt-1 capitalize">{insight.category}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge className={getPriorityColor(insight.priority)}>
                      {insight.priority}
                    </Badge>
                  </div>
                </div>

                <p className="text-sm text-gray-300">{insight.description}</p>

                <div className="grid grid-cols-2 gap-4">
                  <MetricCard
                    title="Impact Score"
                    value={`${insight.impact_score}/100`}
                    variant="analytics"
                    size="sm"
                  />
                  <MetricCard
                    title="Confidence"
                    value={`${insight.confidence}%`}
                    variant="analytics"
                    size="sm"
                  />
                </div>

                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-gray-300">Supporting Data</h5>
                  <div className="grid grid-cols-2 gap-2">
                    {insight.supporting_data.slice(0, 4).map((data, idx) => (
                      <div key={idx} className="text-xs text-gray-400">
                        <span className="text-gray-500">{data.metric}:</span>
                        <span className="text-emerald-400 ml-1">{data.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-gray-300">Recommended Actions</h5>
                  {insight.recommended_actions.slice(0, 3).map((action, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-300">{action}</span>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Timeline: {insight.timeline}</span>
                  <span>Stakeholders: {insight.stakeholders.length}</span>
                </div>
              </div>
            );
          })}
        </div>

        <Button size="sm" variant="outline" className="w-full">
          <Eye className="w-4 h-4 mr-2" />
          View All Insights
        </Button>
      </div>
    </Card>
  );
};

// Executive Summary Card
export const ExecutiveSummaryCard: React.FC<{
  summary: ExecutiveSummary;
  className?: string;
}> = ({ summary, className }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'positive': return 'text-green-400';
      case 'negative': return 'text-red-400';
      case 'neutral': return 'text-gray-400';
      case 'on_track': return 'text-green-400';
      case 'delayed': return 'text-yellow-400';
      case 'completed': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  const getRiskOpportunityIcon = (type: string) => {
    return type === 'risk' ? AlertTriangle : Zap;
  };

  return (
    <Card className={cn(
      "p-6 bg-emerald-500/10 border-emerald-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/20 rounded-lg border border-emerald-500/30">
            <Award className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Executive Summary</h3>
            <p className="text-sm text-gray-400">{summary.period}</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-gray-300 mb-2">Key Achievements</h4>
            <div className="space-y-2">
              {summary.key_achievements.map((achievement, index) => (
                <div key={index} className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-300">{achievement}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-300 mb-2">Critical Metrics</h4>
            <div className="grid grid-cols-2 gap-2">
              {summary.critical_metrics.map((metric, index) => (
                <div key={index} className="p-2 bg-gray-800/50 rounded flex items-center justify-between">
                  <span className="text-sm text-gray-300">{metric.metric}</span>
                  <span className={cn("text-sm font-medium", getStatusColor(metric.status))}>
                    {metric.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-300 mb-2">Strategic Priorities</h4>
            <div className="space-y-3">
              {summary.strategic_priorities.map((priority, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">{priority.priority}</span>
                    <Badge className={getStatusColor(priority.status)}>
                      {priority.status.replace('_', ' ')}
                    </Badge>
                  </div>
                  <ProgressBar
                    value={priority.progress}
                    variant="analytics"
                    size="sm"
                    showPercentage={true}
                  />
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-300 mb-2">Risks & Opportunities</h4>
            <div className="space-y-2">
              {summary.risks_and_opportunities.map((item, index) => {
                const Icon = getRiskOpportunityIcon(item.type);
                const color = item.type === 'risk' ? 'text-red-400' : 'text-green-400';
                
                return (
                  <div key={index} className="flex items-start gap-2 p-2 bg-gray-800/50 rounded">
                    <Icon className={cn("w-4 h-4 flex-shrink-0 mt-0.5", color)} />
                    <div className="flex-1">
                      <span className="text-sm text-gray-300">{item.description}</span>
                      <Badge variant="outline" className="ml-2 text-xs">
                        {item.impact} impact
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-300 mb-2">Next Quarter Focus</h4>
            <div className="space-y-1">
              {summary.next_quarter_focus.map((focus, index) => (
                <div key={index} className="flex items-center gap-2 text-sm">
                  <Target className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                  <span className="text-gray-300">{focus}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <Button size="sm" variant="outline" className="flex-1">
            <Download className="w-4 h-4 mr-2" />
            Export Report
          </Button>
          <Button size="sm" variant="outline">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};

// Forecasting Visualization
export const ForecastingVisualizationCard: React.FC<{
  data: ForecastingVisualization;
  className?: string;
}> = ({ data, className }) => {
  return (
    <Card className={cn(
      "p-6 bg-emerald-500/10 border-emerald-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/20 rounded-lg border border-emerald-500/30">
            <TrendingUp className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">{data.metric} Forecast</h3>
            <p className="text-sm text-gray-400">Predictive analysis with {data.model_accuracy}% accuracy</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <MetricCard
            title="Model Accuracy"
            value={`${data.model_accuracy}%`}
            variant="analytics"
            size="sm"
            icon={Target}
          />
          <MetricCard
            title="Data Points"
            value={data.historical_data.length + data.forecast_data.length}
            variant="analytics"
            size="sm"
            icon={BarChart3}
          />
        </div>

        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300">Recent Historical Data</h4>
          <div className="space-y-1">
            {data.historical_data.slice(-3).map((point, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                <span className="text-sm text-gray-300">{point.period}</span>
                <span className="text-sm text-emerald-400 font-medium">
                  {point.actual.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300">Forecast Data</h4>
          <div className="space-y-2">
            {data.forecast_data.slice(0, 3).map((point, index) => (
              <div key={index} className="p-2 bg-emerald-500/10 rounded">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-300">{point.period}</span>
                  <span className="text-sm text-emerald-400 font-medium">
                    {point.predicted.toLocaleString()}
                  </span>
                </div>
                <div className="text-xs text-gray-500">
                  Range: {point.confidence_lower.toLocaleString()} - {point.confidence_upper.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Key Scenarios</h4>
          {data.scenarios.map((scenario, index) => (
            <div key={index} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
              <span className="text-sm text-gray-300">{scenario.name}</span>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-400">{scenario.probability}%</span>
                <span className="text-emerald-400">Impact: {scenario.impact}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Key Assumptions</h4>
          {data.assumptions.slice(0, 3).map((assumption, index) => (
            <div key={index} className="flex items-start gap-2 text-sm">
              <div className="w-1 h-1 bg-emerald-400 rounded-full mt-2 flex-shrink-0" />
              <span className="text-gray-400">{assumption}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};