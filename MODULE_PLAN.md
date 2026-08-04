# TalentLens — Per-Module Implementation Plan

This is the build reference. For each module: what it does, endpoints, data flow, implementation tasks in order, and acceptance criteria (how you know it's actually done, not just "exists"). Build in this order — later modules depend on earlier ones.

---

## Module 0 — Foundation (Day 1, blocks everything)

**Purpose:** Nothing else can be built until this exists.

**Tasks:**
1. Repo structure:
   ```
   /backend
     /app
       /api/v1          (routers)
       /services
       /repositories
       /models           (SQLAlchemy)
       /schemas          (Pydantic)
       /core             (config, security, deps)
       /ai
         /prompts
         /pipelines
       /workers          (Celery tasks)
     /alembic
     /tests
   /frontend             (Next.js 15)
   /docs
   docker-compose.yml
   ```
2. `docker-compose.yml`: postgres, redis, qdrant, minio, backend, celery-worker, frontend, traefik/nginx — with `healthcheck` blocks
3. `BaseRepository` with auto org-scoping (`WHERE org_id = :current_org_id`) — this is the single most important class in the codebase
4. Global exception handler → consistent `{success, error: {code, message, request_id}}` envelope
5. `structlog` JSON logging middleware, request ID injection
6. Alembic set up, base migration with all Section-5 schema tables from PLANNING.md
7. `/health` and `/health/ready` endpoints

**Acceptance criteria:** `docker compose up` from clean clone brings up all services healthy; `/health` returns 200; Alembic migration runs clean against empty DB.

---

## Module 1 — Authentication & RBAC (Day 2)

**Purpose:** Everything downstream needs an authenticated, org-scoped, role-checked user.

**Endpoints (`/api/v1/auth`):**
- `POST /register` — email, password, org_id (or org creation if first user), role defaults to `hr_manager` for org creators
- `POST /login` — returns access + refresh token
- `POST /refresh` — rotates refresh token, issues new access token
- `POST /logout` — revokes refresh token
- `POST /verify-email` — consumes verification token
- `POST /password-reset/request`
- `POST /password-reset/confirm`
- `GET /oauth/google/login` / `GET /oauth/google/callback`
- `GET /me` — current user profile

**Data flow:** Register → hash password (bcrypt) → create user (unverified) → send verification email (Celery task) → Login checks `is_verified` → issue JWT (access) + opaque refresh token (hashed, stored in `refresh_tokens`).

**Implementation tasks (in order):**
1. `User`, `RefreshToken`, `PasswordReset`, `EmailVerification` models + migration
2. Password hashing utility (Passlib/bcrypt)
3. JWT issue/verify utilities (python-jose), `jti` blacklist check against Redis
4. Register/login/refresh/logout endpoints + services
5. Email verification flow (Celery task sends email via SMTP — use Mailpit locally for dev)
6. Password reset flow, with "invalidate all refresh tokens" on successful reset
7. Google OAuth via authlib, verify `id_token` server-side
8. `get_current_user` FastAPI dependency — resolves JWT → user → attaches `org_id`, `role` to request context
9. Casbin policy model + enforcement dependency (`require_role(...)`) usable on routes, plus service-layer checks for object-level rules
10. Rate limiting on `/login`, `/register`, `/password-reset/*` (SlowAPI)

**Acceptance criteria:** Full register→verify→login→refresh→logout cycle works via API tests. Wrong password / unverified email / expired token all return correct error codes. Cross-role access to a role-restricted test endpoint returns 403.

---

## Module 2 — Organization Management (Day 2, alongside Module 1)

**Purpose:** Multi-tenant foundation; seeded orgs used for isolation testing throughout the rest of the build.

**Endpoints (`/api/v1/organizations`):**
- `POST /` — create org (platform admin only, or self-serve signup flow)
- `GET /{id}` — org details
- `PATCH /{id}` — update org settings
- `GET /{id}/users` — list org users (hr_manager+)
- `PATCH /{id}/users/{user_id}/role` — change a user's role (hr_manager+, audit-logged)

**Data flow:** Org created → first registering user becomes `hr_manager` for that org → subsequent users join via invite (email-based invite token — can be a simple pre-created user record with a "claim" endpoint if time-constrained).

**Implementation tasks:**
1. `Organization` model + migration
2. Org CRUD service/repo
3. Seed script: create 3 demo orgs (DigitalSofts, ABC Software, XYZ Bank) with overlapping-looking data — this seed data is what your isolation tests and demo video both use
4. Cross-org isolation test suite: for every existing endpoint so far, assert org A's token cannot read/write org B's resources

**Acceptance criteria:** Seed script produces 3 orgs with distinct users/data. Isolation test suite passes and is runnable as its own `pytest` target — this is your headline security demo.

---

## Module 3 — Recruitment Module: Departments, Jobs, Pipeline (Day 3)

**Endpoints (`/api/v1/departments`, `/api/v1/jobs`, `/api/v1/jobs/{id}/pipeline-stages`):**
- `POST/GET/PATCH/DELETE /departments`
- `POST/GET/PATCH/DELETE /jobs` (with `department_id`, `requirements` JSONB, `status`)
- `POST /jobs/{id}/pipeline-stages` — create custom stage
- `PATCH /jobs/{id}/pipeline-stages/reorder` — bulk reorder (drag-and-drop support)
- `GET /jobs/{id}/pipeline-stages`

**Data flow:** Job created with default pipeline template (Applied→Screening→Interview→Technical→HR→Offer→Hired) cloned into `pipeline_stages` for that job, then customizable per job.

**Implementation tasks:**
1. `Department`, `Job`, `PipelineStage` models + migration
2. Default pipeline template constant, cloned on job creation
3. CRUD services/repos, soft delete on all
4. Reorder endpoint — accepts list of `{stage_id, order_index}`, updates in one transaction
5. Job embedding trigger stub (real embedding call wired in Module 6, but the `job_embeddings` pointer table and Celery task skeleton set up here)

**Acceptance criteria:** Creating a job auto-creates the default pipeline; stages can be reordered and the new order persists and is returned correctly on `GET`.

---

## Module 4 — Candidate Management & Applications (Day 3–4)

**Endpoints (`/api/v1/candidates`, `/api/v1/applications`):**
- `POST /candidates` (internal, HR-created) / `POST /candidate-portal/register` (candidate self-serve, separate auth context)
- `GET/PATCH /candidates/{id}`
- `POST /candidates/{id}/resume` — file upload → MinIO → triggers parsing task
- `POST /applications` — candidate applies to a job
- `PATCH /applications/{id}/stage` — move to a new pipeline stage (writes `application_stage_history`)
- `GET /applications/{id}` / `GET /jobs/{id}/applications` (pipeline board data)

**Data flow:** Resume upload → MinIO → `resumes` row (status=pending) → Celery task picks up → Module 5 parsing pipeline runs → status updates to done/failed, `resume_parsed_data` populated.

**Implementation tasks:**
1. `Candidate`, `Resume`, `Application`, `ApplicationStageHistory` models + migration
2. Candidate CRUD (both HR-facing and candidate-portal-facing, separate permission contexts)
3. File upload endpoint: MIME + magic-byte validation, size limit, MinIO storage with randomized keys, presigned URL generation for retrieval
4. Application creation + stage-move endpoint (writes history row on every move — this feeds Module 8 analytics directly)
5. Candidate portal auth: candidates are not `users` (no org role) — separate lightweight auth (JWT scoped to `candidate_id`, no org role claims)
6. Notification stub on stage change (real notification wiring in Module 9)

**Acceptance criteria:** Full flow — candidate registers on portal → uploads resume → applies to a job → HR moves them through 2+ pipeline stages → `application_stage_history` has correct rows in order.

---

## Module 5 — Resume Parsing Pipeline (Day 4)

**Purpose:** Turns uploaded PDFs into structured, queryable, embeddable data. This is the first AI module and sets the pattern for all later ones.

**Trigger:** Celery task fired on resume upload (Module 4).

**Data flow (from PLANNING.md Section 7.1):**
```
MinIO file → Docling extraction (layout-aware)
  → Tesseract OCR fallback if low confidence / scanned
  → LLM (instructor, versioned prompt) → structured Pydantic schema
  → resume_parsed_data row
  → chunk resume text → BGE embeddings → upsert to Qdrant (candidate_id, org_id metadata)
  → resumes.parse_status = 'done'
```

**Implementation tasks:**
1. Celery task `parse_resume(resume_id)`
2. Docling integration, text/section extraction
3. OCR fallback branch (Tesseract) for scanned docs
4. `ResumeExtraction` Pydantic schema (Name, Email, Phone, Skills, Experience, Education, Certifications, Projects)
5. `call_llm()` shared utility (this is the reusable core: cache check → LiteLLM call → instructor validation → usage logging → retry via tenacity) — build this once, use it in every AI module from here on
6. Prompt file `prompts/resume_extraction_v1.py`
7. Chunking strategy (section-aware, not naive fixed-width) + BGE embedding via `sentence-transformers`
8. Qdrant collection setup (`candidates` collection, metadata: `org_id`, `candidate_id`)
9. Error handling: failed parse → status='failed', error stored, does not crash the worker

**Acceptance criteria:** Upload a real sample resume → within seconds/minutes it's fully parsed with correct structured fields → visible in Qdrant via a debug query → `ai_usage_logs` has a row with token/cost/latency for the extraction call.

---

## Module 6 — AI Candidate Matching (Day 5)

**Purpose:** The centerpiece AI module — the one the brief most explicitly scrutinizes ("do NOT simply send the resume to ChatGPT").

**Endpoints (`/api/v1/matching`):**
- `POST /jobs/{id}/match` — trigger matching run for a job against candidate pool (async, Celery)
- `GET /applications/{id}/match-result` — retrieve match result for a specific application
- `GET /jobs/{id}/top-candidates` — ranked list

**Data flow (from PLANNING.md Section 7.2):**
```
Job description → embed once (cached) →
Qdrant hybrid search (dense + sparse/BM25) over candidates, org-filtered →
Cross-encoder rerank top-N →
Top-K → call_llm() with matching_v1 prompt →
  {match_pct, missing_skills, strengths, weaknesses, recommendation, interview_questions} →
Redis cache (key = hash(prompt_version + job_id + candidate_id)) →
ai_match_results row + ai_usage_logs row
```

**Implementation tasks:**
1. Job description embedding on job publish (reuse `job_embeddings` pointer table from Module 3)
2. Qdrant hybrid search query (dense vector + BM25 sparse), metadata filter by `org_id` and any structured filters (min experience, required certs) from `resume_parsed_data`
3. Cross-encoder reranking step (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
4. `matching_v1` prompt, `MatchResult` Pydantic schema
5. Wire through `call_llm()` from Module 5
6. `ai_match_results` persistence
7. Celery task for async matching (don't block the request — matching runs in background, frontend polls or gets notified)
8. Endpoint to retrieve results, sorted by `match_pct`

**Acceptance criteria:** Given a real job description and 5+ seeded candidate resumes with varying relevance, matching returns a sensible ranked list with explainable, non-generic reasoning per candidate. Rerun on identical input hits cache (visible in `ai_usage_logs.cache_hit`).

---

## Module 7 — AI Recruiter Copilot (Day 6)

**Purpose:** Demonstrates NL→structured-query capability safely (see SECURITY_PLAN.md Section 3 for why raw NL→SQL is avoided).

**Endpoints (`/api/v1/copilot`):**
- `POST /query` — `{ "query": "Find Python developers with Kubernetes experience" }` → returns interpreted filter + matching candidates

**Data flow (from PLANNING.md Section 7.3):**
```
NL query → call_llm() with copilot_v1 prompt →
  CopilotFilter{skills, min_experience, certifications, keywords} (instructor-validated) →
Deterministic query: JSONB filter on resume_parsed_data (org-scoped) + Qdrant semantic search on keywords →
Response: { interpreted_as: <filter shown to user>, results: [...candidates] }
```

**Implementation tasks:**
1. `CopilotFilter` Pydantic schema, `copilot_v1` prompt
2. Service function: LLM → filter → build SQLAlchemy query from filter fields (never string-concatenated) + Qdrant call for the free-text portion
3. Response includes the interpreted filter explicitly (transparency — this is a demo highlight)
4. Handle ambiguous/unparseable queries gracefully (clarifying-question fallback or "no filter matched" response, not a crash)

**Acceptance criteria:** 3–5 varied natural language queries against seeded data return correct, explainable results with the interpreted filter visible in the response.

---

## Module 8 — Analytics Dashboard (Day 6, backend) / Day 7 (frontend charts)

**Endpoints (`/api/v1/analytics`):**
- `GET /funnel?job_id=` — counts per pipeline stage
- `GET /time-to-hire` — avg days from `applied_at` to `hired` stage, computed from `application_stage_history`
- `GET /offer-acceptance-rate`
- `GET /candidate-sources` — breakdown by `candidates.source`
- `GET /recruiter-performance` — applications moved / hires per recruiter (via `application_stage_history.moved_by`)

**Data flow:** All computed via aggregation queries against `application_stage_history` and `applications` — no separate analytics store needed at this scale, but queries are written to be index-friendly (`(org_id, job_id, created_at)`).

**Implementation tasks:**
1. Aggregation queries in a dedicated `AnalyticsRepository` (raw enough SQL/ORM aggregation, kept out of the service layer's business logic)
2. Endpoints wired to the seed data — verify numbers are sane against manually-checked seed data
3. Frontend: Recharts funnel (bar/funnel chart), line chart for time-to-hire trend, pie/donut for sources, table for recruiter performance

**Acceptance criteria:** All 5 charts render against seeded data with numbers you can manually verify are correct from the underlying `application_stage_history` rows.

---

## Module 9 — Interview Scheduler & AI Feedback (Day 8, thin per SCOPE_LOCK.md)

**Endpoints (`/api/v1/interviews`):**
- `POST /interviews` — schedule (application_id, interviewer_id, scheduled_at, meeting_link)
- `GET /interviews?interviewer_id=` — interviewer's own list (object-level RBAC: interviewer only sees their own)
- `POST /interviews/{id}/feedback` — raw notes in
- `GET /interviews/{id}/feedback` — structured AI feedback out

**Data flow:** Feedback notes → `call_llm()` with `feedback_v1` prompt → `{summary, strengths, weaknesses, recommendation, overall_score}` → `interview_feedback` row.

**Implementation tasks:**
1. `Interview`, `InterviewFeedback` models + migration
2. Scheduling endpoint + email invite (Celery task, reuses email infra from Module 1)
3. Feedback endpoint reusing `call_llm()` pattern exactly as Module 6/7 — should be fast to build since the pattern already exists
4. Object-level RBAC: interviewer role restricted to their own assigned interviews

**Acceptance criteria:** Schedule → mark completed → submit raw notes → structured AI feedback generated and retrievable.

---

## Module 10 — Notifications (Day 8, thin)

**Endpoints (`/api/v1/notifications`):**
- `GET /notifications` — current user/candidate's notifications
- `PATCH /notifications/{id}/read`

**Data flow:** Key events (application stage change, interview scheduled, offer made) create a `notifications` row + trigger one email send via Celery.

**Implementation tasks:**
1. `Notification` model + migration
2. Event hooks in existing services (stage change in Module 4, interview scheduled in Module 9) call a shared `notify()` service function
3. Simple in-app list endpoint + read-state toggle
4. One email template, SMTP send via Celery task

**Acceptance criteria:** Moving an application stage produces a visible notification and (in dev) a visible email in Mailpit.

---

## Module 11 — Frontend (Days 7–8, parallel to backend polish)

**Structure:** Next.js 15 App Router, two auth contexts (HR dashboard vs. candidate portal).

**Screens:**
1. Auth: login, register, verify, reset, Google OAuth button
2. HR Dashboard shell: sidebar nav, org context
3. Jobs: list, create/edit, pipeline board (drag-and-drop via `@dnd-kit`)
4. Candidates: list, detail view with resume viewer + AI match breakdown panel
5. Copilot: simple search-bar UI, shows interpreted filter + results
6. Analytics: 5 charts from Module 8
7. Interviews: schedule form, feedback view
8. Candidate portal: register, resume upload, application status tracker, profile edit

**Implementation tasks:**
1. Auth flow + protected route wrapper, token refresh handling (silent refresh on 401)
2. API client layer (typed, generated from OpenAPI schema if time allows — `openapi-typescript`)
3. Pipeline board component (drag-and-drop calling the reorder/stage-move endpoints)
4. AI match result panel — designed to make the explainability visible (this is a strong demo-video moment: show match %, missing skills, reasoning, not just a number)
5. Charts wired to analytics endpoints
6. Candidate portal as a distinct, simpler layout

**Acceptance criteria:** A full walkthrough — login, create job, seed/upload candidate, see AI match, move through pipeline, view analytics — works end-to-end in the browser with no console errors.

---

## Module 12 — Testing, Security Hardening, CI (Day 9)

**Tasks (cutting across all modules, not a separate feature):**
1. Backfill unit tests for services/repositories not yet covered, target 70%+ via `pytest --cov`
2. Integration tests: real Postgres + Redis, org isolation suite (from Module 2) run as part of this
3. API tests: HTTPX-based, cover auth failures, validation failures, RBAC denials per SECURITY_PLAN.md
4. Mock LLM calls in tests (instructor test mode / fake LiteLLM responses) — deterministic, no API cost in CI
5. Security pass against SECURITY_PLAN.md checklist: rate limiting verified, headers verified (curl check), file upload validation tested with malicious/mismatched files
6. GitHub Actions: lint → test → build Docker image, all green

**Acceptance criteria:** `pytest --cov` reports ≥70%; CI pipeline green on a clean push; manual curl-based security spot-checks pass (headers present, rate limit triggers, cross-org 403s).

---

## Module 13 — Documentation & Deployment (Day 10)

**Tasks:**
1. README: setup instructions (`docker compose up` from clean clone), architecture summary, roadmap section (cut features from SCOPE_LOCK.md)
2. Architecture diagram (from PLANNING.md Section 3, cleaned up visually — use the Visualizer or a diagram tool)
3. ER diagram generated from final SQLAlchemy models
4. Scaling strategy doc (PLANNING.md Section 12, expanded with any real numbers/benchmarks gathered during build)
5. Deploy live demo (Render/Railway for backend + Postgres/Redis, Vercel for frontend, or single VPS running full Compose stack)
6. Record 5–10 min demo video: auth → job creation → candidate application → resume parsing → AI match (explain the pipeline, not just the result) → copilot query → analytics → close on architecture diagram + `ai_usage_logs` table as evidence of production thinking

**Acceptance criteria:** A stranger can clone the repo, run one command, and have a working system; live demo URL is reachable; video clearly demonstrates every Core module from SCOPE_LOCK.md.

---

## Build Order Summary

```
0. Foundation
1. Auth/RBAC ─┐
2. Orgs       ├─→ 3. Jobs/Pipeline ─→ 4. Candidates/Applications ─→ 5. Resume Parsing
                                                                          │
                                                                          ▼
                                                                   6. AI Matching
                                                                          │
                                            ┌─────────────────────────────┼──────────────┐
                                            ▼                             ▼              ▼
                                     7. AI Copilot              8. Analytics    9. Interviews/AI Feedback
                                                                                        │
                                                                                        ▼
                                                                                 10. Notifications
                                                                                        │
11. Frontend (parallel from ~Day 6 once core APIs exist) ──────────────────────────────┘
                                                                                        │
                                                                                        ▼
                                                                          12. Testing/Security/CI
                                                                                        │
                                                                                        ▼
                                                                          13. Docs/Deploy/Video
```
