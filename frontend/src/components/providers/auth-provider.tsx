'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/lib/stores';

interface AuthProviderProps {
  children: React.ReactNode;
}

const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password', '/reset-password'];

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, setLoading } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
    setLoading(false);
  }, [setLoading]);

  useEffect(() => {
    if (!mounted || isLoading) {return;}

    const isPublicRoute = PUBLIC_ROUTES.some(route => pathname.startsWith(route));

    if (!isAuthenticated && !isPublicRoute) {
      router.push('/login');
    } else if (isAuthenticated && isPublicRoute) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, mounted, pathname, router]);

  if (!mounted || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-zinc-200 border-t-zinc-900" />
          <p className="text-sm text-zinc-500">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
