# Linear Provider Documentation

## Overview

The Linear provider enables integration with Linear's issue tracking system through their GraphQL API. It supports creating, retrieving, updating, and synchronizing issues between your workflow and Linear.

## Configuration

The Linear provider requires the following configuration settings:

```bash
# Environment variables
export WORKTREE_LINEAR_API_KEY="lin_api_..."  # Your Linear API key
export WORKTREE_LINEAR_TEAM_ID="team-uuid"     # Optional: Linear team ID
```

Or in your `.env` file:

```env
WORKTREE_LINEAR_API_KEY=lin_api_...
WORKTREE_LINEAR_TEAM_ID=team-uuid
```

## Getting Your Linear API Key

1. Go to Linear Settings → API
2. Click "Personal API keys"
3. Create a new API key with appropriate permissions
4. Copy the key and set it as `WORKTREE_LINEAR_API_KEY`

## Getting Your Team ID

1. Go to your Linear workspace
2. Navigate to Team Settings
3. The team ID is in the URL or you can query it via the API

## Features

### Rate Limiting

The Linear provider includes built-in rate limiting to prevent API throttling:
- Default: 50 requests per minute
- Automatically waits when approaching limits
- Configurable through `LinearRateLimiter` class

### Issue ID Formats

The provider supports both Linear identifier formats:
- **Identifier format**: `DEV-123`, `ENG-456` (team prefix + number)
- **UUID format**: Full UUID strings for internal operations

### State Management

Linear issues have different states that are mapped to internal states:
- **Open states**: `triage`, `backlog`, `unstarted`, `started`
- **Closed states**: `completed`, `canceled`

### Metadata Preservation

The provider preserves Linear-specific metadata:
- `linear_identifier`: Original Linear identifier (e.g., "DEV-123")
- `team_id`: Team UUID
- `team_key`: Team key/prefix
- `state_name`: Full state name from Linear
- `state_type`: Linear state type
- `priority`: Numeric priority value
- `priority_label`: Human-readable priority label

## Usage Examples

### Basic Issue Retrieval

```python
from worktree_flow.providers import LinearIssueProvider

# Initialize provider
provider = LinearIssueProvider(
    api_key="lin_api_...",
    team_id="team-uuid"
)

# Get issue by identifier
issue = await provider.get_issue("DEV-123")
print(f"Issue: {issue.title}")
print(f"State: {issue.state}")
print(f"Labels: {issue.labels}")
```

### Creating Issues

```python
from worktree_flow.models import IssueCreate

# Create new issue
new_issue = IssueCreate(
    title="Implement new feature",
    body="Detailed description of the feature",
    labels=["feature", "backend"]
)

issue = await provider.create_issue(new_issue)
print(f"Created issue: {issue.metadata['linear_identifier']}")
```

### Listing Issues

```python
# List all open issues
issues = await provider.list_issues(state="open", limit=50)

# List closed issues with specific label
closed_bugs = await provider.list_issues(
    state="closed",
    labels=["bug"],
    limit=20
)

# List all issues for the team
all_issues = await provider.list_issues(limit=100)
```

### Updating Issues

```python
# Update issue title and description
updated = await provider.update_issue(
    "issue-uuid",
    title="Updated title",
    body="Updated description"
)
```

### Closing Issues

```python
# Close an issue (sets it to completed state)
closed_issue = await provider.close_issue("issue-uuid")
print(f"Issue closed: {closed_issue.state}")
```

### Using with Provider Registry

```python
from worktree_flow.providers import ProviderRegistry, ProviderType
from worktree_flow.config import settings

# Get Linear provider from registry
provider = ProviderRegistry.get_issue_provider(
    ProviderType.LINEAR,
    api_key=settings.linear_api_key,
    team_id=settings.linear_team_id
)

# Use provider
issue = await provider.get_issue("DEV-123")
```

## CLI Usage

```bash
# Create worktree from Linear issue
worktree create issue DEV-123 --provider linear

# List issues from Linear
worktree list issues --provider linear --state open

# Create issue in Linear
worktree create-issue --provider linear \
    --title "New feature" \
    --body "Description"
```

## HTTP Client Support

The Linear provider supports both `httpx` and `requests` libraries:
- **Preferred**: `httpx` (async support, better performance)
- **Fallback**: `requests` (if httpx is not available)

Install the appropriate library:

```bash
# Option 1: httpx (recommended)
pip install httpx

# Option 2: requests (fallback)
pip install requests
```

## API Considerations

### GraphQL API

Linear uses GraphQL API at `https://api.linear.app/graphql`. All operations are performed through GraphQL queries and mutations.

### Rate Limits

Linear enforces rate limits on their API. The provider's built-in rate limiter helps prevent hitting these limits, but for high-volume operations, consider:
- Batching operations when possible
- Implementing exponential backoff for retries
- Monitoring rate limit headers in responses

### Pagination

For large result sets, use the `limit` parameter:

```python
# Get first 100 issues
issues = await provider.list_issues(limit=100)

# For more, you'd need to implement cursor-based pagination
# (not yet implemented in current version)
```

## Error Handling

The provider raises exceptions for various error conditions:

```python
try:
    issue = await provider.get_issue("DEV-999")
except ValueError as e:
    print(f"Issue not found: {e}")
except Exception as e:
    print(f"API error: {e}")
```

Common errors:
- `ValueError`: Issue not found
- `ImportError`: HTTP library not available
- `Exception`: API errors (authentication, validation, etc.)

## Testing

The provider includes comprehensive tests. Run them with:

```bash
pytest tests/test_linear_provider.py -v
```

Test coverage includes:
- Rate limiting behavior
- Issue transformation
- CRUD operations
- Error handling
- HTTP client fallback
- GraphQL request/response handling

## Limitations

Current implementation limitations:
- Labels and assignees cannot be set during creation (requires ID lookups)
- No support for comments or attachments
- No support for sub-issues or parent issues
- Pagination is basic (cursor-based pagination not implemented)
- No support for custom fields

These limitations may be addressed in future versions.

## Advanced Configuration

### Custom Rate Limiting

```python
from worktree_flow.providers.linear import LinearRateLimiter

# Create provider with custom rate limit
provider = LinearIssueProvider(
    api_key="lin_api_...",
    team_id="team-uuid"
)

# Override rate limiter
provider.rate_limiter = LinearRateLimiter(requests_per_minute=30)
```

### Custom Timeout

The provider uses a 30-second timeout by default. This is configured in the HTTP client initialization.

## Troubleshooting

### "Either httpx or requests library is required"

Install one of the HTTP client libraries:

```bash
pip install httpx  # or pip install requests
```

### "team_id is required to create issues"

Set the team ID when initializing the provider:

```python
provider = LinearIssueProvider(
    api_key="lin_api_...",
    team_id="your-team-uuid"
)
```

### "Linear API error: ..."

Check:
1. API key is valid and not expired
2. API key has appropriate permissions
3. Team ID is correct (if specified)
4. Issue ID/identifier is valid

### Rate limit errors

The built-in rate limiter should prevent most rate limit issues. If you still encounter them:
1. Reduce `requests_per_minute` setting
2. Add delays between operations
3. Implement retry logic with exponential backoff

## Contributing

To extend the Linear provider:

1. Add new methods to `LinearIssueProvider`
2. Follow existing patterns for GraphQL queries
3. Add comprehensive tests
4. Update this documentation

## See Also

- [Linear API Documentation](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
- [Provider Base Classes](../src/worktree_flow/providers/base.py)
- [Provider Registry](../src/worktree_flow/providers/registry.py)
- [Issue Models](../src/worktree_flow/models/issue.py)
