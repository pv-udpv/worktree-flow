"""Provider registry and factory."""

from enum import Enum
from typing import Type

from .base import IssueProvider, PRProvider, GitProvider
from .github import GitHubIssueProvider, GitHubPRProvider, GitHubGitProvider


class ProviderType(str, Enum):
    """Supported provider types."""

    GITHUB = "github"
    LINEAR = "linear"
    GITLAB = "gitlab"
    JIRA = "jira"


class ProviderRegistry:
    """Registry for all providers."""

    _issue_providers: dict[ProviderType, Type[IssueProvider]] = {
        ProviderType.GITHUB: GitHubIssueProvider,
    }

    _pr_providers: dict[ProviderType, Type[PRProvider]] = {
        ProviderType.GITHUB: GitHubPRProvider,
    }

    _git_providers: dict[ProviderType, Type[GitProvider]] = {
        ProviderType.GITHUB: GitHubGitProvider,
    }

    @classmethod
    def get_issue_provider(
        cls, provider_type: ProviderType, **kwargs
    ) -> IssueProvider:
        """Get issue provider instance."""
        provider_class = cls._issue_providers.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown issue provider: {provider_type}")
        return provider_class(**kwargs)

    @classmethod
    def get_pr_provider(cls, provider_type: ProviderType, **kwargs) -> PRProvider:
        """Get PR provider instance."""
        provider_class = cls._pr_providers.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown PR provider: {provider_type}")
        return provider_class(**kwargs)

    @classmethod
    def get_git_provider(cls, provider_type: ProviderType, **kwargs) -> GitProvider:
        """Get Git provider instance."""
        provider_class = cls._git_providers.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown Git provider: {provider_type}")
        return provider_class(**kwargs)

    @classmethod
    def register_issue_provider(
        cls, provider_type: ProviderType, provider_class: Type[IssueProvider]
    ):
        """Register custom issue provider."""
        cls._issue_providers[provider_type] = provider_class
