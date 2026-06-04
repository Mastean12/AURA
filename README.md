# AURA — AI Unified Research Assistant

A full-stack RAG (Retrieval-Augmented Generation) application built with Next.js, FastAPI, PostgreSQL, ChromaDB, LangChain, and OpenAI.

## Stack

| Layer       | Technology                              |
|-------------|-----------------------------------------|
| Frontend    | Next.js 15 + TypeScript + Tailwind CSS  |
| Backend     | FastAPI + SQLAlchemy (async)            |
| Database    | PostgreSQL 16+                          |
| Vector DB   | ChromaDB                                |
| LLM         | OpenAI (GPT-4o / text-embedding-3-small)|
| Orchestration | LangChain                             |

## Project Structure

```
aura/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── api/           # Route handlers
│       ├── services/      # Business logic
│       ├── models/        # SQLAlchemy + Pydantic models
│       ├── database/      # DB connection & ChromaDB client
│       ├── uploads/       # Uploaded files
│       └── vectorstore/   # Local vector store
├── frontend/
│   └── src/
│       ├── app/           # Next.js App Router pages
│       ├── components/    # Reusable UI components
│       ├── lib/           # API client & config
│       └── types/         # TypeScript interfaces
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── docs/
```

## Getting Started

### Prerequisites

- Node.js 22+
- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (optional)

### 1. Clone & configure

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — add your OPENAI_API_KEY
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker (alternative)

```bash
cd docker
docker compose up -d
```

## API Endpoints

| Method | Path                        | Description                 |
|--------|-----------------------------|-----------------------------|
| GET    | `/health`                   | Health check                |
| GET    | `/ping`                     | Minimal health check        |
| POST   | `/api/v1/upload/`           | Upload file (PDF/DOCX/CSV/XLSX) |
| GET    | `/api/v1/documents/`        | List documents              |
| POST   | `/api/v1/chat/`             | Chat with context           |
| POST   | `/api/v1/chat/query`        | Ask a question (RAG)        |
| POST   | `/api/v1/summary/`          | Generate summary            |
| POST   | `/api/v1/analytics/`        | Get data analytics          |
| POST   | `/api/v1/analytics/charts`  | Generate Plotly charts      |
| POST   | `/api/v1/reports/export`    | Export PDF report           |

## Features

- **Upload** — Drag-and-drop file upload for PDF, DOCX, CSV, XLSX
- **Chat** — ChatGPT-style conversational interface with RAG
- **Analytics** — Data profiling with row/column stats, missing values, numeric summaries
- **Charts** — Interactive Plotly bar, pie, and line charts
- **Reports** — AI-generated summaries (executive, findings, recommendations, risks)
- **PDF Export** — Full report generation with embedded charts

## License

MIT
