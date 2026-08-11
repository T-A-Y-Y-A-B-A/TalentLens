from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import DomainException, domain_exception_handler, global_exception_handler
from app.core.logging import setup_logging, configure_logging_middleware
from app.api.v1 import health, auth
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from app.core.rate_limit import limiter
from app.api.v1.departments import router as departments_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.applications import router as applications_router
from app.api.v1.matching import router as matching_router

# Setup logging before app creation
setup_logging()

from contextlib import asynccontextmanager
from app.core.qdrant import init_qdrant

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Qdrant collections on startup
    await init_qdrant()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

from starlette.middleware.sessions import SessionMiddleware

# Secure headers / CORS
# Referrer-Policy, Strict-Transport-Security, etc., typically handled by Traefik/Nginx in production
# but CORS must be configured here.
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL], # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Logging middleware (adds request ID)
configure_logging_middleware(app)

# Routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix=settings.API_V1_STR)
from app.api.v1 import organizations
from app.api.v1.candidate_auth import router as candidate_auth_router
from app.api.v1.invites import router as invites_router
from app.api.v1.notifications import router as notifications_router

app.include_router(organizations.router, prefix=settings.API_V1_STR)
app.include_router(departments_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(candidates_router, prefix=settings.API_V1_STR)
app.include_router(applications_router, prefix=settings.API_V1_STR)
app.include_router(matching_router, prefix=settings.API_V1_STR)
app.include_router(candidate_auth_router, prefix=settings.API_V1_STR)
app.include_router(invites_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)

from app.api.v1.copilot import router as copilot_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.interviews import router as interviews_router

app.include_router(copilot_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(interviews_router, prefix=settings.API_V1_STR)

from app.api.v1.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to TalentLens API"}
