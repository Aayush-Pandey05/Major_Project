import { ProgressEvent, SynthesizedResponse, AgentRunResult } from './types';
import { apiClient } from './axios-instance';

export interface StreamParams {
  query: string;
  sessionId?: string;
  datasetId?: string;
  connectionId?: string;
  anonymousSessionId?: string;
  onProgress?: (event: ProgressEvent) => void;
  onFinalResponse?: (response: SynthesizedResponse) => void;
  onError?: (error: string) => void;
}

/**
 * Centralized streaming client using browser Fetch ReadableStream for Server-Sent Events.
 * Never duplicates streaming logic in UI components.
 */
export async function streamAgentWorkflow(params: StreamParams): Promise<void> {
  const rawBaseUrl = process.env.NEXT_PUBLIC_BACKEND1_URL || 'http://localhost:3001';
  const cleanBase = rawBaseUrl.endsWith('/api') ? rawBaseUrl : `${rawBaseUrl}/api`;
  const streamUrl = `${cleanBase}/agent-gateway/stream`;

  try {
    const response = await fetch(streamUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: params.query,
        sessionId: params.sessionId,
        datasetId: params.datasetId,
        connectionId: params.connectionId,
        anonymousSessionId: params.anonymousSessionId || 'default_session',
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      params.onError?.(errText || `Server responded with status ${response.status}`);
      return;
    }

    if (!response.body) {
      params.onError?.('Streaming response body is not supported by this browser.');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;

        const eventMatch = line.match(/^event:\s*(\w+)/m);
        const dataMatch = line.match(/^data:\s*(.+)$/m);

        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1];
          try {
            const parsedData = JSON.parse(dataMatch[1]);
            if (eventType === 'progress' && params.onProgress) {
              params.onProgress(parsedData as ProgressEvent);
            } else if (eventType === 'final_response' && params.onFinalResponse) {
              params.onFinalResponse(parsedData as SynthesizedResponse);
            } else if (eventType === 'error' && params.onError) {
              params.onError(parsedData.error || 'Unknown streaming error');
            }
          } catch {
            // Ignore non-json data chunks
          }
        }
      }
    }
  } catch (err: any) {
    params.onError?.(err.message || 'Stream connection error.');
  }
}

/**
 * Non-stream synchronous request fallback.
 */
export async function executeAgentWorkflow(dto: {
  query: string;
  sessionId?: string;
  datasetId?: string;
  connectionId?: string;
  anonymousSessionId?: string;
}): Promise<AgentRunResult> {
  const response = await apiClient.post<AgentRunResult>('/agent-gateway/query', dto);
  return response.data;
}
