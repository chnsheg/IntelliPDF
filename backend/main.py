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
