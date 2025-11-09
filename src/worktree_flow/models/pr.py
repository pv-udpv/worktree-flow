"""Pull Request models."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class PullRequest(BaseModel):
    """Universal Pull Request model."""

    id: str = Field(..., description="PR ID")
    number: int = Field(..., description="PR number")
    title: str = Field(..., description="PR title")
    body: Optional[str] = Field(None, description="PR description")
    state: str = Field(..., description="PR state (open, merged, closed)")
    source_branch: str = Field(..., description="Source branch")
    target_branch: str = Field(..., description="Target branch")
    url: str = Field(..., description="PR URL")
    author: str = Field(..., description="PR author")
    reviewers: list[str] = Field(default_factory=list, description="Reviewers")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider-specific data")


class PRCreate(BaseModel):
    """Pull Request creation request."""

    title: str = Field(..., description="PR title")
    body: str = Field(..., description="PR description")
    source_branch: str = Field(..., description="Source branch")
    target_branch: str = Field(..., description="Target branch")
    draft: bool = Field(default=False, description="Create as draft PR")
