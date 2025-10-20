import { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../utils/api';
import wsClient from '../utils/websocket';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load user data if token exists
    if (token) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const loadUser = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      
      // Connect WebSocket for authenticated users
      if (token) {
        wsClient.connect(token);
      }
    } catch (error) {
      console.error('Error loading user:', error);
      // Token might be invalid, clear it
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const data = await authAPI.login(username, password);
      const authToken = data.auth_token;
      
      localStorage.setItem('authToken', authToken);
      setToken(authToken);
      
      // Load user data
      await loadUser();
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const signup = async (username, password, email, role = 'customer') => {
    try {
      await authAPI.signup(username, password, email, role);
      
      // Auto-login after signup
      return await login(username, password);
    } catch (error) {
      console.error('Signup error:', error);
      
      // Parse error messages properly
      let errorMessage = 'Signup failed';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle password validation errors
        if (errorData.password) {
          if (Array.isArray(errorData.password)) {
            errorMessage = errorData.password.join('. ');
          } else {
            errorMessage = errorData.password;
          }
        }
        // Handle username errors
        else if (errorData.username) {
          if (Array.isArray(errorData.username)) {
            errorMessage = errorData.username.join('. ');
          } else {
            errorMessage = errorData.username;
          }
        }
        // Handle email errors
        else if (errorData.email) {
          if (Array.isArray(errorData.email)) {
            errorMessage = errorData.email.join('. ');
          } else {
            errorMessage = errorData.email;
          }
        }
        // Handle other errors
        else if (errorData.detail) {
          errorMessage = errorData.detail;
        }
        // Handle non_field_errors
        else if (errorData.non_field_errors) {
          if (Array.isArray(errorData.non_field_errors)) {
            errorMessage = errorData.non_field_errors.join('. ');
          } else {
            errorMessage = errorData.non_field_errors;
          }
        }
      }
      
      return { 
        success: false, 
        error: errorMessage
      };
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await authAPI.logout();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('authToken');
      setToken(null);
      setUser(null);
      wsClient.disconnect();
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!token && !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

