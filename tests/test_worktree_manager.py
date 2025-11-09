"""Tests for WorktreeManager."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import git

from worktree_flow.core import WorktreeManager
from worktree_flow.models import (
    WorktreeType,
    WorktreeCreate,
    WorktreeMetadata,
)


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test-repo"
        repo_path.mkdir()

        # Initialize git repo
        repo = git.Repo.init(repo_path)

        # Create initial commit
        test_file = repo_path / "README.md"
        test_file.write_text("# Test Repository\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        yield repo_path


@pytest.fixture
def worktree_manager(temp_git_repo):
    """Create WorktreeManager instance for testing."""
    return WorktreeManager(temp_git_repo)


def test_worktree_manager_init(temp_git_repo):
    """Test WorktreeManager initialization."""
    manager = WorktreeManager(temp_git_repo)
    assert manager.repo_path == temp_git_repo.resolve()
    assert manager.repo is not None


def test_worktree_manager_init_invalid_repo():
    """Test WorktreeManager initialization with invalid repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_path = Path(tmpdir) / "not-a-repo"
        invalid_path.mkdir()

        with pytest.raises(ValueError, match="Invalid Git repository"):
            WorktreeManager(invalid_path)


def test_list_worktrees_empty(worktree_manager):
    """Test listing worktrees when none exist (only main repo)."""
    worktree_list = worktree_manager.list_worktrees()
    # Should only have the main repository, which we filter out (bare check)
    assert worktree_list.total >= 0
    assert isinstance(worktree_list.worktrees, list)


def test_create_worktree_basic(worktree_manager):
    """Test creating a basic worktree without issue provider."""
    create_req = WorktreeCreate(
        issue_id="7",
        provider="github",
        worktree_type=WorktreeType.ISSUE,
    )

    worktree_info = worktree_manager.create_worktree(create_req)

    assert worktree_info.name == "issue-7"
    assert worktree_info.branch == "issue/7"
    assert worktree_info.worktree_type == WorktreeType.ISSUE
    assert worktree_info.path.exists()
    assert worktree_info.metadata is not None
    assert worktree_info.metadata.issue_number == 7
    assert worktree_info.metadata.status == "active"


def test_create_worktree_metadata_saved(worktree_manager):
    """Test that metadata is saved correctly."""
    create_req = WorktreeCreate(
        issue_id="8",
        provider="github",
        worktree_type=WorktreeType.FEATURE,
    )

    worktree_info = worktree_manager.create_worktree(create_req)

    # Check metadata file exists
    metadata_file = worktree_info.path / ".task-metadata.json"
    assert metadata_file.exists()

    # Load and verify metadata
    with open(metadata_file, "r") as f:
        data = json.load(f)

    assert data["worktree"] == "feature-8"
    assert data["worktree_type"] == "feature"
    assert data["branch"] == "feature/8"
    assert data["issue_number"] == 8
    assert data["status"] == "active"


def test_create_duplicate_worktree(worktree_manager):
    """Test that creating duplicate worktree fails validation."""
    create_req = WorktreeCreate(
        issue_id="9",
        provider="github",
        worktree_type=WorktreeType.ISSUE,
    )

    # Create first worktree
    worktree_manager.create_worktree(create_req)

    # Try to create duplicate
    with pytest.raises(ValueError, match="Validation failed.*worktree_exists"):
        worktree_manager.create_worktree(create_req)


def test_list_worktrees_with_metadata(worktree_manager):
    """Test listing worktrees includes metadata."""
    # Create a worktree
    create_req = WorktreeCreate(
        issue_id="10",
        provider="github",
        worktree_type=WorktreeType.ISSUE,
    )
    worktree_manager.create_worktree(create_req)

    # List worktrees
    worktree_list = worktree_manager.list_worktrees()

    assert worktree_list.total >= 1

    # Find our worktree
    found = False
    for wt in worktree_list.worktrees:
        if wt.name == "issue-10":
            found = True
            assert wt.worktree_type == WorktreeType.ISSUE
            assert wt.metadata is not None
            assert wt.metadata.issue_number == 10
            break

    assert found, "Created worktree not found in list"


