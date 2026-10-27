import { create } from 'zustand';
import { ProgressEvent, SynthesizedResponse } from '../services/api/types';

interface AgentRunState {
  isExecuting: boolean;
  progressEvents: ProgressEvent[];
  latestResponse: SynthesizedResponse | null;
  errorMessage: string | null;
  setIsExecuting: (executing: boolean) => void;
  addProgressEvent: (event: ProgressEvent) => void;
  setLatestResponse: (response: SynthesizedResponse | null) => void;
  setErrorMessage: (msg: string | null) => void;
  resetRun: () => void;
}

export const useAgentRunStore = create<AgentRunState>((set) => ({
  isExecuting: false,
  progressEvents: [],
  latestResponse: null,
  errorMessage: null,
  setIsExecuting: (isExecuting) => set({ isExecuting }),
  addProgressEvent: (event) =>
    set((state) => ({ progressEvents: [...state.progressEvents, event] })),
  setLatestResponse: (latestResponse) => set({ latestResponse }),
  setErrorMessage: (errorMessage) => set({ errorMessage }),
  resetRun: () =>
    set({
      isExecuting: false,
      progressEvents: [],
      latestResponse: null,
      errorMessage: null,
    }),
}));
