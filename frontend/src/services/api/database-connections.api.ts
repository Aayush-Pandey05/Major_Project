import { apiClient } from './axios-instance';
import { DataSourceMetadata, TableSchema } from './types';

export async function testConnection(
  connectionUrl: string,
): Promise<{ success: boolean; dialect: string; message: string }> {
  const response = await apiClient.post<{ success: boolean; dialect: string; message: string }>(
    '/database-connections/test',
    { connectionUrl },
  );
  return response.data;
}

export async function getSchema(
  connectionUrl: string,
): Promise<{ dialect: string; tables_count: number; tables: TableSchema[] }> {
  const response = await apiClient.post<{
    dialect: string;
    tables_count: number;
    tables: TableSchema[];
  }>('/database-connections/schema', { connectionUrl });
  return response.data;
}

export async function saveConnection(dto: {
  name: string;
  type: string;
  connectionUrl: string;
  anonymousSessionId?: string;
}): Promise<DataSourceMetadata> {
  const response = await apiClient.post<DataSourceMetadata>('/database-connections', dto);
  return response.data;
}

export async function getConnections(
  anonymousSessionId = 'default_session',
): Promise<DataSourceMetadata[]> {
  const response = await apiClient.get<DataSourceMetadata[]>('/database-connections', {
    params: { anonymousSessionId },
  });
  return response.data;
}
