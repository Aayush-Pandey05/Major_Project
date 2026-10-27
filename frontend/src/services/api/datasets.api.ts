import { apiClient } from './axios-instance';
import { Dataset } from './types';

export async function uploadDataset(
  file: File,
  anonymousSessionId = 'default_session',
): Promise<Dataset> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('anonymousSessionId', anonymousSessionId);

  const response = await apiClient.post<Dataset>('/datasets/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function getDatasets(
  anonymousSessionId = 'default_session',
): Promise<Dataset[]> {
  const response = await apiClient.get<Dataset[]>('/datasets', {
    params: { anonymousSessionId },
  });
  return response.data;
}

export async function getDatasetById(id: string): Promise<Dataset> {
  const response = await apiClient.get<Dataset>(`/datasets/${id}`);
  return response.data;
}
