"""Tests for repository initialization with .envrc support."""

import os
from pathlib import Path
import tempfile
import pytest

from worktree_flow.core.init import (
    check_direnv_available,
    create_example_envrc,
    validate_envrc,
    load_envrc,
    initialize_repository,
)


@pytest.fixture
def temp_repo():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_check_direnv_available():
    """Test direnv availability check."""
    # This will return True or False depending on the system
    result = check_direnv_available()
    assert isinstance(result, bool)


def test_create_example_envrc(temp_repo):
    """Test creating example .envrc file."""
    envrc_path = create_example_envrc(temp_repo)
    
    assert envrc_path.exists()
    assert envrc_path.name == ".envrc"
    
    content = envrc_path.read_text()
    assert "WORKTREE_DEFAULT_REPO" in content
    assert "export" in content
    assert "github" in content.lower()


def test_validate_envrc_valid(temp_repo):
    """Test validating a valid .envrc file."""
    envrc_path = create_example_envrc(temp_repo)
    
    is_valid, error = validate_envrc(envrc_path)
    
    assert is_valid
    assert error is None


def test_validate_envrc_not_exists(temp_repo):
    """Test validating non-existent .envrc file."""
    envrc_path = temp_repo / ".envrc"
    
    is_valid, error = validate_envrc(envrc_path)
    
    assert not is_valid
    assert "does not exist" in error


def test_validate_envrc_empty(temp_repo):
    """Test validating empty .envrc file."""
    envrc_path = temp_repo / ".envrc"
    envrc_path.write_text("")
    
    is_valid, error = validate_envrc(envrc_path)
    
    assert not is_valid
    assert "empty" in error.lower()


def test_validate_envrc_invalid_content(temp_repo):
    """Test validating .envrc with invalid content."""
    envrc_path = temp_repo / ".envrc"
    envrc_path.write_text("not a valid envrc file\njust some random text")
    
    is_valid, error = validate_envrc(envrc_path)
    
    assert not is_valid
    assert "valid" in error.lower()


def test_load_envrc_basic(temp_repo):
    """Test loading environment variables from .envrc."""
    envrc_path = temp_repo / ".envrc"
    content = """
# Comment line
export FOO="bar"
export BAZ=qux
export QUOTED='value with spaces'
"""
    envrc_path.write_text(content)
    
    env_vars = load_envrc(envrc_path)
    
    assert env_vars["FOO"] == "bar"
    assert env_vars["BAZ"] == "qux"
    assert env_vars["QUOTED"] == "value with spaces"


def test_load_envrc_with_pwd(temp_repo):
    """Test loading .envrc with $(pwd) substitution."""
    envrc_path = temp_repo / ".envrc"
    content = 'export REPO_PATH="$(pwd)"'
    envrc_path.write_text(content)
    
    env_vars = load_envrc(envrc_path)
    
    assert env_vars["REPO_PATH"] == str(temp_repo.absolute())


def test_load_envrc_not_exists(temp_repo):
    """Test loading from non-existent .envrc file."""
    envrc_path = temp_repo / ".envrc"
    
    env_vars = load_envrc(envrc_path)
    
    assert env_vars == {}


def test_load_envrc_example(temp_repo):
    """Test loading the example .envrc file."""
    create_example_envrc(temp_repo)
    envrc_path = temp_repo / ".envrc"
    
    env_vars = load_envrc(envrc_path)
    
    # Check that some expected variables are present
    assert "WORKTREE_DEFAULT_REPO" in env_vars
    assert "WORKTREE_DEFAULT_ISSUE_PROVIDER" in env_vars
    assert env_vars["WORKTREE_DEFAULT_ISSUE_PROVIDER"] == "github"


def test_initialize_repository_create_envrc(temp_repo):
    """Test initializing repository with .envrc creation."""
    results = initialize_repository(temp_repo, create_envrc=True)
    
    assert results["envrc_created"]
    assert results["envrc_exists"]
    assert results["envrc_valid"]
    assert (temp_repo / ".envrc").exists()


def test_initialize_repository_no_create(temp_repo):
    """Test initializing repository without creating .envrc."""
    results = initialize_repository(temp_repo, create_envrc=False)
    
    assert not results["envrc_created"]
    assert not results["envrc_exists"]
    assert not (temp_repo / ".envrc").exists()


def test_initialize_repository_existing_envrc(temp_repo):
    """Test initializing repository with existing .envrc."""
    # Create .envrc first
    create_example_envrc(temp_repo)
    
    results = initialize_repository(temp_repo, create_envrc=True, force_create=False)
    
    assert not results["envrc_created"]
    assert results["envrc_exists"]
    assert results["envrc_valid"]


def test_initialize_repository_force_overwrite(temp_repo):
    """Test initializing repository with force overwrite."""
    # Create .envrc first
    envrc_path = temp_repo / ".envrc"
    envrc_path.write_text("export OLD_VAR=old")
    
    results = initialize_repository(temp_repo, create_envrc=True, force_create=True)
    
    assert results["envrc_created"]
    assert results["envrc_exists"]
    assert results["envrc_valid"]
    
    # Check that new content is present
    content = envrc_path.read_text()
    assert "WORKTREE_DEFAULT_REPO" in content
    assert "OLD_VAR" not in content


def test_initialize_repository_invalid_path():
    """Test initializing with invalid repository path."""
    invalid_path = Path("/nonexistent/path/to/repo")
    
    results = initialize_repository(invalid_path)
    
    assert "does not exist" in results["message"]


def test_initialize_repository_loads_env_vars(temp_repo):
    """Test that initialization loads environment variables."""
    results = initialize_repository(temp_repo, create_envrc=True)
    
    assert len(results["loaded_env_vars"]) > 0
    assert "WORKTREE_DEFAULT_REPO" in results["loaded_env_vars"]
