# AI Talent Acquisition Platform — Project Plan

**Owner:** Tayyaba
**Timeline:** 7–10 days, full-time
**Goal:** Pass technical assignment evaluation (100-mark rubric) by demonstrating production-grade backend, AI, and system design engineering — not by maximizing feature count.

---

## 1. Guiding Principle

The rubric weights tell the real story:

| Area | Marks |
|---|---|
| Backend Engineering | 20 |
| AI Engineering | 20 |
| System Architecture | 15 |
| Frontend | 10 |
| Database Design | 10 |
| Security | 10 |
| DevOps & Docker | 5 |
| Testing | 5 |
| Documentation | 5 |

**65 of 100 marks live in Backend + AI + Architecture + Database.** Bonus features (voice agent, WhatsApp, OCR, multi-region, etc.) are worth **zero rubric marks**. Time discipline: build the core deeply and correctly; mention bonus features only as a documented roadmap, don't build them.

**Non-negotiable red line from the brief:** "Do NOT simply send the resume to ChatGPT." Every AI feature must show real engineering — embeddings, hybrid retrieval, reranking, prompt versioning, caching, token/cost tracking — with the LLM call as the *last* step, not the only step.
**human-in-the-loop, scores inform not auto-rejection.**
---

## 2. Tech Stack (final, as specified in the assignment)

### Backend
- **FastAPI** — async Python API framework
- **PostgreSQL** — primary relational store
- **SQLAlchemy 2.0** (async) — ORM
- **Alembic** — migrations
- **Redis** — caching, rate-limit counters, Celery broker
- **Celery** — background workers (resume parsing, email, AI analysis, report generation)

### Frontend
- **Next.js 15** (App Router)
- **React 18**
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui** for components
- **Recharts** for analytics charts
- **@dnd-kit** for the drag-and-drop pipeline board

### Auth
- **JWT** (access + refresh tokens)
- **OAuth (Google)** via `authlib`
- **Passlib** (bcrypt) for password hashing
- **python-jose** for JWT signing

### AI / ML Stack
- **Embeddings:** `BAAI/bge-large-en-v1.5` via `sentence-transformers`, self-hosted (no API cost, no external dependency, deterministic)
- **Vector DB:** **Qdrant** (self-hosted via Docker) — hybrid search (dense + sparse/BM25) support built in
- **Reranking:** Cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- **Document parsing:** **Docling** (preserves resume structure — headings, tables, sections) with `pytesseract` as OCR fallback for scanned PDFs
- **LLM generation layer:** **Hybrid approach** — abstracted via **LiteLLM** so the provider is swappable.
  - Default: Anthropic Claude (Haiku for cheap/fast tasks like extraction; Sonnet for matching explanations and copilot reasoning)
  - Documented alternative: Ollama + Qwen2.5/Llama 3.3 for a fully self-hosted deployment — this swap requires only a config change, which is itself a system-design talking point
  - **Why hybrid, not fully local:** running a local LLM reliably (VRAM, latency, model ops) is significant infra risk for a 7–10 day solo build. Local embeddings + reranking (the retrieval quality layer) stay self-hosted; only the final generation step is a managed call. This is documented explicitly in the README as a deliberate tradeoff, not an oversight.
- **Structured output:** `instructor` library (Pydantic-validated LLM outputs — no fragile JSON regex parsing)
- **Prompt versioning:** prompts stored as versioned templates in `/app/ai/prompts/` with a version string persisted alongside every AI result in the DB
- **Caching:** Redis-backed cache keyed on `hash(prompt_version + input)` to avoid recomputing identical AI calls
- **Token/cost tracking:** every LLM call logged to `ai_usage_logs` (tokens in/out, cost, latency, cache hit/miss)

### Storage
- **MinIO** (S3-compatible, self-hosted) for resumes, certificates, generated reports

### Search / RBAC
- **Casbin** for RBAC + org-scoped policy enforcement (in addition to app-layer org filtering)

### Deployment
- **Docker** + **Docker Compose** (single `docker compose up` startup)
- **GitHub Actions** for CI: lint → test → build image
- Kubernetes/Helm: documented as a scaling path in the Scaling Strategy doc, not built (correctly scoped as "Optional" in the brief)

### Observability
- Structured JSON logging (`structlog`) with request IDs and error IDs on every log line
- Prometheus + Grafana: basic setup (`/metrics` endpoint via `prometheus-fastapi-instrumentator`) — enough to show the pattern, not a full dashboard suite

---

## 3. High-Level Architecture

