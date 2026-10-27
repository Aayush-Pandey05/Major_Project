# API Contracts Specification

## 1. Architecture & Protocol Summary

- **Frontend Client**: Next.js App Router issuing requests through a centralized Axios API layer.
- **Backend 1 (NestJS)**: Main application gateway, Neon PostgreSQL persistence, session tracking, file upload coordination. Running on `http://localhost:3001/api`.
- **Backend 2 (FastAPI)**: Analytical engine, LangGraph agent orchestration, model inference, read-only SQL execution. Running on `http://localhost:8000/api/v1`.
- **Request Flow**: `Frontend → Backend 1 → Backend 2`. Frontend never bypasses Backend 1.

---

## 2. Backend 1 API Endpoints (`http://localhost:3001/api`)

### 2.1 Chat & Sessions
- **`POST /chat/sessions`**
  - **Body**: `{ "anonymousSessionId": "string", "title": "string" }`
  - **Response**: `{ "id": "uuid", "title": "string", "createdAt": "iso", "updatedAt": "iso" }`
- **`GET /chat/sessions`**
  - **Query**: `anonymousSessionId=string`
  - **Response**: `Array<ChatSession>` (capped at 10 most recent sessions)
- **`GET /chat/sessions/:id`**
  - **Response**: `{ "id": "uuid", "title": "string", "messages": [ { "id": "uuid", "role": "user"|"assistant", "content": "string", "planIntent": "string", "structuredData": {...} } ] }`
- **`DELETE /chat/sessions/:id`**
  - **Response**: `{ "success": true, "message": "string" }`

### 2.2 Datasets
- **`POST /datasets/upload`**
  - **Content-Type**: `multipart/form-data` (Field: `file`, `anonymousSessionId`)
  - **Response**: `{ "id": "string", "originalFilename": "string", "rowCount": 100, "columnCount": 8, "profile": { "columns": [...], "numerical_summary": {...}, "preview_rows": [...] } }`
- **`GET /datasets`**
  - **Query**: `anonymousSessionId=string`
  - **Response**: `Array<Dataset>`
- **`GET /datasets/:id`**
  - **Response**: `Dataset` with full metadata and preview.

### 2.3 External Database Connections
- **`POST /database-connections/test`**
  - **Body**: `{ "connectionUrl": "postgresql://... or sqlite:///... or mysql://..." }`
  - **Response**: `{ "success": true, "dialect": "postgresql", "message": "string" }`
- **`POST /database-connections/schema`**
  - **Body**: `{ "connectionUrl": "string" }`
  - **Response**: `{ "dialect": "string", "tables_count": 5, "tables": [ { "table_name": "orders", "columns": [...] } ] }`
- **`POST /database-connections`**
  - **Body**: `{ "name": "string", "type": "postgresql", "connectionUrl": "string", "anonymousSessionId": "string" }`
  - **Response**: Connection metadata with masked password.
- **`GET /database-connections`**
  - **Response**: `Array<DataSourceMetadata>`

### 2.4 Agent Gateway
- **`POST /agent-gateway/query`**
  - **Body**: `{ "query": "string", "sessionId": "string", "datasetId": "string", "connectionId": "string" }`
  - **Response**:
    ```json
    {
      "sessionId": "string",
      "planIntent": "forecasting",
      "targetAgents": ["ml_agent", "visualization_agent", "synthesis_agent"],
      "progressEvents": [...],
      "response": {
        "answer": "string",
        "summary": "string",
        "key_findings": ["..."],
        "tables": [...],
        "charts": [...],
        "metrics": {...},
        "evidence": [...],
        "limitations": [...]
      },
      "executionTimeMs": 1420
    }
    ```
- **`POST /agent-gateway/stream`**
  - **Body**: `{ "query": "string", "sessionId": "string", ... }`
  - **Stream Protocol**: `text/event-stream`
  - **Events Emitted**: `event: progress`, `event: final_response`, `event: error`.

### 2.5 Model Evaluations & Results
- **`GET /model-evaluations`**
  - **Response**: Genuine benchmark metrics for Isolation Forest and XGBoost models.
- **`GET /results/download/:filename`**
  - **Response**: Download stream for generated analytical CSVs, reports, and charts.
- **`GET /health`**
  - **Response**: Health status of Backend 1, database persistence mode, and Backend 2.

---

## 3. Backend 2 Internal API Endpoints (`http://localhost:8000/api/v1`)

- **`POST /datasets/profile`**: Profiles uploaded CSV/Excel/Parquet files without modifying source data.
- **`POST /database/test`**: Tests external SQL connection.
- **`POST /database/schema`**: Introspects tables, columns, and types.
- **`POST /database/query`**: Validates read-only policy and executes query with row limits.
- **`POST /agents/execute`**: Executes the full LangGraph multi-agent pipeline.
- **`POST /agents/stream`**: Streams real-time execution progress events and final synthesis via SSE.
- **`POST /agents/anomaly`**: Direct invocation of Isolation Forest anomaly detector.
- **`POST /agents/forecast`**: Direct invocation of XGBoost sales forecaster.
- **`GET /evaluations`**: Exposes real model evaluation metadata JSON files.
- **`GET /results/download/{filename}`**: Serves downloadable generated results.
- **`GET /health`**: Health status of FastAPI, loaded models, and OpenAI configuration.
