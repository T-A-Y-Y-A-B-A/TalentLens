# TalentLens — Scope Lock

This is the contract for the build. If it's not listed here, it doesn't get built until everything above it is done. Revisit only if running significantly ahead of schedule.

---

## CORE — must be excellent (this is where the marks are)

| Feature | Definition of "done" |
|---|---|
| **Auth + RBAC + multi-tenant** | Register, login, refresh, password reset, email verification, Google OAuth all working. 4 roles enforced via Casbin at the service layer. Org isolation proven with an automated test suite (org A cannot see org B's data under any endpoint). |
| **Job / Candidate / Pipeline CRUD** | Departments, Jobs, custom per-job pipeline stages, drag-and-drop stage transitions, Candidates CRUD, resume upload to MinIO. Stage moves write to `application_stage_history`. |
| **Resume parsing** | Docling extraction → structured Pydantic-validated fields (name, email, phone, skills, experience, education, certifications, projects) → stored in `resume_parsed_data`. Runs as a Celery task, status visible (pending/processing/done/failed). |
| **AI Matching** | Full pipeline: embed → Qdrant hybrid search → cross-encoder rerank → LLM explanation (match %, missing skills, strengths, weaknesses, recommendation, interview questions). Cached, versioned, logged to `ai_usage_logs`. |
| **AI Copilot (one query type)** | NL query → constrained structured filter (skills, min experience, certifications, keywords) → deterministic query + Qdrant semantic search. Interpreted filter shown back to the user. One well-built query type beats three shallow ones. |
| **Basic analytics** | Hiring funnel, time-to-hire, offer acceptance rate, candidate sources, recruiter performance — computed from real data (`application_stage_history`), rendered with Recharts. |

**Bar for "excellent":** clean layering (router→service→repo), tested, org-scoped, handles edge cases (empty states, malformed resumes, no matches found), visible in the demo video with real data — not just "it exists."

---

## THIN BUT PRESENT — functional, not polished

| Feature | Definition of "thin but done" |
|---|---|
| **Interview scheduler** | Create a slot (date/time), assign interviewer, generate a meeting link field (can be a manually-entered Zoom/Meet link, no live calendar API sync), send email invite. No availability-conflict detection, no calendar UI beyond a simple list. |
| **AI interview feedback** | Reuses the exact same `call_llm()` pattern as matching. Raw notes in → structured summary/strengths/weaknesses/score out. One prompt version, no fine-tuning of output quality beyond "it works and is explainable." |
| **Notifications** | In-app notification records created on key events (application moved, interview scheduled, offer made) + one email trigger via a simple SMTP/transactional email call. No real-time push, no WhatsApp, no in-app read-state UI polish. |

**Bar for "thin but present":** the feature works end-to-end once, is visible in the demo, and is honestly described in the README as "MVP-level, here's what production would add." Do not spend more than ~1 day total across all three.

---

## CUT — documented only, not built

Each gets 1–2 sentences in the README under "Roadmap / What I'd build next," showing you know *how* you'd build it without spending build time on it:

- **Voice interview agent** — would use a real-time speech pipeline (e.g. Twilio Media Streams + Whisper + LLM) feeding into the same `interview_feedback` structured-output pattern already built.
- **WhatsApp notifications** — same `notifications` table, new channel adapter via WhatsApp Business API; no schema change needed.
- **OCR for certificates** — Tesseract fallback already exists in the resume pipeline; extending it to certificate-specific extraction is a new prompt + schema, not new infrastructure.
- **Duplicate candidate detection** — cosine similarity threshold on existing `candidate_embeddings` in Qdrant; the infrastructure is already there, just needs a scheduled dedup job.
- **AI job description generator** — same `call_llm()`/`instructor` pattern used for matching, applied to a JD-generation prompt.
- **Candidate skill graph** — graph DB (Neo4j) or a Postgres adjacency model over extracted skills; visualization layer only, no new AI work.
- **Referral system** — straightforward CRUD + a `source` field already exists on `candidates`.
- **Resume similarity search** — subsumed by the matching pipeline's existing vector search; would just expose candidate-to-candidate similarity as a separate endpoint.
- **AI fraud detection** — anomaly detection on resume/application patterns (duplicate content, inconsistent dates) — a v2 ML classifier, not built.
- **Interview recording analysis** — would sit on top of the voice agent once that exists.
- **Multi-language support** — i18n on frontend + multilingual embedding model swap; mostly a frontend/config effort.
- **Live notifications** — WebSocket layer (or Supabase Realtime-style service) over the existing `notifications` table.
- **Feature flags** — Unleash/Flagsmith integration point; not needed at this scale.
- **Multi-region deployment** — covered narratively in the Scaling Strategy doc, not built.
- **Kubernetes / Helm** — Docker Compose is what's graded; k8s manifests documented as the natural next step in Scaling Strategy, not built.

---

## Rule of thumb if time gets tight

If behind schedule by Day 7: cut from the bottom of "Thin but present" first (notifications → scheduler → AI feedback), never touch Core. Core with rough edges beats Core-plus-Thin with a broken piece.
