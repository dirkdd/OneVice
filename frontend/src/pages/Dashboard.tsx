import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Header } from "./sections/Header";
import { AssistantBar } from "./sections/AssistantBar";
import { Sidebar } from "./sections/Sidebar";
import { MainContent } from "./sections/MainContent";
import { ChatInterface } from "./sections/ChatInterface";
import { ProjectContextPanel } from "./sections/ProjectContextPanel";
import { CollapsedSummary } from "@/components/ui/collapsed-summary";

export type DashboardContext = "home" | "pre-call-brief" | "case-study" | "talent-discovery" | "bid-proposal";

export const Dashboard = (): JSX.Element => {
  const [currentContext, setCurrentContext] = useState<DashboardContext>("home");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true); // Default to collapsed
  const [showProjectPanel, setShowProjectPanel] = useState(false);
  const [mainContentCollapsed, setMainContentCollapsed] = useState(false);

  // Auto-expand when context changes
  useEffect(() => {
    if (mainContentCollapsed) {
      setMainContentCollapsed(false);
    }
  }, [currentContext]);

  // Keyboard shortcut for toggle (Cmd/Ctrl + \)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
        e.preventDefault();
        setMainContentCollapsed(prev => !prev);
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0b] text-white overflow-hidden">
      {/* Top Header - Full Width */}
      <Header />
      
      {/* Body with Sidebar and Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar 
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          currentContext={currentContext}
          onContextChange={setCurrentContext}
        />
        
        {/* Main Content Side */}
        <div className="flex flex-col flex-1">
          {/* Assistant Identity Bar */}
          <AssistantBar context={currentContext} />
          
          {/* Content Area */}
          <div className="flex flex-1 overflow-hidden">
            <div className="flex-1 flex flex-col lg:flex-row min-h-0">
              {/* MainContent with Collapse/Expand */}
              <div className="flex-1 lg:w-3/5 flex flex-col min-h-0">
                <AnimatePresence mode="wait">
                  {mainContentCollapsed ? (
                    <motion.div
                      key="collapsed"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="flex-1"
                    >
                      <CollapsedSummary 
                        context={currentContext}
                        onClick={() => setMainContentCollapsed(false)}
                      />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="expanded"
                      className="flex-1 overflow-y-auto relative"
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ duration: 0.3, ease: "easeOut" }}
                    >
                      <MainContent 
                        context={currentContext}
                        onShowProjectPanel={() => setShowProjectPanel(true)}
                        onCollapse={() => setMainContentCollapsed(true)}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              
              {/* ChatInterface - Side Panel */}
              <div className="w-full lg:w-2/5 flex flex-col min-h-0">
                <ChatInterface context={currentContext} />
              </div>
            </div>
            
            {/* Project Context Panel */}
            {showProjectPanel && (
              <ProjectContextPanel 
                context={currentContext}
                onClose={() => setShowProjectPanel(false)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};