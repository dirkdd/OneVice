'use client';

import React, { 
  createContext, 
  useContext, 
  ReactNode 
} from 'react';
import { useUser, useAuth as useClerkAuth, useClerk } from '@clerk/clerk-react';
import { User } from '@/lib/api/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  logout: () => Promise<void>;
  clearError: () => void;
  getToken: () => Promise<string | null>;
}

// Helper function to map Clerk user to App user format
function mapClerkUserToAppUser(clerkUser: any): User {
  return {
    id: clerkUser.id,
    name: clerkUser.fullName || `${clerkUser.firstName || ''} ${clerkUser.lastName || ''}`.trim() || 'User',
    email: clerkUser.primaryEmailAddress?.emailAddress || '',
    role: 'user', // Default role - can be customized based on Clerk metadata
  };
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { isLoaded, isSignedIn, user: clerkUser } = useUser();
  const { signOut } = useClerk();
  const { getToken: getClerkToken } = useClerkAuth();

  // Map Clerk state to your existing AuthState interface
  const state: AuthState = {
    user: clerkUser ? mapClerkUserToAppUser(clerkUser) : null,
    isAuthenticated: isSignedIn || false,
    isLoading: !isLoaded,
    error: null,
  };

  const logout = async () => {
    try {
      await signOut();
    } catch (error: any) {
      console.error('Logout failed:', error);
      // Clerk handles the logout state automatically
    }
  };

  const clearError = () => {
    // No-op since Clerk handles errors internally
    // Keep for backward compatibility
  };

  const getToken = async (): Promise<string | null> => {
    try {
      return await getClerkToken();
    } catch (error) {
      console.error('Failed to get token:', error);
      return null;
    }
  };

  const value: AuthContextType = {
    ...state,
    logout,
    clearError,
    getToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export { AuthContext };