import React from "react";
import { Badge } from "@/components/ui/badge";
import { DashboardContext } from "@/pages/Dashboard";

interface CollapsedSummaryProps {
  context: DashboardContext;
  onClick: () => void;
  className?: string;
}

const contextLabels: Record<DashboardContext, string> = {
  home: "Dashboard Overview",
  "pre-call-brief": "Pre-Call Brief Generator",
  "case-study": "Case Study Portfolio",
  "talent-discovery": "Talent Discovery",
  "bid-proposal": "Bidding Proposal Generator",
};

export const CollapsedSummary: React.FC<CollapsedSummaryProps> = ({
  context,
  onClick,
  className = ""
}) => {
  return (
    <div 
      className={`bg-gray-800/30 backdrop-blur-sm border-b border-gray-700/50 p-4 cursor-pointer 
                  hover:bg-gray-800/40 transition-all duration-300 h-full flex items-center ${className}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between max-w-6xl mx-auto">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-white">
            {contextLabels[context]}
          </span>
          <Badge 
            variant="outline" 
            className="text-xs border-gray-600/50 text-gray-400 bg-gray-700/30"
          >
            Collapsed • Click to expand
          </Badge>
        </div>
        
        {/* Quick stats when collapsed */}
        <div className="flex items-center gap-6 text-xs text-gray-500">
          <span>8 Active Projects</span>
          <span>•</span>
          <span>92% Efficiency</span>
          <span>•</span>
          <span>Last updated 2m ago</span>
        </div>
      </div>
    </div>
  );
};