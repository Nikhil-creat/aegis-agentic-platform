# Aegis Autonomous Agentic Platform

**Enterprise-grade Autonomous Agentic AI Platform** — Multi-agent orchestration, Agentic RAG with reranking, CNN-based visual understanding, secure polyglot code execution, and full observability.

> **Designed and Developed by NIKHIL CHARY SRIRAMOJU**
> BTech CSE | [GitHub](https://github.com/Nikhil-creat) · [LinkedIn](https://in.linkedin.com/in/nikhil-chary-sriramoju-95041b38a)

---

## 1. Architecture Overview

```
                              ┌─────────────────────────────┐
                              │   Next.js Frontend (SSE/WS)  │
                              └───────────────┬──────────────┘
                                              │ HTTPS / WSS
                              ┌───────────────▼──────────────┐
                              │   FastAPI Gateway (JWT/CORS)  │
                              └───┬───────────┬───────────┬───┘
                     ┌────────────┘           │           └─────────────┐
             ┌───────▼───────┐        ┌───────▼───────┐        ┌────────▼────────┐
             │  Agent Service │        │  RAG Service   │        │ Code-Exec Service│
             │ (LangGraph     │        │ (Qdrant + BGE  │        │ (Docker sandbox   │
             │  ReAct loops,  │        │  Reranker +    │        │  ephemeral        │
             │  Guardrails)   │        │  Redis cache)  │        │  workers)         │
             └───────┬───────┘        └───────┬───────┘        └────────┬────────┘
                     │                        │                         │
             ┌───────▼────────────────────────▼─────────────────────────▼───────┐
             │   Celery Workers  ⇆  Redis/RabbitMQ Broker  ⇆  PostgreSQL         │
             └───────┬─────────────────────────────────────────────────┬────────┘
                     │                                                 │
             ┌───────▼───────┐                                ┌────────▼────────┐
             │ CNN Vision Svc │                                │  Observability   │
             │ (PyTorch)      │                                │ OTel/Prometheus/ │
             └────────────────┘                                │ Grafana/Phoenix  │
                                                                 └─────────────────┘
```

### Microservices
| Service | Responsibility | Port |
|---|---|---|
| `gateway` | FastAPI main router, auth, SSE/WS streaming | 8000 |
| `agent-service` | LangGraph ReAct multi-agent orchestration, guardrails | internal |
| `rag-service` | Multi-hop retrieval, query expansion, reranking, semantic cache | internal |
| `vision-service` | CNN-based image/diagram feature extraction | internal |
| `exec-service` | Sandboxed polyglot code execution engine | internal |
| `worker` | Celery async task processing | internal |
| `postgres` | Relational store (users, audit logs, sessions) | 5432 |
| `qdrant` | Vector database | 6333 |
| `redis` | Cache + broker | 6379 |
| `prometheus` / `grafana` | Metrics + dashboards | 9090 / 3001 |

---

## 2. Directory Structure

```
agentic-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint, SSE/WS routes
│   │   ├── core/
│   │   │   ├── config.py           # pydantic-settings env config
│   │   │   ├── security.py         # JWT auth, password hashing
│   │   │   ├── telemetry.py        # OpenTelemetry setup
│   │   │   └── guardrails.py       # input/output safety filters
│   │   ├── agents/
│   │   │   ├── graph.py            # LangGraph orchestration + ReAct loop
│   │   │   ├── tools.py            # tool registry (RAG, code-exec, vision)
│   │   │   └── self_correction.py  # error-driven retry/reflection loop
│   │   ├── rag/
│   │   │   ├── retriever.py        # multi-hop retrieval + query expansion
│   │   │   ├── reranker.py         # cross-encoder / BGE reranker
│   │   │   └── semantic_cache.py   # Redis semantic cache
│   │   ├── execution/
│   │   │   ├── sandbox_manager.py  # Docker ephemeral worker orchestration
│   │   │   └── language_configs.py # per-language image/limits config
│   │   ├── models/
│   │   │   ├── schemas.py          # Pydantic v2 request/response models
│   │   │   └── db_models.py        # SQLAlchemy ORM models
│   │   └── api/
│   │       ├── routes_agents.py
│   │       ├── routes_exec.py
│   │       ├── routes_rag.py
│   │       └── routes_auth.py
│   ├── workers/
│   │   └── celery_app.py           # Celery app + async task defs
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/                    # Next.js app router pages
│   ├── src/components/             # AgentConsole, CodeRunner, ChatStream
│   ├── src/lib/sse.ts              # SSE/WS client hook
│   ├── package.json
│   └── Dockerfile
├── infra/
│   ├── prometheus/prometheus.yml
│   └── grafana/dashboards/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 3. Local Setup & Execution

### Prerequisites
- Docker & Docker Compose v2+
- 8GB+ RAM recommended (CNN + vector DB + LLM calls)
- An LLM provider API key (OpenAI/Anthropic) for agent reasoning

### Steps
```bash
git clone <repo-url> agentic-platform && cd agentic-platform
cp .env.example .env          # fill in OPENAI_API_KEY / ANTHROPIC_API_KEY, JWT_SECRET, etc.

docker compose build
docker compose up -d

# Verify services
docker compose ps
curl http://localhost:8000/health

# Frontend
open http://localhost:3000
```

### Running Tests
```bash
docker compose exec gateway pytest -v --cov=app
```

### Tearing Down
```bash
docker compose down -v   # -v also removes DB/vector volumes
```

---

## 4. Security Notes
- Code execution containers run with `--network none`, `--read-only`, non-root user, `--memory=256m`, `--cpus=0.5`, and a hard wall-clock timeout — enforced in `sandbox_manager.py`.
- JWT access + refresh tokens; secrets loaded via `pydantic-settings` from `.env`, never hardcoded.
- Guardrails layer (`core/guardrails.py`) screens both inbound prompts (injection/jailbreak heuristics) and outbound agent responses (toxicity/PII heuristics) before they reach the user or execution engine.
- All inter-service calls are internal-network-only; only `gateway` and `frontend` are published.

---

## 5. Credits
**Designed & Developed by Nikhil Chary Sriramoju**
Principal Architecture, AI/ML Systems Design & Full-Stack Implementation.
