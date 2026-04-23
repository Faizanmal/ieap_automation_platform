import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, TokenResponse } from '@/types/api';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  setUser: (user: User) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setAuth: (user: User, accessToken: string, refreshToken?: string) => void;
  login: (tokens: TokenResponse, user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true,
      
      setUser: (user) => set({ user }),
      
      setTokens: (accessToken, refreshToken) => 
        set({ accessToken, refreshToken, isAuthenticated: true }),
      
      setAuth: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken: refreshToken || null,
          isAuthenticated: true,
          isLoading: false,
        }),
      
      login: (tokens, user) => 
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          user,
          isAuthenticated: true,
          isLoading: false,
        }),
      
      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        }),
      
      setLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: 'ieap-auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
