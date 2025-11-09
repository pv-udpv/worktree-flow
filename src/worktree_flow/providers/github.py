"""GitHub provider implementation."""

from typing import Optional
from github import Github, GithubException

from ..models import Issue, IssueCreate, PullRequest, PRCreate
from .base import IssueProvider, PRProvider, GitProvider


class GitHubIssueProvider(IssueProvider):
    """GitHub issues provider."""

    def __init__(self, token: str, repo_name: str):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_name)

    async def get_issue(self, issue_id: str) -> Issue:
        """Get GitHub issue."""
        gh_issue = self.repo.get_issue(int(issue_id))

        return Issue(
            id=str(gh_issue.number),
            number=gh_issue.number,
            title=gh_issue.title,
            body=gh_issue.body,
            state=gh_issue.state,
            labels=[label.name for label in gh_issue.labels],
            assignees=[a.login for a in gh_issue.assignees],
            url=gh_issue.html_url,
            created_at=gh_issue.created_at,
            updated_at=gh_issue.updated_at,
            metadata={
                "comments": gh_issue.comments,
                "milestone": gh_issue.milestone.title if gh_issue.milestone else None,
            },
        )

    async def list_issues(
        self,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[Issue]:
        """List GitHub issues."""
        gh_issues = self.repo.get_issues(
            state=state or "open",
            labels=labels or [],
        )[:limit]

        return [await self.get_issue(str(issue.number)) for issue in gh_issues]

    async def create_issue(self, issue: IssueCreate) -> Issue:
        """Create GitHub issue."""
        gh_issue = self.repo.create_issue(
            title=issue.title,
            body=issue.body,
            labels=issue.labels or [],
        )
        return await self.get_issue(str(gh_issue.number))

    async def update_issue(self, issue_id: str, **kwargs) -> Issue:
        """Update GitHub issue."""
        gh_issue = self.repo.get_issue(int(issue_id))
        gh_issue.edit(**kwargs)
        return await self.get_issue(issue_id)

    async def close_issue(self, issue_id: str) -> Issue:
        """Close GitHub issue."""
        return await self.update_issue(issue_id, state="closed")


class GitHubPRProvider(PRProvider):
    """GitHub Pull Requests provider."""

    def __init__(self, token: str, repo_name: str):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_name)

    async def get_pr(self, pr_id: str) -> PullRequest:
        """Get GitHub PR."""
        pr = self.repo.get_pull(int(pr_id))

        return PullRequest(
            id=str(pr.number),
            number=pr.number,
            title=pr.title,
            body=pr.body,
            state="merged" if pr.merged else pr.state,
            source_branch=pr.head.ref,
            target_branch=pr.base.ref,
            url=pr.html_url,
            author=pr.user.login,
            reviewers=[r.login for r in pr.get_review_requests()[0]],
            created_at=pr.created_at,
            updated_at=pr.updated_at,
            metadata={
                "mergeable": pr.mergeable,
                "commits": pr.commits,
            },
        )

    async def create_pr(self, pr: PRCreate) -> PullRequest:
        """Create GitHub PR."""
        gh_pr = self.repo.create_pull(
            title=pr.title,
            body=pr.body,
            head=pr.source_branch,
            base=pr.target_branch,
            draft=pr.draft,
        )
        return await self.get_pr(str(gh_pr.number))

    async def update_pr(self, pr_id: str, **kwargs) -> PullRequest:
        """Update GitHub PR."""
        pr = self.repo.get_pull(int(pr_id))
        pr.edit(**kwargs)
        return await self.get_pr(pr_id)

    async def merge_pr(self, pr_id: str, method: str = "merge") -> PullRequest:
        """Merge GitHub PR."""
        pr = self.repo.get_pull(int(pr_id))
        pr.merge(merge_method=method)
        return await self.get_pr(pr_id)

    async def list_prs(self, state: Optional[str] = None) -> list[PullRequest]:
        """List GitHub PRs."""
        prs = self.repo.get_pulls(state=state or "open")
        return [await self.get_pr(str(pr.number)) for pr in prs]


class GitHubGitProvider(GitProvider):
    """GitHub Git operations provider."""

    def __init__(self, token: str, repo_name: str):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_name)

    async def create_branch(self, branch_name: str, from_branch: str) -> bool:
        """Create branch."""
        try:
            ref = self.repo.get_git_ref(f"heads/{from_branch}")
            self.repo.create_git_ref(f"refs/heads/{branch_name}", ref.object.sha)
            return True
        except GithubException:
            return False

    async def delete_branch(self, branch_name: str) -> bool:
        """Delete branch."""
        try:
            ref = self.repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
            return True
        except GithubException:
            return False

    async def get_default_branch(self) -> str:
        """Get default branch."""
        return self.repo.default_branch
