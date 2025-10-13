import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      // Redirect to login if needed
    }
    return Promise.reject(error);
  }
);

export interface ChatMessage {
  content: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  context?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface MetricData {
  name: string;
  value: number;
  timestamp: string;
  labels: Record<string, string>;
  unit: string;
}

export interface AlertData {
  name: string;
  severity: string;
  description: string;
  service: string;
  timestamp: string;
  labels: Record<string, string>;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  services: Record<string, string>;
}

export const api = {
  // Health check
  async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Chat endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post('/chat', request);
    return response.data;
  },

  async getSessionHistory(sessionId: string): Promise<ChatMessage[]> {
    const response = await apiClient.get(`/sessions/${sessionId}/history`);
    return response.data.history;
  },

  async clearSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/sessions/${sessionId}`);
  },

  // Metrics endpoints
  async getMetrics(query?: string, timeRange: string = '1h'): Promise<MetricData[]> {
    const response = await apiClient.get('/metrics', {
      params: { query, time_range: timeRange }
    });
    return response.data.metrics;
  },

  async getMetricsSummary(): Promise<{
    metrics_count: number;
    services: string[];
    connectors: string[];
    connector_summaries: Record<string, any>;
    last_updated: string;
  }> {
    const response = await apiClient.get('/metrics/summary');
    return response.data;
  },

  // Alerts endpoints
  async getActiveAlerts(): Promise<{
    alerts: AlertData[];
    count: number;
    timestamp: string;
  }> {
    const response = await apiClient.get('/alerts');
    return response.data;
  },

  // Services endpoints
  async getServices(): Promise<{
    services: Record<string, string[]>;
    total_count: number;
    timestamp: string;
  }> {
    const response = await apiClient.get('/services');
    return response.data;
  },

  // Conversation summary
  async getConversationSummary(sessionId: string): Promise<{
    session_id: string;
    message_count: number;
    start_time: string;
    last_activity: string;
    topics: string[];
  }> {
    const response = await apiClient.get(`/conversations/${sessionId}/summary`);
    return response.data;
  },
};

export default api;