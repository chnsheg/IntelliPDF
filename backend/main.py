"""
IntelliPDF Backend Main Application.

This module initializes the FastAPI application with all middleware,
routers, and lifecycle event handlers.
"""

from app.api.v1.endpoints import health
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.requests import Request

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.database.session import close_engine
from app.infrastructure.ai.gemini_client import close_gemini_client

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info(f"Starting IntelliPDF Backend v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Gemini API: {settings.gemini_base_url}")
    logger.info(f"Gemini Model: {settings.gemini_model}")

    # Create necessary directories
    from pathlib import Path
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_db_path).mkdir(parents=True, exist_ok=True)
    Path("./data").mkdir(exist_ok=True)
    Path("./logs").mkdir(exist_ok=True)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_engine()
    await close_gemini_client()
    logger.info("Application shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Next-generation intelligent PDF knowledge management platform",
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan
)


# Temporary middleware: log raw request body for POST /.../chat to capture 422-causing payloads
@app.middleware("http")
async def log_chat_request_body(request: Request, call_next):
    try:
        path = str(request.url.path)
        if request.method == "POST" and path.startswith(settings.api_v1_prefix + "/documents/") and path.endswith("/chat"):
            # Read raw body
            body_bytes = await request.body()
            try:
                body_text = body_bytes.decode("utf-8")
            except Exception:
                body_text = str(body_bytes)
            # Raw body is noisy; keep as DEBUG so we can enable when needed
            logger.debug(f"CHAT_RAW_BODY path={path}; body={body_text}")

            # Try to parse and normalize common frontend aliases to expected backend schema
            normalized_body_text = body_text
            try:
                import json

                parsed = json.loads(body_text) if body_text else {}
                changed = False

                # Map common aliases to 'question'
                if isinstance(parsed, dict):
                    if 'message' in parsed and 'question' not in parsed:
                        parsed['question'] = parsed.pop('message')
                        changed = True
                    if 'prompt' in parsed and 'question' not in parsed:
                        parsed['question'] = parsed.pop('prompt')
                        changed = True

                    # CamelCase -> snake_case for conversation history
                    if 'conversationHistory' in parsed and 'conversation_history' not in parsed:
                        parsed['conversation_history'] = parsed.pop(
                            'conversationHistory')
                        changed = True

                    # Ensure top_k and temperature are present as primitives
                    if 'topK' in parsed and 'top_k' not in parsed:
                        parsed['top_k'] = parsed.pop('topK')
                        changed = True

                if changed:
                    normalized_body_text = json.dumps(
                        parsed, ensure_ascii=False)
                    # Normalization is useful informational context
                    logger.info(
                        f"CHAT_NORMALIZED_BODY path={path}; normalized_body={normalized_body_text}")
                    body_bytes = normalized_body_text.encode('utf-8')

                # Ensure 'question' respects backend max_length (2000)
                try:
                    if isinstance(parsed, dict) and 'question' in parsed and isinstance(parsed['question'], str):
                        qlen = len(parsed['question'])
                        if qlen > 2000:
                            orig = parsed['question']
                            parsed['question'] = parsed['question'][:2000]
                            normalized_body_text = json.dumps(
                                parsed, ensure_ascii=False)
                            body_bytes = normalized_body_text.encode('utf-8')
                            logger.warning(
                                f"CHAT_TRUNCATED_BODY path={path}; original_length={qlen}; truncated_to=2000")
                except Exception as e:
                    logger.exception(
                        f"Failed to enforce question length limit: {e}")

            except Exception as e:
                logger.exception(f"Failed to normalize chat request body: {e}")

            # rebuild request for downstream handlers
            # Make the modified body available on the original Request instance
            # so that any later code (including our validation exception handler)
            # reads the normalized/truncated payload. We do this defensively
            # because Request.body() caches into request._body.
            try:
                setattr(request, "_body", body_bytes)
            except Exception:
                # Not critical - downstream will still receive the rebuilt request
                logger.debug(
                    "Could not set request._body; proceeding with rebuilt request")

            async def receive():
                return {"type": "http.request", "body": body_bytes, "more_body": False}
            new_request = Request(request.scope, receive)
            return await call_next(new_request)
    except Exception as e:
        logger.exception(f"Failed to log chat request body: {e}")
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Log raw request body on validation errors (422) to help frontend debugging.
    Delegates to FastAPI's default handler for response formatting.
    """
    try:
        body_bytes = await request.body()
        # Try decode safely
        try:
            body_text = body_bytes.decode('utf-8')
        except Exception:
            body_text = str(body_bytes)
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(
            f"RequestValidationError for path={request.url.path}; raw_body={body_text}; errors={exc.errors()}")
    except Exception as log_exc:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to log raw body for validation error: {log_exc}")

    # Delegate to default handler to preserve response format
    return await request_validation_exception_handler(request, exc)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include health check at root level (not under /api/v1)
app.include_router(health.router, tags=["health"])

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to IntelliPDF API",
        "version": settings.app_version,
        "docs": "/api/docs" if not settings.is_production else None,
        "health": f"{settings.api_v1_prefix}/health",
        "test_gemini": f"{settings.api_v1_prefix}/test/gemini"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
