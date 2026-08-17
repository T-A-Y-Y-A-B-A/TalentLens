# TalentLens: Deployment & Scaling Guide

This document outlines the deployment process for TalentLens across local and production environments, along with a comprehensive architecture strategy for scaling the platform to enterprise-grade workloads.

---

## 1. Deployment Guide

TalentLens is built entirely on containerized, open-source technologies, ensuring parity between local development and production environments.

### Local Development (Docker Compose)
The repository includes a `docker-compose.yml` that orchestrates the entire stack.

**Prerequisites:**
- Docker and Docker Compose installed.
- Node.js 18+ (for local Next.js development).

**Steps:**
1. Clone the repository:
   ```bash
   git clone https://github.com/T-A-Y-Y-A-B-A/TalentLens.git
   cd TalentLens
   ```
2. Start the Backend Infrastructure:
   ```bash
   docker-compose up -d
   ```
   *This single command spins up PostgreSQL, Redis, Qdrant, MinIO, the FastAPI backend (on port 8000), and the Celery worker.*
3. Start the Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *The frontend is now available at `http://localhost:3000`.*

### Production Deployment (PaaS/Cloud)

TalentLens is currently deployed and live at the following public URLs:
*   **Live Frontend (Vercel):** [https://talent-lens-bice.vercel.app](https://talent-lens-bice.vercel.app)
*   **Live Backend API (Railway):** [https://talentlens-backend-production.up.railway.app/docs](https://talentlens-backend-production.up.railway.app/docs)

**Backend (Railway):**
1. **Provision Managed Services:** Spin up **PostgreSQL** and **Redis** directly from the Railway dashboard.
2. **Custom Services:** Deploy **Qdrant** (Vector DB) and **MinIO** (Object Storage) using Docker images. Ensure MinIO has persistent volume mounts.
3. **Deploy the Code:** Link your GitHub repo to Railway and deploy two separate services (the **FastAPI Backend** and the **Celery Worker**), ensuring you set the `Root Directory` to `/backend` for both.
4. **Environment Variables:** In your FastAPI service, map the database credentials exactly. Crucially, explicitly map `POSTGRES_HOST` and `POSTGRES_PORT` (e.g. `postgres.railway.internal:5432`) rather than just relying on a generic database URL.
5. **Generate Public Domain:** Go to the FastAPI service settings and click "Generate Domain" to expose it to the internet. (e.g., `talentlens-backend-production.up.railway.app`).

**Frontend (Vercel):**
1. Import the GitHub repository into Vercel.
2. Set the Root Directory to `/frontend` in the project settings.
3. Add the **`BACKEND_URL`** environment variable and set it to your generated Railway domain: `https://talentlens-backend-production.up.railway.app`.
4. Vercel's `next.config.ts` will automatically configure API rewrites (proxying `/api/v1/*` to the backend) to avoid CORS issues and obscure the direct backend URL from the client. **Note:** Ensure you Redeploy Vercel after adding the `BACKEND_URL` variable so it is baked into the build!

---

## 2. Scaling Strategy

The assignment requires the system to reliably support **10,000 companies, 1 million candidates, and 500 recruiters simultaneously.**

TalentLens was purposefully designed with a decoupled, stateless, and asynchronous architecture to support this exact scale.

### A. Supporting 10,000 Companies (Multi-Tenancy)
*   **Database Isolation at the ORM Level:** We do not rely on developers remembering to filter queries by company. Instead, our SQLAlchemy `BaseRepository` utilizes a `TenantMixin`. Every single query automatically injects a `WHERE org_id = current_org_id` clause. This structural isolation means database performance and security remain rock-solid regardless of how many companies onboard.
*   **Database Sharding:** As the `jobs` and `applications` tables grow across 10,000 companies, PostgreSQL can be logically partitioned by `org_id`. Because all queries filter by `org_id`, Postgres will only scan the partition belonging to the active company, keeping query times incredibly fast.

### B. Supporting 1,000,000 Candidates (AI & Vector Search)
Searching through 1 million resumes using AI embeddings is computationally expensive. We solve this via **Hybrid Search with Strict Metadata Filtering**:
*   **Qdrant Metadata Filtering:** When a candidate applies, their embedding is stored in Qdrant along with an `org_id` payload. When a recruiter runs an AI Match or Copilot search, the query is pre-filtered by the recruiter's `org_id`. 
*   **Why this scales:** Instead of running a vector similarity search across 1,000,000 candidates, Qdrant filters the search space down to the ~500 candidates that belong to that specific company *before* calculating cosine similarity. This turns an $O(N)$ vector search into a near-instant lookup.
*   **MinIO Object Storage:** Storing 1 million PDF resumes in a database would destroy performance. Instead, PDFs are pushed directly to MinIO (S3 compatible), and the database only stores the lightweight `file_url`.

### C. Supporting 500 Simultaneous Recruiters (High Concurrency)
If 500 recruiters upload resumes or trigger AI matching at the exact same second, a synchronous API would crash.
*   **Event-Driven Background Processing:** FastAPI does not process resumes. When a recruiter uploads a resume, FastAPI instantly saves a `ParseStatus = pending` record to Postgres, drops a message into **Redis**, and returns a 200 OK to the recruiter in under 50ms.
*   **Celery Horizontal Scaling:** The heavy lifting (Docling PDF extraction, LiteLLM API calls, embedding generation) is picked up by **Celery workers**. If 500 recruiters trigger jobs, we can horizontally auto-scale the Celery worker pods in Kubernetes. 
*   **Stateless API:** The FastAPI web nodes are completely stateless. JWTs manage sessions, meaning we can put an Nginx/Traefik Load Balancer in front of FastAPI and spin up dozens of API replicas to handle the web traffic seamlessly.

---

## 3. Summary of Bottlenecks and Mitigations

| Component | Bottleneck Risk at Scale | Mitigation Strategy |
| :--- | :--- | :--- |
| **Relational Data** | Postgres tables grow too large. | Partitioning by `org_id`. Read-replicas for analytical dashboard queries. |
| **AI Matching** | Vector search across 1M candidates. | Qdrant payload pre-filtering by `org_id`. Cross-encoder reranking only applied to the top 50 results. |
| **Document Parsing** | OCR / Docling maxes out CPU. | Decoupled Celery workers. Can be shifted to dedicated GPU instances independently of the web API. |
| **API Throughput** | 500 concurrent connections. | `asyncpg` and FastAPI asynchronous event loops. Horizontal scaling of stateless API pods. |
