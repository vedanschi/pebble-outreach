import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add JWT token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Authentication API calls
export const login = async (credentials) => {
  const response = await apiClient.post('/auth/login', credentials);
  return response.data;
};

export const signup = async (userData) => {
  const response = await apiClient.post('/auth/signup', userData);
  return response.data;
};

// Campaign API calls
export const fetchCampaigns = async () => {
  const response = await apiClient.get('/campaigns');
  return response.data;
};

export const createCampaign = async (campaignData) => {
  const response = await apiClient.post('/campaigns', campaignData);
  return response.data;
};

// CSV Upload API call
export const uploadCSV = async (formData) => {
  const response = await apiClient.post('/campaigns/upload-csv', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Email Generation API call
export const generateEmail = async (prompt) => {
  const response = await apiClient.post('/llm', { prompt });
  return response.data;
};

// Follow-up API calls
export const fetchFollowUps = async () => {
  const response = await apiClient.get('/followup-rules');
  return response.data;
};

export const createFollowUp = async (followUpData) => {
  const response = await apiClient.post('/followup-rules', followUpData);
  return response.data;
};