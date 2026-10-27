# Frontend API Architecture & State Management

## 1. Architectural Principles

In accordance with strict clean-code and full-stack engineering standards:
1. **Centralized API Layer**: Raw HTTP requests are NEVER written inside React UI components.
2. **Dedicated Domain Modules**: Every analytical domain has a dedicated, strongly-typed API file in `frontend/src/services/api/`.
3. **Single Reusable Axios Instance**: Shared client configuration with normalized timeout, base URL (`NEXT_PUBLIC_BACKEND1_URL`), headers, and error formatting.
4. **Resilient Streaming**: Real-time agent progress events and final response delivery handled via `streaming-client.ts`.
5. **Selective State Management with Zustand**: Stores are used strictly for genuinely shared cross-component state, avoiding store bloat.

---

## 2. API Layer Directory Structure

```text
frontend/src/services/api/
├── axios-instance.ts           # Configured Axios client
├── chat.api.ts                 # Sessions, messages, thread management
├── datasets.api.ts             # File upload, profiling, metadata
├── database-connections.api.ts # DB testing, schemas, connection registry
├── results.api.ts              # Analytical results and download links
├── evaluations.api.ts          # Genuine model benchmarks
├── health.api.ts               # Full system health checks
├── streaming-client.ts         # SSE streaming client for real-time progress
├── types.ts                    # Shared TypeScript interfaces & DTOs
└── index.ts                    # Barrel export
```

---

## 3. Module Details & Signatures

### 3.1 `axios-instance.ts`
Exports `apiClient`, configured with:
- Base URL: `process.env.NEXT_PUBLIC_BACKEND1_URL || 'http://localhost:3001/api'`
- Timeout: 30,000 ms
- Request and response interceptors normalizing errors into `{ message, statusCode, details }`.

### 3.2 `chat.api.ts`
- `createSession(anonymousSessionId?, title?): Promise<ChatSession>`
- `getRecentSessions(anonymousSessionId?): Promise<ChatSession[]>`
- `getSessionById(id: string): Promise<ChatSession>`
- `deleteSession(id: string): Promise<void>`
- `sendMessage(dto: SendMessageDto): Promise<ChatMessage>`

### 3.3 `datasets.api.ts`
- `uploadDataset(file: File, anonymousSessionId?): Promise<Dataset>`
- `getDatasets(anonymousSessionId?): Promise<Dataset[]>`
- `getDatasetById(id: string): Promise<Dataset>`

### 3.4 `database-connections.api.ts`
- `testConnection(url: string): Promise<{ success: boolean; dialect: string; message: string }>`
- `getSchema(url: string): Promise<{ dialect: string; tables: TableSchema[] }>`
- `saveConnection(dto: CreateConnectionDto): Promise<DataSourceMetadata>`
- `getConnections(anonymousSessionId?): Promise<DataSourceMetadata[]>`

### 3.5 `streaming-client.ts`
Uses the browser Fetch ReadableStream API to consume Server-Sent Events from `POST /agent-gateway/stream`:
```typescript
await streamAgentWorkflow({
  query: "Forecast sales for next 14 days",
  sessionId: "session-123",
  datasetId: "ds-456",
  onProgress: (event) => console.log(event.agent, event.message),
  onFinalResponse: (resp) => setResponse(resp),
  onError: (err) => console.error(err)
});
```

---

## 4. Zustand State Management Architecture

State is partitioned into focused, single-responsibility stores located in `frontend/src/stores/`:

1. **`useSessionStore`**:
   - `activeSessionId: string | null`
   - `sessions: ChatSession[]`
   - `messages: ChatMessage[]`
   - `setActiveSession(id: string)`
   - `refreshSessions()`
   - `deleteSession(id: string)`

2. **`useDatasetStore`**:
   - `activeDataset: Dataset | null`
   - `datasets: Dataset[]`
   - `setActiveDataset(dataset: Dataset | null)`
   - `refreshDatasets()`

3. **`useDataSourceStore`**:
   - `activeConnection: DataSourceMetadata | null`
   - `connections: DataSourceMetadata[]`
   - `setActiveConnection(conn: DataSourceMetadata | null)`

4. **`useAgentRunStore`**:
   - `isExecuting: boolean`
   - `currentAgent: string | null`
   - `progressEvents: ProgressEvent[]`
   - `activeResponse: SynthesizedResponse | null`
   - `addProgressEvent(event: ProgressEvent)`
   - `reset()`
