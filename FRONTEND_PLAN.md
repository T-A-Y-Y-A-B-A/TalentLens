# TalentLens — Frontend Plan

Locked reference for frontend build, on par with PLANNING.md / SCOPE_LOCK.md / SECURITY_PLAN.md / MODULE_PLAN.md. Covers: page map per principal, permission matrix, auth/identity flows, the invite system, and build order.

**Key principle throughout:** frontend role checks are UX only (avoid flashing UI a user can't use, route them correctly). Every check here has an independent, authoritative enforcement on the backend (Casbin role check + service-layer object check). A frontend-only check is never the sole gate on an action.

---

## 1. Identity Model

Two structurally separate principal types — never merged into one auth system:

- **Staff** — `users` table, JWT carries `role`, `org_id`, `is_platform_admin`, `type: "staff"`
- **Candidate** — `candidates` table, JWT carries `candidate_id` only, `type: "candidate"`, no org/role concept

`type` claim is checked by every backend dependency so a candidate token can never be replayed against staff endpoints, and vice versa.

Frontend never decodes the JWT for logic. Login/refresh responses include an explicit `user` (staff) or `candidate` object; this hydrates a React context (`StaffAuthProvider` / `CandidateAuthProvider`) that the UI reads from. Route trees are fully separate:

```
/portal/*      → CandidateAuthProvider
/dashboard/*   → StaffAuthProvider
/admin/*       → StaffAuthProvider, additionally gated on is_platform_admin
```

---

## 2. Organizations — Fixed, Not Self-Serve

**No `POST /organizations` endpoint exists publicly.** Three orgs are seeded once via a startup script, never created through registration:

```python
ORGANIZATIONS = [
    {"name": "DigitalSofts", "slug": "digitalsofts", "plan": "enterprise"},
    {"name": "ABC Software", "slug": "abc-software", "plan": "pro"},
    {"name": "XYZ Bank", "slug": "xyz-bank", "plan": "enterprise"},
]

SEED_USERS = [  # one pre-seeded HR Manager per org — solves the bootstrap problem
    {"org": "digitalsofts", "email": "hr@digitalsofts.demo", "role": "hr_manager"},
    {"org": "abc-software",  "email": "hr@abc-software.demo",  "role": "hr_manager"},
    {"org": "xyz-bank",      "email": "hr@xyz-bank.demo",      "role": "hr_manager"},
]

SEED_PLATFORM_ADMIN = {"email": "admin@talentlens.demo", "is_platform_admin": True}
```
Document these credentials in README under "Demo Accounts" so evaluators can log in as any role without needing live invite emails.

---

## 3. Staff Registration — Two Paths

**Path A — Invite-based (production-realistic, primary path):**
HR Manager creates an invite (email + role, org taken from their own session) → Celery sends email with `/accept-invite?token=...` link → invitee's email/org/role are pre-filled and locked, they only set name + password.

**Path B — Open demo path (so evaluators can self-serve):**
`/register` shows a dropdown of the 3 seeded orgs. Role is **never** a form field — hardcoded to `recruiter` server-side regardless of what's submitted. An HR Manager can promote them afterward via the team page if higher access is needed.

**Rule that never changes:** role is never asserted by the registering user. It's either automatic (org-creation path — not applicable here since orgs are fixed) or set by someone with authority (HR Manager invite) or defaulted to least-privilege (open demo path).

### Invite data model (new — not previously in schema)
```python
class Invite(Base):
    id: UUID              # PK
    org_id: UUID           # FK organizations.id
    email: str
    role: Literal["recruiter", "interviewer"]   # HR Manager cannot invite another hr_manager
    token_hash: str
    invited_by: UUID       # FK users.id
    status: Literal["pending", "accepted", "revoked", "expired"]
    expires_at: datetime
    created_at, updated_at
```
Endpoints: `POST /organizations/invites` (create), `PATCH /invites/{id}/revoke`, `POST /invites/{id}/resend`, `POST /invites/accept` (consumes token, `org_id`/`role`/`email` resolved server-side — never client-supplied).

---

## 4. Candidate Registration

Fully separate form, no org/role concept at all:
- Full name, email, phone (optional), password + confirm

Candidates use one account across all orgs' job postings — that's the point of being a separate principal.

---

## 5. Page Map by Role

### Public (no auth)
| Page | Purpose |
|---|---|
| `/login` | Staff login (password + Google OAuth) |
| `/register` | Open demo registration (org dropdown, role hardcoded to recruiter) |
| `/accept-invite?token=` | Invite consumption — pre-filled, locked email/org/role |
| `/verify-email` | Email verification link target |
| `/forgot-password`, `/reset-password` | Password reset |
| `/oauth/google/callback` | OAuth redirect handler |
| `/jobs`, `/jobs/[id]` | Public job marketplace listing/detail, "Apply" → candidate portal |

### Candidate Portal (`/portal/*`)
| Page | Purpose |
|---|---|
| `/portal/register`, `/portal/login`, `/portal/forgot-password` | Candidate auth |
| `/portal/dashboard` | Applications overview |
| `/portal/jobs` | Browse published jobs |
| `/portal/apply/[job_id]` | Apply + resume upload |
| `/portal/applications/[id]` | Status tracking — simplified stage labels (`applied / under_review / interview_scheduled / offer / hired / not_selected`), never raw internal `pipeline_stages.name` |
| `/portal/profile` | Edit info, manage resume |
| `/portal/notifications` | Notification list |

### Super Admin (`/admin/*`)
| Page | Purpose |
|---|---|
| `/admin` | Platform overview — org/user counts, total AI spend |
| `/admin/organizations` | List 3 seeded orgs + stats |
| `/admin/organizations/[id]` | Support-view drill-in, read-only unless explicit audited impersonation |
| `/admin/usage` | Cross-org `ai_usage_logs` view, filterable |
| `/admin/audit-logs` | Cross-org audit log viewer |

Deliberately thin — this role exists to prove multi-tenancy works, not to be a full console.

### HR Manager (`/dashboard/*`)
| Page | Purpose |
|---|---|
| `/dashboard` | Org overview |
| `/dashboard/jobs`, `/dashboard/jobs/new`, `/dashboard/jobs/[id]`, `/dashboard/jobs/[id]/pipeline` | Full job + pipeline management incl. delete |
| `/dashboard/candidates`, `/dashboard/candidates/[id]` | Full candidate visibility |
| `/dashboard/copilot` | AI Copilot |
| `/dashboard/interviews`, `/dashboard/interviews/new`, `/dashboard/interviews/[id]` | Org-wide interview management |
| `/dashboard/analytics` | Full org analytics |
| **`/dashboard/settings/team`** | **Team list + Invite Staff action (see Section 3)** |
| `/dashboard/settings/departments` | Department CRUD |
| `/dashboard/settings/org` | Org profile/branding |

### Recruiter (`/dashboard/*`)
Same as HR Manager minus: job delete, `/dashboard/settings/*` (entire settings tree hidden from sidebar and guarded server-side).

### Interviewer (`/dashboard/*`)
| Page | Purpose |
|---|---|
| `/dashboard` | Their upcoming interviews only |
| `/dashboard/interviews` | Own interviews only — same route as other roles, backend returns filtered list |
| `/dashboard/interviews/[id]` | Detail + feedback submission form |
| `/dashboard/candidates/[id]` | Only reachable via link from their own interview detail — object-checked (candidate must have an application tied to their assigned interview) |

Narrowest sidebar — effectively 2 nav items. No jobs list, no copilot, no analytics, no settings.

---

## 6. Permission Matrix (condensed — full detail in SECURITY_PLAN.md)

| Action | Super Admin | HR Manager | Recruiter | Interviewer | Candidate |
|---|---|---|---|---|---|
| Manage org settings | ✅ | ✅ | ❌ | ❌ | — |
| Invite/manage staff | ❌ | ✅ | ❌ | ❌ | — |
| Create/delete department | ❌ | ✅ | ❌ | ❌ | — |
| Create/edit job | ❌ | ✅ | ✅ | ❌ | — |
| Delete job | ❌ | ✅ | ❌ | ❌ | — |
| Move pipeline stage | ❌ | ✅ | ✅ | ❌ | — |
| View all candidates | ✅ (support) | ✅ | ✅ | ❌ | — |
| View own application only | — | — | — | — | ✅ |
| Trigger AI matching | ❌ | ✅ | ✅ | ❌ | — |
| Use AI Copilot | ❌ | ✅ | ✅ | ❌ | — |
| Schedule interview | ❌ | ✅ | ✅ | ❌ | — |
| Submit interview feedback | ❌ | ❌ | ❌ | ✅ (own only) | — |
| View analytics | ✅ platform-wide | ✅ org | ✅ read-only | ❌ | — |

Object-level rules (interviewer sees only own interviews, candidate sees only own applications) are enforced in the service layer via direct ownership checks, not Casbin — see SECURITY_PLAN.md.

---

## 7. Shared Permission Helper (frontend)

Centralized, mirrors the Casbin policy table conceptually so frontend/backend rules stay aligned even though enforced independently:
```ts
// lib/permissions.ts
export const can = {
  createJob: (role: Role) => ["hr_manager", "recruiter"].includes(role),
  deleteJob: (role: Role) => role === "hr_manager",
  manageTeam: (role: Role) => role === "hr_manager",
  manageDepartments: (role: Role) => role === "hr_manager",
  useCopilot: (role: Role) => ["hr_manager", "recruiter"].includes(role),
  viewAnalytics: (role: Role) => ["hr_manager", "recruiter"].includes(role),
};
```
Used to conditionally render nav links/buttons — never the actual security boundary.

---

## 8. Build Order (frontend-first, per current plan)

Since building frontend before backend, use a mock API layer (fixed JSON fixtures matching the Pydantic schemas above) so pages render meaningfully; swap in real endpoints once Module 0–1 backend exists.

1. Auth shell — login/register/accept-invite pages + role-based layout/sidebar driven by mock `user` context
2. `/dashboard/jobs` + `/dashboard/jobs/[id]/pipeline` (kanban — highest visual impact)
3. `/dashboard/candidates/[id]` with AI match panel (mocked match data — AI Engineering demo centerpiece)
4. `/dashboard/copilot`
5. `/dashboard/analytics`
6. `/dashboard/settings/team` (invite flow UI)
7. `/portal/*` candidate side
8. `/dashboard/interviews`, `/admin/*` last (thin scope per SCOPE_LOCK.md)

---

## 9. Open Item Carried Over

JWT storage: localStorage vs HttpOnly cookie decision (flagged in SECURITY_PLAN.md) must be resolved before wiring real auth — affects how the frontend auth context reads the token. Recommended: HttpOnly, Secure, SameSite=Strict cookie for access token; refresh handled via a Next.js route handler proxying to FastAPI, never exposed to client JS.
