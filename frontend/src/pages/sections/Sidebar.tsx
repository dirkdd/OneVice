import React from "react";
import { Button } from "@/components/ui/button";
import { Plus, MessageCircle, FileText, Users, Lightbulb, PieChart, User, Menu, Loader2 } from "lucide-react";
import { DashboardContext } from "../Dashboard";
import { useRecentConversations } from "@/hooks/useViewData";

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  currentContext: DashboardContext;
  onContextChange: (context: DashboardContext) => void;
}

export const Sidebar = ({ collapsed, onToggleCollapse, currentContext, onContextChange }: SidebarProps): JSX.Element => {
  const { data: recentConversations, isLoading: conversationsLoading, error: conversationsError } = useRecentConversations();
  
  const quickActions = [
    { 
      icon: MessageCircle, 
      label: "Pre-Call Brief", 
      subtitle: "Generate client intelligence",
      context: "pre-call-brief" as DashboardContext
    },
    { 
      icon: FileText, 
      label: "Case Study", 
      subtitle: "Quickly access portfolio",
      context: "case-study" as DashboardContext
    },
    { 
      icon: Users, 
      label: "Talent", 
      subtitle: "Discovery Portfolio",
      context: "talent-discovery" as DashboardContext
    },
    { 
      icon: Lightbulb, 
      label: "Bid Proposal", 
      subtitle: "Generate Proposals",
      context: "bid-proposal" as DashboardContext
    },
  ];

  const formatTime = (timestamp: string) => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) {
      return `${diffInMinutes} minutes ago`;
    } else if (diffInMinutes < 1440) {
      const hours = Math.floor(diffInMinutes / 60);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      const days = Math.floor(diffInMinutes / 1440);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    }
  };

  return (
    <div className={`${collapsed ? 'w-16' : 'w-[300px]'} bg-[#0a0a0b] border-r border-gray-800 flex flex-col transition-all duration-300`}>
      {/* Sidebar Header */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onToggleCollapse}
            className="hover:bg-gray-800"
          >
            <Menu className="w-5 h-5" />
          </Button>
        </div>
        
        {!collapsed && (
          <Button 
            variant="gold"
            className="w-full rounded-lg"
            onClick={() => onContextChange("home")}
          >
            <Plus className="w-4 h-4 mr-2" />
            NEW CONVERSATION
          </Button>
        )}
        
        {collapsed && (
          <Button 
            variant="ghost" 
            size="icon"
            className="w-full p-3 rounded-lg hover:bg-gray-800/50"
            onClick={() => onContextChange("home")}
          >
            <Plus className="w-5 h-5 text-gray-400" />
          </Button>
        )}
      </div>

      {/* Quick Actions */}
      <div className="px-6 mb-6">
        {!collapsed && <h3 className="text-sm font-medium text-gray-400 mb-4">QUICK ACTIONS</h3>}
        <div className="space-y-3">
          {quickActions.map((action, index) => (
            <div
              key={index}
              className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'} p-3 rounded-lg hover:bg-gray-800/50 cursor-pointer group ${
                currentContext === action.context ? 'bg-gray-800/70' : ''
              }`}
              onClick={() => onContextChange(action.context)}
            >
              <action.icon className={`w-5 h-5 ${collapsed ? 'flex-shrink-0' : ''} ${
                currentContext === action.context ? 'text-white' : 'text-gray-400 group-hover:text-white'
              }`} />
              {!collapsed && (
                <div>
                  <div className="text-sm font-medium text-white">{action.label}</div>
                  <div className="text-xs text-gray-400">{action.subtitle}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Conversations */}
      {!collapsed && (
        <div className="px-6 flex-1 overflow-y-auto">
          <h3 className="text-sm font-medium text-gray-400 mb-4">RECENT CONVERSATIONS</h3>
          
          {conversationsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            </div>
          ) : conversationsError ? (
            <div className="text-center py-4">
              <p className="text-xs text-red-400 mb-2">Failed to load conversations</p>
              <p className="text-xs text-gray-500">{conversationsError}</p>
            </div>
          ) : recentConversations && recentConversations.length > 0 ? (
            <div className="space-y-3">
              {recentConversations.map((conversation, index) => (
                <div
                  key={conversation.id || index}
                  className="p-3 rounded-lg hover:bg-gray-800/50 cursor-pointer"
                  onClick={() => {
                    // TODO: Load conversation history and set context
                    if (conversation.context) {
                      onContextChange(conversation.context);
                    }
                  }}
                >
                  <div className="text-sm font-medium text-white mb-1">{conversation.title}</div>
                  <div className="text-xs text-gray-400 mb-2 line-clamp-2">
                    {conversation.subtitle || conversation.last_message_preview || `${conversation.message_count} messages`}
                  </div>
                  <div className="text-xs text-gray-500">{formatTime(conversation.updated_at)}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <MessageCircle className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              <p className="text-xs text-gray-500">No recent conversations</p>
            </div>
          )}
        </div>
      )}

      {/* Bottom Status */}
      <div className="p-6 border-t border-gray-800">
        {!collapsed ? (
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>SYSTEM STATUS</span>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>ONLINE</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          </div>
        )}
      </div>
    </div>
  );
};