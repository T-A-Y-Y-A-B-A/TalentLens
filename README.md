# TalentLens 🎯

**An AI-Powered Applicant Tracking System (ATS) and Recruitment Platform**

TalentLens is a modern, multi-tenant ATS designed to streamline the hiring process using state-of-the-art AI. Instead of relying on generic LLM wrappers, TalentLens utilizes a robust pipeline of semantic search, hybrid vector matching, cross-encoder reranking, and deterministic extraction to evaluate candidates fairly, transparently, and securely.

---

## 🌟 Live Demo

- **Frontend Application:** [https://talent-lens-bice.vercel.app](https://talent-lens-bice.vercel.app)
- **Backend API Docs (Swagger):** [https://talentlens-backend-production.up.railway.app/docs](https://talentlens-backend-production.up.railway.app/docs)

### Demo Accounts
The system is pre-seeded with isolated demo organizations. You can log in using the following credentials:

**HR Manager Accounts (Full Access within their Org)**
- **Email:** `hr@digitalsofts.demo` | **Password:** `password123`
- **Email:** `hr@abc-software.demo` | **Password:** `password123`
- **Email:** `hr@xyz-bank.demo` | **Password:** `password123`

**Super Admin (Cross-Org Analytics & Audit Logs)**


*Candidates can register their own accounts via the open Candidate Portal.*

---

## 🚀 Key Features

### 🧠 Advanced AI Pipelines
- **Resume Parsing:** Uploaded PDFs are parsed via Docling/OCR, structured using an LLM via Instructor, and chunked & embedded using `BGE-small` models into Qdrant.
- **Precision Matching:** Job descriptions are semantically matched against candidate profiles using a Hybrid Search (Dense Vectors + Sparse BM25), reranked via a cross-encoder (`ms-marco-MiniLM-L-6-v2`), and finally evaluated by an LLM to generate explainable match percentages, missing skills, and strengths.
- **AI Recruiter Copilot:** Natural language search for candidates (e.g., *"Find Python developers with AWS certs"*). The query is deterministically mapped to structured JSON filters before hitting the database, preventing prompt injection and SQL injection risks.
- **AI Interview Feedback:** Interviewers submit raw notes, and the AI generates structured, objective feedback summaries and scoring.

### 🏢 Enterprise-Grade Architecture
- **Multi-Tenancy:** Strict, database-level organization isolation using SQLAlchemy `BaseRepository` scoped queries.
- **Role-Based Access Control (RBAC):** Built-in permission matrix (Super Admin, HR Manager, Recruiter, Interviewer) enforced by Casbin.
- **Asynchronous Processing:** Celery and Redis manage heavy background tasks (email sending, resume parsing, AI matching) without blocking the API.
- **Dual-Portal System:** Fully isolated authentication scopes for Staff (JWT `user`) and Candidates (JWT `candidate_id`), ensuring a candidate token can never access staff endpoints.

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL 15 + AsyncPG + Alembic (Migrations)
- **Vector Store:** Qdrant (Hybrid Search)
- **Message Broker & Cache:** Redis
- **Background Workers:** Celery
- **Object Storage:** MinIO (S3 compatible)
- **AI Tooling:** LiteLLM, Instructor (Structured Outputs), Sentence-Transformers

### Frontend
- **Framework:** Next.js 15 (App Router) + TypeScript
- **Styling:** Tailwind CSS + Radix UI + Lucide Icons
- **State & Data Fetching:** React Hooks + OpenAPI Typed Client
- **Charts:** Recharts (Analytics Dashboard)
- **Interactions:** `@dnd-kit` for drag-and-drop Kanban pipeline boards

---

## 🏗️ Local Development Setup

The entire stack is containerized and can be spun up with a single command.

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)

### 1. Start the Backend Infrastructure
Navigate to the root directory and run:
```bash
docker compose up -d
```
This spins up:
- PostgreSQL (`localhost:5433`)
- Redis (`localhost:6379`)
- Qdrant (`localhost:6333`)
- MinIO (`localhost:9000`)
- Backend API (`localhost:8000`)
- Celery Worker

*The backend will automatically run Alembic migrations and seed the database with demo organizations and users on startup.*

### 2. Start the Frontend
In a new terminal, navigate to the frontend directory:
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:3000`.

---

## 🔒 Security Posture

TalentLens was built with a "Secure by Design" philosophy:
1. **No Raw LLM SQL Generation:** AI Copilot maps to predefined Pydantic schemas which drive SQLAlchemy filters.
2. **Strict Multi-Tenancy:** The `current_org_id` is injected into every repository call at the dependency level. Cross-tenant data leakage is structurally prevented.
3. **Audit Logging:** Critical actions (stage moves, role changes) generate immutable audit trails viewable by Super Admins.
4. **AI Observability:** Every LLM call logs tokens, cost, latency, and prompt versions to the `ai_usage_logs` table.

---

## 📂 Repository Structure

```
├── backend/               # FastAPI Application
│   ├── app/
│   │   ├── api/v1/        # Route handlers
│   │   ├── core/          # Config, Security, Casbin RBAC, Qdrant
│   │   ├── models/        # SQLAlchemy Models
│   │   ├── schemas/       # Pydantic validation schemas
│   │   ├── services/      # Business logic
│   │   └── workers/       # Celery Tasks (Parsing, Matching, Emails)
│   ├── tests/             # Pytest suite
│   └── alembic/           # Database migrations
├── frontend/              # Next.js Application
│   ├── src/app/           # App Router Pages
│   └── src/components/    # Shared UI Components
├── docker-compose.yml     # Local Infrastructure
└── PLANNING.md            # Original architecture and spec documents
```

---

*Built for the future of recruiting.* 🚀
