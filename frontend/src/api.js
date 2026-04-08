import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const predictText = async (text) => {
  const response = await api.post('/api/predict', { text });
  return response.data;
};

export const predictURL = async (url) => {
  const response = await api.post('/api/predict-url', { url });
  return response.data;
};

export const getMonitorData = async (query = 'latest news', limit = 10) => {
  const response = await api.get('/api/monitor', { params: { query, limit } });
  return response.data;
};

export const getHistory = async (limit = 50, offset = 0) => {
  const response = await api.get('/api/history', { params: { limit, offset } });
  return response.data;
};

export const getDashboard = async () => {
  const response = await api.get('/api/dashboard');
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

export default api;
