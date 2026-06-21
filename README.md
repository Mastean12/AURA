# AURA — AI Unified Research Assistant & Enterprise Intelligence Platform

A full-stack AI-powered analytics platform that transforms raw data into executive intelligence. From descriptive analytics and forecasting to autonomous AI analysis and board-ready reporting.

## Stack

| Layer       | Technology                              |
|-------------|-----------------------------------------|
| Frontend    | Next.js 15 + TypeScript + Tailwind CSS + Lucide Icons |
| Backend     | FastAPI + SQLAlchemy (async)            |
| Database    | PostgreSQL 16+                          |
| Vector DB   | ChromaDB                                |
| LLM         | Gemini 2.5 Flash (primary), Gemini 2.0 Flash (fallback), OpenAI GPT-4o |
| AI SDK      | google-genai, openai                    |
| Charts      | Plotly (backend) + SVG/HTML (frontend)  |
| Reports     | fpdf2 (PDF generation)                  |

## Architecture

```
Frontend (Next.js App Router)
  │ fetch()
  ▼
API Layer (FastAPI — 7 routers, 30+ endpoints)
  │
  ├── /api/v1/documents/       — Upload, list, delete, classify documents
  ├── /api/v1/chat/            — General chat & RAG query
  ├── /api/v1/analytics/       — Column stats, charts, insights, health, chat
  ├── /api/v1/predictive/      — Forecasting, anomalies, risk scoring, recommendations
  ├── /api/v1/enterprise/      — Industry dashboards, multi-doc, comparison, autonomous analysis
  ├── /api/v1/summary/         — AI summaries by type
  └── /api/v1/reports/         — Analytics report + board report + executive briefing PDFs
  │
  ▼
Business Services (16 services)
  │ generate_response()
  ▼
AI Layer (gemini_client.py → ai_service.py)
  │
  ├── Primary: gemini-2.5-flash (3 retries, exponential backoff)
  ├── Fallback: gemini-2.0-flash
  └── Secondary: OpenAI GPT-4o (3 retries, exponential backoff)
```

## Project Structure

```
aura/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app, middleware, health endpoints
│       ├── config.py            # Pydantic Settings (env-file based)
│       ├── api/                 # Route handlers
│       │   ├── upload.py        # Document CRUD + upload
│       │   ├── chat.py          # Chat + RAG
│       │   ├── summary.py       # AI summaries
│       │   ├── analytics.py     # Column analysis, insights, charts, health, chat
│       │   ├── predictive.py    # Forecast, anomalies, risk, recommendations
│       │   ├── enterprise.py    # Industry, multi-doc, comparison, autonomous
│       │   └── reports.py       # PDF report generation
│       ├── services/            # 22 business logic services
│       ├── models/              # SQLAlchemy + Pydantic models
│       ├── database/            # Async engine, session factory, migrations
│       ├── uploads/             # Uploaded files
│       └── vectorstore/         # Local vector store
├── frontend/
│   └── src/
│       ├── app/                 # Next.js App Router pages
│       │   ├── page.tsx         # Dashboard
│       │   ├── upload/          # Document Manager with type classification
│       │   ├── chat/            # Conversational AI chat
│       │   ├── analytics/       # Executive Summary, Health Score, KPIs, Charts, Insights
│       │   ├── predictive/      # Forecast Dashboard, Anomalies, Risk Scorecard, Recommendations
│       │   ├── enterprise/      # Industry Intelligence, Multi-Doc, Comparison, Autonomous Analyst
│       │   └── reports/         # Summary export & PDF generation
│       ├── components/          # Sidebar, UploadZone, HealthCheck, TypingIndicator
│       ├── lib/                 # API client (all endpoints) & config
│       └── types/               # TypeScript interfaces
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── docs/
```

## Features

### Phase 1 — AI Executive Intelligence
- **Executive Summary** — AI-generated 2-3 sentence business overview with confidence score
- **Smart KPI Discovery** — Auto-detect Finance/Sales/HR/Operations KPIs from column names
- **AURA Intelligence** — Key findings, risks, opportunities, recommendations with confidence
- **Chart Insight Cards** — AI explains what happened, why, and recommended action for every chart
- **Analytics Chat** — Conversational Q&A over datasets with session history
- **Business Health Score** — Dataset quality scoring across completeness, quality, consistency

### Phase 2 — Executive Predictive Intelligence
Full 7-module pipeline that transforms model outputs into executive decisions.

- **Prediction Explanation Engine** — Translates model outputs into business language
  - SHAP-style feature importance ranking with percentage contribution
  - Confidence calculation from data quality, sample size, model performance, feature strength
  - Natural-language executive summary explaining what was predicted, why, and business impact
- **Forecast Timeline Engine** — Multi-model forecasting with automatic model selection
  - 30-day, 90-day, 180-day, 365-day projections with confidence bands
  - Four competing models: linear trend, quadratic trend, exponential smoothing, Random Forest (lag-based)
  - Auto-selects best performer by RMSE on holdout validation
  - Trend direction (up/down/stable), growth %, and confidence per horizon
- **Segment-Level Prediction Engine** — Automatically identifies driving segments
  - Numeric columns split at median into high/low risk groups
  - Categorical columns scored per category (min 5 records per segment)
  - Each segment includes risk score, population count, and estimated revenue impact
- **What-If Simulation Engine** — Tests business strategies before implementation
  - Five scenario types: retention program, price change, budget increase, contract changes, staffing changes
  - Automatically selects the highest-correlated feature as lever
  - Outputs before/after values, change %, and improvement direction
