# System Architecture & Technical Specification

## 1. High-Level Architectural Overview

The **Multi-Agent AI Data Analyst** is built as a modular, three-tier decoupled system:

```text
                     +---------------------------------------+
                     |           Next.js Frontend            |
                     |       TypeScript, Tailwind CSS        |
                     |   Axios API Layer, Plotly.js, Zustand |
                     +---------------------------------------+
                                         |
                                  REST APIs / SSE
                                         v
                     +---------------------------------------+
                     |           NestJS Backend 1            |
                     |  Prisma ORM, Session/Chat Persistence |
                     |   Upload Coordination, Agent Gateway  |
                     +---------------------------------------+
                                  |             |
                                  |             v
                                  |    +--------------------+
                                  |    |  Neon PostgreSQL   |
                                  |    |  Application DB    |
                                  |    +--------------------+
                                  v
                     +---------------------------------------+
                     |           FastAPI Backend 2           |
                     |          Python, LangGraph            |
                     |   Analytical Agents & Model Inference |
                     +---------------------------------------+
                                         |
                 +-----------------------+-----------------------+
                 |                       |                       |
                 v                       v                       v
          +--------------+       +---------------+       +---------------+
          |  SQL Agent   |       | Statistical   |       |   ML Agent    |
          |  (Read-Only  |       |     Agent     |       |   (XGBoost    |
          |  Execution)  |       | (Isolation    |       |  Forecasting) |
          +--------------+       |    Forest)    |       +---------------+
                 |               +---------------+               |
                 +-----------------------+-----------------------+
                                         |
                                         v
                             +-----------------------+
                             |  Visualization Agent  |
                             |   (Plotly Engine)     |
                             +-----------------------+
                                         |
                                         v
                             +-----------------------+
                             |    Synthesis Agent    |
                             |   (Evidence Fusion)   |
                             +-----------------------+
```

---

## 2. Tier Responsibilities

### Tier 1: Next.js Frontend
- **Technology**: Next.js (App Router), TypeScript, Tailwind CSS, Plotly.js, Zustand.
- **Role**: Presentation and interaction.
- **Architectural Rules**:
  - No raw Axios calls inside React UI components. All requests flow through `src/services/api/`.
  - Zero Python agent details or direct calls to Backend 2.
  - Streaming progress handled via centralized `streaming-client.ts`.
  - Zustand used selectively for cross-cutting state (active conversation, active dataset, current data source, global execution state).

### Tier 2: NestJS Backend 1
- **Technology**: NestJS, TypeScript, Prisma ORM, Neon PostgreSQL.
- **Role**: Main application persistence and gateway.
- **Responsibilities**:
  - Manages anonymous chat sessions and message threads.
  - Strictly enforces the **10-conversation retention limit** per anonymous session.
  - Coordinates file uploads and computes initial SHA-256 checksums.
  - Stores sanitized database connection metadata (passwords never exposed).
  - Gateways requests to Python Backend 2 and streams Server-Sent Events back to the frontend.

### Tier 3: FastAPI Backend 2
- **Technology**: Python, FastAPI, LangGraph, Scikit-learn, XGBoost, Pandas, Plotly.
- **Role**: Specialized analytical engine and multi-agent graph.
- **Responsibilities**:
  - Houses the migrated model artifacts (`isolation_forest_retail_model.joblib`, `xgboost_sales_forecasting_model.joblib`).
  - Executes LangGraph multi-agent orchestration.
  - Enforces strict read-only guarantees on uploaded datasets and connected SQL databases.
  - Computes counterfactual anomaly explanations and recursive multi-step forecasts.
  - Generates interactive Plotly specifications.

---

## 3. Specialized Multi-Agent Framework

| Agent | LLM Usage | Core Technology | Primary Responsibility |
|---|---|---|---|
| **Orchestrator Agent** | OpenAI (or fallback rules) | LangGraph, ChatOpenAI | Intent detection, workflow selection, parameter extraction. |
| **SQL Agent** | OpenAI (or fallback rules) | SQLAlchemy, Regex Parser | Natural language to candidate SQL, mutation validation, read-only query execution. |
| **Statistical Agent** | **ZERO LLM** (Deterministic) | Scikit-learn, Isolation Forest | Invoice feature engineering, retail anomaly detection, Pearson correlations, descriptive statistics. |
| **ML Agent** | **ZERO LLM** (Deterministic) | XGBoost, Pandas | Recursive multi-step sales forecasting, calendar encoding, lag/rolling feature extraction. |
| **Visualization Agent** | **ZERO LLM** (Deterministic) | Plotly Python | Interactive chart specifications (time series, scatter anomaly plots, correlation heatmaps, bar charts). |
| **Synthesis Agent** | OpenAI (or template rules) | ChatOpenAI | Evidence-based synthesis preserving exact numbers, tables, metrics, and limitations. |

---

## 4. Key Security Boundaries

1. **Source Immutability**: Uploaded files are read into detached in-memory DataFrames. Source files are verified with SHA-256 before and after operations; they are never modified.
2. **Read-Only External Databases**: External databases are queried strictly using single-statement `SELECT` / `WITH` statements with statement timeouts and row limits.
3. **Secret Isolation**: `OPENAI_API_KEY` and database credentials are kept strictly server-side. Passwords are never returned to the frontend or sent to LLMs.
4. **Database Separation**: Neon PostgreSQL is the application database. Application data is never written to connected company databases.
