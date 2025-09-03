import React from "react";
import { cn } from "@/lib/utils";
import { Card } from "./card";
import { Badge } from "./badge";
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  DollarSign,
  Target,
  Calendar,
  Users,
  Award,
  BarChart3,
  PieChart,
  Activity,
  AlertCircle,
  CheckCircle,
  Clock
} from "lucide-react";

// Shared Types for Agent Visualizations
export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    value: string | number;
    label?: string;
  };
  icon?: React.ComponentType<any>;
  variant?: 'sales' | 'talent' | 'analytics';
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  variant?: 'sales' | 'talent' | 'analytics';
  size?: 'sm' | 'default' | 'lg';
  showPercentage?: boolean;
  className?: string;
}

export interface StatusIndicatorProps {
  status: 'success' | 'warning' | 'error' | 'info' | 'pending';
  label: string;
  description?: string;
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export interface DataListProps {
  items: Array<{
    label: string;
    value: string | number;
    status?: 'success' | 'warning' | 'error' | 'info';
    action?: React.ReactNode;
  }>;
  variant?: 'sales' | 'talent' | 'analytics';
  className?: string;
}

// Agent Color Schemes
const agentStyles = {
  sales: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    accent: 'bg-blue-500',
    glow: 'shadow-blue-500/20'
  },
  talent: {
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/30', 
    text: 'text-purple-400',
    accent: 'bg-purple-500',
    glow: 'shadow-purple-500/20'
  },
  analytics: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400', 
    accent: 'bg-emerald-500',
    glow: 'shadow-emerald-500/20'
  }
} as const;

// Metric Card Component
export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  variant = 'analytics',
  size = 'default',
  className
}) => {
  const styles = agentStyles[variant];
  
  const TrendIcon = trend?.direction === 'up' ? TrendingUp : 
                  trend?.direction === 'down' ? TrendingDown : Minus;

  const sizeClasses = {
    sm: 'p-3',
    default: 'p-4',
    lg: 'p-6'
  };

  const titleSizes = {
    sm: 'text-xs',
    default: 'text-sm',
    lg: 'text-base'
  };

  const valueSizes = {
    sm: 'text-lg',
    default: 'text-2xl',
    lg: 'text-3xl'
  };

  return (
    <Card className={cn(
      "relative overflow-hidden backdrop-blur-sm border transition-all duration-300",
      "hover:scale-105 hover:shadow-lg",
      styles.bg,
      styles.border,
      styles.glow,
      sizeClasses[size],
      className
    )}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {Icon && (
            <div className={cn(
              "p-2 rounded-lg",
              styles.bg,
              styles.border,
              "border"
            )}>
              <Icon className={cn("w-4 h-4", styles.text)} />
            </div>
          )}
          <h3 className={cn(
            "font-medium text-gray-300",
            titleSizes[size]
          )}>
            {title}
          </h3>
        </div>
        
        {trend && (
          <div className={cn(
            "flex items-center gap-1 px-2 py-1 rounded-full text-xs",
            trend.direction === 'up' ? 'bg-green-500/20 text-green-400' :
            trend.direction === 'down' ? 'bg-red-500/20 text-red-400' :
            'bg-gray-500/20 text-gray-400'
          )}>
            <TrendIcon className="w-3 h-3" />
            <span>{trend.value}</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <div className={cn(
          "font-bold",
          styles.text,
          valueSizes[size]
        )}>
          {value}
        </div>
        
        {subtitle && (
          <p className="text-xs text-gray-400">
            {subtitle}
          </p>
        )}
        
        {trend?.label && (
          <p className="text-xs text-gray-500">
            {trend.label}
          </p>
        )}
      </div>
    </Card>
  );
};

// Progress Bar Component
export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  variant = 'analytics',
  size = 'default',
  showPercentage = true,
  className
}) => {
  const styles = agentStyles[variant];
  const percentage = (value / max) * 100;
  
  const heights = {
    sm: 'h-1',
    default: 'h-2',
    lg: 'h-3'
  };

  return (
    <div className={cn("space-y-2", className)}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between text-sm">
          {label && (
            <span className="text-gray-300 font-medium">
              {label}
            </span>
          )}
          {showPercentage && (
            <span className={cn("font-bold", styles.text)}>
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      
      <div className={cn(
        "relative overflow-hidden rounded-full bg-gray-800",
        heights[size]
      )}>
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500 ease-out",
            styles.accent
          )}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
        <div className={cn(
          "absolute inset-0 rounded-full opacity-50",
          styles.glow
        )} />
      </div>
    </div>
  );
};

