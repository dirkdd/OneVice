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
  DollarSign,
  TrendingUp,
  Target,
  Calendar,
  Users,
  Briefcase,
  Phone,
  Mail,
  Star,
  Clock,
  Building,
  AlertCircle,
  CheckCircle,
  Calculator,
  PieChart,
  BarChart3,
  ExternalLink,
  Filter
} from "lucide-react";

// Sales-specific Types
export interface LeadScoringData {
  score: number;
  factors: Array<{
    factor: string;
    impact: 'high' | 'medium' | 'low';
    value: string;
    points: number;
  }>;
  recommendation: string;
  confidence: 'high' | 'medium' | 'low';
}

export interface RevenueProjection {
  period: string;
  projected: number;
  actual?: number;
  confidence_interval: {
    min: number;
    max: number;
  };
  factors: string[];
}

export interface ClientAnalysis {
  client: {
    id: string;
    name: string;
    type: string;
    logo?: string;
  };
  relationship_score: number;
  total_projects: number;
  total_revenue: number;
  last_interaction: string;
  next_opportunity?: {
    project: string;
    value: number;
    probability: number;
    timeline: string;
  };
  health_status: 'excellent' | 'good' | 'at_risk' | 'critical';
}

export interface MarketOpportunity {
  id: string;
  title: string;
  market_size: number;
  competition_level: 'low' | 'medium' | 'high';
  timeline: string;
  requirements: string[];
  success_probability: number;
  estimated_revenue: number;
}

export interface BudgetBreakdown {
  total_budget: number;
  categories: Array<{
    category: string;
    amount: number;
    percentage: number;
    status: 'on_track' | 'over_budget' | 'under_budget';
  }>;
  utilization_rate: number;
  remaining_budget: number;
}

export interface ROICalculation {
  investment: number;
  expected_return: number;
  roi_percentage: number;
  payback_period: number;
  risk_level: 'low' | 'medium' | 'high';
  assumptions: string[];
  sensitivity_analysis?: Array<{
    scenario: string;
    roi: number;
    probability: number;
  }>;
}

// Sales Agent Components

