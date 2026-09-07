# 🚀 Fresher.AI — Next-Gen AI Career Acceleration & RAG Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?style=for-the-badge&logo=qdrant)](https://qdrant.tech/)
[![Google Gemini](https://img.shields.io/badge/Gemini_Embedding_2-768--dim-8E75C2?style=for-the-badge&logo=google)](https://ai.google.dev/)
[![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker_Compose-Local_Dev-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**Fresher.AI** is a production-grade, multimodal AI career acceleration platform tailored for students, freshers, and engineers. It integrates an authoritative **Career Knowledge Base** (`fresher_ai_kb`), **Qdrant Vector Database**, **Gemini Embedding 2 (768-dim)**, and an intelligent **RAG Retrieval Engine** to ground personalizations—delivering personalized learning roadmaps, evidence-based resume ATS audits, and adaptive mock interviews without LLM hallucination.

---

## 🏛️ System Architecture

```text
                                  FRESHER.AI
                                       │
                   ┌───────────────────┴───────────────────┐
                   │                                       │
             React Frontend                         FastAPI Backend
           (Vite, TailwindCSS)                       (Port: 8000)
                                                           │
                   ┌───────────────────────────────────────┼───────────────────┐
                   │                                       │                   │
                 Resume                                 Roadmap               Chat
                   │                                       │                   │
                   └───────────────────┬───────────────────┘                   │
                                       │                                       │
                                Skill Extraction                               │
                                       │                                       │
                              Skill Normalization                              │
                                       │                                       │
                               ┌───────▼───────┐                               │
                               │  RAG ENGINE   │                               │
                               └───────┬───────┘                               │
                                       │                                       │
                             Gemini Embedding 2 (768-dim)                      │
                                       │                                       │
                                 Qdrant Vectors                                │
                               (fresher_ai_knowledge)                          │
                                       │                                       │
                   ┌───────────────────┼───────────────────┐                   │
                   │                   │                   │                   │
                 Skills            Resources            Projects               │
                YouTube             Roadmaps           Interview               │
                 Tools             Playlists            Evidence               │
                                       │                                       │
                                     Redis ◄───────────────────────────────────┘
                                 Cache Results
                                       │
                              Personalized Output
```

---

## 📂 Project Structure

```text
FresherAI/
├── backend_fastapi/              # FastAPI application server
│   ├── app/
│   │   ├── agents/               # AI reasoning agents (Roadmap, Resume, Interview)
│   │   ├── ai/                   # Multi-provider router (Groq, Gemini)
│   │   ├── core/                 # DB, Redis, Security, and Configuration
│   │   ├── routes/               # 100% backward-compatible REST API routers
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Core services: Qdrant, Embedding, Retrieval, SkillGap
│   │   └── main.py               # FastAPI entry point with health checks
│   ├── tests/                    # 31 unit & integration tests
│   ├── Dockerfile                # Multi-stage production Python container
│   ├── requirements.txt          # Python dependencies
│   ├── ingest_kb.py              # Knowledge Base vector ingestion script
│   └── validate_rag.py           # Master 12-point system validation script
├── fresher_ai_kb/                # Authoritative Career Knowledge Base
│   ├── data/                     # 17 domain modules (Roles, Skills, Roadmaps, Projects, etc.)
│   ├── json_export/              # Pre-exported structured payloads
│   └── export_json.py            # JSON & payload exporter
├── frontend/                     # React 19 + Vite frontend
│   ├── src/                      # UI components, pages, Redux store, and API clients
│   ├── Dockerfile                # Multi-stage Node/Nginx container
│   ├── nginx.conf                # Reverse proxy for local frontend container
│   └── package.json              # NPM dependencies
├── .github/workflows/ci.yml      # CI pipeline for linting, tests, and Docker builds
├── docker-compose.yml            # Multi-service local orchestrator (App + Redis + Qdrant)
├── ingest_kb.py                  # Root launcher for KB ingestion
├── validate_rag.py               # Root launcher for RAG validation suite
├── .env.example                  # Environment configuration template
├── render.yaml                   # Cloud deployment blueprint
└── README.md                     # Platform documentation
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `backend_fastapi/.env`:

```env
# Server
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-or-anon-key

# Redis
REDIS_URL=redis://localhost:6379

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_KB_COLLECTION=fresher_ai_knowledge

# Embeddings (Configurable source of truth)
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768

# LLM Providers
GROQ_API_KEY=your_groq_api_key
GROQ_FAST_MODEL=llama-3.3-70b-versatile
GROQ_COMPLEX_MODEL=openai/gpt-oss-120b
LLM_MODEL=llama-3.3-70b-versatile

GEMINI_API_KEY=your_gemini_api_key
GEMINI_FAST_MODEL=gemini-2.0-flash
GEMINI_COMPLEX_MODEL=gemini-2.5-pro

# Auth & Billing
FIREBASE_SERVICE_ACCOUNT_PATH=app/config/serviceAccountKey.json
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

---

## 🚀 Quickstart & Local Development

### 1. Ingest Knowledge Base into Qdrant

Ingest all 471 canonical records across 17 sheets into the 768-dimension collection:

```bash
# From workspace root
python ingest_kb.py

# Or inside backend_fastapi
cd backend_fastapi
python ingest_kb.py
```

### 2. Validate System & RAG Pipeline

Run the comprehensive 12-point validation check:

```bash
python validate_rag.py
```

Expected output:
```text
======================================================================
🔍 FRESHER.AI MASTER SYSTEM VALIDATION SUITE
======================================================================
[01/12] Environment Config ............ PASS  Model: gemini-embedding-2, Dim: 768
[02/12] Embedding Generation .......... PASS  Vector size: 768
[03/12] Qdrant Connection ............. PASS  Collection: fresher_ai_knowledge
[04/12] Vector Dimension & Count ...... PASS  Points: 471, Dim: 768
[05/12] Semantic Search ............... PASS  Retrieved 2 resources
[06/12] Metadata Filtering (YouTube) .. PASS  Found verified playlists
[07/12] Skill Normalization ........... PASS  Mapped ReactJS->React, Mongo->MongoDB
[08/12] Skill Gap Engine .............. PASS  Strong: 2, Missing: 14
[09/12] Roadmap RAG Generation ........ PASS  Modules generated: 6, Grounded: True
[10/12] Resume RAG Analysis ........... PASS  Skills: 3, Score: 55
[11/12] Redis Caching ................. PASS  Cache write & read verified
[12/12] API Health Endpoints .......... PASS  /health: 200, /health/dependencies: 200
======================================================================
VALIDATION SUMMARY: 12/12 CHECKS PASSED
======================================================================
```

### 3. Run Automated Tests

Execute all 31 unit, integration, and RAG tests:

```bash
cd backend_fastapi
pytest tests -v
```

---

## 🐳 Docker Compose Architecture

Run the full platform locally with all four services:

```bash
# Start all containers
docker compose up --build

# Verify config
docker compose config
```

### Services & Ports:
| Service | Image / Build | Port | Purpose |
| :--- | :--- | :--- | :--- |
| `frontend` | `./frontend/Dockerfile` | `5173:80` | React 19 UI with Nginx reverse proxy |
| `backend` | `./backend_fastapi/Dockerfile` | `8000:8000` | FastAPI application server |
| `redis` | `redis:7-alpine` | `6379:6379` | In-memory caching & session state |
| `qdrant` | `qdrant/qdrant:latest` | `6333:6333` | Vector search & knowledge indexing |

Containers communicate using internal Docker DNS names (`backend:8000`, `redis:6379`, `qdrant:6333`).

---

## 🔍 Core Platform Components

### 1. Authoritative Knowledge Base (`fresher_ai_kb`)
- The single source of truth containing 25 career roles, 139+ canonical skills, verified YouTube educators and playlists (India-relevant & global), portfolio projects, interview question rubrics, and week-by-week progressive outlines.

### 2. Qdrant Service (`app/services/qdrant_service.py`)
- Manages collection lifecycle with strict 768-dim validation.
- Creates payload indexes on `entity_type`, `role_ids`, `skill_ids`, `difficulty`, `category`.
- Supports filtered vector similarity search with cosine distance.

### 3. Skill Gap Engine (`app/services/skill_gap_engine.py`)
- Normalizes informal candidate skills (`"ReactJS"` $\to$ `"React"`, `"Fast API"` $\to$ `"FastAPI"`, `"Mongo"` $\to$ `"MongoDB"`).
- Compares candidate skills against role requirements to categorize skills into `Strong`, `Partial`, and `Missing`.
- Orders missing skills to respect progressive learning prerequisites (Beginner $\to$ Intermediate $\to$ Advanced).

### 4. RAG Roadmap Agent (`app/agents/roadmap_agent.py`)
- Grounded strictly in retrieved Knowledge Base records.
- Skips already mastered fundamentals and prioritizes missing skill gaps.
- Replaces generic YouTube search links with verified playlists and documentation.

### 5. RAG Resume Agent (`app/agents/resume_agent.py`)
- Normalizes resume skills against canonical KB skills.
- Retrieves target role expectations and evidence patterns from Qdrant.
- Adheres to the Google X-Y-Z formula (`Accomplished [X] as measured by [Y] by doing [Z]`) using bracketed placeholders (`[X]%`) to prevent metric hallucination.

### 6. Health Check Endpoints
- `GET /health`: Lightweight service ping (`{"status": "ok"}`).
- `GET /health/dependencies`: Deep health report on Backend, Redis, Qdrant, and Database.

---

## ☁️ Future GCP Deployment Target

When ready for Google Cloud Platform production deployment:

```text
GitHub Push (main)
        ↓
GitHub Actions (CI/CD)
        ↓
Google Artifact Registry (Container Images)
        ↓
Google Cloud Run (FastAPI Backend Container)
        │
        ├── Google Cloud Memorystore (Redis)
        ├── Supabase PostgreSQL / Cloud SQL
        └── Qdrant Cloud (Managed Vector DB)
```

- **Cloud Run**: Host containerized FastAPI with automatic autoscaling to zero.
- **Secret Manager**: Securely inject `GEMINI_API_KEY`, `GROQ_API_KEY`, `SUPABASE_KEY`.
- **Memorystore**: Managed Redis cluster for distributed caching.
- **Vercel / Cloud Run**: Frontend hosting with global CDN.

---

## 📄 License
Fresher.AI is proprietary software. All rights reserved.
