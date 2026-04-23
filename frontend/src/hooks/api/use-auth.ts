import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/lib/api/auth';
import type { LoginRequest, RegisterRequest } from '@/types/api';
import { useAuthStore } from '@/lib/stores';
import { useRouter } from 'next/navigation';

export function useLogin() {
    const setTokens = useAuthStore((state) => state.setTokens);
    const router = useRouter();

    return useMutation({
        mutationFn: (data: LoginRequest) => authApi.login(data),
        onSuccess: (data) => {
            setTokens(data.access_token, data.refresh_token);
            // We also fetch the user profile immediately after login
            // implementation of fetching user profile would go here or be triggered separately
            router.push('/dashboard');
        },
    });
}

export function useRegister() {
    const router = useRouter();

    return useMutation({
        mutationFn: (data: RegisterRequest) => authApi.register(data),
        onSuccess: () => {
            router.push('/login?registered=true');
        },
    });
}

export function useUser() {
    const { data: user, isLoading, error } = useQuery({
        queryKey: ['auth', 'me'],
        queryFn: () => authApi.me(),
        retry: false,
    });

    return { user, isLoading, error };
}

export function useLogout() {
    const logoutStore = useAuthStore((state) => state.logout);
    const queryClient = useQueryClient();
    const router = useRouter();

    return useMutation({
        mutationFn: () => authApi.logout(),
        onSuccess: () => {
            logoutStore();
            queryClient.clear();
            router.push('/login');
        },
    });
}
