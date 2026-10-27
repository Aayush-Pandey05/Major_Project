import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { ApiError } from './types';

const rawBaseUrl = process.env.NEXT_PUBLIC_BACKEND1_URL || 'http://localhost:3001';
const baseURL = rawBaseUrl.endsWith('/api') ? rawBaseUrl : `${rawBaseUrl}/api`;

export const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout: 45000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error) => Promise.reject(error),
);

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string; detail?: string; error?: string }>) => {
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      'An unexpected network error occurred.';

    const normalizedError: ApiError = {
      message,
      statusCode: error.response?.status,
      details: error.response?.data,
    };

    return Promise.reject(normalizedError);
  },
);
