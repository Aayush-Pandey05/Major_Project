import { create } from 'zustand';
import { ChatSession, ChatMessage } from '../services/api/types';

interface SessionState {
  activeSessionId: string | null;
  sessions: ChatSession[];
  messages: ChatMessage[];
  isLoading: boolean;
  setActiveSessionId: (id: string | null) => void;
  setSessions: (sessions: ChatSession[]) => void;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setIsLoading: (loading: boolean) => void;
  resetSession: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  activeSessionId: null,
  sessions: [],
  messages: [],
  isLoading: false,
  setActiveSessionId: (id) => set({ activeSessionId: id }),
  setSessions: (sessions) => set({ sessions }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setIsLoading: (isLoading) => set({ isLoading }),
  resetSession: () => set({ activeSessionId: null, messages: [] }),
}));
