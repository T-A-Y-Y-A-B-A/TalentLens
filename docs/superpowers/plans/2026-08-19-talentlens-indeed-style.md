# TalentLens Indeed-Style Job Board & AI Enhancer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Overhaul the candidate job board UI to look like Indeed (with salary ranges and structured sections), expand the database schema to support these detailed fields, and give HR an "Enhance with AI" tool to auto-generate structured job descriptions from rough notes.

**Architecture:**
- **Backend:** Expand `Job` model in `recruitment.py` and schemas in `schemas/recruitment.py`. Create Alembic migration. Add `POST /api/v1/jobs/enhance` endpoint for AI generation.
- **Frontend (HR):** Update `dashboard/jobs/page.tsx` with the AI Enhancer tool and new form fields.
- **Frontend (Candidate):** Update `SplitLayout.tsx` to render salary badges and rich structured sections (company info, responsibilities, expectations, benefits).

---

### Task 1: Backend Database & Schema Evolution

**Files:**
- Modify: `D:\TalentLens\backend\app\models\recruitment.py`
- Modify: `D:\TalentLens\backend\app\schemas\recruitment.py`
- Create: Alembic migration script

**Interfaces:**
- Add to `Job`:
  - `salary_range` (String, nullable)
  - `company_description` (String, nullable)
  - `key_responsibilities` (JSON, nullable)
  - `expectations` (JSON, nullable)
  - `benefits` (JSON, nullable)
- Update `JobRead` and `JobCreate` schemas to match.
- Generate and apply Alembic migration (`alembic revision --autogenerate -m "add indeed style job fields"`, then `alembic upgrade head`).

### Task 2: AI Enhancer API Endpoint

**Files:**
- Modify: `D:\TalentLens\backend\app\api\v1\jobs.py` (or create a dedicated enhancer route).

**Interfaces:**
- Create `POST /api/v1/jobs/enhance` accepting `{"rough_notes": "..."}`.
- Use `openai.AsyncOpenAI()` (or existing LLM client in backend) to prompt the AI to parse rough notes into a structured JSON response:
  - `title`, `description`, `salary_range`, `company_description`, `key_responsibilities` (list), `expectations` (list), `benefits` (list).
- Return this JSON to the frontend.

### Task 3: HR Dashboard - AI Job Creation Form

**Files:**
- Modify: `D:\TalentLens\frontend\src\app\dashboard\jobs\page.tsx`
- Run: `cd frontend && npm run generate:api`

**Interfaces:**
- Add a new "Enhance with AI" section at the top of the job creation dialog.
- Bind the returned AI JSON to the local React states (`title`, `salary_range`, `key_responsibilities`, etc.).
- Update the job submission payload to include the new fields when calling `POST /api/v1/jobs`.

### Task 4: Candidate Portal - Indeed-Style UI Redesign

**Files:**
- Modify: `D:\TalentLens\frontend\src\components\JobBoard\SplitLayout.tsx`

**Interfaces:**
- Redesign the right-hand detail pane.
- Add a prominent Salary Badge below the title.
- Render `company_description`.
- Render `key_responsibilities` as a bulleted list.
- Render `expectations` and `benefits`.
- Ensure mobile responsiveness and clean typography (`prose prose-zinc`).
