"""Pydantic model tests."""

from datetime import datetime
import pytest

from worktree_flow.models import (
    WorktreeType,
    WorktreeMetadata,
    Issue,
    PullRequest,
)


def test_worktree_type_enum():
    """Test WorktreeType enum."""
    assert WorktreeType.EPIC == "epic"
    assert WorktreeType.FEATURE == "feature"
    assert WorktreeType.ISSUE == "issue"


def test_worktree_metadata():
    """Test WorktreeMetadata model."""
    metadata = WorktreeMetadata(
        worktree="issue-7",
        worktree_type=WorktreeType.ISSUE,
        branch="issue/7/test",
        base_branch="main",
        created_at=datetime.now(),
    )
    assert metadata.worktree == "issue-7"
    assert metadata.worktree_type == WorktreeType.ISSUE
    assert metadata.status == "active"


def test_issue_model():
    """Test Issue model."""
    issue = Issue(
        id="7",
        number=7,
        title="Test Issue",
        state="open",
        url="https://github.com/owner/repo/issues/7",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert issue.number == 7
    assert issue.title == "Test Issue"
    assert issue.labels == []


def test_pr_model():
    """Test PullRequest model."""
    pr = PullRequest(
        id="15",
        number=15,
        title="Test PR",
        state="open",
        source_branch="feature/test",
        target_branch="main",
        url="https://github.com/owner/repo/pull/15",
        author="user",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert pr.number == 15
    assert pr.source_branch == "feature/test"
