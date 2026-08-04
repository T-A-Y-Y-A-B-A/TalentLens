import logging
import sys
# pyrefly: ignore [missing-import]
import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI
from asgi_correlation_id import correlation_id

def setup_logging():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def configure_logging_middleware(app: FastAPI):
    app.add_middleware(CorrelationIdMiddleware)

    @app.middleware("http")
    async def structlog_middleware(request, call_next):
        req_id = correlation_id.get() or "unknown"
        request.state.request_id = req_id
        structlog.contextvars.bind_contextvars(
            request_id=req_id,
            path=request.url.path,
            method=request.method,
        )
        response = await call_next(request)
        return response
