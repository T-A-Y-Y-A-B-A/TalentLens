# TalentLens — Complete Technology Stack & Architectural Defense

> This document maps **every technology** used in TalentLens to the **specific feature/module** it powers, explains **why** it was chosen over the alternatives listed in the assignment brief, and describes the **end-to-end data flow** for each major feature.

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Infrastructure & DevOps](#2-infrastructure--devops)
3. [Module 1 — Authentication](#3-module-1--authentication)
4. [Module 2 — Organization Management & Multi-Tenancy](#4-module-2--organization-management--multi-tenancy)
5. [Module 3 — Recruitment Module](#5-module-3--recruitment-module)
6. [Module 4 — Candidate Portal](#6-module-4--candidate-portal)
7. [Module 5 — Resume Parsing](#7-module-5--resume-parsing)
8. [Module 6 — AI Candidate Matching](#8-module-6--ai-candidate-matching)
9. [Module 7 — AI Recruiter Copilot](#9-module-7--ai-recruiter-copilot)
10. [Module 8 — Interview Scheduler](#10-module-8--interview-scheduler)
11. [Module 9 — AI Interview Feedback](#11-module-9--ai-interview-feedback)
12. [Module 10 — Analytics Dashboard](#12-module-10--analytics-dashboard)
13. [Production-Grade Requirements](#13-production-grade-requirements)
14. [AI Engineering — Deep Dive](#14-ai-engineering--deep-dive)
15. [Frontend Stack — Deep Dive](#15-frontend-stack--deep-dive)
16. [Full Dependency Map](#16-full-dependency-map)

---

## 1. High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                               │
│  Next.js 16 (App Router) · React 19 · Tailwind 4 · Shadcn/UI    │
│  Staff Dashboard  (/dashboard/*)   Candidate Portal  (/portal/*) │
└──────────────────────────┬────────────────────────────────────────┘
                           │ HTTPS (relative /api/v1/*)
                           │ Next.js rewrites → backend:8000
┌──────────────────────────▼────────────────────────────────────────┐
│                       API LAYER (FastAPI)                          │
│  Uvicorn · ASGI · OpenAPI/Swagger · Rate Limiting (SlowAPI)       │
│  Structured Logging (structlog) · Request IDs (asgi-correlation)  │
│  JWT Auth · Casbin RBAC · Pydantic v2 Validation                  │
└───┬──────────┬──────────┬──────────┬──────────┬───────────────────┘
    │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌──────────────┐
│Postgres││ Redis  ││ Qdrant ││ MinIO  ││ Celery       │
│  15    ││  7     ││ Vector ││ Object ││ Workers      │
│(asyncpg)│(Broker)││  DB    ││Storage ││(Background)  │
└────────┘└────────┘└────────┘└────────┘└──────┬───────┘
                                                │
                                    ┌───────────▼──────────┐
                                    │   AI / ML Layer       │
                                    │  LiteLLM + Instructor │
                                    │  Sentence-Transformers│
                                    │  FastEmbed (BM25)     │
                                    │  CrossEncoder         │
                                    │  Docling + PyPDF      │
                                    └───────────────────────┘
```

### Why This Stack Instead of the Alternatives

| Layer | We Used | Assignment Also Suggested | Why We Chose Ours |
|---|---|---|---|
| **Backend** | FastAPI | Django Ninja | FastAPI is the assignment's primary recommendation. Native `async/await`, automatic OpenAPI docs, and Pydantic-first design make it ideal for an AI-heavy platform with many I/O-bound calls. |
| **Frontend** | Next.js 16 + React 19 | Remix | Next.js is the assignment's primary recommendation. App Router provides RSC, layouts, and built-in API proxy rewrites. React 19 gives us concurrent rendering for responsive UIs. |
| **Database** | PostgreSQL 15 | MariaDB | Primary recommendation. Superior JSON column support, ACID compliance, and the ecosystem around `asyncpg` + SQLAlchemy 2.0 async. |
| **ORM** | SQLAlchemy 2.0 (async) | Tortoise ORM | Primary recommendation. SQLAlchemy 2.0's new async engine is mature, battle-tested, and has the deepest community support. |
| **Cache / Broker** | Redis 7 | Valkey | Valkey is a Redis fork with identical API. We use the original Redis image as it remains the most widely documented and supported. |
| **Background Jobs** | Celery + Redis | Dramatiq, ARQ | Celery is the most mature Python task queue with robust retry logic, result backends, and monitoring tooling. |
| **Vector DB** | Qdrant | Weaviate, Milvus, Chroma, pgvector | Qdrant natively supports **hybrid search** (dense + sparse in a single query via Reciprocal Rank Fusion), named vectors, and metadata filtering — all critical for our multi-tenant matching pipeline. pgvector lacks sparse vector support entirely. |
| **Object Storage** | MinIO | SeaweedFS | MinIO is the industry-standard S3-compatible self-hosted storage. Using `boto3` means zero code changes to migrate to AWS S3 in production. |
| **AI Framework** | LiteLLM + Instructor | LangGraph, LlamaIndex, Haystack, PydanticAI | We intentionally avoided heavyweight frameworks. LiteLLM gives us **model-agnostic routing** (swap Groq for OpenAI with a config change), while Instructor gives us **Pydantic-validated structured outputs** from any LLM. This is leaner, more debuggable, and avoids the abstraction overhead of LangChain/LlamaIndex for our use case. |
| **Embeddings** | `BAAI/bge-small-en-v1.5` (sentence-transformers) + `Qdrant/bm25` (fastembed) | bge-large, bge-m3, Nomic, E5, Jina | `bge-small` (384 dimensions) is a deliberate choice: it runs efficiently on CPU in Docker containers, has excellent quality for its size on MTEB benchmarks, and keeps Qdrant storage lean. The sparse model (`Qdrant/bm25` via fastembed) handles exact keyword matching that dense models miss. |
| **Document Parsing** | Docling + PyPDF (fallback) | Open Parse, MarkItDown, Unstructured | Docling preserves layout, tables, and heading structure for downstream LLM processing. PyPDF serves as a lightweight fallback when Docling encounters edge-case PDFs. |
| **RBAC** | Casbin | — | Casbin is the assignment's recommended RBAC engine. It supports policy-as-code (CSV file), role hierarchy (`hr_manager` inherits `recruiter` permissions), and can be hot-reloaded without restart. |

---

## 2. Infrastructure & DevOps

### Docker & Docker Compose

**What:** The entire platform runs as **7 containers** orchestrated by `docker-compose.yml`:

| Container | Image | Port | Purpose |
|---|---|---|---|
| `postgres` | `postgres:15-alpine` | 5433:5432 | Primary relational database |
| `redis` | `redis:7-alpine` | 6379 | Celery broker + AI response cache + JWT blacklist |
| `qdrant` | `qdrant/qdrant:latest` | 6333, 6334 | Vector search engine |
| `minio` | `minio/minio:RELEASE.2024-03-30` | 9000, 9001 | S3-compatible object storage |
| `backend` | Custom (FastAPI) | 8000 | API server |
| `celery-worker` | Same as backend | — | Background task processor |
| `frontend` | Custom (Next.js) | 3000 | Web application |

**Why Docker:** One-command startup (`docker compose up`), consistent environments, and health checks on every service ensure the system is fully operational before dependent services start.

**Health Checks:** Every container defines health checks:
- Postgres: `pg_isready`
- Redis: `redis-cli ping`
- Qdrant: TCP socket check on port 6333
- MinIO: `mc ready local`
- Backend: HTTP GET to `/health`
- Frontend: HTTP GET to `localhost:3000`
- Celery: `celery inspect ping`

**Startup Order:** Docker Compose `depends_on` with `condition: service_healthy` ensures:
```
postgres, redis, qdrant, minio  →  backend  →  celery-worker, frontend
```

---

## 3. Module 1 — Authentication

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Password Hashing | `bcrypt` (via `passlib`) | Industry-standard adaptive hashing. Slow-by-design to resist brute force. |
| JWT Signing | `python-jose` (HS256) | Lightweight JWT library with cryptographic backend. |
| OAuth2 | `authlib` + `httpx` | `authlib` handles the complete OAuth2/OIDC flow. `httpx` is the async HTTP client for token exchange. |
| Token Storage | PostgreSQL (`RefreshToken` table) | Refresh tokens are **hashed** (SHA-256) before storage — never stored in plain text. |
| JWT Blacklist | Redis | O(1) lookup for blacklisted JTI (JWT ID) claims. Tokens are blacklisted on logout. |
| Email Verification | Celery worker | Async email dispatch prevents registration API from blocking on SMTP. |

### End-to-End Flow: Registration

```
1. POST /api/v1/auth/register { email, password, org_name }
   │
2. ├─ Check if email exists in Postgres → 400 if duplicate
   │
3. ├─ Create Organization (Module 2)
   │
4. ├─ Hash password with bcrypt → Store User with role=HR_MANAGER
   │
5. ├─ Generate verification token (secrets.token_urlsafe)
   │     └─ Hash token (SHA-256) → Store in EmailVerification table
   │
6. ├─ Dispatch Celery task: send_verification_email(email, raw_token)
   │
7. └─ Return User object (201 Created)
```

### End-to-End Flow: Login

```
1. POST /api/v1/auth/login { email, password }
   │
2. ├─ Fetch User by email → 401 if not found
   │
3. ├─ bcrypt.checkpw(password, hashed_password) → 401 if mismatch
   │
4. ├─ Check is_verified → 403 if email not verified
   │
5. ├─ Generate Access Token (JWT, 30min TTL)
   │     └─ Claims: { sub: user_id, org_id, role, jti: uuid, exp }
   │
6. ├─ Generate Refresh Token (secrets.token_urlsafe(64))
   │     └─ Hash (SHA-256) → Store in RefreshToken table (30-day TTL)
   │
7. └─ Return { access_token, refresh_token }
```

### Security: Refresh Token Rotation

When a client uses a refresh token, the old token is **immediately revoked** and a new pair is issued. If a revoked token is presented again (token reuse detected), **all sessions for that user are revoked** as a security measure — this catches replay attacks.

### Google OAuth Flow

```
1. GET /api/v1/auth/google/login → Redirect to Google consent screen
   │
2. Google redirects to /api/v1/auth/google/callback?code=...
   │
3. ├─ authlib exchanges code for Google access_token
   │
4. ├─ httpx fetches user profile from Google
   │
5. ├─ Upsert User (oauth_provider="google", is_verified=True)
   │
6. └─ Issue JWT + Refresh Token → Redirect to frontend with tokens
```

### Dual-Portal JWT Isolation

Staff JWTs contain `role: "hr_manager" | "recruiter" | "interviewer"`. Candidate JWTs contain `role: "candidate"`. The `get_current_user` and `get_current_candidate` dependencies in FastAPI are **separate functions** that explicitly verify the role claim, making it impossible for a candidate to access staff endpoints or vice versa.

---

## 4. Module 2 — Organization Management & Multi-Tenancy

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Data Model | PostgreSQL with `org_id` FK on every table | Every resource (User, Job, Candidate, Application, etc.) carries an `org_id` foreign key. |
| Query Isolation | SQLAlchemy `WHERE org_id = :current_org_id` | Every repository query is scoped by the authenticated user's `org_id` extracted from their JWT. |
| Vector Isolation | Qdrant `FieldCondition` filter | Qdrant queries filter by `org_id` in the payload, ensuring semantic search never crosses tenant boundaries. |
| RBAC | Casbin (policy-as-code) | Role hierarchy: `hr_manager` inherits all `recruiter` permissions. Interviewers have read-only access to interviews and candidates. |

### How Tenant Isolation Works

```
HTTP Request with JWT
        │
   ┌────▼────┐
   │ FastAPI  │  get_current_user() extracts org_id from JWT claims
   │Dependency│
   └────┬────┘
        │  org_id is injected into every service/repository call
        │
   ┌────▼─────────────────────────────────────┐
   │ Service Layer                             │
   │  enforce_role(role, resource, action)     │  ← Casbin check
   │  .where(Model.org_id == current_org_id)   │  ← SQL isolation
   └────┬─────────────────────────────────────┘
        │
   ┌────▼─────────────────────────────────────┐
   │ Qdrant (for AI features)                  │
   │  Filter(must=[FieldCondition(             │
   │    key="org_id",                          │
   │    match=MatchValue(value=org_id)         │
   │  )])                                      │  ← Vector isolation
   └───────────────────────────────────────────┘
```

Every layer enforces isolation independently. Even if a bug in one layer is exploited, the others still block cross-tenant access.

### Casbin RBAC Policy

The RBAC model uses a CSV policy file (`rbac_policy.csv`) with the ACL format: `p, <role>, <resource>, <action>`:

```
p, hr_manager, organization, read
p, hr_manager, jobs, manage          ← manage = create + read + update + delete
p, hr_manager, candidates, manage
p, hr_manager, copilot, use

p, recruiter, jobs, read
p, recruiter, jobs, create
p, recruiter, candidates, manage
p, recruiter, interviews, manage

p, interviewer, interviews, read
p, interviewer, interviews, update   ← Can submit feedback
p, interviewer, candidates, read     ← Read-only

g, hr_manager, recruiter             ← Role inheritance
```

The `g` (grouping) rule means `hr_manager` automatically inherits every `recruiter` permission without duplication.

---

## 5. Module 3 — Recruitment Module

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Data Model | PostgreSQL: `Department`, `Job`, `PipelineStage` tables | Fully relational with foreign keys. Jobs have customizable pipeline stages. |
| Default Pipeline | Auto-generated on job creation | `["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"]` — 6 stages created automatically, customizable after. |
| Soft Delete | `deleted_at` timestamp column | Jobs and Departments are never hard-deleted. `WHERE deleted_at IS NULL` is enforced on all queries. |
| Drag-and-Drop | `@dnd-kit/core` + `@dnd-kit/sortable` (frontend) | Lightweight, accessible DnD library for the Kanban board view. |
| Pipeline Customization | `PUT /api/v1/jobs/{id}/pipeline-stages` | Replaces all stages atomically — delete existing, insert new ones. |

### End-to-End Flow: Creating a Job

```
1. POST /api/v1/jobs { title, description, requirements, department_id }
   │
2. ├─ Casbin: enforce_role(role, "jobs", "create")
   │
3. ├─ Verify department belongs to user's org → 404 if not
   │
4. ├─ Create Job row with org_id = current_user.org_id
   │
5. ├─ Auto-create 6 default PipelineStage rows (order_index 0-5)
   │
6. ├─ Trigger Celery task: embed_job(job_id)
   │     └─ Generate dense + sparse vectors → Upsert to Qdrant "jobs" collection
   │
7. └─ Return Job with pipeline_stages (selectinload)
```

### Job Embedding Pipeline (Background)

When a job is created or updated, a Celery worker embeds it into Qdrant for later candidate matching:

```
embed_job(job_id):
  1. Fetch Job from Postgres
  2. Build text: "{title} {description} {requirements}"
  3. Generate dense vector: BAAI/bge-small-en-v1.5 (384 dimensions)
  4. Generate sparse vector: Qdrant/bm25 via fastembed
  5. Save JobEmbedding metadata to Postgres
  6. Upsert to Qdrant "jobs" collection:
     - vector: { dense: [...], sparse: { indices: [...], values: [...] } }
     - payload: { job_id, org_id, title }
```

---

## 6. Module 4 — Candidate Portal

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Separate Auth | Dedicated `candidate_auth.py` routes | Candidates have their own register/login flow, completely separate from staff auth. |
| File Upload | MinIO (via `boto3` presigned URLs) | Resumes are uploaded to S3-compatible storage. The backend generates presigned upload URLs so the frontend can upload directly to MinIO without routing through FastAPI. |
| Status Tracking | PostgreSQL `Application` table + `ApplicationStageHistory` | Every stage transition is recorded with timestamp for full audit trail. |
| Notifications | In-app notification system | Stored in Postgres, delivered via REST polling on the portal. |
| Frontend | Next.js App Router (`/portal/*` routes) | Separate layout and navigation from the staff dashboard. |

### End-to-End Flow: Candidate Applies to a Job

```
1. Candidate registers → Gets JWT with role="candidate"
   │
2. GET /api/v1/portal/jobs → Browse open jobs (filtered to orgs candidate applied to)
   │
3. POST /api/v1/portal/applications { job_id, resume_file }
   │
4. ├─ Upload resume to MinIO bucket "resumes" with key: {candidate_id}/{uuid}.pdf
   │
5. ├─ Create Resume row (file_url = "s3://resumes/...", parse_status = PENDING)
   │
6. ├─ Create Application row (status = "applied", stage = first pipeline stage)
   │
7. ├─ Dispatch Celery task: parse_resume(resume_id)
   │     └─ (See Module 5 for full flow)
   │
8. └─ Return Application (201 Created)
```

---

## 7. Module 5 — Resume Parsing

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| PDF Extraction (Primary) | **Docling** | Preserves layout, tables, headings, and document structure. Converts complex PDFs to Markdown for optimal LLM processing. Recommended by assignment. |
| PDF Extraction (Fallback) | **PyPDF** | Lightweight, pure-Python fallback for when Docling encounters edge-case PDFs (scanned images without text layers, corrupted files). |
| Structured Extraction | **LiteLLM + Instructor** | LLM extracts structured `ResumeExtraction` Pydantic model from raw Markdown text. Instructor guarantees the output conforms to our schema. |
| Embedding | **sentence-transformers** (`bge-small`) + **fastembed** (`bm25`) | Dual-vector embedding (dense + sparse) for hybrid search. |
| Vector Storage | **Qdrant** | Stores embeddings with metadata (`candidate_id`, `skills`) for later retrieval. |
| Orchestration | **Celery** | The entire pipeline runs as a background task, never blocking the API. |

### End-to-End Flow: Resume Parsing Pipeline

This is the most complex pipeline in TalentLens. Here is the complete data flow:

```
parse_resume(resume_id) — Celery Worker
│
├── 1. SET STATUS: resume.parse_status = PROCESSING
│
├── 2. DOWNLOAD: Fetch PDF from MinIO (s3://resumes/...)
│       └─ boto3.get_object() → BytesIO buffer
│
├── 3. EXTRACT TEXT:
│       ├── TRY: Docling DocumentConverter → export_to_markdown()
│       └── CATCH: PyPDF PdfReader → page.extract_text() for each page
│       └── FAIL: Raise if extracted_text is empty
│
├── 4. SAVE RAW TEXT: resume.raw_text = extracted_text
│
├── 5. LLM STRUCTURED EXTRACTION:
│       ├── Prompt: RESUME_EXTRACTION_PROMPT (versioned in prompts/)
│       ├── Model: settings.GROQ_MODEL_EXTRACT (e.g., llama-3.3-70b)
│       ├── Response Model: ResumeExtraction (Pydantic)
│       │     ├── name: str
│       │     ├── email: str
│       │     ├── phone: str
│       │     ├── skills: List[str]
│       │     ├── experience: List[{title, company, start_date, end_date, description}]
│       │     ├── education: List[{degree, institution, graduation_year}]
│       │     ├── certifications: List[str]
│       │     └── projects: List[{name, description}]
│       └── Instructor validates output against Pydantic schema
│
├── 6. SAVE TO POSTGRES: Create ResumeParsedData row linked to Resume
│
├── 7. GENERATE EMBEDDINGS:
│       ├── Build text: "Skills: Python, FastAPI\nExperience: SWE at Google\n..."
│       ├── Dense: BAAI/bge-small-en-v1.5 → 384-dim float vector
│       └── Sparse: Qdrant/bm25 via fastembed → { indices: [], values: [] }
│
├── 8. UPSERT TO QDRANT ("candidates" collection):
│       ├── vector: { dense: [...384 floats], sparse: { indices, values } }
│       └── payload: { candidate_id, skills: [...] }
│
├── 9. SYNC ORG VISIBILITY: Update Qdrant payload with org_ids the candidate has applied to
│       └─ Ensures copilot/matching only finds candidates visible to the querying org
│
└── 10. SET STATUS: resume.parse_status = DONE
```

### Why Docling + LLM (Not spaCy Alone)

The assignment suggests spaCy or HuggingFace Transformers for resume extraction. We use **Docling for document parsing** (converting PDF to structured Markdown) and then an **LLM via Instructor for information extraction**. This approach is superior because:

1. **Docling** handles the hard problem of PDF layout — tables, multi-column resumes, headers — and produces clean Markdown.
2. **The LLM** understands context. It can correctly parse "Python (5 years)" as a skill even if the format varies wildly between resumes. spaCy NER would require custom training for every format variation.
3. **Instructor** guarantees the output matches our `ResumeExtraction` Pydantic schema, with automatic retries if the LLM returns invalid JSON.

---

## 8. Module 6 — AI Candidate Matching

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Dense Embeddings | `BAAI/bge-small-en-v1.5` (sentence-transformers) | Captures semantic meaning — "React.js" ≈ "frontend development" |
| Sparse Embeddings | `Qdrant/bm25` (fastembed) | Captures exact keyword matches — "Kubernetes" must match "Kubernetes" exactly |
| Hybrid Search | Qdrant **Reciprocal Rank Fusion** (RRF) | Merges dense + sparse results into a single ranking |
| Re-Ranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` (CrossEncoder) | Precise pairwise scoring after initial retrieval |
| LLM Reasoning | LiteLLM + Instructor → `CandidateMatchOutput` | Generates human-readable match %, missing skills, strengths, weaknesses, recommendation, and interview questions |
| Caching | Redis (30-day TTL) + PostgreSQL (`AIMatchResult`) | Prevents redundant LLM calls. Cache key = hash of (prompt_version + job.updated_at + resume.updated_at) |
| Cost Tracking | PostgreSQL (`AIUsageLog`) | Logs every LLM call with latency, cache hit/miss, prompt version |

### End-to-End Flow: Job-Based Matching Pipeline

This is **not** a simple "send resume to ChatGPT" approach. It is a multi-stage retrieval pipeline:

```
POST /api/v1/matching/jobs/{job_id}/run → Celery task: run_job_matching_pipeline
│
├── STAGE 1: CANDIDATE RETRIEVAL (SQL)
│     └─ SELECT candidates WHO HAVE APPLIED to this specific job
│        (only candidates with parsed resumes are eligible)
│
├── STAGE 2: CROSS-ENCODER RE-RANKING
│     ├─ For each candidate: create pair (job_text, candidate_text)
│     ├─ CrossEncoder.predict(pairs) → raw relevance scores
│     ├─ Sort candidates by score (descending)
│     └─ Normalize scores to 0-100 range for display
│
├── STAGE 3: TIERED LLM ANALYSIS
│     ├─ TOP 5 candidates → Full LLM reasoning:
│     │     ├─ match_pct (0-100)
│     │     ├─ missing_skills: ["Kubernetes", "AWS"]
│     │     ├─ strengths: ["Strong Python", "ML experience"]
│     │     ├─ weaknesses: ["No cloud experience"]
│     │     ├─ recommendation: "Hire / No Hire"
│     │     └─ interview_questions: ["Describe your ML pipeline experience..."]
│     │
│     └─ REMAINING candidates → Lightweight result:
│           ├─ match_pct from normalized CrossEncoder score
│           └─ ats_score from keyword intersection
│
├── STAGE 4: CACHING
│     ├─ Cache key = SHA256(prompt_version + job.id + job.updated_at + candidate.id + resume.updated_at)
│     ├─ If key exists in Redis → Return cached AIMatchResult from Postgres
│     └─ If new → Store in Postgres + Set Redis key (30-day TTL)
│
└── STAGE 5: USAGE LOGGING
      └─ AIUsageLog: { endpoint, prompt_version, cache_hit, latency_ms, candidates_matched }
```

### Why This Pipeline (Not Just an LLM Call)

The assignment explicitly states: **"Do NOT simply send the resume to ChatGPT."** Our pipeline uses 4 distinct technologies:

1. **SQL Pre-filtering** — Only candidates who applied to the job are considered (tenant-isolated).
2. **CrossEncoder Re-ranking** — A specialized neural model that scores (query, document) pairs with much higher accuracy than embedding cosine similarity alone.
3. **Tiered LLM Analysis** — Only the top 5 candidates get expensive LLM reasoning. The rest get lightweight scores. This reduces LLM API costs by 80%+ for large candidate pools.
4. **Deterministic Caching** — If neither the job nor the resume has changed, the cached result is returned instantly.

### ATS Score Calculation

In addition to the AI match, every candidate gets a lightweight **ATS (Applicant Tracking System) score** based on keyword intersection:

```python
matched_skills = [skill for skill in resume_skills if skill.lower() in job_text.lower()]
ats_score = (len(matched_skills) / len(resume_skills)) * 100.0
```

This provides an explainable, deterministic score alongside the AI-generated one.

---

## 9. Module 7 — AI Recruiter Copilot

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| NL → Structured Filter | LiteLLM + Instructor → `CopilotFilter` | Converts natural language into a deterministic JSON filter object — **never generates SQL**. |
| Semantic Search | Qdrant (dense vector search) | Finds candidates whose skills/experience are semantically similar to the query. |
| Tenant Isolation | Qdrant `org_ids` filter + Postgres `Application.org_id` | Double-layered: Qdrant filters by org, then Postgres validates. |
| Prompt Versioning | `copilot_v1.py` | Prompts are versioned files in `ai/prompts/`, enabling A/B testing and rollback. |

### End-to-End Flow: Natural Language Query

```
Recruiter types: "Find Python developers with Kubernetes experience, not rejected"
│
├── STAGE 1: NL → STRUCTURED FILTER (LLM)
│     ├─ System prompt: COPILOT_SYSTEM_PROMPT (versioned)
│     ├─ LLM extracts: CopilotFilter {
│     │     skills: ["Python", "Kubernetes"],
│     │     exclude_stages: ["rejected"],
│     │     keywords: [],
│     │     ...
│     │   }
│     └─ Instructor validates output against CopilotFilter Pydantic model
│
├── STAGE 2: QDRANT SEMANTIC SEARCH
│     ├─ Build search text: "Skills: Python, Kubernetes"
│     ├─ Generate dense embedding with bge-small
│     ├─ Query Qdrant "candidates" collection:
│     │     - query: dense_vector
│     │     - filter: org_ids CONTAINS current_user.org_id    ← TENANT ISOLATION
│     │     - limit: 50
│     └─ Returns list of candidate_ids
│
├── STAGE 3: POSTGRES INTERSECTION
│     ├─ SELECT Candidate, ResumeParsedData, Application
│     ├─ WHERE Candidate.id IN (qdrant_candidate_ids)
│     ├─ AND Application.org_id = current_user.org_id         ← DOUBLE ISOLATION
│     ├─ AND Application.status NOT IN (exclude_stages)
│     └─ AND Application.job_id = filter.job_id (if specified)
│
└── STAGE 4: RETURN RESULTS
      └─ { interpreted_as: CopilotFilter, results: [{ candidate_id, name, skills, ... }] }
```

### Security: Why We Never Generate SQL

The assignment warns about SQL injection. Our Copilot **never generates SQL**. Instead:
1. The LLM outputs a **Pydantic model** (`CopilotFilter`) with typed fields.
2. These fields are used to construct **parameterized SQLAlchemy queries**.
3. Even if the LLM outputs malicious strings, they are treated as data values in parameterized queries, not executable SQL.

---

## 10. Module 8 — Interview Scheduler

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Data Model | PostgreSQL: `Interview` table | Stores scheduled_at, meeting_link, interviewer, notes, status. |
| Email Invites | Celery task: `send_interview_email` | Non-blocking async email dispatch with interview details and meeting link. |
| Calendar View | Next.js + Recharts (frontend) | Interviews displayed on the staff dashboard. |
| Availability | Time-slot based scheduling | Interviewers set availability, system checks for conflicts. |

### End-to-End Flow: Scheduling an Interview

```
1. POST /api/v1/interviews { application_id, scheduled_at, meeting_link, interviewer_ids }
   │
2. ├─ Casbin: enforce_role(role, "interviews", "manage")
   │
3. ├─ Verify Application belongs to user's org (via Job.org_id join)
   │
4. ├─ Create Interview row
   │
5. ├─ Dispatch Celery tasks:
   │     ├─ send_interview_email(candidate_email, details)
   │     └─ send_interview_email(interviewer_email, details)
   │
6. └─ Return Interview (201 Created)
```

---

## 11. Module 9 — AI Interview Feedback

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| LLM Analysis | LiteLLM + Instructor → `InterviewFeedbackOutput` | Generates summary, strengths, weaknesses, recommendation, and score from raw interviewer notes. |
| Grounding Context | Candidate resume data + Job description | LLM is grounded with the candidate's skills and the job requirements to avoid hallucination. |
| Caching | Row-level upsert (same notes = same result) | If notes haven't changed, cached feedback is returned without an LLM call. |
| Prompt Engineering | `interview_feedback_v1.py` | Versioned prompt with explicit scoring rubric (2/10 to 10/10) and recommendation mapping. |
| Usage Tracking | `AIUsageLog` | Every LLM call logs latency, prompt version, and whether it was a cache hit. |

### End-to-End Flow: Submitting Interview Feedback

```
POST /api/v1/interviews/{id}/feedback { raw_notes: "Candidate showed strong Python..." }
│
├── 1. ORG CHECK: Verify Interview belongs to user's org (via Application → Job → org_id)
│       └─ Returns 404 (not 403) to prevent information leakage
│
├── 2. RBAC: enforce_role(role, "interviews", "update")
│
├── 3. CACHE CHECK: If existing feedback has same raw_notes → return cached
│
├── 4. PULL GROUNDING CONTEXT:
│       ├─ Candidate's resume skills: ["Python", "FastAPI", "Docker"]
│       ├─ Candidate's latest experience: "SWE at Google (3 years)"
│       └─ Job description excerpt (capped at 1000 chars to prevent token explosion)
│
├── 5. BUILD PROMPT: Inject notes + context into versioned prompt template
│       └─ Prompt includes explicit scoring rubric and recommendation options
│
├── 6. LLM CALL:
│       ├─ Model: GROQ_MODEL_MATCH
│       ├─ Response: InterviewFeedbackOutput {
│       │     summary: "The candidate demonstrated...",
│       │     strengths: ["Strong Python fundamentals", ...],
│       │     weaknesses: ["Limited cloud experience"],
│       │     recommendation: "Hire",
│       │     overall_score: 7.5
│       │   }
│       └─ Instructor validates against Pydantic schema
│
├── 7. UPSERT: Create or update InterviewFeedback row
│
├── 8. LOG: AIUsageLog { endpoint: "interview_feedback", latency_ms, prompt_version }
│
└── 9. RETURN: InterviewFeedback with AI-generated fields
```

### Prompt Engineering: Scoring Rubric

The prompt includes a detailed scoring rubric to prevent LLMs from defaulting to middle-of-the-road scores:

| Score | Meaning |
|---|---|
| 2/10 | Serious red flags, inability to explain basic concepts |
| 4/10 | Below bar, material gaps in core requirements |
| 6/10 | Borderline, meets some areas but misses others |
| 8/10 | Strong candidate, solid command of requirements |
| 10/10 | Exceptional, exceeded expectations |

---

## 12. Module 10 — Analytics Dashboard

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Data Source | PostgreSQL (Application, ApplicationStageHistory, Job, AIMatchResult) | All metrics are computed from relational data — no separate analytics database needed. |
| Charts | **Recharts** (frontend) | React-native charting library with beautiful defaults. Renders funnel charts, bar charts, pie charts, and trend lines. |
| Metrics | Computed in `analytics.py` service | Server-side aggregation for security (raw data never exposed to frontend). |

### Metrics Computed

| Metric | How It's Calculated |
|---|---|
| **Time to Hire** | Average days between `Application.applied_at` and `ApplicationStageHistory.moved_at` for "Hired" stages |
| **Pipeline Conversion** | `(total_hired / total_applied) × 100` |
| **AI Match Success Rate** | % of candidates with AI match ≥ 80% who progressed to Interview or Hired stage |
| **Pipeline Trend** | Monthly `applied` vs `hired` counts over last 6 months |
| **Department Hires** | Hires grouped by `Job.department.name` |
| **Candidate Sources** | Application counts grouped by `Candidate.source` (Direct, Referral, LinkedIn, etc.) |
| **Active Jobs** | Count of open jobs and unique departments with open positions |

---

## 13. Production-Grade Requirements

### Layered Architecture

We follow the exact architecture mandated by the assignment:

```
Controllers (api/v1/*.py)       → Route definitions, input parsing, response formatting
       │
Services (services/*.py)        → Business logic, Casbin enforcement, orchestration
       │
Repositories (repositories/)    → Database queries (base.py provides generic CRUD)
       │
Database (models/*.py)          → SQLAlchemy ORM models
```

**No business logic in routes.** Routes are thin wrappers that call services.

### Error Handling

Every error follows the assignment's required JSON format:

```json
{
  "success": false,
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job does not exist",
    "request_id": "abc123-..."
  }
}
```

This is implemented via:
- `DomainException` — Custom exception with `code`, `message`, and `status_code`
- `domain_exception_handler` — Catches all `DomainException` and formats the response
- `global_exception_handler` — Catches unhandled exceptions, generates a unique `error_id`, logs the full traceback, and returns a safe 500 response

### Structured Logging

Every log line is JSON, making it compatible with ELK/Loki/CloudWatch:

```json
{
  "level": "info",
  "timestamp": "2026-08-12T18:05:10Z",
  "message": "parse_resume_success",
  "request_id": "abc123-...",
  "resume_id": "def456-...",
  "path": "/api/v1/candidates/...",
  "method": "POST"
}
```

Implemented with:
- **structlog** — Structured JSON logging with context variables
- **asgi-correlation-id** — Auto-generates a unique `request_id` per HTTP request and binds it to all log entries

### Rate Limiting

**SlowAPI** (built on limits) is applied globally via ASGI middleware. Configurable per-route:
- Auth endpoints: Stricter limits (e.g., 5 requests/minute for login)
- AI endpoints: Rate-limited to prevent abuse of expensive LLM calls
- General API: Standard limits

### Security Measures

| Requirement | Implementation |
|---|---|
| Rate Limiting | SlowAPI middleware |
| RBAC | Casbin enforcer with CSV policy |
| Input Validation | Pydantic v2 models on every endpoint |
| SQL Injection Prevention | SQLAlchemy parameterized queries (never raw SQL) |
| XSS Prevention | React's default escaping + API returns JSON (not HTML) |
| Secure Headers | CORS restricted to `FRONTEND_URL` only |
| File Validation | MIME type checking + size limits on resume upload |
| Password Security | bcrypt hashing (adaptive cost factor) |
| Token Security | Refresh tokens SHA-256 hashed before storage |
| Session Security | JWT blacklist via Redis for instant revocation |

### Database Design

| Feature | Implementation |
|---|---|
| Indexes | UUID primary keys (auto-generated), foreign keys indexed |
| Foreign Keys | Every table references `org_id`, cascading where appropriate |
| Constraints | `NOT NULL`, `CHECK` constraints, enum types for status fields |
| Soft Delete | `deleted_at` timestamp column (NULL = active) |
| Audit Fields | `created_at`, `updated_at` on all models (via SQLAlchemy `Base`) |

---

## 14. AI Engineering — Deep Dive

### Why Not LangChain / LlamaIndex / Haystack?

The assignment lists these as recommended AI frameworks. We chose **not** to use them for deliberate engineering reasons:

| Framework | Why We Didn't Use It |
|---|---|
| **LangChain / LangGraph** | Heavyweight abstraction layer that obscures what's happening. For our use case (structured extraction + matching), we need explicit control over prompts, retries, and caching. LangChain's chains would add complexity without value. |
| **LlamaIndex** | Designed primarily for document Q&A over large corpora. Our resume parsing is a single-document extraction task, and our matching uses custom pipelines, not LlamaIndex's retrieval. |
| **Haystack** | Production-grade but opinionated. Would force us into Haystack's pipeline abstraction when our pipeline is already well-structured with explicit stages. |

Instead, we use **three targeted libraries** that together cover everything these frameworks provide:

1. **LiteLLM** — Model-agnostic API calls (swap Groq → OpenAI → Anthropic with one config change)
2. **Instructor** — Pydantic-validated structured outputs from any LLM
3. **tenacity** — Retry logic with exponential backoff (3 attempts, 2-10s waits)

### AI Caching Strategy

```
Cache Key = SHA256(prompt_version + job.id + job.updated_at + candidate.id + resume.updated_at)
```

- **Why prompt_version?** If we change the prompt, old cached results are invalidated.
- **Why updated_at timestamps?** If the job description or resume changes, the match is re-computed.
- **Storage:** Redis (fast lookup, 30-day TTL) + Postgres `AIMatchResult` (persistent).
- **Hit rate:** In production, once a matching round completes, subsequent views are instant cache hits.

### Token Usage & Cost Tracking

Every LLM call is logged to the `AIUsageLog` table:

```sql
AIUsageLog:
  id, org_id, user_id, endpoint, prompt_version,
  cache_hit (bool), candidates_matched (int),
  latency_ms (float), created_at
```

This enables:
- Per-organization cost attribution
- Cache hit rate monitoring
- Latency tracking for SLA compliance
- Prompt version A/B testing

### Prompt Versioning

All prompts are stored as **versioned Python files** in `ai/prompts/`:

```
ai/prompts/
├── resume_extraction.py        # RESUME_EXTRACTION_PROMPT
├── copilot_v1.py              # COPILOT_SYSTEM_PROMPT
└── interview_feedback_v1.py   # FEEDBACK_SYSTEM_PROMPT + PROMPT_VERSION
```

Each prompt file includes a `PROMPT_VERSION` string. When the prompt changes, the version changes, invalidating all caches.

---

## 15. Frontend Stack — Deep Dive

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Framework | **Next.js 16** (App Router) | SSR, file-based routing, layouts, API rewrites. React 19 concurrent features. |
| Styling | **Tailwind CSS v4** + **Shadcn/UI** | Utility-first CSS with accessible, customizable components. No CSS-in-JS runtime overhead. |
| Data Fetching | **@tanstack/react-query** | Server state management with caching, background refetching, optimistic updates. |
| API Client | **openapi-fetch** + **openapi-typescript** | Type-safe API client auto-generated from the backend's OpenAPI schema. End-to-end type safety. |
| Forms | **react-hook-form** + **zod** | Performant forms with schema-based validation (mirrors Pydantic on backend). |
| Charts | **Recharts** | React-native charts for the analytics dashboard. |
| DnD | **@dnd-kit/core** + **@dnd-kit/sortable** | Kanban board for pipeline stage management. |
| Icons | **lucide-react** | Clean, consistent icon set. |
| Theming | **next-themes** | Dark/light mode toggle. |
| Toasts | **sonner** | Beautiful toast notifications. |

### Frontend Architecture

```
frontend/src/
├── app/
│   ├── (auth)/              # Auth pages (login, register, password-reset)
│   ├── dashboard/           # Staff portal
│   │   ├── analytics/       # Charts & metrics
│   │   ├── candidates/      # Candidate list & profiles
│   │   ├── copilot/         # AI search interface
│   │   ├── interviews/      # Interview management
│   │   ├── jobs/            # Job listings & pipeline
│   │   └── layout.tsx       # Shared sidebar navigation
│   ├── portal/              # Candidate self-service portal
│   │   ├── applications/    # Application tracking
│   │   ├── dashboard/       # Candidate dashboard
│   │   ├── jobs/            # Browse & apply
│   │   ├── profile/         # Profile management
│   │   └── layout.tsx       # Separate portal navigation
│   └── page.tsx             # Landing page
├── components/
│   ├── ui/                  # Shadcn components (Button, Dialog, etc.)
│   └── JobMatches.tsx       # AI matching results component
└── lib/
    └── api/                 # Type-safe API client (openapi-fetch)
```

### API Proxy Architecture

The frontend never calls the backend directly from the browser:

```
Browser → Next.js (port 3000) → /api/v1/* → Rewrite → Backend (port 8000)
```

This is configured in `next.config.ts` rewrites. Benefits:
- Same-origin requests (no CORS issues in the browser)
- Backend URL is never exposed to the client
- Can add caching/auth layers at the Next.js level

---

## 16. Full Dependency Map

### Backend (`requirements.txt`)

| Package | Module(s) | Purpose |
|---|---|---|
| `fastapi` | All | Web framework |
| `uvicorn[standard]` | All | ASGI server |
| `sqlalchemy[asyncio]` | All | Async ORM |
| `asyncpg` | All | Async PostgreSQL driver |
| `alembic` | All | Database migrations |
| `pydantic[email]` | All | Data validation |
| `pydantic-settings` | All | Environment config |
| `structlog` | All | Structured logging |
| `asgi-correlation-id` | All | Request ID tracing |
| `celery` | Modules 5, 6, 8 | Background task queue |
| `redis` | Modules 1, 6, 7 | Cache + broker |
| `passlib[bcrypt]` | Module 1 | Password hashing |
| `python-jose[cryptography]` | Module 1 | JWT |
| `authlib` | Module 1 | OAuth2/OIDC |
| `httpx` | Module 1 | Async HTTP client |
| `slowapi` | All | Rate limiting |
| `casbin` | Modules 2-10 | RBAC |
| `litellm` | Modules 5, 6, 7, 9 | LLM provider abstraction |
| `instructor` | Modules 5, 6, 7, 9 | Structured LLM outputs |
| `sentence-transformers` | Modules 5, 6, 7 | Dense embeddings |
| `fastembed` | Modules 5, 6 | Sparse (BM25) embeddings |
| `qdrant-client` | Modules 5, 6, 7 | Vector search |
| `docling` | Module 5 | PDF layout extraction |
| `pypdf` | Module 5 | PDF text fallback |
| `pytesseract` | Module 5 | OCR for scanned docs |
| `boto3` | Module 4, 5 | MinIO / S3 client |
| `aiofiles` | Module 4 | Async file handling |
| `itsdangerous` | Module 1 | Secure token signing |
| `python-multipart` | Module 4 | File upload parsing |
| `psycopg2-binary` | Celery workers | Sync Postgres for Celery |
| `aiosqlite` | Testing | SQLite for test DB |

### Frontend (`package.json`)

| Package | Module(s) | Purpose |
|---|---|---|
| `next` (16) | All | React framework |
| `react` (19) | All | UI library |
| `tailwindcss` (v4) | All | Styling |
| `shadcn` (v4) | All | UI components |
| `@tanstack/react-query` | All | Server state management |
| `openapi-fetch` | All | Type-safe API client |
| `openapi-typescript` | All | Schema type generation |
| `react-hook-form` | Forms | Form state management |
| `zod` | Forms | Schema validation |
| `@hookform/resolvers` | Forms | Zod ↔ react-hook-form bridge |
| `recharts` | Module 10 | Charts & analytics |
| `@dnd-kit/core` | Module 3 | Drag-and-drop |
| `@dnd-kit/sortable` | Module 3 | Sortable DnD |
| `lucide-react` | All | Icons |
| `next-themes` | All | Dark mode |
| `sonner` | All | Toast notifications |
| `date-fns` | Modules 8, 10 | Date formatting |
| `clsx` + `tailwind-merge` | All | Conditional classnames |
| `class-variance-authority` | All | Component variants |

---

> **Summary:** Every technology in TalentLens was chosen to solve a specific engineering problem. We avoided heavyweight frameworks (LangChain, LlamaIndex) in favor of targeted, composable libraries (LiteLLM + Instructor + sentence-transformers) that give us full control over the AI pipeline. Every data flow enforces multi-tenant isolation at multiple layers (JWT → Casbin → SQL → Qdrant). Every LLM call is cached, tracked, and version-controlled.
