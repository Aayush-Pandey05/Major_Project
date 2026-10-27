import { apiClient } from './axios-instance';
import { ChatSession, ChatMessage } from './types';

export async function createSession(
  anonymousSessionId = 'default_session',
  title = 'New Analysis',
): Promise<ChatSession> {
  const response = await apiClient.post<ChatSession>('/chat/sessions', {
    anonymousSessionId,
    title,
  });
  return response.data;
}

export async function getRecentSessions(
  anonymousSessionId = 'default_session',
): Promise<ChatSession[]> {
  const response = await apiClient.get<ChatSession[]>('/chat/sessions', {
    params: { anonymousSessionId },
  });
  return response.data;
}

export async function getSessionById(id: string): Promise<ChatSession> {
  const response = await apiClient.get<ChatSession>(`/chat/sessions/${id}`);
  return response.data;
}

export async function deleteSession(id: string): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(
    `/chat/sessions/${id}`,
  );
  return response.data;
}

export async function sendMessage(sessionId: string, content: string): Promise<ChatMessage> {
  const response = await apiClient.post<ChatMessage>('/chat/messages', {
    sessionId,
    content,
  });
  return response.data;
}
