"""Worktree management core logic."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import git
from git import Repo

from ..config import settings
from ..models import (
    WorktreeType,
    WorktreeMetadata,
    WorktreeInfo,
    WorktreeCreate,
    WorktreeList,
    ValidationResult,
    ValidationError,
)
from ..providers.base import IssueProvider


class WorktreeManager:
    """Manages Git worktrees with metadata and validation."""

    METADATA_FILE = ".task-metadata.json"

    def __init__(self, repo_path: Path):
        """Initialize WorktreeManager.

        Args:
            repo_path: Path to the Git repository
        
        Raises:
            ValueError: If path is invalid or not a Git repository
        """
        # Validate and resolve path to prevent path injection
        try:
            # Convert to Path object and resolve to absolute path
            path_obj = Path(repo_path)
            
            # Require absolute paths or convert CWD-relative paths
            if not path_obj.is_absolute():
                path_obj = Path.cwd() / path_obj
            
            resolved_path = path_obj.resolve(strict=True)
            
            # Additional security checks
            if not resolved_path.exists():
                raise ValueError(f"Repository path does not exist: {repo_path}")
            if not resolved_path.is_dir():
                raise ValueError(f"Repository path is not a directory: {repo_path}")
            
            # Store the validated, absolute path
            self.repo_path = resolved_path
            
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid repository path: {repo_path}") from e

        # Verify it's actually a Git repository using GitPython
        try:
            self.repo = Repo(self.repo_path)
        except git.exc.InvalidGitRepositoryError as e:
            raise ValueError(f"Invalid Git repository: {repo_path}") from e

    def list_worktrees(
        self,
        worktree_type: Optional[WorktreeType] = None,
    ) -> WorktreeList:
        """List all worktrees.

        Args:
            worktree_type: Optional filter by worktree type

        Returns:
            WorktreeList with all worktrees and metadata
        """
        worktrees = []

        # Get all git worktrees
        try:
            # Parse git worktree list output
            output = self.repo.git.worktree("list", "--porcelain")
            current_worktree = {}

            for line in output.split("\n"):
                line = line.strip()
                if not line:
                    if current_worktree:
                        worktrees.append(current_worktree)
                        current_worktree = {}
                    continue

                if line.startswith("worktree "):
                    current_worktree["path"] = Path(line[9:])
                elif line.startswith("branch "):
                    current_worktree["branch"] = line[7:].replace("refs/heads/", "")
                elif line.startswith("bare"):
                    current_worktree["bare"] = True

            # Don't forget the last one
            if current_worktree:
                worktrees.append(current_worktree)

        except git.exc.GitCommandError:
            # No worktrees or error listing them
            pass

        # Build WorktreeInfo for each worktree
        worktree_infos = []
        for wt in worktrees:
            if wt.get("bare"):
                continue  # Skip bare repository

            path = wt["path"]
            branch = wt.get("branch", "")
            name = path.name

            # Try to load metadata
            metadata = self._load_metadata(path)

            # Filter by type if requested
            if worktree_type and metadata and metadata.worktree_type != worktree_type:
                continue

            info = WorktreeInfo(
                path=path,
                name=name,
                branch=branch,
                base_branch=metadata.base_branch if metadata else "main",
                worktree_type=metadata.worktree_type if metadata else WorktreeType.CUSTOM,
                metadata=metadata,
            )
            worktree_infos.append(info)

        return WorktreeList(worktrees=worktree_infos, total=len(worktree_infos))

    def create_worktree(
        self,
        create_req: WorktreeCreate,
        issue_provider: Optional[IssueProvider] = None,
    ) -> WorktreeInfo:
        """Create a new worktree.

        Args:
            create_req: Worktree creation request
            issue_provider: Issue provider to fetch issue details

        Returns:
            WorktreeInfo for the created worktree

        Raises:
            ValueError: If validation fails or worktree cannot be created
        """
        # Determine base branch
        if create_req.parent_worktree:
            parent_metadata = self._find_worktree_metadata(create_req.parent_worktree)
            if not parent_metadata:
                raise ValueError(f"Parent worktree not found: {create_req.parent_worktree}")
            base_branch = parent_metadata.branch
            parent_branch = parent_metadata.branch
        else:
            base_branch = self.repo.active_branch.name
            parent_branch = None

        # Generate names
        issue_number = None
        title = None

        if create_req.issue_id:
            # Extract issue number
            try:
                issue_number = int(create_req.issue_id.split("-")[-1])
            except (ValueError, IndexError):
                try:
                    issue_number = int(create_req.issue_id)
                except ValueError:
                    raise ValueError(f"Invalid issue ID format: {create_req.issue_id}")

            # Fetch issue details if provider available
            if issue_provider:
                import asyncio
                try:
                    issue = asyncio.run(issue_provider.get_issue(str(issue_number)))
                    title = issue.title
                except Exception as e:
                    # Continue without title if fetch fails
                    title = f"Issue {issue_number}"

            # Generate worktree name (sanitized to prevent path traversal)
            worktree_name = self._sanitize_name(f"{create_req.worktree_type.value}-{issue_number}")
            branch_name = f"{create_req.worktree_type.value}/{issue_number}"
        else:
            # Custom worktree without issue
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            worktree_name = self._sanitize_name(f"custom-{timestamp}")
            branch_name = worktree_name

        # Validate before creating
        validation = self._validate_create(
            worktree_name=worktree_name,
            worktree_type=create_req.worktree_type,
            parent_worktree=create_req.parent_worktree,
        )
        if not validation.valid:
            error_messages = [f"{e.code}: {e.message}" for e in validation.errors]
            raise ValueError(f"Validation failed: {', '.join(error_messages)}")

        # Create the worktree
        worktree_path = self.repo_path.parent / worktree_name

        if worktree_path.exists():
            raise ValueError(f"Worktree path already exists: {worktree_path}")

        try:
            # Create new branch and worktree
            self.repo.git.worktree("add", "-b", branch_name, str(worktree_path), base_branch)
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to create worktree: {e}")

        # Create metadata
        metadata = WorktreeMetadata(
            worktree=worktree_name,
            worktree_type=create_req.worktree_type,
            branch=branch_name,
            base_branch=base_branch,
            parent_worktree=create_req.parent_worktree,
            parent_branch=parent_branch,
            issue_number=issue_number,
            issue_provider=create_req.provider if create_req.issue_id else None,
            title=title,
            status="active",
            created_at=datetime.now(),
        )

        # Save metadata
        self._save_metadata(worktree_path, metadata)

        return WorktreeInfo(
            path=worktree_path,
            name=worktree_name,
            branch=branch_name,
            base_branch=base_branch,
            worktree_type=create_req.worktree_type,
            metadata=metadata,
        )

    def _validate_create(
        self,
        worktree_name: str,
        worktree_type: WorktreeType,
        parent_worktree: Optional[str] = None,
    ) -> ValidationResult:
        """Validate worktree creation request.

        Args:
            worktree_name: Name of the worktree to create
            worktree_type: Type of worktree
            parent_worktree: Optional parent worktree name

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []
        checks = []

        # Check if worktree name already exists
        checks.append("worktree_name_unique")
        existing = self._find_worktree_metadata(worktree_name)
        if existing:
            errors.append(
                ValidationError(
                    code="worktree_exists",
                    message=f"Worktree already exists: {worktree_name}",
                    fix_suggestion="Use a different name or remove the existing worktree",
                )
            )

        # Check hierarchy depth if guardrails enabled
        if settings.enforce_guardrails:
            checks.append("hierarchy_depth")
            depth = self._calculate_hierarchy_depth(parent_worktree)
            if depth >= settings.max_hierarchy_depth:
                errors.append(
                    ValidationError(
                        code="max_depth_exceeded",
                        message=f"Maximum hierarchy depth ({settings.max_hierarchy_depth}) exceeded",
                        fix_suggestion="Create worktree at a lower level or increase max_hierarchy_depth",
                    )
                )

        # Check parent-child type compatibility
        if parent_worktree:
            checks.append("parent_child_compatibility")
            parent_metadata = self._find_worktree_metadata(parent_worktree)
            if parent_metadata:
                # Epic can have features, features can have subissues
                valid_combinations = {
                    WorktreeType.EPIC: [WorktreeType.FEATURE],
                    WorktreeType.FEATURE: [WorktreeType.SUBISSUE, WorktreeType.ISSUE],
                }
                allowed_types = valid_combinations.get(parent_metadata.worktree_type, [])
                if worktree_type not in allowed_types and settings.enforce_guardrails:
                    warnings.append(
                        f"Unusual hierarchy: {worktree_type} under {parent_metadata.worktree_type}"
                    )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            checks_performed=checks,
        )

    def _calculate_hierarchy_depth(self, worktree_name: Optional[str]) -> int:
        """Calculate hierarchy depth for a worktree.

        Args:
            worktree_name: Name of the worktree

        Returns:
            Depth in hierarchy (0 = root, 1 = first level, etc.)
        """
        if not worktree_name:
            return 0

        depth = 1
        current = self._find_worktree_metadata(worktree_name)
        while current and current.parent_worktree:
            depth += 1
            current = self._find_worktree_metadata(current.parent_worktree)
            if depth > 10:  # Safety limit
                break
        return depth

    def _find_worktree_metadata(self, worktree_name: str) -> Optional[WorktreeMetadata]:
        """Find metadata for a worktree by name.

        Args:
            worktree_name: Name of the worktree

        Returns:
            WorktreeMetadata if found, None otherwise
        """
        worktree_path = self.repo_path.parent / worktree_name
        return self._load_metadata(worktree_path)

    def _load_metadata(self, worktree_path: Path) -> Optional[WorktreeMetadata]:
        """Load worktree metadata from file.

        Args:
            worktree_path: Path to the worktree directory

        Returns:
            WorktreeMetadata if file exists and is valid, None otherwise
        """
        metadata_file = worktree_path / self.METADATA_FILE
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)
            return WorktreeMetadata(**data)
        except (json.JSONDecodeError, ValueError):
            return None

    def _save_metadata(self, worktree_path: Path, metadata: WorktreeMetadata) -> None:
        """Save worktree metadata to file.

        Args:
            worktree_path: Path to the worktree directory
            metadata: Metadata to save
        """
        metadata_file = worktree_path / self.METADATA_FILE
        with open(metadata_file, "w") as f:
            json.dump(metadata.model_dump(mode="json"), f, indent=2, default=str)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize worktree name to prevent path traversal.

        Args:
            name: The name to sanitize

        Returns:
            Sanitized name safe for use in file paths

        Raises:
            ValueError: If name is invalid after sanitization
        """
        import re
        
        # Remove any path separators and other dangerous characters
        sanitized = re.sub(r'[/\\\.]+', '-', name)
        sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '', sanitized)
        
        # Ensure it's not empty and doesn't start with a dash
        sanitized = sanitized.strip('-_')
        
        if not sanitized:
            raise ValueError(f"Invalid name after sanitization: {name}")
        
        return sanitized
