import { create } from 'zustand';
import { DataSourceMetadata } from '../services/api/types';

interface DataSourceState {
  activeConnection: DataSourceMetadata | null;
  connections: DataSourceMetadata[];
  isLoading: boolean;
  setActiveConnection: (conn: DataSourceMetadata | null) => void;
  setConnections: (conns: DataSourceMetadata[]) => void;
  setIsLoading: (loading: boolean) => void;
}

export const useDataSourceStore = create<DataSourceState>((set) => ({
  activeConnection: null,
  connections: [],
  isLoading: false,
  setActiveConnection: (activeConnection) => set({ activeConnection }),
  setConnections: (connections) => set({ connections }),
  setIsLoading: (isLoading) => set({ isLoading }),
}));
