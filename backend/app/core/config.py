"""
Configuration management for IntelliPDF application.

This module provides centralized configuration management using Pydantic Settings,
supporting environment variables, .env files, and multi-environment deployments.
"""

from functools import lru_cache
from typing import Literal, Optional
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.

    All settings support environment variable overrides and .env file loading.
    Configuration is validated at startup to prevent runtime errors.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== Application Settings ====================
    app_name: str = Field(
        default="IntelliPDF",
        description="Application name"
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode flag"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    # ==================== API Settings ====================
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 route prefix"
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    api_port: int = Field(
        default=8000,
        ge=1000,
        le=65535,
        description="API server port"
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )

    # ==================== Database Settings ====================
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/intellipdf",
        description="PostgreSQL async connection string"
    )
    database_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy SQL query logging"
    )
    database_pool_size: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Maximum overflow connections"
    )

    # ==================== Redis Settings ====================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_cache_ttl: int = Field(
        default=3600,
        ge=60,
        description="Redis cache TTL in seconds"
    )

    # ==================== Gemini AI Settings ====================
    gemini_api_key: str = Field(
        default="",
        description="Gemini API key"
    )
    gemini_base_url: str = Field(
        default="http://localhost:8132",
        description="Gemini API base URL"
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini model name"
    )
    gemini_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for response generation"
    )
    gemini_max_tokens: int = Field(
        default=2048,
        ge=256,
        le=32000,
        description="Maximum tokens for completion"
    )

    # ==================== OpenAI Settings ====================
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model name"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-large",
        description="OpenAI embedding model"
    )
    openai_max_tokens: int = Field(
        default=4096,
        ge=256,
        le=128000,
        description="Maximum tokens for completion"
    )
    openai_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for response generation"
    )
    openai_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="OpenAI API request timeout in seconds"
    )

    # ==================== Vector Database Settings ====================
    chroma_db_path: str = Field(
        default="./data/chroma_db",
        description="ChromaDB persistent storage path"
    )
    chroma_collection_name: str = Field(
        default="intellipdf_documents",
        description="ChromaDB collection name"
    )
    embedding_dimension: int = Field(
        default=3072,
        description="Vector embedding dimension (text-embedding-3-large)"
    )
    max_retrieval_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of retrieval results"
    )

    # ==================== File Storage Settings ====================
    upload_dir: str = Field(
        default="./data/uploads",
        description="File upload storage directory"
    )
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        ge=1024 * 1024,  # Minimum 1MB
        le=500 * 1024 * 1024,  # Maximum 500MB
        description="Maximum file upload size in bytes"
    )
    allowed_extensions: list[str] = Field(
        default=[".pdf"],
        description="Allowed file extensions"
    )

    # ==================== PDF Processing Settings ====================
    pdf_processing_timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="PDF processing timeout in seconds"
    )
    pdf_max_pages: int = Field(
        default=500,
        ge=1,
        le=10000,
        description="Maximum number of pages to process"
    )
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Target chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Chunk overlap size in characters"
    )

    # ==================== Security Settings ====================
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        min_length=32,
        description="Secret key for encryption and signing"
    )
    access_token_expire_minutes: int = Field(
        default=60 * 24 * 7,  # 7 days
        ge=15,
        description="Access token expiration time in minutes"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )

    # ==================== Performance Settings ====================
    worker_count: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of worker processes"
    )
    max_concurrent_requests: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Maximum concurrent API requests"
    )
    request_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="API request timeout in seconds"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",  # Prevent extra fields
        validate_default=True
    )

    @validator("upload_dir", "chroma_db_path", pre=True)
    def create_directories(cls, v: str) -> str:
        """Ensure required directories exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return v

    @validator("openai_api_key")
    def validate_openai_key(cls, v: str, values: dict) -> str:
        """Validate OpenAI API key in production."""
        if values.get("environment") == "production" and not v:
            raise ValueError("OpenAI API key is required in production")
        return v

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings instance.

    Uses LRU cache to ensure single settings instance across application.
    Settings are loaded once and reused for all requests.

    Returns:
        Settings: Validated application settings
    """
    return Settings()


# Export settings instance for convenience
settings = get_settings()
