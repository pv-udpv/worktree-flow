"""Repository initialization logic with .envrc support."""

import os
import shutil
from pathlib import Path
from typing import Optional


def check_direnv_available() -> bool:
    """Check if direnv is installed and available.
    
    Returns:
        True if direnv is available, False otherwise.
    """
    return shutil.which("direnv") is not None


def create_example_envrc(repo_path: Path) -> Path:
    """Create an example .envrc file in the repository.
    
    Args:
        repo_path: Path to the repository.
        
    Returns:
        Path to the created .envrc file.
    """
    envrc_path = repo_path / ".envrc"
    
    example_content = """# Worktree Flow environment configuration
# This file is loaded by direnv (https://direnv.net/)
#
# NOTE: This file is committed to the repository.
# For local overrides, create .envrc.local (which is gitignored)

# Export repository path
export WORKTREE_DEFAULT_REPO="$(pwd)"

# GitHub configuration (optional)
# export WORKTREE_GITHUB_TOKEN="ghp_..."
# export WORKTREE_GITHUB_REPO="owner/repo"

# Linear configuration (optional)
# export WORKTREE_LINEAR_API_KEY="lin_api_..."
# export WORKTREE_LINEAR_TEAM_ID="team-id"

# GitLab configuration (optional)
# export WORKTREE_GITLAB_TOKEN="glpat-..."
# export WORKTREE_GITLAB_PROJECT="project-id"

# Jira configuration (optional)
# export WORKTREE_JIRA_URL="https://your-domain.atlassian.net"
# export WORKTREE_JIRA_EMAIL="your-email@example.com"
# export WORKTREE_JIRA_API_TOKEN="..."

# Default provider settings
export WORKTREE_DEFAULT_ISSUE_PROVIDER="github"
export WORKTREE_DEFAULT_PR_PROVIDER="github"
export WORKTREE_DEFAULT_GIT_PROVIDER="github"

# Validation settings
export WORKTREE_MAX_HIERARCHY_DEPTH="3"
export WORKTREE_ENFORCE_GUARDRAILS="true"

# Logging
export WORKTREE_LOG_LEVEL="INFO"

# Load local overrides if present
[[ -f .envrc.local ]] && source_env .envrc.local
"""
    
    envrc_path.write_text(example_content)
    return envrc_path


def validate_envrc(envrc_path: Path) -> tuple[bool, Optional[str]]:
    """Validate .envrc file content.
    
    Args:
        envrc_path: Path to the .envrc file.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not envrc_path.exists():
        return False, "File does not exist"
    
    if not envrc_path.is_file():
        return False, "Path is not a file"
    
    try:
        content = envrc_path.read_text()
        
        # Check if file is not empty
        if not content.strip():
            return False, "File is empty"
        
        # Basic validation - check if it looks like a shell script
        lines = content.strip().split("\n")
        has_export = any(
            line.strip().startswith("export ") or line.strip().startswith("#")
            for line in lines
        )
        
        if not has_export:
            return False, "File does not appear to be a valid .envrc file"
        
        return True, None
        
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def load_envrc(envrc_path: Path) -> dict[str, str]:
    """Load environment variables from .envrc file.
    
    This parses simple export statements from the .envrc file.
    Note: This does not execute the file, only parses export statements.
    
    Args:
        envrc_path: Path to the .envrc file.
        
    Returns:
        Dictionary of environment variables.
    """
    env_vars = {}
    
    if not envrc_path.exists():
        return env_vars
    
    try:
        content = envrc_path.read_text()
        
        for line in content.split("\n"):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            
            # Parse export statements
            if line.startswith("export "):
                line = line[7:]  # Remove "export "
                
                # Split on first = only
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Handle $(pwd) or other command substitutions
                    if "$(pwd)" in value:
                        value = value.replace("$(pwd)", str(envrc_path.parent.absolute()))
                    
                    env_vars[key] = value
        
        return env_vars
        
    except Exception:
        return env_vars


def initialize_repository(
    repo_path: Path,
    create_envrc: bool = True,
    force_create: bool = False,
) -> dict:
    """Initialize repository for worktree workflow.
    
    Args:
        repo_path: Path to the repository.
        create_envrc: Whether to create .envrc if it doesn't exist.
        force_create: Whether to overwrite existing .envrc.
        
    Returns:
        Dictionary with initialization results.
    """
    results = {
        "repo_path": str(repo_path.absolute()),
        "envrc_exists": False,
        "envrc_created": False,
        "envrc_valid": False,
        "direnv_available": False,
        "loaded_env_vars": {},
        "message": "",
    }
    
    # Check if repository path exists
    if not repo_path.exists():
        results["message"] = f"Repository path does not exist: {repo_path}"
        return results
    
    # Check direnv availability
    results["direnv_available"] = check_direnv_available()
    
    # Check for existing .envrc
    envrc_path = repo_path / ".envrc"
    results["envrc_exists"] = envrc_path.exists()
    
    # Handle .envrc creation
    if results["envrc_exists"]:
        if force_create:
            create_example_envrc(repo_path)
            results["envrc_created"] = True
            results["message"] = "Created new .envrc file (overwritten)"
        else:
            results["message"] = ".envrc already exists"
    elif create_envrc:
        create_example_envrc(repo_path)
        results["envrc_created"] = True
        results["envrc_exists"] = True
        results["message"] = "Created example .envrc file"
    
    # Validate .envrc
    if envrc_path.exists():
        is_valid, error = validate_envrc(envrc_path)
        results["envrc_valid"] = is_valid
        
        if not is_valid:
            results["message"] += f" (validation failed: {error})"
        else:
            # Load environment variables
            results["loaded_env_vars"] = load_envrc(envrc_path)
    
    return results
