"""Dependency injection for FastAPI."""

from typing import Annotated
from pathlib import Path

from fastapi import Depends, Query

from ..config import settings


def get_repo_path(
    repo_path: Annotated[
        Path | None,
        Query(description="Repository path"),
    ] = None,
) -> Path:
    """Get repository path from query param or settings."""
    if repo_path:
        return Path(repo_path)
    if settings.default_repo:
        return Path(settings.default_repo)
    return Path.cwd()