// Lead Scoring Display
export const LeadScoringCard: React.FC<{
  data: LeadScoringData;
  className?: string;
}> = ({ data, className }) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'bg-red-500/20 text-red-400 border-red-400/30';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-400/30';
      case 'low': return 'bg-green-500/20 text-green-400 border-green-400/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-400/30';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-blue-500/10 border-blue-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
              <Target className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Lead Scoring</h3>
              <p className="text-sm text-gray-400">AI-powered lead assessment</p>
            </div>
          </div>
          
          <div className="text-right">
            <div className={cn("text-4xl font-bold", getScoreColor(data.score))}>
              {data.score}
            </div>
            <div className="text-sm text-gray-400">out of 100</div>
          </div>
        </div>

        <ProgressBar
          value={data.score}
          variant="sales"
          label="Lead Score"
          size="lg"
        />

        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Scoring Factors
          </h4>
          {data.factors.map((factor, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className={getImpactColor(factor.impact)}>
                  {factor.impact}
                </Badge>
                <span className="text-sm text-gray-300">{factor.factor}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">{factor.value}</span>
                <span className="text-sm font-medium text-blue-400">+{factor.points}pts</span>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <h5 className="text-sm font-medium text-white mb-1">Recommendation</h5>
              <p className="text-sm text-gray-300">{data.recommendation}</p>
              <Badge variant="outline" className="mt-2 text-xs">
                {data.confidence} confidence
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

// Revenue Projections Chart
export const RevenueProjectionCard: React.FC<{
  projections: RevenueProjection[];
  className?: string;
}> = ({ projections, className }) => {
  return (
    <Card className={cn(
      "p-6 bg-blue-500/10 border-blue-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
            <TrendingUp className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Revenue Projections</h3>
            <p className="text-sm text-gray-400">Predictive revenue analysis</p>
          </div>
        </div>

        <div className="space-y-4">
          {projections.map((projection, index) => (
            <div key={index} className="p-4 bg-gray-800/50 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-white">{projection.period}</h4>
                <div className="text-right">
                  <div className="text-lg font-bold text-blue-400">
                    ${projection.projected.toLocaleString()}
                  </div>
                  {projection.actual && (
                    <div className="text-xs text-gray-400">
                      Actual: ${projection.actual.toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>
                  Range: ${projection.confidence_interval.min.toLocaleString()} - 
                  ${projection.confidence_interval.max.toLocaleString()}
                </span>
              </div>
              
              <div className="flex flex-wrap gap-1">
                {projection.factors.map((factor, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {factor}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

// Client Analysis Card
export const ClientAnalysisCard: React.FC<{
  data: ClientAnalysis;
  className?: string;
}> = ({ data, className }) => {
  const getHealthColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'text-green-400 bg-green-500/20 border-green-400/30';
      case 'good': return 'text-blue-400 bg-blue-500/20 border-blue-400/30';
      case 'at_risk': return 'text-yellow-400 bg-yellow-500/20 border-yellow-400/30';
      case 'critical': return 'text-red-400 bg-red-500/20 border-red-400/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-blue-500/10 border-blue-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
              <Building className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">{data.client.name}</h3>
              <p className="text-sm text-gray-400">{data.client.type}</p>
            </div>
          </div>
          
          <Badge className={getHealthColor(data.health_status)}>
            {data.health_status.replace('_', ' ')}
          </Badge>
        </div>

        <QuickStats
          variant="sales"
          columns={3}
          stats={[
            {
              label: "Relationship Score",
              value: `${data.relationship_score}/100`,
              icon: Star
            },
            {
              label: "Total Projects",
              value: data.total_projects,
              icon: Briefcase
            },
            {
              label: "Total Revenue",
              value: `$${data.total_revenue.toLocaleString()}`,
              icon: DollarSign
            }
          ]}
        />

        <div className="p-4 bg-gray-800/50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-300">Last Interaction</span>
          </div>
          <p className="text-sm text-white">{new Date(data.last_interaction).toLocaleDateString()}</p>
        </div>

        {data.next_opportunity && (
          <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
            <div className="flex items-start gap-3">
              <Target className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h5 className="text-sm font-medium text-white mb-1">Next Opportunity</h5>
                <p className="text-sm text-gray-300 mb-2">{data.next_opportunity.project}</p>
                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <span>Value: ${data.next_opportunity.value.toLocaleString()}</span>
                  <span>Probability: {data.next_opportunity.probability}%</span>
                  <span>Timeline: {data.next_opportunity.timeline}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <Button size="sm" variant="outline" className="flex-1">
            <Phone className="w-4 h-4 mr-2" />
            Contact
          </Button>
          <Button size="sm" variant="outline" className="flex-1">
            <Mail className="w-4 h-4 mr-2" />
            Email
          </Button>
          <Button size="sm" variant="outline">
            <ExternalLink className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};

// Market Opportunity Indicator
export const MarketOpportunityCard: React.FC<{
  opportunity: MarketOpportunity;
  className?: string;
}> = ({ opportunity, className }) => {
  const getCompetitionColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-400 bg-green-500/20';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20';
      case 'high': return 'text-red-400 bg-red-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-blue-500/10 border-blue-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
            <Target className="w-6 h-6 text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white">{opportunity.title}</h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={getCompetitionColor(opportunity.competition_level)}>
                {opportunity.competition_level} competition
              </Badge>
              <span className="text-sm text-gray-400">{opportunity.timeline}</span>
            </div>
          </div>
        </div>

        <QuickStats
          variant="sales"
          columns={3}
          stats={[
            {
              label: "Market Size",
              value: `$${opportunity.market_size.toLocaleString()}`,
              icon: PieChart
            },
            {
              label: "Success Rate",
              value: `${opportunity.success_probability}%`,
              icon: TrendingUp
            },
            {
              label: "Est. Revenue",
              value: `$${opportunity.estimated_revenue.toLocaleString()}`,
              icon: DollarSign
            }
          ]}
        />

        <ProgressBar
          value={opportunity.success_probability}
          variant="sales"
          label="Success Probability"
        />

        <div className="space-y-2">
          <h5 className="text-sm font-medium text-gray-300">Requirements</h5>
          <div className="space-y-1">
            {opportunity.requirements.map((req, index) => (
              <div key={index} className="flex items-center gap-2 text-sm">
                <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">{req}</span>
              </div>
            ))}
          </div>
        </div>

        <Button className="w-full" size="sm">
          <Target className="w-4 h-4 mr-2" />
          Pursue Opportunity
        </Button>
      </div>
    </Card>
  );
};

// Budget Breakdown Component
export const BudgetBreakdownCard: React.FC<{
  data: BudgetBreakdown;
  className?: string;
}> = ({ data, className }) => {
  return (
    <Card className={cn(
      "p-6 bg-blue-500/10 border-blue-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
            <PieChart className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Budget Breakdown</h3>
            <p className="text-sm text-gray-400">Total: ${data.total_budget.toLocaleString()}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <MetricCard
            title="Utilization Rate"
            value={`${data.utilization_rate}%`}
            variant="sales"
            size="sm"
            icon={BarChart3}
          />
          <MetricCard
            title="Remaining Budget"
            value={`$${data.remaining_budget.toLocaleString()}`}
            variant="sales"
            size="sm"
            icon={DollarSign}
          />
        </div>

        <div className="space-y-3">
          <h5 className="text-sm font-medium text-gray-300">Categories</h5>
          {data.categories.map((category, index) => (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-300">{category.category}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-blue-400 font-medium">
                    ${category.amount.toLocaleString()}
                  </span>
                  <Badge variant="outline" className={cn(
                    "text-xs",
                    category.status === 'on_track' ? 'text-green-400 border-green-400/30' :
                    category.status === 'over_budget' ? 'text-red-400 border-red-400/30' :
                    'text-yellow-400 border-yellow-400/30'
                  )}>
                    {category.status.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
              <ProgressBar
                value={category.percentage}
                variant="sales"
                size="sm"
              />
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

// ROI Calculator Component
export const ROICalculatorCard: React.FC<{
  data: ROICalculation;
  className?: string;
}> = ({ data, className }) => {
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-400 bg-green-500/20 border-green-400/30';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-400/30';
      case 'high': return 'text-red-400 bg-red-500/20 border-red-400/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-400/30';
    }
  };

  return (
    <Card className={cn(
      "p-6 bg-blue-500/10 border-blue-500/30 backdrop-blur-sm",
      className
    )}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-500/20 rounded-lg border border-blue-500/30">
            <Calculator className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">ROI Analysis</h3>
            <p className="text-sm text-gray-400">Return on Investment calculation</p>
          </div>
        </div>

        <QuickStats
          variant="sales"
          columns={2}
          stats={[
            {
              label: "Investment",
              value: `$${data.investment.toLocaleString()}`,
              icon: DollarSign
            },
            {
              label: "Expected Return",
              value: `$${data.expected_return.toLocaleString()}`,
              icon: TrendingUp
            }
          ]}
        />

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-blue-500/10 rounded-lg text-center">
            <div className="text-2xl font-bold text-blue-400 mb-1">
              {data.roi_percentage}%
            </div>
            <div className="text-sm text-gray-400">ROI Percentage</div>
          </div>
          <div className="p-4 bg-blue-500/10 rounded-lg text-center">
            <div className="text-2xl font-bold text-blue-400 mb-1">
              {data.payback_period}
            </div>
            <div className="text-sm text-gray-400">Months Payback</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-300">Risk Level:</span>
          <Badge className={getRiskColor(data.risk_level)}>
            {data.risk_level} risk
          </Badge>
        </div>

        {data.sensitivity_analysis && (
          <div className="space-y-2">
            <h5 className="text-sm font-medium text-gray-300">Sensitivity Analysis</h5>
            {data.sensitivity_analysis.map((scenario, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-800/30 rounded">
                <span className="text-sm text-gray-300">{scenario.scenario}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-blue-400">{scenario.roi}%</span>
                  <span className="text-xs text-gray-500">({scenario.probability}%)</span>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="space-y-2">
          <h5 className="text-sm font-medium text-gray-300">Key Assumptions</h5>
          <div className="space-y-1">
            {data.assumptions.map((assumption, index) => (
              <div key={index} className="flex items-start gap-2 text-sm">
                <div className="w-1 h-1 bg-blue-400 rounded-full mt-2 flex-shrink-0" />
                <span className="text-gray-400">{assumption}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};