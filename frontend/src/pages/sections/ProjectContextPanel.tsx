import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { X, User, Clock, DollarSign, AlertTriangle } from "lucide-react";
import { DashboardContext } from "../Dashboard";

interface ProjectContextPanelProps {
  context: DashboardContext;
  onClose: () => void;
}

export const ProjectContextPanel = ({ context, onClose }: ProjectContextPanelProps): JSX.Element => {
  const renderProjectContext = () => {
    switch (context) {
      case "bid-proposal":
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-white mb-2">CURRENT PROJECT</h3>
              <div className="bg-gray-800/50 rounded-lg p-4">
                <h4 className="font-medium text-white">Netflix Documentary</h4>
                <p className="text-sm text-gray-400">Sustainable Fashion Series</p>
                <div className="flex gap-2 mt-2">
                  <Badge className="bg-blue-500/20 text-blue-400">Budget: $3.2M</Badge>
                  <Badge className="bg-green-500/20 text-green-400">Timeline: 36 weeks</Badge>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">RECOMMENDED TALENT</h3>
              <div className="space-y-3">
                {[
                  { name: "Sarah Chen", role: "Senior Creative Director", status: "Available", efficiency: "95%" },
                  { name: "Marcus Rodriguez", role: "Creative Director", status: "2 weeks", efficiency: "92%" },
                  { name: "Alex Thompson", role: "Creative Director", status: "Available", efficiency: "90%" }
                ].map((talent, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-gray-300" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white">{talent.name}</div>
                        <div className="text-xs text-gray-400">{talent.role}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-white">{talent.efficiency}</div>
                      <div className="text-xs text-gray-400">{talent.status}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-2">RISK ASSESSMENT</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                  <span className="text-sm text-white">Budget Risk</span>
                  <Badge className="bg-red-500/20 text-red-400">LOW</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                  <span className="text-sm text-white">Timeline Risk</span>
                  <Badge className="bg-yellow-500/20 text-yellow-400">MEDIUM</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                  <span className="text-sm text-white">Talent Risk</span>
                  <Badge className="bg-red-500/20 text-red-400">LOW</Badge>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-white mb-2">PROJECT CONTEXT</h3>
              <p className="text-gray-400">Select a specific context to view relevant project details and recommendations.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="w-80 bg-[#0a0a0b] border-l border-gray-800 p-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-medium text-white">Project Context</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="w-5 h-5" />
        </Button>
      </div>
      
      {renderProjectContext()}
    </div>
  );
};