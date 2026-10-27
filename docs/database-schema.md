# Neon PostgreSQL Application Database & Retention Policy

## 1. Overview

The application uses **Neon PostgreSQL** as its persistence layer, accessed through **Prisma ORM** in Backend 1.

The database stores application-level entities:
- Anonymous chat sessions and conversation threads
- Chat message history and structured agent responses
- Dataset upload records and profiling metadata
- Registered external database connection metadata (with masked credentials)
- Agent execution telemetry and run metrics
- Model evaluation benchmarks
- Generated result references

---

## 2. Entity Relational Schema

```text
ChatSession (1) <────── (N) ChatMessage
ChatSession (1) <────── (N) AgentRun (1) <────── (N) AgentRunMetric
ChatSession (1) <────── (N) AnalysisResult

Dataset (independent registry)
DataSource (independent connection registry)
ModelEvaluation (independent benchmark storage)
```

### 2.1 Table Definitions

#### `ChatSession`
- `id` (UUID, Primary Key)
- `anonymousSessionId` (String, Indexed): Identifies the local single-user or browser session.
- `title` (String): Human-readable conversation thread title.
- `createdAt` (Timestamp, Default: `now()`)
- `updatedAt` (Timestamp, Updated automatically on new activity)
- **Index**: `(anonymousSessionId, updatedAt)` for fast ordered retrieval of active threads.

#### `ChatMessage`
- `id` (UUID, Primary Key)
- `sessionId` (UUID, Foreign Key → `ChatSession.id`, `ON DELETE CASCADE`)
- `role` (String: `"user"` | `"assistant"` | `"system"`)
- `content` (Text): The Markdown formatted message body.
- `planIntent` (String, Optional): The identified analytical intent (e.g., `"forecasting"`, `"anomaly_detection"`).
- `structuredData` (JSONB, Optional): Structured tables, chart specifications, metrics, and evidence.
- `createdAt` (Timestamp, Default: `now()`)
- **Index**: `(sessionId, createdAt)`

#### `Dataset`
- `id` (UUID, Primary Key)
- `anonymousSessionId` (String, Indexed)
- `originalFilename` (String): Name of the file as uploaded by user.
- `storedFilename` (String): Unique safe filename on disk.
- `filePath` (String): Storage path on disk.
- `sha256Checksum` (String): SHA-256 hash computed upon receipt to guarantee immutability.
- `rowCount` (Integer)
- `columnCount` (Integer)
- `metadataJson` (JSONB): Complete column types, missingness, and profiling statistics.
- `createdAt` (Timestamp)

#### `DataSource`
- `id` (UUID, Primary Key)
- `anonymousSessionId` (String, Indexed)
- `name` (String): User-assigned label (e.g. `"Production Analytics DB"`).
- `type` (String: `"postgresql"` | `"mysql"` | `"sqlite"`).
- `host`, `port`, `databaseName`, `username` (Strings, Optional).
- `isReadOnly` (Boolean, Default: `true`).
- `createdAt` (Timestamp).

#### `AgentRun` & `AgentRunMetric`
- Tracks agent execution duration, plan intent, status, and associated evaluation metrics per run.

#### `ModelEvaluation`
- Stores genuine evaluation metrics and parameter specifications for the Isolation Forest and XGBoost models.

#### `AnalysisResult`
- References generated separate output CSV files, Plotly chart dumps, and downloadable markdown reports.

---

## 3. Ten-Conversation Retention Policy

To balance local persistence with clean resource utilization, the system enforces a strict **10-conversation retention policy**:
1. When a user creates a new chat session or interacts with an existing one, the session's `updatedAt` is refreshed.
2. The system checks the total number of conversation threads for that `anonymousSessionId`.
3. If the total exceeds 10, the oldest thread (by `updatedAt`) and all of its associated `ChatMessage` rows are deleted in a single consistent transaction.
4. **Note**: The limit applies to conversation threads, NOT to the number of messages inside each thread. A thread can contain unlimited analytical messages and history.

---

## 4. Neon PostgreSQL Setup Instructions

If you have a Neon project:
1. Log in to [Neon Console](https://console.neon.tech).
2. Select your project and navigate to **Dashboard**.
3. Copy the **Connection String** (choose **Pooled Connection** for `DATABASE_URL` and **Direct Connection** for `DIRECT_URL`).
4. Paste the connection strings into your root `.env` and `backend1/.env`:
   ```dotenv
   DATABASE_URL="postgresql://user:password@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
   DIRECT_URL="postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require"
   ```
5. Apply the Prisma schema:
   ```bash
   cd backend1
   npx prisma db push
   ```
6. Backend 1 will automatically switch from local session mode to live Neon persistence.
