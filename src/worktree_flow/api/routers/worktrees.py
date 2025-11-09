"""Worktree management endpoints."""

from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query

from ...models import WorktreeInfo, WorktreeList, WorktreeType
from ..deps import get_repo_path

router = APIRouter()


@router.post("/create/issue", response_model=WorktreeInfo)
async def create_from_issue(
    issue_id: str = Query(..., description="Issue ID or number"),
    provider: str = Query(default="github", description="Provider name"),
    repo_path: Path = Depends(get_repo_path),
):
    """Create worktree from issue.

    **Example:**
    ```
    POST /worktrees/create/issue?issue_id=7&provider=github
    ```

    **Response:**
    - Returns WorktreeInfo with path, branch, and metadata
    """
    # TODO: Implement with WorktreeManager
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - coming soon!",
    )


@router.post("/create/epic", response_model=WorktreeInfo)
async def create_epic(
    issue_id: str = Query(..., description="Epic issue ID"),
    repo_path: Path = Depends(get_repo_path),
):
    """Create epic-level worktree.

    **Example:**
    ```
    POST /worktrees/create/epic?issue_id=7
    ```
    """
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - coming soon!",
    )


@router.post("/create/feature", response_model=WorktreeInfo)
async def create_feature(
    issue_id: str = Query(..., description="Feature issue ID"),
    parent_worktree: str = Query(..., description="Parent worktree name"),
    repo_path: Path = Depends(get_repo_path),
):
    """Create feature worktree under epic.

    **Example:**
    ```
    POST /worktrees/create/feature?issue_id=7.1&parent_worktree=epic-7
    ```
    """
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - coming soon!",
    )


@router.get("/list", response_model=WorktreeList)
async def list_worktrees(
    worktree_type: Optional[WorktreeType] = Query(
        None, description="Filter by worktree type"
    ),
    repo_path: Path = Depends(get_repo_path),
):
    """List all worktrees.

    **Example:**
    ```
    GET /worktrees/list?type=epic
    ```
    """
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - coming soon!",
    )


@router.get("/{worktree_name}", response_model=WorktreeInfo)
async def get_worktree(
    worktree_name: str,
    repo_path: Path = Depends(get_repo_path),
):
    """Get worktree details.

    **Example:**
    ```
    GET /worktrees/issue-7
    ```
    """
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - coming soon!",
    )


@router.delete("/{worktree_name}")
async def remove_worktree(
    worktree_name: str,
    force: bool = Query(default=False, description="Force removal"),
    repo_path: Path = Depends(get_repo_path),
):
    """Remove worktree.

    **Example:**
    ```
    DELETE /worktrees/issue-7?force=false
    ```
    """
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - coming soon!",
    )


@router.post("/{worktree_name}/merge")
async def merge_to_parent(
    worktree_name: str,
    repo_path: Path = Depends(get_repo_path),
):
    """Merge worktree to parent.

    **Example:**
    ```
    POST /worktrees/issue-7/merge
    ```
    """
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - coming soon!",
    )


@router.post("/{worktree_name}/sync")
async def sync_with_parent(
    worktree_name: str,
    repo_path: Path = Depends(get_repo_path),
):
    """Sync worktree with parent branch.

    **Example:**
    ```
    POST /worktrees/issue-7/sync
    ```
    """
    raise HTTPException(
        status_code=501,
        detail="Not implemented yet - coming soon!",
    )
