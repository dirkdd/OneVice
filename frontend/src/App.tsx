import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ClerkProvider } from "@/providers/ClerkProvider";
import { AuthProvider } from "@/contexts/AuthContext";
import { AgentPreferencesProvider } from "@/contexts/AgentPreferencesContext";
import { PerformanceProvider, AnimationMonitor } from "@/animations/performance";
import { useApiClient } from "@/hooks/useApiClient";
import ProtectedRoute from "@/components/ProtectedRoute";
import NotFound from "@/pages/not-found";

import { Login } from "@/pages/Login";
import { Dashboard } from "@/pages/Dashboard";
import { AgentTestShowcase } from "@/components/ui/agent-test-showcase";
import { AgentSelectionDemo } from "@/components/ui/agent-selection-demo";

function Router() {
  return (
    <Switch>
      {/* Add pages below */}
      <Route path="/" component={Login} />
      <Route path="/dashboard">
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      </Route>
      <Route path="/agents-test" component={AgentTestShowcase} />
      <Route path="/agent-selection-demo" component={AgentSelectionDemo} />
      {/* Fallback to 404 */}
      <Route component={NotFound} />
    </Switch>
  );
}

function AppContent() {
  // Initialize API client with Clerk authentication
  useApiClient();

  return (
    <QueryClientProvider client={queryClient}>
      <PerformanceProvider initialMode="balanced">
        <AnimationMonitor enableMonitoring={true}>
          <TooltipProvider>
            <Toaster />
            <Router />
          </TooltipProvider>
        </AnimationMonitor>
      </PerformanceProvider>
    </QueryClientProvider>
  );
}

function App() {
  return (
    <ClerkProvider>
      <AuthProvider>
        <AgentPreferencesProvider>
          <AppContent />
        </AgentPreferencesProvider>
      </AuthProvider>
    </ClerkProvider>
  );
}

export default App;
