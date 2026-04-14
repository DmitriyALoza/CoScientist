# CoScientist

An autonomous AI co-scientist for wet-lab biology. CoScientist wraps a multi-agent LangGraph system — literature scout, hypothesis generator, SOP adapter, experiment manager, and more — behind a production-grade web interface built with Next.js and FastAPI.

## Architecture

```
CoScientist/
├── frontend/          # Next.js 16 + React 19 + TypeScript + Tailwind CSS v4
├── backend/           # FastAPI + LangGraph agent system
└── docker-compose.yml # Postgres + Qdrant + MinIO + backend + frontend
```

The two services are independently deployable. Each has its own `Dockerfile` and can be built and run without the other.

**Why FastAPI instead of Next.js API routes?** The agent system runs on LangGraph with persistent async event loops — it's architecturally cleanest as a dedicated Python process. Next.js API routes would be a thin proxy adding latency for no gain.

## Agent Roster

| Agent | Role |
|-------|------|
| `literature_scout` | PubMed + Semantic Scholar search, local KB retrieval |
| `hypothesis_generator` | Brainstorms and ranks hypotheses with novelty/feasibility/evidence scores |
| `debate_manager` | Planner / Critic / Red Team multi-agent stress-testing |
| `sop_adapter` | Protocol adaptation, SOP diffs, risk flagging |
| `controls_generator` | QC checklist generation by assay type |
| `troubleshooter` | Interactive diagnosis for unexpected results (validation mode) |
| `eln_scribe` | Renders run data into structured ELN markdown |
| `experiment_manager` | Closed-loop experiment planning and iteration tracking |
| `memory_agent` | Workspace knowledge storage and retrieval |
| `tool_executor` | Experiment simulation and cost estimation |
| `data_analyst` | Statistical analysis and plotting |
| `image_analyst` | Lab image classification (western blots, gels, microscopy) |
| `structure_analyst` | AlphaFold / ColabFold protein folding (premium) |

Chat mode determines routing:

- **Normal** — general assistant, routes based on user intent
- **Validation** — troubleshoots unexpected results
- **Protocol** — adapts SOPs and generates controls

## Pages

| Route | Description |
|-------|-------------|
| `/dashboard` | Metrics overview — ELN count, citations, hypotheses, experiments, KB stats |
| `/chat` | Real-time streaming chat with agent badge, citations panel, tool trace |
| `/documents` | Knowledge base management — ingest PDFs, SOPs, reports; semantic search |
| `/hypotheses` | Hypothesis sets with score breakdowns and debate history |
| `/experiments` | Closed-loop experiment tracking with iteration progress |
| `/how-it-works` | Architecture overview and agent explainer |
| `/settings` | LLM provider, model, observability, and workspace config |

## API Endpoints

```
GET  /api/health
GET  /api/metrics
GET  /api/runs
POST /api/runs
GET  /api/runs/{run_id}
GET  /api/runs/{run_id}/eln
GET  /api/runs/{run_id}/citations
GET  /api/hypotheses
GET  /api/experiments
GET  /api/kb/stats
POST /api/kb/ingest
POST /api/kb/search
WS   /api/chat
```

## Infrastructure

| Service | Image | Purpose |
|---------|-------|---------|
| `postgres` | postgres:16-alpine | Session checkpointing, future auth |
| `qdrant` | qdrant/qdrant | Vector database for RAG / knowledge base |
| `minio` | minio/minio | S3-compatible object store for artifacts |
| `backend` | local build | FastAPI + LangGraph agents |
| `frontend` | local build | Next.js web interface |

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- API key for at least one LLM provider (Anthropic, OpenAI, or Google)

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```env
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...
# or
GOOGLE_API_KEY=...
```

### 2. Start everything

```bash
docker compose up --build
```

This starts all five services in the correct dependency order. On first boot, MinIO creates the `eln-kb` bucket automatically.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| MinIO console | http://localhost:9001 |
| Qdrant dashboard | http://localhost:6333/dashboard |

### 3. Stop

```bash
docker compose down        # stop containers, keep volumes
docker compose down -v     # stop and delete all data
```

## Local Development (without Docker)

Run the backend and frontend separately for faster iteration.

### Backend

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
cd backend
cp .env.example .env      # add your API key
uv sync
uv run uvicorn main:app --reload --port 8000
```

Requires Qdrant and MinIO running locally, or set `STORAGE_BACKEND=local` and `QDRANT_URL=http://localhost:6333` in `.env`.

### Frontend

Requires Node.js 22+.

```bash
cd frontend
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Open http://localhost:3000.

## WebSocket Chat Protocol

The chat endpoint at `ws://localhost:8000/api/chat` uses a simple streaming protocol.

**Client → Server:**
```json
{
  "type": "message",
  "content": "What controls do I need for a flow cytometry panel?",
  "mode": "normal",
  "thread_id": "optional-uuid-for-conversation-continuity",
  "user_id": "default",
  "run_id": null,
  "docs": [{ "name": "protocol.txt", "text": "..." }]
}
```

**Server → Client (streamed):**
```json
{ "type": "token",     "text": "For a...",        "agent": "controls_generator" }
{ "type": "citation",  "citation": { ... } }
{ "type": "tool_call", "tool_call": { ... } }
{ "type": "done",      "thread_id": "abc-123",    "agent": "controls_generator" }
{ "type": "error",     "message": "..." }
```

## Tech Stack

**Frontend**
- Next.js 16 (App Router) + React 19 + TypeScript
- Tailwind CSS v4 + `@tailwindcss/typography`
- Recharts (dashboard charts)
- TanStack Query v5 (data fetching)
- `react-markdown` (agent response rendering)
- Lucide React (icons)

**Backend**
- FastAPI + uvicorn
- LangGraph + LangChain (multi-agent orchestration)
- Qdrant (vector search)
- Anthropic / OpenAI / Google Gemini / Ollama (LLM providers)
- sentence-transformers (local embeddings)
- boto3 + MinIO (S3-compatible object storage)
- PostgreSQL (via SQLAlchemy, for checkpointing)
- OpenTelemetry (optional tracing)

## Premium Features

The following capabilities are available as add-ons and are disabled by default:

| Feature | Description |
|---------|-------------|
| R Analysis Runtime | Execute R scripts, analyze statistical outputs, import Rmd notebooks |
| ColabFold Integration | AlphaFold2 structure predictions directly from the workflow |

Contact us to enable premium features for your deployment.

## License

MIT
