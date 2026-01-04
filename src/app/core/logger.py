"""Centralized logging configuration using Loguru."""

import os
import sys

from loguru import logger

# Remove default handler
logger.remove()

# Check environment directly from .env
is_production = os.getenv("ENVIRONMENT", "development") == "production"

# Configure based on environment
if is_production:
    logger.add(
        sys.stdout,
        level="INFO",
        format="{level: <8} | {name}:{function}:{line} - {message}",
        colorize=False,
    )
else:
    logger.add(
        sys.stdout,
        level="DEBUG",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

__all__ = ["logger"]