// Status Indicator Component
export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  description,
  size = 'default',
  className
}) => {
  const statusConfig = {
    success: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/20' },
    warning: { icon: AlertCircle, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
    error: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/20' },
    info: { icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    pending: { icon: Clock, color: 'text-gray-400', bg: 'bg-gray-500/20' }
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  const iconSizes = {
    sm: 'w-3 h-3',
    default: 'w-4 h-4', 
    lg: 'w-5 h-5'
  };

  const textSizes = {
    sm: 'text-xs',
    default: 'text-sm',
    lg: 'text-base'
  };

  return (
    <div className={cn(
      "flex items-center gap-3 p-3 rounded-lg border backdrop-blur-sm",
      config.bg,
      "border-current/20",
      className
    )}>
      <div className={cn(
        "flex items-center justify-center p-2 rounded-full",
        config.bg
      )}>
        <Icon className={cn(iconSizes[size], config.color)} />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className={cn(
          "font-medium text-white",
          textSizes[size]
        )}>
          {label}
        </div>
        {description && (
          <div className={cn(
            "text-gray-400 mt-1",
            size === 'sm' ? 'text-xs' : 'text-xs'
          )}>
            {description}
          </div>
        )}
      </div>
    </div>
  );
};

// Data List Component
export const DataList: React.FC<DataListProps> = ({
  items,
  variant = 'analytics',
  className
}) => {
  const styles = agentStyles[variant];

  return (
    <div className={cn(
      "space-y-2 p-4 rounded-lg border backdrop-blur-sm",
      styles.bg,
      styles.border,
      className
    )}>
      {items.map((item, index) => (
        <div key={index} className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="text-sm text-gray-300 truncate">
              {item.label}
            </span>
            {item.status && (
              <Badge variant="outline" className={cn(
                "text-xs",
                item.status === 'success' ? 'text-green-400 border-green-400/30' :
                item.status === 'warning' ? 'text-yellow-400 border-yellow-400/30' :
                item.status === 'error' ? 'text-red-400 border-red-400/30' :
                'text-blue-400 border-blue-400/30'
              )}>
                {item.status}
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={cn("text-sm font-medium", styles.text)}>
              {item.value}
            </span>
            {item.action && item.action}
          </div>
        </div>
      ))}
    </div>
  );
};

// Quick Stats Grid Component
export interface QuickStatsProps {
  stats: Array<{
    label: string;
    value: string | number;
    icon?: React.ComponentType<any>;
    trend?: { direction: 'up' | 'down' | 'neutral'; value: string };
  }>;
  variant?: 'sales' | 'talent' | 'analytics';
  columns?: 2 | 3 | 4;
  className?: string;
}

export const QuickStats: React.FC<QuickStatsProps> = ({
  stats,
  variant = 'analytics',
  columns = 3,
  className
}) => {
  const gridClasses = {
    2: 'grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-3',
    4: 'grid-cols-2 lg:grid-cols-4'
  };

  return (
    <div className={cn(
      "grid gap-4",
      gridClasses[columns],
      className
    )}>
      {stats.map((stat, index) => (
        <MetricCard
          key={index}
          title={stat.label}
          value={stat.value}
          icon={stat.icon}
          trend={stat.trend}
          variant={variant}
          size="sm"
        />
      ))}
    </div>
  );
};