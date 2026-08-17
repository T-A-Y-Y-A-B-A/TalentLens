# TalentLens API Documentation

This document outlines the core RESTful endpoints available in the TalentLens API. The backend is built with FastAPI, which auto-generates an OpenAPI (Swagger) schema available at `/docs` when running the application.

## Base URL
All API requests should be prefixed with `/api/v1`.
- **Local environment:** `http://localhost:8000/api/v1`
- **Production environment:** `https://talentlens-backend-production.up.railway.app/api/v1`

---

## 1. Authentication (Staff)

Staff authentication uses JWT access tokens and opaque refresh tokens. Roles include `hr_manager`, `recruiter`, and `interviewer`.

### `POST /auth/login`
Authenticates a staff user.
- **Request Body**: `OAuth2PasswordRequestForm` (`username` = email, `password`)
- **Response**: 
  ```json
  {
    "access_token": "eyJhb...",
    "refresh_token": "d7a8...",
    "token_type": "bearer",
    "user": { "id": "...", "email": "...", "role": "hr_manager", "org_id": "..." }
  }
  ```

### `POST /auth/register`
Open demo registration for testing. Auto-assigns the `recruiter` role.
- **Request Body**: `{ "email": "...", "password": "...", "name": "...", "org_id": "..." }`

### `POST /auth/refresh`
Rotates the refresh token and issues a new access token.
- **Request Body**: `{ "refresh_token": "..." }`

### `GET /auth/oauth/google/login` & `GET /auth/oauth/google/callback`
Initiates and handles the Google OAuth flow for staff users.

---

## 2. Authentication (Candidate Portal)

Candidates use a completely separate auth context from staff. Their JWTs contain a `candidate_id` rather than an `org_id` or `role`.

### `POST /candidate-portal/login`
- **Request Body**: `{ "email": "...", "password": "..." }`
- **Response**: `{ "access_token": "...", "candidate": { ... } }`

### `POST /candidate-portal/register`
- **Request Body**: `{ "email": "...", "password": "...", "name": "..." }`

### `GET /candidate-portal/oauth/google/callback`
Handles Google OAuth specifically for candidate users.

---

## 3. Organizations & Invites

### `GET /organizations/{id}`
Retrieve organization details. (Requires Staff Token)

### `POST /invites`
Create a new invite for a staff member.
- **Auth**: `hr_manager` only.
- **Request Body**: `{ "email": "new_hire@example.com", "role": "recruiter" }`
- **Response**: `{ "id": "...", "token_hash": "..." }` (Triggers Celery email task)

### `POST /invites/accept`
Accept an invite using the token sent via email.
- **Request Body**: `{ "token": "...", "password": "...", "name": "..." }`

---

## 4. Jobs & Pipeline

### `GET /jobs`
List all jobs within the current organization. (Publicly accessible if filtered to published jobs, otherwise requires Staff Token).

### `POST /jobs`
Create a new job posting.
- **Auth**: `hr_manager` or `recruiter`.
- **Request Body**: `{ "title": "Software Engineer", "department_id": "...", "description": "...", "requirements": [...] }`

### `GET /jobs/{id}/pipeline-stages`
Get the Kanban pipeline stages for a specific job.

### `PATCH /jobs/{id}/pipeline-stages/reorder`
Reorder pipeline stages (drag-and-drop).
- **Request Body**: `[{ "id": "stage_id_1", "order_index": 0 }, { "id": "stage_id_2", "order_index": 1 }]`

---

## 5. Candidates & Applications

### `POST /candidates/resume`
Upload a candidate's resume PDF.
- **Auth**: Staff Token or Candidate Token.
- **Form Data**: `file` (PDF)
- **Response**: `{ "id": "...", "file_url": "...", "parse_status": "pending" }` (Triggers Docling extraction Celery task).

### `GET /candidates/{id}`
Retrieve candidate details and structured parsed resume data (`resume_parsed_data`).

### `POST /applications`
Apply to a job.
- **Request Body**: `{ "candidate_id": "...", "job_id": "..." }`

### `PATCH /applications/{id}/stage`
Move a candidate to a new pipeline stage.
- **Auth**: `hr_manager` or `recruiter`.
- **Request Body**: `{ "stage_id": "..." }`
- **Side Effect**: Logs a row in `application_stage_history` (used for analytics) and triggers a notification.

---

## 6. AI & Semantic Search

### `POST /copilot/query`
Natural language candidate search.
- **Auth**: `hr_manager` or `recruiter`.
- **Request Body**: `{ "query": "Find React devs with 5+ years experience" }`
- **Response**:
  ```json
  {
    "interpreted_as": {
      "skills": ["React"],
      "min_experience_years": 5,
      "keywords": []
    },
    "results": [ ...candidate_profiles ]
  }
  ```

### `POST /jobs/{id}/match`
Trigger an async background task to match all candidates against this job description using hybrid semantic search and cross-encoder reranking.

### `GET /applications/{id}/match-result`
Retrieve the AI evaluation for a specific application.
- **Response**: 
  ```json
  {
    "match_pct": 88.5,
    "missing_skills": ["Docker"],
    "strengths": ["Strong frontend architecture experience"],
    "recommendation": "Advance to technical screen."
  }
  ```

---

## 7. Interviews & AI Feedback

### `POST /interviews`
Schedule an interview.
- **Auth**: `hr_manager` or `recruiter`.
- **Request Body**: `{ "application_id": "...", "interviewer_id": "...", "scheduled_at": "..." }`

### `GET /interviews`
List interviews. 
- **RBAC Note**: If the user is an `interviewer`, this endpoint forcefully filters the results so they only see interviews assigned to them.

### `POST /interviews/{id}/feedback`
Submit raw interview notes and generate structured AI feedback.
- **Request Body**: `{ "raw_notes": "Candidate did great on the system design..." }`
- **Response**: Generates `{ "ai_summary": "...", "overall_score": 8.5, "ai_strengths": [...] }`

---

## 8. Analytics (HR Managers)

### `GET /analytics/funnel`
Get candidate drop-off metrics per pipeline stage for a specific job.

### `GET /analytics/time-to-hire`
Calculates the average time from `applied_at` to the `hired` pipeline stage.

### `GET /analytics/recruiter-performance`
Counts application stage moves and hires per recruiter in the organization.

---

## Error Handling

All API errors return a standard JSON envelope:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'email' must be a valid email address.",
    "request_id": "req-12345"
  }
}
```
