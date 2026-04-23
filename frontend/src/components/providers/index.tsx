'use client';

import { QueryProvider } from './query-provider';
import { AuthProvider } from './auth-provider';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Toaster } from '@/components/ui/sonner';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryProvider>
      <TooltipProvider>
        <AuthProvider>
          {children}
          <Toaster />
        </AuthProvider>
      </TooltipProvider>
    </QueryProvider>
  );
}
