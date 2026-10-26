"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { ROUTES } from "@/lib/constants";
import { clearToken, getToken, setToken } from "@/lib/token";
import * as authService from "@/services/auth";
import type { CurrentUser, LoginPayload, RegisterPayload } from "@/types/user";

interface AuthContextValue {
  user: CurrentUser | null;
  /** True while the initial session check (token -> /users/me) is in flight. */
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    authService
      .getCurrentUser()
      .then(setUser)
      .catch(() => {
        // Invalid/expired token — the axios interceptor already
        // clears it and redirects on a 401 from an authenticated
        // endpoint; nothing further to do here.
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(
    async (payload: LoginPayload) => {
      const { access_token } = await authService.login(payload);
      setToken(access_token);
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
      router.push(ROUTES.library);
    },
    [router],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      await authService.register(payload);
      await login({ email: payload.email, password: payload.password });
    },
    [login],
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    router.push(ROUTES.login);
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
    }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