```
                         ┌─────────────────────┐
                         │   Next.js Frontend   │
                         │  (HR Dashboard +     │
                         │   Candidate Portal)  │
                         └──────────┬───────────┘
                                    │ HTTPS
                         ┌──────────▼───────────┐
                         │   Nginx / Traefik     │  (rate limiting, TLS, secure headers)
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │       FastAPI          │
                         │  /api/v1/...           │
                         │                        │
                         │  Routers (controllers) │
                         │        ↓                │
                         │  Services (business    │
                         │  logic)                │
                         │        ↓                │
                         │  Repositories (data     │
                         │  access, org-scoped)   │
                         └───┬───────┬───────┬────┘
                             │       │       │
              ┌──────────────┘       │       └────────────────┐
              ▼                      ▼                        ▼
      ┌───────────────┐    ┌────────────────┐        ┌───────────────┐
      │  PostgreSQL   │    │     Redis       │        │    MinIO      │
      │  (system of   │    │  (cache,        │        │  (resumes,    │
      │   record)     │    │   rate limit,   │        │   files)      │
      └───────────────┘    │   Celery broker)│        └───────────────┘
                            └───────┬────────┘
                                    │
                         ┌──────────▼───────────┐
                         │   Celery Workers      │
                         │  - resume parsing     │
                         │  - AI matching        │
                         │  - email sending      │
                         │  - report generation  │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │     AI Layer           │
                         │  Docling → chunk       │
                         │  → BGE embeddings      │
                         │  → Qdrant (hybrid      │
                         │    search)             │
                         │  → Cross-encoder       │
                         │    rerank              │
                         │  → LiteLLM → Claude/   │
                         │    Ollama (via         │
                         │    instructor)         │
                         └───────────────────────┘
```

### Layering rule (enforced in code review of my own PRs)
- **Routers:** parse/validate request, call one service method, return response. No business logic, no DB queries.
- **Services:** orchestrate business rules, call one or more repositories, enforce authorization decisions beyond basic RBAC.
- **Repositories:** the *only* layer that touches SQLAlchemy directly. Every repository method is implicitly org-scoped via a base class (`BaseRepository.__init__(self, org_id: UUID, db: AsyncSession)`), so it is structurally impossible to forget a tenant filter.

---

## 4. Multi-Tenancy Strategy

**Approach: shared database, shared schema, `org_id` discriminator column on every tenant-owned table, enforced at the repository layer.**

Why this over schema-per-tenant or DB-per-tenant: it scales to 10,000 organizations without connection-pool explosion or migration fan-out (running one Alembic migration across 10,000 schemas is an operational nightmare). It's also the industry-standard pattern for mid-size B2B SaaS (Slack, Notion-style orgs).

Enforcement layers (defense in depth):
1. **Repository base class** auto-injects `WHERE org_id = :current_org_id` on every query — a developer cannot bypass this without explicitly opting out.
2. **JWT claim** carries `org_id`; middleware resolves it once per request into request-scoped context.
3. **Postgres row-level security (RLS)** policies as a second, DB-level enforcement layer — documented and demoed even if the app layer is the primary enforcement, because it shows defense-in-depth thinking to evaluators.
4. **Super Admin** is modeled as `is_platform_admin: bool` on `users`, not a nullable `org_id` — keeps `org_id NOT NULL` everywhere, avoids null-check bugs, and platform-admin cross-org queries go through a clearly separate, audited code path.

---

## 5. Database Schema

Conventions applied to every table:
- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- `org_id UUID NOT NULL REFERENCES organizations(id)` (tenant-owned tables)
- `created_at`, `updated_at` (auto via trigger or SQLAlchemy `onupdate`)
- `created_by`, `updated_by` (nullable UUID → users.id)
- `deleted_at TIMESTAMPTZ NULL` (soft delete; all repository reads filter `deleted_at IS NULL` by default)
- Indexes: every FK column, every `org_id`, composite `(org_id, status)` / `(org_id, created_at)` where filtering is common

### Identity & Tenancy
- **organizations**: id, name, slug (unique), plan, settings (JSONB)
- **users**: id, org_id, email (unique per org), hashed_password, role (enum: super_admin / hr_manager / recruiter / interviewer), is_platform_admin, is_verified, oauth_provider, oauth_id, last_login_at
- **refresh_tokens**: id, user_id, token_hash, expires_at, revoked_at
- **password_resets**: id, user_id, token_hash, expires_at, used_at
- **email_verifications**: id, user_id, token_hash, expires_at, used_at

