import React, { createContext, useState, useContext, useEffect } from 'react';
import { authApi } from '../services/api';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token');
    if (token) {
      refreshUser();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    setUser(response.user);
  };

  const register = async (userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => {
    const response = await authApi.register(userData);
    setUser(response.user);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      localStorage.removeItem('auth_token');
    }
  };

  const refreshUser = async () => {
    try {
      const response = await authApi.refreshToken();
      setUser(response.user);
    } catch (error) {
      console.error('Token refresh error:', error);
      localStorage.removeItem('auth_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
