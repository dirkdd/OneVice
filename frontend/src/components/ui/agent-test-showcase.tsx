import React, { useState } from "react";
import { Card } from "./card";
import { Button } from "./button";
import { Separator } from "./separator";
import { AgentType, AgentMetadata } from "@/lib/api/types";
import { AgentBadge, SalesAgentBadge, TalentAgentBadge, AnalyticsAgentBadge } from "./agent-badge";
import { 
  AgentMessage, 
  SalesMessage, 
  TalentMessage, 
  AnalyticsMessage 
} from "./agent-message";
import { 
  AgentProcessingIndicator,
  SalesProcessingIndicator,
  TalentProcessingIndicator,
  AnalyticsProcessingIndicator
} from "./agent-processing-indicator";

export const AgentTestShowcase: React.FC = () => {
  const [showProcessing, setShowProcessing] = useState(false);

  const sampleMetadata: AgentMetadata = {
    agent_type: AgentType.SALES,
    processing_time: "1.2s",
    confidence: "high",
    sources: ["Client Database", "Market Analysis", "Revenue Reports"],
    query_complexity: "moderate"
  };

  const sampleMessages = {
    sales: "Based on your client history and current market trends, I recommend focusing on the documentary series opportunity with StreamCorp. Their budget range of $2.5M-3.2M aligns perfectly with your production capabilities, and they have a 95% renewal rate for successful partnerships. The project timeline of 8 months allows for optimal resource allocation while maintaining quality standards.",
    talent: "I've identified 3 ideal directors for your documentary project: Maria Rodriguez (87% success rate, $15K/episode), James Chen (92% success rate, $18K/episode), and Sarah Williams (89% success rate, $16K/episode). All are available for your Q2 production window and have proven track records in documentary storytelling. Maria Rodriguez offers the best budget efficiency while maintaining high quality.",
    analytics: "Your Q4 performance shows strong momentum: 23% revenue growth, 89% client retention, and 15% improvement in project delivery times. Top performing segments include documentary production (35% of revenue) and commercial work (28% of revenue). Budget efficiency increased by 12%, with talent costs optimized to 68% of total budget vs. industry average of 72%."
  };

  return (
    <div className="p-6 space-y-8 bg-gray-900 min-h-screen">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-white">OneVice Agent System Showcase</h1>
          <p className="text-gray-400">Interactive demonstration of AI agent response indicators</p>
        </div>

        {/* Agent Badges Section */}
        <Card className="bg-gray-800 border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Agent Badges</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">Standard Badges</h3>
              <div className="flex flex-wrap gap-3">
                <SalesAgentBadge size="sm" />
                <TalentAgentBadge size="default" />
                <AnalyticsAgentBadge size="lg" />
              </div>
            </div>
            
            <Separator className="bg-gray-700" />
            
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">With Confidence & Processing Time</h3>
              <div className="flex flex-wrap gap-3">
                <AgentBadge 
                  agent={AgentType.SALES} 
                  metadata={sampleMetadata}
                  showConfidence={true}
                  showProcessingTime={true}
                />
                <AgentBadge 
                  agent={AgentType.TALENT} 
                  metadata={{...sampleMetadata, agent_type: AgentType.TALENT, confidence: "medium"}}
                  showConfidence={true}
                  showProcessingTime={true}
                />
                <AgentBadge 
                  agent={AgentType.ANALYTICS} 
                  metadata={{...sampleMetadata, agent_type: AgentType.ANALYTICS, confidence: "low"}}
                  showConfidence={true}
                  showProcessingTime={true}
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Processing Indicators Section */}
        <Card className="bg-gray-800 border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Processing Indicators</h2>
            <Button
              onClick={() => setShowProcessing(!showProcessing)}
              variant={showProcessing ? "destructive" : "default"}
              size="sm"
            >
              {showProcessing ? "Hide" : "Show"} Processing
            </Button>
          </div>
          
          {showProcessing && (
            <div className="space-y-4">
              <SalesProcessingIndicator 
                stage="analyzing"
                metadata={sampleMetadata}
              />
              <TalentProcessingIndicator 
                stage="searching"
                metadata={{...sampleMetadata, agent_type: AgentType.TALENT, query_complexity: "complex"}}
              />
              <AnalyticsProcessingIndicator 
                stage="generating"
                metadata={{...sampleMetadata, agent_type: AgentType.ANALYTICS, query_complexity: "simple"}}
              />
            </div>
          )}
        </Card>

        {/* Agent Messages Section */}
        <Card className="bg-gray-800 border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Agent Messages</h2>
          <div className="space-y-6">
            {/* User Message Example */}
            <AgentMessage
              message={{
                type: 'user_message',
                content: "What's the best opportunity for our Q2 production schedule?",
                timestamp: new Date().toISOString()
              }}
            />
            
            {/* Sales Agent Response */}
            <SalesMessage
              content={sampleMessages.sales}
              metadata={sampleMetadata}
            />
            
            {/* User Message Example */}
            <AgentMessage
              message={{
                type: 'user_message',
                content: "Who would be the best director for this documentary project?",
                timestamp: new Date().toISOString()
              }}
            />
            
            {/* Talent Agent Response */}
            <TalentMessage
              content={sampleMessages.talent}
              metadata={{
                ...sampleMetadata,
                agent_type: AgentType.TALENT,
                processing_time: "2.1s",
                confidence: "high",
                sources: ["Talent Database", "Project History", "Availability Calendar"]
              }}
            />
            
            {/* User Message Example */}
            <AgentMessage
              message={{
                type: 'user_message',
                content: "How is our overall performance this quarter?",
                timestamp: new Date().toISOString()
              }}
            />
            
            {/* Analytics Agent Response */}
            <AnalyticsMessage
              content={sampleMessages.analytics}
              metadata={{
                ...sampleMetadata,
                agent_type: AgentType.ANALYTICS,
                processing_time: "0.8s",
                confidence: "high",
                sources: ["Performance Dashboard", "Financial Reports", "Client Feedback"],
                query_complexity: "complex"
              }}
            />
          </div>
        </Card>

        {/* Integration Notes */}
        <Card className="bg-gray-800 border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Integration Notes</h2>
          <div className="space-y-3 text-sm text-gray-300">
            <p>• Agent badges automatically show with appropriate colors and icons</p>
            <p>• Processing indicators cycle through agent-specific messages</p>
            <p>• Messages display with agent context, confidence levels, and processing times</p>
            <p>• All components are accessible and follow OneVice design system</p>
            <p>• Backend should send messages with <code className="bg-gray-700 px-1 rounded">agent</code> and <code className="bg-gray-700 px-1 rounded">agent_metadata</code> fields</p>
          </div>
        </Card>
      </div>
    </div>
  );
};