### Recruitment Structure
- **departments**: id, org_id, name
- **jobs**: id, org_id, department_id, title, description, requirements (JSONB), status (draft/open/closed), created_by
- **pipeline_stages**: id, job_id, name, order_index — per-job pipelines, not a global enum, so drag-and-drop reordering and custom pipelines are trivial
- **job_embeddings**: job_id, qdrant_point_id, model_version (pointer only — vectors live in Qdrant, not Postgres)

### Candidates
- **candidates**: id, org_id, email, phone, name, profile (JSONB), source (referral/portal/manual)
- **resumes**: id, candidate_id, file_url (MinIO), parse_status (pending/processing/done/failed), raw_text
- **resume_parsed_data**: id, resume_id, skills (JSONB), experience (JSONB), education (JSONB), certifications (JSONB), projects (JSONB)
- **candidate_embeddings**: candidate_id, qdrant_point_id, model_version

### Applications (pipeline in motion)
- **applications**: id, org_id, candidate_id, job_id, current_stage_id, status, applied_at
- **application_stage_history**: id, application_id, from_stage_id, to_stage_id, moved_by, moved_at, notes — source of truth for funnel + time-to-hire analytics

### AI
- **ai_match_results**: id, application_id, match_pct, missing_skills (JSONB), strengths (JSONB), weaknesses (JSONB), recommendation, prompt_version, model_used, generated_at
- **ai_usage_logs**: id, org_id, feature (matching/copilot/feedback/jd_generation), input_tokens, output_tokens, cost_usd, latency_ms, cache_hit (bool), created_at

### Interviews
- **interviews**: id, application_id, interviewer_id, scheduled_at, meeting_link, status
- **interview_feedback**: id, interview_id, raw_notes, ai_summary, ai_strengths (JSONB), ai_weaknesses (JSONB), ai_recommendation, overall_score

### Supporting
- **notifications**: id, recipient_type (user/candidate), recipient_id, type, channel, payload (JSONB), read_at, sent_at
- **audit_logs**: id, org_id, actor_id, action, entity_type, entity_id, diff (JSONB), created_at

*(Full ER diagram to be generated as a separate deliverable once models are finalized — see Deliverables checklist.)*

---

## 6. Module Scope — What Gets Built Deeply vs. Thinly vs. Documented Only

### Build deeply (where the marks are)
1. **Auth & RBAC** — register, login, refresh, password reset, email verification, Google OAuth, 4 roles, org isolation
2. **Organization management** — multi-tenant CRUD, proper isolation demoed with 2–3 seeded orgs
3. **Recruitment module** — departments, jobs, custom drag-and-drop pipeline
4. **Candidate portal** — register, resume upload, status tracking, profile update
5. **Resume parsing** — Docling → structured extraction → stored JSON
6. **AI candidate matching** — the full pipeline: embed → hybrid search in Qdrant → cross-encoder rerank → LLM explanation (match %, missing skills, strengths/weaknesses, recommendation, generated interview questions)
7. **AI Recruiter Copilot** — natural language → constrained structured query (not raw text-to-SQL — see Section 7 for why) → results
8. **Analytics dashboard** — hiring funnel, time-to-hire, offer acceptance, candidate sources, recruiter performance — all computed from `application_stage_history`, real data, not mocked

### Build thin but functional
9. **Interview scheduler** — basic calendar slot creation + email invite + meeting link field (no real calendar-provider sync — documented as a v2 integration point with Cal.com)
10. **AI interview feedback** — notes in → structured summary/strengths/weaknesses/score out, same LLM+instructor pattern as matching (cheap to add once the pattern exists)

### Document only, do not build
- Voice interview agent, WhatsApp notifications, OCR for certificates (beyond the fallback already in the resume pipeline), duplicate candidate detection, AI job description generator, skill graph, referral system, resume similarity search (subsumed by matching), AI fraud detection, interview recording analysis, multi-language support, live notifications (WebSocket), feature flags, multi-region deployment.
- These go into the README as a **"Roadmap / What I'd build next"** section with 1–2 sentences each on approach — shows awareness without burning build time on zero-mark features.

---

## 7. AI Engineering — Detailed Design

### 7.1 Resume Parsing Pipeline
```
PDF/DOCX upload → MinIO
    → Celery task triggered
    → Docling extraction (layout-aware: headings, tables, sections)
    → fallback to Tesseract OCR if Docling confidence low / scanned doc
    → LLM (via instructor) extracts structured fields into a Pydantic schema:
        Name, Email, Phone, Skills[], Experience[], Education[], Certifications[], Projects[]
    → stored in resume_parsed_data
    → chunked + embedded (BGE) → upserted into Qdrant with candidate_id metadata
```

