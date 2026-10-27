import { create } from 'zustand';
import { Dataset } from '../services/api/types';

interface DatasetState {
  activeDataset: Dataset | null;
  datasets: Dataset[];
  isLoading: boolean;
  setActiveDataset: (dataset: Dataset | null) => void;
  setDatasets: (datasets: Dataset[]) => void;
  setIsLoading: (loading: boolean) => void;
}

export const useDatasetStore = create<DatasetState>((set) => ({
  activeDataset: null,
  datasets: [],
  isLoading: false,
  setActiveDataset: (dataset) => set({ activeDataset: dataset }),
  setDatasets: (datasets) => set({ datasets }),
  setIsLoading: (isLoading) => set({ isLoading }),
}));
