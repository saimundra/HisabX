import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const tokenExpiry = localStorage.getItem('token_expiry');
    
    if (token && tokenExpiry) {
      const now = new Date().getTime();
      const expiryTime = parseInt(tokenExpiry);
      
      // Check if token is still valid (not expired)
      if (now < expiryTime) {
        loadUser();
      } else {
        // Token expired, clear storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_expiry');
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const response = await authAPI.getProfile();
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      // Clear all tokens if user loading fails
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token_expiry');
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password });
      const { access_token, refresh_token } = response.data;
      
      // Calculate expiry time (1 day from now)
      const now = new Date().getTime();
      const expiryTime = now + (24 * 60 * 60 * 1000); // 24 hours in milliseconds
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('token_expiry', expiryTime.toString());
      
      await loadUser();
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || 'Login failed. Please try again.',
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || 'Registration failed. Please try again.',
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expiry');
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated,
        login,
        register,
        logout,
        loadUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
