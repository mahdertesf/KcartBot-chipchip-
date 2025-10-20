import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (username, password) => {
    const response = await api.post('/auth/token/login/', { username, password });
    return response.data;
  },
  
  signup: async (username, password, email, role = 'customer') => {
    const response = await api.post('/auth/users/', {
      username,
      password,
      email,
      role,
    });
    return response.data;
  },
  
  logout: async () => {
    const response = await api.post('/auth/token/logout/');
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/users/me/');
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  sendMessage: async (message, history = []) => {
    const response = await api.post('/api/chat/', { message, history });
    return response.data;
  },
  
  getHistory: async () => {
    const response = await api.get('/api/chat/');
    return response.data;
  },
};

// Notification API
export const notificationAPI = {
  getNotifications: async () => {
    const response = await api.get('/api/notifications/');
    return response.data;
  },
};

// Order Action API
export const orderActionAPI = {
  acceptOrder: async (orderId, reason = '') => {
    const response = await api.post('/api/orders/action/', {
      order_id: orderId,
      action: 'accept',
      reason: reason
    });
    return response.data;
  },
  
  declineOrder: async (orderId, reason = '') => {
    const response = await api.post('/api/orders/action/', {
      order_id: orderId,
      action: 'decline',
      reason: reason
    });
    return response.data;
  }
};

export default api;

