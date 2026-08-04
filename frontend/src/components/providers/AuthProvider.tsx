"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { components } from "@/lib/api/schema";

type UserProfile = components["schemas"]["UserProfile"];

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
  checkRole: (allowedRoles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchUser = async () => {
    try {
      const { data, error } = await apiClient.GET("/api/v1/auth/me");
      if (data) {
        setUser(data as UserProfile);
      } else {
        setUser(null);
      }
    } catch (err) {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = (token: string) => {
    localStorage.setItem("access_token", token);
    setIsLoading(true);
    fetchUser();
  };

  const logout = async () => {
    try {
      await apiClient.POST("/api/v1/auth/logout");
    } catch (e) {
      // Ignore errors on logout
    } finally {
      localStorage.removeItem("access_token");
      setUser(null);
      router.push("/login");
    }
  };

  const checkRole = (allowedRoles: string[]) => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  // Basic protection wrapper - will be overridden by layout wrappers for specific contexts
  // but useful as a fallback.
  useEffect(() => {
    if (!isLoading && !user && pathname?.startsWith("/dashboard")) {
      router.push("/login");
    }
  }, [isLoading, user, pathname, router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, checkRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
