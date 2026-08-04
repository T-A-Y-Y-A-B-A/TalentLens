# TalentLens — Security Plan

Security is worth 10 rubric marks directly, but it also underpins Backend (20) and Architecture (15) — a system evaluators can poke a hole in during a 5-minute review costs you more than a missing bonus feature. This doc is the checklist to build against and the checklist to demo against.

---

## 1. Authentication

| Control | Implementation |
|---|---|
| Password storage | bcrypt via Passlib, cost factor 12. Never log or return password fields, even hashed. |
| Access tokens | JWT, short-lived (15 min), signed with a rotated secret (python-jose), contain `sub`, `org_id`, `role`, `is_platform_admin`, `exp`, `jti`. |
| Refresh tokens | Opaque random token, stored hashed in `refresh_tokens` table, long-lived (7–14 days), rotated on every use (old one revoked when a new one is issued — detects token replay). |
| Token revocation | Revoked/rotated refresh tokens tracked in DB; access-token `jti` blacklist in Redis for immediate logout/revocation without waiting for expiry. |
| Google OAuth | `authlib`, verify `id_token` signature and `aud` claim server-side, never trust client-supplied profile data without re-verification. |
| Email verification | Required before first login on password-based accounts; verification token single-use, expires in 24h. |
| Password reset | Single-use token, expires in 30 min, invalidates all existing refresh tokens for that user on successful reset (kills any hijacked session). |
| Brute-force protection | Rate limit login attempts per email + per IP (see Section 4); exponential lockout after N failed attempts. |

---

## 2. Authorization (RBAC + Multi-Tenant Isolation)

