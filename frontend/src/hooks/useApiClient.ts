import { useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { apiClient } from '@/lib/api/client';

/**
 * Hook to initialize the API client with Clerk authentication
 * This should be used at the app level to ensure API calls use Clerk tokens
 */
export function useApiClient() {
  const { getToken } = useAuth();

  useEffect(() => {
    // Set up the API client to use Clerk's getToken function
    apiClient.setClerkAuth(getToken);
  }, [getToken]);

  return apiClient;
}