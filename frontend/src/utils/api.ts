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
export const login = async (credentials: Record<string, any>) => {
  const response = await apiClient.post('/auth/login', credentials);
  return response.data;
};

export const signup = async (userData: Record<string, any>) => {
  const response = await apiClient.post('/auth/signup', userData);
  return response.data;
};

// Campaign API calls
export const fetchCampaigns = async () => {
  const response = await apiClient.get('/campaigns');
  return response.data;
};

export const getCampaignDetails = async (campaignId: number) => {
  const response = await apiClient.get(`/campaigns/${campaignId}`);
  return response.data;
};

export const createCampaign = async (campaignData: Record<string, any>) => {
  const response = await apiClient.post('/campaigns', campaignData);
  return response.data;
};

// CSV Upload API call
export const uploadCSV = async (campaignId: number, formData: FormData) => {
  const response = await apiClient.post(`/campaigns/${campaignId}/upload-csv`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Email Generation API call
export const generateEmail = async (prompt: string) => {
  const response = await apiClient.post('/llm', { prompt });
  return response.data;
};

// Sent Emails API
export const getSentEmails = async (campaignId: number) => {
  const response = await apiClient.get(`/campaigns/${campaignId}/sent-emails`);
  return response.data;
};

// Follow-up API calls
export const fetchFollowUps = async (campaignId: number) => {
  const response = await apiClient.get(`/campaigns/${campaignId}/followup-rules`);
  return response.data;
};

export const createFollowUp = async (campaignId: number, followUpData: Record<string, any>) => {
  const response = await apiClient.post(`/campaigns/${campaignId}/followup-rules`, followUpData);
  return response.data;
};

export const updateFollowUp = async (campaignId: number, followUpId: number, followUpData: Record<string, any>) => {
  const response = await apiClient.put(`/campaigns/${campaignId}/followup-rules/${followUpId}`, followUpData);
  return response.data;
};

export const deleteFollowUp = async (campaignId: number, followUpId: number) => {
  const response = await apiClient.delete(`/campaigns/${campaignId}/followup-rules/${followUpId}`);
  return response.data;
};

// Email sending controls (start, pause, stop)
export const startEmailSending = async (campaignId: number) => {
  const response = await apiClient.post(`/campaigns/${campaignId}/send/start`);
  return response.data;
};

export const pauseEmailSending = async (campaignId: number) => {
  const response = await apiClient.post(`/campaigns/${campaignId}/send/pause`);
  return response.data;
};

export const stopEmailSending = async (campaignId: number) => {
  const response = await apiClient.post(`/campaigns/${campaignId}/send/stop`);
  return response.data;
};

// Campaign stats (optional, if separate endpoint)
export const getCampaignStats = async (campaignId: number) => {
  const response = await apiClient.get(`/campaigns/${campaignId}/stats`);
  return response.data;
};