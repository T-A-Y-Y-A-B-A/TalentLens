from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import DomainException, domain_exception_handler, global_exception_handler
from app.core.logging import setup_logging, configure_logging_middleware
from app.api.v1 import health, auth
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.rate_limit import limiter
from app.api.v1.departments import router as departments_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.applications import router as applications_router

# Setup logging before app creation
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
app.state.limiter = limiter

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
app.include_router(organizations.router, prefix=settings.API_V1_STR)
app.include_router(departments_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(candidates_router, prefix=settings.API_V1_STR)
app.include_router(applications_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to TalentLens API"}
