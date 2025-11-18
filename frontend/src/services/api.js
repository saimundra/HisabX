import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Don't set Content-Type for FormData - let browser handle it with boundary
    if (config.data instanceof FormData) {
      // Delete Content-Type to let browser set it automatically with boundary
      delete config.headers['Content-Type'];
    } else {
      config.headers['Content-Type'] = 'application/json';
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          // Attempt to refresh token
          const refreshResponse = await axios.post(`http://localhost:8000/api/token/refresh/`, {
            refresh: refreshToken
          });
          
          const { access } = refreshResponse.data;
          
          // Update token and expiry
          const now = new Date().getTime();
          const expiryTime = now + (24 * 60 * 60 * 1000); // 1 day
          
          localStorage.setItem('access_token', access);
          localStorage.setItem('token_expiry', expiryTime.toString());
          
          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } else {
          throw new Error('No refresh token available');
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_expiry');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/register/', data),
  login: (data) => api.post('/login/', data),
  getProfile: () => api.get('/profile/'),
};

export default api;