### 7.2 AI Candidate Matching Pipeline
```
Job description (embedded once, cached)
    → Qdrant hybrid search (dense vector + BM25/sparse) over candidate_embeddings,
      filtered by metadata (org_id, min experience, required certs)
    → top-N candidates
    → Cross-encoder reranks (resume chunk, job description) pairs for precision
    → Top-K reranked candidates go to LLM (via instructor, versioned prompt) for:
        match_pct, missing_skills, strengths, weaknesses, recommendation, interview_questions
    → result cached in Redis (key = hash(prompt_version + job_id + candidate_id))
    → persisted to ai_match_results with prompt_version + model_used for auditability
    → every call logged to ai_usage_logs (tokens, cost, latency, cache_hit)
```

This is the pipeline the brief explicitly asks for (embeddings → hybrid search → RAG → metadata filtering) and it directly answers "do NOT simply send the resume to ChatGPT" — the LLM only ever sees a small, retrieval-narrowed, reranked context.

### 7.3 AI Recruiter Copilot
Natural language ("Find Python developers with Kubernetes experience") is **not** translated into raw freeform SQL — that's a SQL-injection and hallucination risk with a live production database. Instead:
```
NL query → LLM (via instructor) → constrained Pydantic filter schema
    (skills: list[str], min_experience: int, certifications: list[str], keywords: str)
    → filter schema converted deterministically to a parameterized query
      against resume_parsed_data (JSONB filters) + Qdrant semantic search for the free-text part
    → results returned + the interpreted filter shown to the HR user for transparency
```
This is safer, explainable (the user sees what the AI understood their query as), and still demonstrates NL→structured-query capability without the injection surface of NL→raw-SQL.

### 7.4 Prompt Versioning, Caching, Cost Tracking
- Prompts live as versioned template files (`prompts/matching_v1.py`, `prompts/copilot_v1.py`) — never inline strings in service code
- Every AI call wrapped in a single `call_llm()` service function that: checks Redis cache → calls LiteLLM → logs to `ai_usage_logs` → returns structured (instructor-validated) result → retries with exponential backoff on transient failure (via `tenacity`)
- This one wrapper is a strong, easy-to-demo piece of "production AI engineering" in the demo video

---

## 8. Security Checklist

- [ ] Rate limiting (SlowAPI, Redis-backed) — per-user and per-IP tiers
- [ ] RBAC via Casbin, enforced in service layer (not just route decorators)
- [ ] Input validation via Pydantic v2 models on every endpoint
- [ ] SQL injection prevention — SQLAlchemy ORM only, no raw string interpolation anywhere; Copilot NL query never becomes raw SQL (see 7.3)
- [ ] XSS prevention — output encoding on frontend, `Content-Security-Policy` header
- [ ] Secure headers — `helmet`-equivalent middleware (HSTS, X-Frame-Options, X-Content-Type-Options)
- [ ] File validation — MIME-type check + magic-byte check (not just extension) + max size on all uploads
- [ ] Secrets via environment variables only, `.env.example` committed, real `.env` gitignored
- [ ] Password hashing via bcrypt (Passlib), never reversible storage
- [ ] JWT short-lived access tokens + rotating refresh tokens, revocation list in Redis

---

## 9. Error Handling & Logging

Consistent envelope on every error response:
```json
{
  "success": false,
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job does not exist",
    "request_id": "..."
  }
}
```
- `structlog` JSON logging, every log line carries `request_id` (generated in middleware) and `error_id` (generated on exception)
- Global exception handler maps domain exceptions (`JobNotFoundError`, `InsufficientPermissionsError`, etc.) to the correct HTTP status + error code, so services raise semantic exceptions, not HTTP exceptions directly — keeps services framework-agnostic

---

## 10. Testing Strategy (target: 70%+ coverage)

