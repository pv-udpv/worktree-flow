"""Base provider interfaces."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import Issue, IssueCreate, PullRequest, PRCreate


class IssueProvider(ABC):
    """Abstract issue provider interface."""

    @abstractmethod
    async def get_issue(self, issue_id: str) -> Issue:
        """Get issue by ID."""
        pass

    @abstractmethod
    async def list_issues(
        self,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[Issue]:
        """List issues."""
        pass

    @abstractmethod
    async def create_issue(self, issue: IssueCreate) -> Issue:
        """Create new issue."""
        pass

    @abstractmethod
    async def update_issue(self, issue_id: str, **kwargs) -> Issue:
        """Update issue."""
        pass

    @abstractmethod
    async def close_issue(self, issue_id: str) -> Issue:
        """Close issue."""
        pass


class PRProvider(ABC):
    """Abstract Pull Request provider interface."""

    @abstractmethod
    async def get_pr(self, pr_id: str) -> PullRequest:
        """Get PR by ID."""
        pass

    @abstractmethod
    async def create_pr(self, pr: PRCreate) -> PullRequest:
        """Create PR."""
        pass

    @abstractmethod
    async def update_pr(self, pr_id: str, **kwargs) -> PullRequest:
        """Update PR."""
        pass

    @abstractmethod
    async def merge_pr(self, pr_id: str, method: str = "merge") -> PullRequest:
        """Merge PR."""
        pass

    @abstractmethod
    async def list_prs(self, state: Optional[str] = None) -> list[PullRequest]:
        """List PRs."""
        pass


class GitProvider(ABC):
    """Abstract Git operations provider interface."""

    @abstractmethod
    async def create_branch(self, branch_name: str, from_branch: str) -> bool:
        """Create branch."""
        pass

    @abstractmethod
    async def delete_branch(self, branch_name: str) -> bool:
        """Delete branch."""
        pass

    @abstractmethod
    async def get_default_branch(self) -> str:
        """Get default branch name."""
        pass
