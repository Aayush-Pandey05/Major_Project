# Multi-Agent AI Data Analyst — Full-Stack Enterprise Platform

[![System Architecture](https://img.shields.io/badge/Architecture-3--Tier%20Decoupled-blue.svg)](docs/architecture.md)
[![Backend 1](https://img.shields.io/badge/Backend%201-NestJS%2011%20%2B%20Prisma-E0234E.svg)](backend1/)
[![Backend 2](https://img.shields.io/badge/Backend%202-FastAPI%20%2B%20LangGraph-009688.svg)](backend2/)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%20%2B%20Tailwind%20%2B%20Plotly-black.svg)](frontend/)
[![Source Immutability](https://img.shields.io/badge/Data%20Policy-Strict%20Read--Only-green.svg)](docs/read-only-data-policy.md)

A complete, modular, final-year major project that empowers users to upload CSV/Excel datasets or connect existing SQL databases, ask analytical questions in natural language, and receive evidence-based answers, statistical calculations, Isolation Forest anomaly detections, XGBoost time-series forecasts, interactive Plotly visualizations, and downloadable reports.

---

## 1. System Architecture

```text
                      Next.js Frontend (Port 3000)
                      TypeScript, Tailwind CSS, Plotly
                                     |
                              REST / SSE Stream
                                     v
                      NestJS Backend 1 (Port 3001)
                      Prisma ORM, Session Persistence
                        |                        |
                        v                        v
                 Neon PostgreSQL         FastAPI Backend 2 (Port 8000)
                 Application DB           LangGraph Orchestrator
                                                 |
             +-----------------------------------+-----------------------------------+
             |                                   |                                   |
             v                                   v                                   v
         SQL Agent                       Statistical Agent                       ML Agent
     (Read-Only Safe)                 (Isolation Forest Model)             (XGBoost Forecaster)
             |                                   |                                   |
             +-----------------------------------+-----------------------------------+
                                                 |
                                                 v
                                        Visualization Agent
                                         (Plotly JS Engine)
                                                 |
                                                 v
                                          Synthesis Agent
                                         (Evidence Fusion)
```

---

## 2. Key Capabilities & Features

1. **Pre-Trained Machine Learning Models (Zero Retraining Required)**:
   - **Isolation Forest Retail Anomaly Detector**: Evaluated with 300 estimators on retail transactions. Identifies unusual order combinations, computes counterfactual feature contributions, and highlights statistical outliers.
   - **XGBoost Recursive Time-Series Forecaster**: 350-tree hist model generating multi-step sales forecasts with external covariates (WTI oil prices, holidays, calendar coordinates, promotion signals). Genuine 16-day validation RMSLE: `0.4088`, WAPE: `17.07%`.
   - **Generic Dataset Fallback**: Automatic unsupervised Isolation Forest and lag-regression forecasters for non-retail schemas.

2. **Strict Read-Only Data Policy & Source Immutability**:
   - Uploaded files are parsed into detached in-memory DataFrames.
   - Cryptographic SHA-256 checksums are verified before and after operations, mathematically guaranteeing source files are never altered, appended to, or overwritten.
   - All results, forecasts, and anomaly exports are stored separately in `storage/generated_results/`.

3. **Safe Read-Only External SQL Connections**:
   - Connect PostgreSQL, MySQL, or SQLite databases.
   - Strict AST/Regex parser rejects all mutations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, `MERGE`).
   - Read-only transaction enforcement and row limits protect source databases. Passwords are never sent to OpenAI or exposed client-side.

4. **Centralized Frontend API Architecture**:
   - Clean, modular Axios request functions in `frontend/src/services/api/`.
   - Zero raw HTTP requests scattered inside UI components.
   - Real-time Server-Sent Events (SSE) streaming progress timeline via `streaming-client.ts`.
   - Selective Zustand state management for shared session, dataset, and database state.

5. **Neon PostgreSQL Application Database & 10-Conversation Retention**:
   - Persists chat sessions and messages using Prisma ORM.
   - Strictly enforces a 10-conversation retention limit per anonymous session, removing the oldest thread and messages in a consistent transaction when exceeded.

6. **Restricted OpenAI Usage**:
   - Only the Orchestrator Agent, SQL Agent, and Synthesis Agent use the OpenAI API key.
   - All statistical calculations, feature engineering, Isolation Forest scoring, XGBoost forecasting, and Plotly visualization generation operate 100% deterministically in Python without OpenAI calls.

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js (App Router), TypeScript, Tailwind CSS, Plotly.js |
| **Frontend API / State** | Centralized Axios Client, Zustand, Browser Fetch SSE |
| **Backend 1** | NestJS, TypeScript, Prisma ORM |
| **Application Database** | Neon PostgreSQL |
| **Backend 2** | Python 3.12+, FastAPI, Uvicorn |
| **Agent Orchestration** | LangGraph, LangChain OpenAI |
| **Machine Learning** | Scikit-learn (Isolation Forest), XGBoost, Pandas, NumPy, SciPy |
| **Testing** | Jest for NestJS; Pytest for Python |

---

## 4. Quick Start & Setup

### Prerequisites
- Node.js `v20+` or `v24+`
- Python `3.10+` or `3.14+`

### Step 1: Clone and Configure Environment
```bash
cp .env.example .env
```
Edit `.env` to configure your `OPENAI_API_KEY` and optional Neon `DATABASE_URL`.

### Step 2: Setup Python Backend 2
```bash
cd backend2
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

### Step 3: Setup NestJS Backend 1
```bash
cd backend1
npm install
npx prisma generate
cd ..
```

### Step 4: Setup Next.js Frontend
```bash
cd frontend
npm install
cd ..
```

---

## 5. Running the System

Start the 3 applications in separate terminal windows:

```bash
# Terminal 1: Python Backend 2 (Port 8000)
cd backend2
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload

# Terminal 2: NestJS Backend 1 (Port 3001)
cd backend1
npm run start:dev

# Terminal 3: Next.js Frontend (Port 3000)
cd frontend
npm run dev
```

Open your browser to: **`http://localhost:3000`**

---

## 6. Running Tests

```bash
# Backend 2 Python Tests (16 tests covering models, immutability, SQL safety, LangGraph)
cd backend2
.\venv\Scripts\python.exe -m pytest

# Backend 1 NestJS Tests (Chat session 10-conversation retention transaction tests)
cd backend1
npm test
```

---

## 7. Model Migration & Cleanup Notice

The original model implementations from the temporary root folders `files/` and `ml_model/` have been migrated into:
- `backend2/app/models/anomaly_detection/`
- `backend2/app/models/forecasting/`
- `backend2/app/models/artifacts/`

The entire application runs independently of `files/` and `ml_model/`. Once verified locally, these two temporary folders can safely be removed:
```powershell
Remove-Item -Recurse -Force files, ml_model
```

---

## 8. Documentation Index

- [Architecture & Technical Specification](docs/architecture.md)
- [Setup & Local Development Guide](docs/setup.md)
- [API Contracts (Backend 1 & Backend 2)](docs/api-contracts.md)
- [Database Schema & 10-Conversation Retention](docs/database-schema.md)
- [Model Integration & Benchmark Diagnostics](docs/model-integration.md)
- [Read-Only Data Policy & Immutability Guarantee](docs/read-only-data-policy.md)
- [Frontend API Layer & State Management](docs/frontend-api-layer.md)