- **Unit tests** (Pytest): services and repositories in isolation, DB mocked or via a test transaction that rolls back
- **Integration tests**: real Postgres (test container) + real Redis, testing repository → DB behavior and org-isolation specifically (a dedicated test suite that asserts org A can never see org B's data — this is a strong thing to point at in the demo video)
- **API tests** (HTTPX + Pytest): full request/response cycle per endpoint, including auth failures, validation failures, RBAC denials
- **AI pipeline tests**: mock the LLM call (via `instructor`'s test mode / a fake LiteLLM response) so tests are deterministic and don't burn API cost; test the retrieval/reranking logic against fixture data separately from the generation step
- CI runs the full suite on every push (GitHub Actions)

---

## 11. DevOps

- `Dockerfile` per service (backend, frontend), multi-stage builds to keep images small
- `docker-compose.yml`: postgres, redis, qdrant, minio, backend, celery-worker, celery-beat (if needed for scheduled jobs), frontend, nginx/traefik — one-command `docker compose up`
- Health check endpoints (`/health`, `/health/ready`) wired into Compose `healthcheck` blocks so dependent services wait properly
- `.env.example` with every required variable documented
- GitHub Actions pipeline: lint (ruff/eslint) → test (pytest, vitest) → build Docker image → (optionally) push to a registry

---

## 12. Scaling Strategy (documentation deliverable)

To be written up as a dedicated doc answering the brief's explicit question — target numbers: **10,000 organizations, 1M candidates, 500 concurrent recruiters.**

Key points to cover:
- **DB**: read replicas for analytics queries; partitioning `application_stage_history` and `ai_usage_logs` by month once volume justifies it; connection pooling via PgBouncer
- **Vector search**: Qdrant supports horizontal sharding/clustering — collections can be sharded by org or by size tier
- **API**: stateless FastAPI instances behind a load balancer, horizontal autoscaling on CPU/request-latency
- **Background jobs**: Celery workers scaled independently per queue (parsing queue vs. AI queue vs. email queue) so a burst in resume uploads doesn't starve email sending
- **Caching**: Redis cluster for AI result caching at scale, cache hit rate as a monitored metric
- **Multi-tenancy at scale**: shared-DB model holds up to a point; documented migration path to DB-per-large-tenant for the biggest customers (e.g., a bank with strict data residency needs) as a hybrid model
- **Cost control at scale**: `ai_usage_logs` becomes the basis for per-org AI cost attribution and budget alerts

---

## 13. Deliverables Checklist

- [ ] GitHub repository (clean commit history, meaningful messages)
- [ ] Live demo (deploy backend + frontend somewhere reachable — e.g., Railway/Render for backend services, Vercel for frontend, or a single VPS running the full Compose stack)
- [ ] Docker setup (`docker compose up` works from a clean clone)
- [ ] README (setup instructions, architecture summary, roadmap section for unbuilt bonus features)
- [ ] Architecture diagram (the diagram in Section 3, cleaned up visually)
- [ ] ER diagram (generated from final SQLAlchemy models)
- [ ] API documentation (auto-generated Swagger/OpenAPI at `/docs`, plus a short Postman/curl walkthrough in README)
- [ ] Scaling strategy doc (Section 12, expanded)
- [ ] Demo video (5–10 min): walk through auth → job creation → candidate application → resume parsing → AI match result → copilot query → analytics dashboard → point out the layered architecture and the `ai_usage_logs` table as evidence of production thinking

---

## 14. Day-by-Day Plan (7–10 days, full-time)

| Day | Focus |
|---|---|
| 1 | Repo scaffold, Docker Compose (postgres/redis/qdrant/minio wired and healthy), DB schema → Alembic migrations, ER diagram draft |
| 2 | Auth (register/login/refresh/verify/reset/Google OAuth), RBAC (Casbin), org isolation middleware + tests |
| 3 | Departments/Jobs/Pipeline stages CRUD, Candidates CRUD + resume upload to MinIO |
| 4 | Resume parsing pipeline (Docling → structured extraction → Celery task), embeddings into Qdrant |
| 5 | AI matching pipeline end-to-end (hybrid search → rerank → LLM explanation → caching → usage logging) |
| 6 | AI Recruiter Copilot + Analytics dashboard queries (backend) |
| 7 | Frontend: dashboard shell, job/candidate management, pipeline board (drag-and-drop), candidate profile w/ AI match view |
| 8 | Frontend: analytics charts, candidate portal, interview scheduler + AI feedback (thin), notifications (basic) |
| 9 | Testing push to 70%+ coverage, security pass (rate limiting, headers, file validation), CI pipeline green |
| 10 | Docs (README, architecture/ER diagrams finalized, scaling strategy), deploy live demo, record demo video, final polish |

*Buffer built in: if running behind by Day 7, cut Day 8's "thin" scheduler/notifications work first — they're worth the least rubric marks.*

---

## 15. What to Explicitly Call Out to Evaluators

Evaluators are grading judgment, not just output. Worth stating directly in the README/demo:
1. Why hybrid AI (local embeddings/rerank + managed LLM generation) was chosen over fully local or fully API-based
2. Why NL→Copilot uses a constrained filter schema instead of raw NL→SQL (security reasoning)
3. Why shared-DB multi-tenancy with `org_id` was chosen over schema/DB-per-tenant, and the scaling path if that changes
4. What was deliberately cut (bonus feature list) and why, with a one-line "how I'd build it" for each
