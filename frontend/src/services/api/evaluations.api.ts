import { apiClient } from './axios-instance';

export async function getModelEvaluations(): Promise<{
  anomaly_detection: any;
  forecasting: any;
}> {
  const response = await apiClient.get<{
    anomaly_detection: any;
    forecasting: any;
  }>('/model-evaluations');
  return response.data;
}
