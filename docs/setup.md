# Complete Setup & Local Development Guide

## 1. Environment & Runtime Prerequisites

Ensure your system has the following runtimes installed:
- **Node.js**: `v20.0.0` or higher (`v24.x` recommended)
- **npm**: `v10.x` or `v11.x`
- **Python**: `3.10` or higher (`3.12` - `3.14` supported)

---

## 2. Step-by-Step Installation

### Step 2.1: Python Backend 2 Setup
```bash
cd backend2

# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (Linux / macOS: source venv/bin/activate)

# 3. Install dependencies
pip install -r requirements.txt
```

### Step 2.2: NestJS Backend 1 Setup
```bash
cd ../backend1

# 1. Install dependencies
npm install

# 2. Generate Prisma Client
npx prisma generate
```

### Step 2.3: Next.js Frontend Setup
```bash
cd ../frontend

# 1. Install dependencies
npm install
```

---

## 3. Environment Configuration

Copy `.env.example` at the workspace root to `.env`:
```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:
```dotenv
# 1. OpenAI API Key (Only used by Orchestrator, SQL Agent, and Synthesis Agent)
OPENAI_API_KEY=sk-proj-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# 2. Neon PostgreSQL Connection URL
# Replace with your connection string from console.neon.tech
DATABASE_URL="postgresql://username:password@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
DIRECT_URL="postgresql://username:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require"

# 3. Service Ports
FRONTEND_URL=http://localhost:3000
BACKEND1_PORT=3001
BACKEND1_URL=http://localhost:3001
BACKEND2_PORT=8000
BACKEND2_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND1_URL=http://localhost:3001
```

### Applying Prisma Migrations to Neon
Once your `DATABASE_URL` is set, push the schema to Neon:
```bash
cd backend1
npx prisma db push
```

---

## 4. Running the Applications

Start each application independently in separate terminal windows:

### Terminal 1: Python FastAPI Backend 2 (Port 8000)
```bash
cd backend2
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: NestJS Backend 1 (Port 3001)
```bash
cd backend1
npm run start:dev
```

### Terminal 3: Next.js Frontend (Port 3000)
```bash
cd frontend
npm run dev
```

Visit the dashboard in your browser:
**`http://localhost:3000`**

---

## 5. Running Automated Test Suites

### 5.1 Backend 2 Python Tests (Pytest)
Verifies Isolation Forest inference, XGBoost sales forecasting, strict source-data immutability, SQL read-only validation, and LangGraph workflow orchestration:
```bash
cd backend2
.\venv\Scripts\python.exe -m pytest
```

### 5.2 Backend 1 NestJS Tests (Jest)
Verifies the 10-conversation retention transaction logic, session history, and gateway communication:
```bash
cd backend1
npm test
```

---

## 6. Removing Temporary Model Folders

The trained Isolation Forest model, XGBoost model, feature engineering pipelines, metadata, and reference history have been migrated into `backend2/app/models/`.

Both Backend 1 and Backend 2 operate completely independently of the root-level `files/` and `ml_model/` folders.

Once you have verified the application locally, you can safely delete the two temporary source folders:
```powershell
Remove-Item -Recurse -Force files, ml_model
```
