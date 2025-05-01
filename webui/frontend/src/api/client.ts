import axios, { AxiosResponse, AxiosInstance, AxiosRequestConfig } from 'axios';
import { ApiResponse } from '../types';

const apiClient: AxiosInstance = axios.create({
  baseURL: '',  // 移除'/api'前缀，因为服务端点已包含前缀
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
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
    return response.data;
  },
  (error) => {
    if (error.response) {
      console.error('API错误:', error.response.data);
      return Promise.reject(error.response.data);
    } else if (error.request) {
      console.error('请求错误: 未收到响应');
      return Promise.reject({ message: '未收到服务器响应，请检查网络连接' });
    } else {
      console.error('错误:', error.message);
      return Promise.reject({ message: '请求设置错误' });
    }
  }
);

const api = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return apiClient.get(url, config);
  },

  post: <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return apiClient.post(url, data, config);
  },

  put: <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return apiClient.put(url, data, config);
  },

  delete: <T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return apiClient.delete(url, config);
  },

  upload: <T>(url: string, file: File, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post(url, formData, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
    });
  }
};

export default api;
