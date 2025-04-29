import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse } from '../types';

const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30秒超时
});

apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Request error:', error.message);
    }
    return Promise.reject(error);
  }
);

export const request = async <T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> => {
  try {
    const response = await apiClient(config);
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : '未知错误',
    };
  }
};

export const api = {
  get: <T>(url: string, params?: any): Promise<ApiResponse<T>> => {
    return request<T>({ method: 'GET', url, params });
  },
  post: <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
    return request<T>({ method: 'POST', url, data });
  },
  put: <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
    return request<T>({ method: 'PUT', url, data });
  },
  delete: <T>(url: string, params?: any): Promise<ApiResponse<T>> => {
    return request<T>({ method: 'DELETE', url, params });
  },
};

export default api;