- **Early Warning System** — Detects threats before they become critical
  - Rapid-change monitoring: warning if recent 5-period mean deviates >10% from earlier baseline
  - Anomaly spike detection: z-score > 3 flags unusual patterns
  - Severity: critical (>30% change), high (>10%), medium (decreases or spikes)
  - Each alert includes impact statement and recommended action
- **Prescriptive Analytics** — Recommends actions ranked by priority
  - Action recommendation with expected impact %, revenue preserved, ROI, and effort level
  - Priority score (0–100) based on risk severity
- **Industry Intelligence Layer** — Business-context-aware analysis
  - Auto-detects industry from column names (Telecom, Retail, Banking, Insurance, Manufacturing, Healthcare, Logistics, SaaS)
  - Industry-specific KPI library (5 KPIs per industry)
  - Industry-specific recommendations (3 risk/recommendation/impact triplets per industry)
  - Forecast enrichment with industry-context commentary
- **Autonomous Pipeline** — End-to-end orchestration
  - Data quality audit → problem detection → model selection → prediction → risk analysis → explanation → simulation → report

### Phase 3 — Enterprise Intelligence
- **Industry Intelligence** — Auto-detect business domain (Finance/Sales/HR/Operations/NGO)
  - Industry-specific KPI cards and strategic recommendations
- **Multi-Document Intelligence** — Analyze multiple documents together
  - Consolidated summary, cross-document themes, conflicts, and cross-references
- **Cross-Document Comparison** — Compare two documents side-by-side
  - Similarities, differences, key changes, recommended actions
- **Board-Level Reports** — Professional 10-section board-ready PDF export with embedded charts

### Phase 4 — Autonomous AI Analyst
- **Autonomous Analysis** — One-click organizational assessment
  - Business Health Score, Top 5 Risks, Top 5 Opportunities, 30/90/365-day forecasts
  - Strategic recommendations with impact/urgency/confidence ratings
- **Executive Briefing** — One-page CEO-ready briefing with summary, health, risks, opportunities, forecast, actions

### Platform Features
- **Document Manager** — File upload with type classification (PDF/Word/Excel/Other)
  - Grouped document library with individual & batch delete
- **AI Reliability** — Retry with exponential backoff (3 attempts), fallback model, user-friendly error messages
  - Request ID tracing across all logs, AI health monitoring endpoint
- **Industry Coverage** — Telecom, Retail, Banking, Insurance, Manufacturing, Healthcare, Logistics, SaaS, General Business

## Getting Started

### Prerequisites

- Node.js 22+
- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (optional)
- Gemini API key (or OpenAI API key)

### 1. Clone & configure

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — add your GEMINI_API_KEY or OPENAI_API_KEY
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux:   source .venv/bin/activate
pip install -r requirements.txt
python run.py
# Server starts at http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# App starts at http://localhost:3000
```

### 4. Docker (alternative)

```bash
cd docker
docker compose up -d
```

## API Endpoints

### Core
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ai` | AI provider health (model, latency, key status) |
| GET | `/ping` | Minimal health check |
| GET | `/test-ai` | Test AI provider connectivity |

### Documents
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/documents/` | List all documents |
| POST | `/api/v1/documents/` | Create document metadata |
| GET | `/api/v1/documents/{id}` | Get single document |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/documents/batch-delete` | Bulk delete documents |
| POST | `/api/v1/upload/` | Upload file (PDF/DOCX/CSV/XLSX) |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat/` | Chat with message history |
| POST | `/api/v1/chat/query` | RAG query with context retrieval |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analytics/` | Column-level statistics |
| POST | `/api/v1/analytics/charts` | Plotly charts for a column |
| POST | `/api/v1/analytics/charts/all` | All chart types + correlation heatmap |
| POST | `/api/v1/analytics/insights` | AI-generated insights (findings, risks, opportunities) |
| POST | `/api/v1/analytics/executive-summary` | AI executive summary |
| POST | `/api/v1/analytics/health` | Dataset health scoring |
| GET | `/api/v1/analytics/kpis` | Smart KPI discovery |
| POST | `/api/v1/analytics/chat` | Conversational analytics over dataset |
| POST | `/api/v1/analytics/chart-insight` | AI chart insight (what/why/action) |

### Predictive
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/predictive/forecast` | Time-series forecast with confidence intervals |
| POST | `/api/v1/predictive/anomalies` | Anomaly detection with severity scores |
| POST | `/api/v1/predictive/risk-score` | Business risk scoring (0-100) |
| POST | `/api/v1/predictive/recommendations` | AI strategic recommendations |
| POST | `/api/v1/predictive/analysis` | Full executive predictive analysis (7-module pipeline) |

### Enterprise
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/analytics/industry-dashboard` | Industry detection + KPI dashboard |
| POST | `/api/v1/analytics/multi-document` | Multi-document intelligence |
| POST | `/api/v1/analytics/compare` | Cross-document comparison |
| POST | `/api/v1/analytics/autonomous-analysis` | Full autonomous organizational analysis |

### Reports
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/summary/` | Generate AI summary by type |
| POST | `/api/v1/reports/export` | Export analytics PDF report |
| POST | `/api/v1/reports/board-report` | Board-level PDF report (10 sections) |
| POST | `/api/v1/reports/executive-briefing` | One-page executive briefing |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `AURA` | Application name |
| `DEBUG` | `true` | Debug mode (SQL echo, verbose logs) |
| `SECRET_KEY` | `change-me` | App secret key |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL async connection string |
| `AI_PROVIDER` | `gemini` | Active AI provider (`gemini` or `openai`) |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model |
| `OPENAI_API_KEY` | — | OpenAI API key (fallback) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model |
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8000` | ChromaDB port |

## License

MIT
