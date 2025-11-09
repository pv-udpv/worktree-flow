"""Worktree models."""

from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class WorktreeType(str, Enum):
    """Worktree type enumeration."""

    EPIC = "epic"
    FEATURE = "feature"
    SUBISSUE = "subissue"
    ISSUE = "issue"
    CUSTOM = "custom"


class WorktreeMetadata(BaseModel):
    """Worktree metadata stored in .task-metadata.json."""

    worktree: str = Field(..., description="Worktree directory name")
    worktree_type: WorktreeType = Field(..., description="Worktree type")
    branch: str = Field(..., description="Git branch name")
    base_branch: str = Field(..., description="Base branch")

    parent_worktree: Optional[str] = Field(None, description="Parent worktree name")
    parent_branch: Optional[str] = Field(None, description="Parent branch")

    issue_number: Optional[int] = Field(None, description="Linked issue number")
    issue_provider: Optional[str] = Field(None, description="Issue provider (github, linear)")
    title: Optional[str] = Field(None, description="Task title")

    pr_number: Optional[int] = Field(None, description="Pull request number")
    status: str = Field(default="active", description="Status: active, pr_created, merged")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    commits: list[dict] = Field(default_factory=list, description="Commit history")
    sub_worktrees: list[dict] = Field(default_factory=list, description="Child worktrees")
    bindings: dict = Field(default_factory=dict, description="External context bindings")


class WorktreeInfo(BaseModel):
    """Worktree information response."""

    path: Path = Field(..., description="Absolute worktree path")
    name: str = Field(..., description="Worktree name")
    branch: str = Field(..., description="Branch name")
    base_branch: str = Field(..., description="Base branch")
    worktree_type: WorktreeType = Field(..., description="Worktree type")
    metadata: Optional[WorktreeMetadata] = Field(None, description="Full metadata")


class WorktreeCreate(BaseModel):
    """Worktree creation request."""

    issue_id: Optional[str] = Field(None, description="Issue ID or number")
    provider: str = Field(default="github", description="Provider name")
    worktree_type: WorktreeType = Field(default=WorktreeType.ISSUE, description="Type")
    parent_worktree: Optional[str] = Field(None, description="Parent worktree")
    repo_path: Optional[Path] = Field(None, description="Repository path")


class WorktreeList(BaseModel):
    """List of worktrees."""

    worktrees: list[WorktreeInfo] = Field(..., description="Worktree list")
    total: int = Field(..., description="Total count")
