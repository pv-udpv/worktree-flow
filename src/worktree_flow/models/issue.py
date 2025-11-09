"""Issue models."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class Issue(BaseModel):
    """Universal issue model."""

    id: str = Field(..., description="Issue ID")
    number: int = Field(..., description="Issue number")
    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(None, description="Issue description")
    state: str = Field(..., description="Issue state (open, closed)")
    labels: list[str] = Field(default_factory=list, description="Labels")
    assignees: list[str] = Field(default_factory=list, description="Assignees")
    url: str = Field(..., description="Issue URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider-specific data")


class IssueCreate(BaseModel):
    """Issue creation request."""

    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(None, description="Issue description")
    labels: Optional[list[str]] = Field(None, description="Labels to apply")
    assignees: Optional[list[str]] = Field(None, description="Users to assign")