def test_list_worktrees_filter_by_type(worktree_manager):
    """Test filtering worktrees by type."""
    # Create different types of worktrees
    worktree_manager.create_worktree(
        WorktreeCreate(issue_id="11", worktree_type=WorktreeType.ISSUE)
    )
    worktree_manager.create_worktree(
        WorktreeCreate(issue_id="12", worktree_type=WorktreeType.FEATURE)
    )

    # Filter by type
    issue_list = worktree_manager.list_worktrees(worktree_type=WorktreeType.ISSUE)
    feature_list = worktree_manager.list_worktrees(worktree_type=WorktreeType.FEATURE)

    # Check that filtering works
    issue_names = [wt.name for wt in issue_list.worktrees]
    feature_names = [wt.name for wt in feature_list.worktrees]

    assert "issue-11" in issue_names
    assert "issue-11" not in feature_names
    assert "feature-12" in feature_names
    assert "feature-12" not in issue_names


def test_validation_hierarchy_depth(worktree_manager, monkeypatch):
    """Test validation of hierarchy depth."""
    # Set max depth to 2
    from worktree_flow import config
    monkeypatch.setattr(config.settings, "max_hierarchy_depth", 2)
    monkeypatch.setattr(config.settings, "enforce_guardrails", True)

    # Create epic (depth 0)
    epic = worktree_manager.create_worktree(
        WorktreeCreate(issue_id="20", worktree_type=WorktreeType.EPIC)
    )

    # Create feature under epic (depth 1)
    feature = worktree_manager.create_worktree(
        WorktreeCreate(
            issue_id="21",
            worktree_type=WorktreeType.FEATURE,
            parent_worktree="epic-20",
        )
    )

    # Try to create subissue under feature (depth 2) - should fail
    with pytest.raises(ValueError, match="Maximum hierarchy depth"):
        worktree_manager.create_worktree(
            WorktreeCreate(
                issue_id="22",
                worktree_type=WorktreeType.SUBISSUE,
                parent_worktree="feature-21",
            )
        )


def test_create_worktree_with_parent(worktree_manager):
    """Test creating child worktree with parent."""
    # Create parent epic
    parent = worktree_manager.create_worktree(
        WorktreeCreate(issue_id="30", worktree_type=WorktreeType.EPIC)
    )

    # Create child feature
    child = worktree_manager.create_worktree(
        WorktreeCreate(
            issue_id="31",
            worktree_type=WorktreeType.FEATURE,
            parent_worktree="epic-30",
        )
    )

    assert child.metadata.parent_worktree == "epic-30"
    assert child.metadata.parent_branch == parent.branch
    assert child.base_branch == parent.branch


def test_create_worktree_nonexistent_parent(worktree_manager):
    """Test creating worktree with nonexistent parent fails."""
    with pytest.raises(ValueError, match="Parent worktree not found"):
        worktree_manager.create_worktree(
            WorktreeCreate(
                issue_id="40",
                worktree_type=WorktreeType.FEATURE,
                parent_worktree="nonexistent",
            )
        )


def test_load_metadata_nonexistent(worktree_manager):
    """Test loading metadata from nonexistent worktree."""
    metadata = worktree_manager._load_metadata(Path("/nonexistent/path"))
    assert metadata is None


def test_calculate_hierarchy_depth(worktree_manager):
    """Test hierarchy depth calculation."""
    # Create hierarchy: epic -> feature
    worktree_manager.create_worktree(
        WorktreeCreate(issue_id="50", worktree_type=WorktreeType.EPIC)
    )
    worktree_manager.create_worktree(
        WorktreeCreate(
            issue_id="51",
            worktree_type=WorktreeType.FEATURE,
            parent_worktree="epic-50",
        )
    )

    # Calculate depth
    depth_none = worktree_manager._calculate_hierarchy_depth(None)
    assert depth_none == 0

    depth_epic = worktree_manager._calculate_hierarchy_depth("epic-50")
    assert depth_epic == 1

    depth_feature = worktree_manager._calculate_hierarchy_depth("feature-51")
    assert depth_feature == 2
