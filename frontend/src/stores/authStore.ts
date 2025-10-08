/**
 * Authentication Store
 * 
 * Manages user authentication state including login, logout, and token management.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
    id: string;
    username: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    is_superuser: boolean;
    created_at: string;
    last_login_at?: string;
}

export interface AuthState {
    // State
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;

    // Actions
    setUser: (user: User | null) => void;
    setToken: (token: string | null) => void;
    login: (user: User, token: string) => void;
    logout: () => void;
    setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            // Initial state
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,

            // Set user
            setUser: (user) => set({
                user,
                isAuthenticated: !!user
            }),

            // Set token
            setToken: (token) => set({ token }),

            // Login action
            login: (user, token) => set({
                user,
                token,
                isAuthenticated: true,
                isLoading: false
            }),

            // Logout action
            logout: () => set({
                user: null,
                token: null,
                isAuthenticated: false,
                isLoading: false
            }),

            // Set loading state
            setLoading: (loading) => set({ isLoading: loading }),
        }),
        {
            name: 'auth-storage', // Key in localStorage
            partialize: (state) => ({
                user: state.user,
                token: state.token,
                isAuthenticated: state.isAuthenticated
            }),
        }
    )
);
