"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type AuthUser } from "@/lib/api";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: {
    email: string;
    password: string;
    role: "customer" | "brand";
    display_name: string;
    brand_name?: string;
  }) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let token: string | null = null;
    try {
      token = localStorage.getItem("auth_token");
    } catch {
      // ignore
    }
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => {
        try {
          localStorage.removeItem("auth_token");
        } catch {
          // ignore
        }
      })
      .finally(() => setLoading(false));
  }, []);

  function persist(token: string, user: AuthUser) {
    try {
      localStorage.setItem("auth_token", token);
    } catch {
      // ignore
    }
    setUser(user);
  }

  async function login(email: string, password: string) {
    const result = await api.login(email, password);
    persist(result.token, result.user);
  }

  async function signup(data: {
    email: string;
    password: string;
    role: "customer" | "brand";
    display_name: string;
    brand_name?: string;
  }) {
    const result = await api.signup(data);
    persist(result.token, result.user);
  }

  function logout() {
    try {
      localStorage.removeItem("auth_token");
    } catch {
      // ignore
    }
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
