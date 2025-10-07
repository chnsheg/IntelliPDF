"""
Structured logging configuration for IntelliPDF application.

This module provides centralized logging configuration with structured logging,
log rotation, and environment-specific settings.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from .config import Settings, get_settings


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages and redirect to loguru.

    This handler allows integration with third-party libraries that use
    standard Python logging while maintaining structured loguru output.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process a logging record and send it to loguru.

        Args:
            record: Standard logging record
        """
        # Get corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the log originated
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(settings: Settings) -> None:
    """
    Configure application logging system.

    Sets up loguru with appropriate handlers, formatters, and rotation
    based on environment settings.

    Args:
        settings: Application settings
    """
    # Remove default loguru handler
    logger.remove()

    # Console logging format
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # File logging format (JSON for production)
    if settings.is_production:
        file_format = (
            "{{"
            '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"logger": "{name}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}"'
            "}}"
        )
    else:
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )

    # Add console handler
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.log_level,
        colorize=True,
        backtrace=settings.debug,
        diagnose=settings.debug,
    )

    # Add file handler with rotation
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "intellipdf_{time:YYYY-MM-DD}.log",
        format=file_format,
        level=settings.log_level,
        rotation="00:00",  # Rotate at midnight
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress rotated logs
        backtrace=True,
        diagnose=settings.debug,
        enqueue=True,  # Thread-safe logging
    )

    # Add error-specific log file
    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="ERROR",
        rotation="00:00",
        retention="90 days",  # Keep error logs longer
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set levels for third-party loggers
    for logger_name in ["uvicorn", "uvicorn.access", "sqlalchemy", "httpx"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
        logging.getLogger(logger_name).propagate = False

    logger.info(f"Logging configured for {settings.environment} environment")


def get_logger(name: str) -> Any:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logger.bind(module=name)


# Initialize logging on module import
settings = get_settings()
setup_logging(settings)
