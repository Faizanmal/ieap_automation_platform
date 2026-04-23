import { authApi } from '@/lib/api/auth';
import { useMutation, useQuery } from '@tanstack/react-query';

export interface ApiKeyData {
  name: string;
  scopes?: string[];
}

export function useApiKeys() {
  return useQuery({
    queryKey: ['auth', 'api-keys'],
    queryFn: () => authApi.listApiKeys(),
  });
}

export function useCreateApiKey() {
  return useMutation({
    mutationFn: (data: ApiKeyData) => authApi.createApiKey(data),
  });
}

export function useDeleteApiKey() {
  return useMutation({
    mutationFn: (keyId: string) => authApi.deleteApiKey(keyId),
  });
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: (email: string) => authApi.requestPasswordReset(email),
  });
}

export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: ({ token, new_password }: { token: string; new_password: string }) =>
      authApi.confirmPasswordReset(token, new_password),
  });
}

export function useOAuthLogin() {
  const startOAuthFlow = (provider: 'google' | 'github' | 'microsoft') => {
    const redirectUri = `${window.location.origin}/dashboard`;
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/oauth/${provider}?redirect_uri=${encodeURIComponent(redirectUri)}`;
  };

  return { startOAuthFlow };
}

export function useOAuthProviders() {
  return useQuery({
    queryKey: ['auth', 'oauth', 'providers'],
    queryFn: async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/oauth/providers`);
        return response.json();
      } catch {
        return [];
      }
    },
  });
}