| Control | Implementation |
|---|---|
| Role model | 4 roles (super_admin, hr_manager, recruiter, interviewer) enforced via **Casbin** policies, checked in the **service layer**, not just route decorators — so authorization can't be bypassed by calling a service method directly from another code path. |
| Tenant isolation | Every tenant-owned table has `org_id`. `BaseRepository` auto-injects `WHERE org_id = :current_org_id` on every query — structurally impossible to forget. `org_id` comes from the verified JWT claim, never from a request body or query param. |
| Defense in depth | Postgres Row-Level Security (RLS) policies as a second enforcement layer beneath the app-layer filtering — even a bug in the repository layer can't leak cross-org data. |
| Platform admin | `is_platform_admin` flag, cross-org access routed through a separate, explicitly audited service path (every platform-admin action written to `audit_logs`). |
| Object-level checks | Beyond role checks: e.g. an `interviewer` can only see interviews they're assigned to, not all interviews in the org — enforced in the service layer per-endpoint. |
| Isolation testing | Dedicated automated test suite: seed 2+ orgs with overlapping data, assert every endpoint returns 403/404 (not the other org's data) when accessed cross-org. This is the single most demo-worthy security test to show evaluators. |

---

## 3. Input Validation & Injection Prevention

| Control | Implementation |
|---|---|
| Request validation | Pydantic v2 models on every endpoint — reject unexpected fields, enforce types/lengths/formats before any business logic runs. |
| SQL injection | SQLAlchemy ORM exclusively; no raw string interpolation into queries anywhere in the codebase (grep-checked before submission). AI Copilot NL query is deliberately **not** translated into raw SQL — it maps to a constrained, typed filter schema instead, closing off the highest-risk injection surface in the whole system. |
| XSS | React/Next.js auto-escapes output by default; any place raw HTML is rendered (e.g. AI-generated summaries) is explicitly sanitized (`DOMPurify`) before render. `Content-Security-Policy` header set to restrict script sources. |
| File upload validation | MIME-type check **and** magic-byte inspection (not just file extension), max file size enforced, files scanned for allowed types only (PDF/DOCX for resumes), stored in MinIO with randomized object keys (never trust user-supplied filenames for storage paths). |
| JSONB field validation | Structured fields stored as JSONB (skills, experience, etc.) are validated against a Pydantic schema before insert — prevents malformed or oversized blobs from AI extraction reaching the DB unchecked. |
| LLM output validation | All LLM responses parsed via `instructor` against a strict Pydantic schema — a malformed or injected LLM response fails validation rather than silently propagating bad data (also mitigates basic prompt-injection-via-resume-content, since the output shape is enforced regardless of what the model was tricked into saying). |

---

## 4. Rate Limiting & Abuse Prevention

| Control | Implementation |
|---|---|
| Global rate limit | SlowAPI + Redis, per-IP baseline on all endpoints. |
| Auth endpoints | Stricter limits on `/login`, `/register`, `/password-reset` specifically (these are the highest-value brute-force targets). |
| AI endpoints | Per-org rate limit on matching/copilot calls — protects both against abuse and against runaway AI cost, ties directly into the cost-tracking story in `ai_usage_logs`. |
| Candidate portal | Separate, lower rate-limit tier for unauthenticated/candidate-facing endpoints (resume upload, status check) since this is the most public-facing surface. |

---

## 5. Transport & Headers

| Control | Implementation |
|---|---|
| TLS | Terminated at Traefik/Nginx in front of the API; HTTP → HTTPS redirect enforced. |
| Secure headers | `Strict-Transport-Security`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy` — via a FastAPI middleware (`secure` library or hand-rolled). |
| CORS | Explicit allow-list of frontend origins only, credentials-aware CORS config, no wildcard `*` in production. |

---

## 6. Secrets & Configuration

| Control | Implementation |
|---|---|
| Secrets management | All secrets (DB creds, JWT signing key, LLM API keys, OAuth client secret, S3/MinIO keys) via environment variables only. `.env.example` committed with placeholder values and comments; real `.env` gitignored, never committed — checked before every commit. |
| Secret rotation | JWT signing key and refresh-token hashing salt documented as rotatable via env var swap + a grace-period dual-key verification window (documented, not necessarily built, given time constraints). |
| Least privilege | Separate DB roles/credentials for the app vs. migrations where feasible; MinIO bucket policies scoped to only what the app needs. |

---

## 7. Data Protection

| Control | Implementation |
|---|---|
| Soft delete | `deleted_at` on all tenant tables — no hard deletes from the API, preserves audit trail and prevents accidental data loss from cascading. |
| Audit logging | `audit_logs` table records actor, action, entity, and diff for sensitive operations (role changes, deletions, platform-admin actions). |
| PII handling | Candidate PII (email, phone, resume content) is the most sensitive data in the system — access to raw resume files gated by the same org+role checks as everything else; resume file URLs are never permanently public (MinIO presigned URLs with short expiry, not public buckets). |
| AI data handling | Resume content sent to the managed LLM (Claude via LiteLLM) only after retrieval narrowing (see AI pipeline) — minimizes the amount of raw PII sent externally per call. Documented explicitly as a privacy-conscious design choice. |

---

## 8. Dependency & Container Security

| Control | Implementation |
|---|---|
| Dependency scanning | `pip-audit` / OWASP Dependency-Check and `npm audit` run in CI; documented as a required, non-blocking-initially check. |
| Static analysis | `bandit` run in CI for common Python security anti-patterns (hardcoded secrets, unsafe eval, etc.). |
| Container scanning | `trivy` scan on built Docker images as a CI step, documented even if only run manually given time constraints. |
| Minimal images | Multi-stage Docker builds, non-root user inside containers, no dev dependencies in production images. |

---

## 9. What Gets Demoed vs. What Gets Documented

Given the timeline, be explicit about which of the above is **fully implemented and demoable** vs. **implemented at a basic level** vs. **documented as the production-hardening path**:

**Fully implemented, demo-ready:**
- JWT auth + refresh + revocation, RBAC via Casbin, org isolation (with the automated cross-org test suite — this is the headline security demo)
- Pydantic validation everywhere, file upload validation, SQLAlchemy-only queries
- Rate limiting on auth + AI endpoints
- Secure headers, CORS lockdown
- Soft delete + audit logging on sensitive actions

**Basic level, mentioned honestly:**
- Postgres RLS as a secondary layer (policy examples included, not exhaustively applied to every table)
- Dependency/container scanning (CI step present, not a full triage workflow)
- Secret rotation (documented process, not automated)

**Documented as roadmap:**
- WAF / DDoS protection at the infra layer (would sit in front of Traefik in a real deployment — Cloudflare or similar)
- Full SOC2-style access review workflows, penetration testing

This honesty is itself a positive signal to evaluators — it shows you can distinguish "secure enough for this exercise" from "secure enough for a bank's HR data" (relevant since XYZ Bank is literally one of the seeded orgs in the brief), and that you know the difference.
