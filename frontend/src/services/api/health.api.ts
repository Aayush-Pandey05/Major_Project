import { apiClient } from './axios-instance';
import { SystemHealth } from './types';

export async function checkSystemHealth(): Promise<SystemHealth> {
  const response = await apiClient.get<SystemHealth>('/health');
  return response.data;
}
