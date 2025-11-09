# WorktreeManager Implementation

This document describes the implementation of the WorktreeManager with list and create functionality.

## Overview

The implementation provides real Git worktree management through:
- A core `WorktreeManager` class that handles all worktree operations
- CLI commands (`list` and `create`) that use WorktreeManager
- API endpoints that expose the same functionality via REST
- Comprehensive validation and guardrails

## Architecture

```
User Input (CLI/API)
    ↓
WorktreeManager (Business Logic)
    ↓
├─→ GitPython (Git Operations)
├─→ IssueProvider (Issue Fetching)
└─→ Guardrails (Validation)
```

## Core Components

### WorktreeManager Class

Location: `src/worktree_flow/core/worktree_manager.py`

**Key Methods:**
- `list_worktrees()` - Lists all worktrees with metadata
- `create_worktree()` - Creates new worktree from issue or custom
- `_validate_create()` - Validates worktree creation request
- `_load_metadata()` / `_save_metadata()` - Metadata persistence

**Security Features:**
- Path validation with `resolve(strict=True)`
- Name sanitization to prevent path traversal
- Absolute path requirement
- Multiple validation layers

### CLI Commands

Location: `src/worktree_flow/cli/app.py`

**`worktree list`**
```bash
worktree list [--repo PATH]
```
- Displays worktrees in a rich table format
- Shows: Name, Type, Branch, Base Branch, Status

**`worktree create`**
```bash
worktree create ISSUE_ID [--provider PROVIDER] [--repo PATH]
```
- Creates worktree from issue
- Fetches issue details from provider
- Generates branch and worktree names
- Validates before creation

### API Endpoints

Location: `src/worktree_flow/api/routers/worktrees.py`

**GET `/worktrees/list`**
- Query params: `worktree_type` (optional), `repo_path` (optional)
- Returns: `WorktreeList` model

**POST `/worktrees/create/issue`**
- Query params: `issue_id`, `provider`, `repo_path` (optional)
- Returns: `WorktreeInfo` model

## Validation & Guardrails

### Hierarchy Depth Check
- Configurable via `settings.max_hierarchy_depth` (default: 3)
- Prevents overly deep hierarchies
- Enabled via `settings.enforce_guardrails`

### Name Validation
- Ensures worktree names are unique
- Sanitizes names to prevent path traversal
- Removes dangerous characters

### Parent-Child Compatibility
- Epic → Feature
- Feature → Subissue/Issue
- Warnings for unusual hierarchies

## Metadata Management

Each worktree has a `.task-metadata.json` file containing:
```json
{
  "worktree": "issue-7",
  "worktree_type": "issue",
  "branch": "issue/7",
  "base_branch": "main",
  "parent_worktree": null,
  "parent_branch": null,
  "issue_number": 7,
  "issue_provider": "github",
  "title": "Issue Title",
  "status": "active",
  "created_at": "2025-11-09T...",
  "updated_at": null,
  "commits": [],
  "sub_worktrees": [],
  "bindings": {}
}
```

## Testing

Location: `tests/test_worktree_manager.py`

**Test Coverage:**
- Initialization (valid & invalid repos)
- List operations (empty, with data, filtering)
- Create operations (basic, with parent, custom)
- Validation (depth, duplicates, parents)
- Metadata persistence
- Edge cases

## Usage Examples

### CLI Usage

```bash
# List all worktrees
worktree list

# Create worktree from GitHub issue #7
worktree create 7

# Create with specific provider
worktree create DEV-123 --provider linear

# Specify repository
worktree create 8 --repo /path/to/repo
```

### API Usage

```bash
# List worktrees
curl http://localhost:8000/worktrees/list

# Filter by type
curl http://localhost:8000/worktrees/list?worktree_type=epic

# Create from issue
curl -X POST "http://localhost:8000/worktrees/create/issue?issue_id=7&provider=github"
```

### Python Usage

```python
from pathlib import Path
from worktree_flow.core import WorktreeManager
from worktree_flow.models import WorktreeCreate, WorktreeType

# Initialize manager
manager = WorktreeManager(Path("/path/to/repo"))

# List worktrees
worktrees = manager.list_worktrees()
for wt in worktrees.worktrees:
    print(f"{wt.name}: {wt.branch}")

# Create worktree
create_req = WorktreeCreate(
    issue_id="7",
    provider="github",
    worktree_type=WorktreeType.ISSUE,
)
worktree_info = manager.create_worktree(create_req)
print(f"Created: {worktree_info.path}")
```

## Configuration

Settings in `config.py`:
- `default_repo` - Default repository path
- `max_hierarchy_depth` - Maximum worktree nesting (default: 3)
- `enforce_guardrails` - Enable validation (default: True)
- Provider settings (GitHub, Linear, GitLab, Jira tokens)

## Security Considerations

### Path Injection Prevention
- All paths are validated with `resolve(strict=True)`
- Existence and directory checks
- Absolute path requirement
- GitPython provides additional validation

### Name Sanitization
- Removes path separators (/, \, .)
- Allows only alphanumeric, dash, underscore
- Prevents empty names

### CodeQL Alerts
Three false positive alerts for path injection:
- Operations on validated, absolute paths only
- Read-only checks (exists, is_dir)
- Constrained to Git repository operations

## Future Enhancements

Potential improvements:
- Additional providers (Linear, Jira, GitLab)
- Async issue fetching
- Worktree removal/cleanup
- Merge operations
- Sync with parent branch
- PR creation integration
- Binding management (Perplexity, Slack, etc.)
