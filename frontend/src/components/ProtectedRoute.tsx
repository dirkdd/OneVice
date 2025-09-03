'use client';

import React, { ReactNode } from 'react';
import { useLocation } from 'wouter';
import { useUser } from '@clerk/clerk-react';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const { isLoaded, isSignedIn } = useUser();
  const [, setLocation] = useLocation();

  // Show loading spinner while Clerk is checking auth status
  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-sm">Verifying access...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isSignedIn) {
    setLocation('/');
    return fallback || (
      <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 text-sm">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  // Render protected content if authenticated
  return <>{children}</>;
}

export default ProtectedRoute;