"""Configuration management."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="WORKTREE_",
        case_sensitive=False,
    )

    # Paths
    default_repo: Optional[Path] = Field(default=None, description="Default repository path")

    # Provider settings
    default_issue_provider: str = Field(default="github", description="Default issue provider")
    default_pr_provider: str = Field(default="github", description="Default PR provider")
    default_git_provider: str = Field(default="github", description="Default Git provider")

    # GitHub
    github_token: Optional[str] = Field(default=None, description="GitHub API token")
    github_repo: Optional[str] = Field(default=None, description="GitHub repo (owner/name)")

    # Linear
    linear_api_key: Optional[str] = Field(default=None, description="Linear API key")
    linear_team_id: Optional[str] = Field(default=None, description="Linear team ID")

    # GitLab
    gitlab_token: Optional[str] = Field(default=None, description="GitLab API token")
    gitlab_project: Optional[str] = Field(default=None, description="GitLab project ID")

    # Jira
    jira_url: Optional[str] = Field(default=None, description="Jira instance URL")
    jira_email: Optional[str] = Field(default=None, description="Jira user email")
    jira_api_token: Optional[str] = Field(default=None, description="Jira API token")

    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=False, description="Enable auto-reload")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")

    # Validation settings
    max_hierarchy_depth: int = Field(default=3, description="Maximum hierarchy depth")
    enforce_guardrails: bool = Field(default=True, description="Enforce validation guardrails")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")


# Global settings instance
settings = Settings()
