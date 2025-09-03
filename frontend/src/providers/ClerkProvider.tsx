import { ClerkProvider as ClerkProviderBase } from '@clerk/clerk-react';
import { ReactNode } from 'react';

interface ClerkProviderProps {
  children: ReactNode;
}

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!publishableKey) {
  throw new Error('Missing VITE_CLERK_PUBLISHABLE_KEY environment variable');
}

export function ClerkProvider({ children }: ClerkProviderProps) {
  return (
    <ClerkProviderBase 
      publishableKey={publishableKey}
      afterSignOutUrl="/"
      signInFallbackRedirectUrl="/dashboard"
      signUpFallbackRedirectUrl="/dashboard"
    >
      {children}
    </ClerkProviderBase>
  );
}