# Linear Provider Implementation

This implementation adds full Linear integration to the worktree-flow project.

## What's New

### Files Created
- **`src/worktree_flow/providers/linear.py`** - Complete Linear provider implementation (621 lines)
- **`tests/test_linear_provider.py`** - Comprehensive test suite (447 lines, 17 test cases)
- **`docs/linear_provider.md`** - Full documentation (330 lines)

### Files Modified
- **`src/worktree_flow/providers/registry.py`** - Registered Linear provider
- **`src/worktree_flow/providers/__init__.py`** - Exported Linear provider

## Features

### Core Functionality
- ✅ Full IssueProvider interface implementation
- ✅ GraphQL API integration with Linear
- ✅ Dual HTTP client support (httpx/requests)
- ✅ Built-in rate limiting (50 req/min default)
- ✅ Smart issue ID handling (identifiers like DEV-123 or UUIDs)

### Operations Supported
1. **get_issue(issue_id)** - Retrieve by identifier or UUID
2. **list_issues(state, labels, limit)** - List with filters
3. **create_issue(issue)** - Create new issues
4. **update_issue(issue_id, **kwargs)** - Update existing issues
5. **close_issue(issue_id)** - Close/complete issues

### Rate Limiting
- Automatic rate limiting to prevent API throttling
- Configurable requests per minute (default: 50)
- Transparent waiting mechanism

### Model Transformation
- Converts Linear GraphQL responses to internal Issue models
- Preserves Linear-specific metadata:
  - linear_identifier (e.g., "DEV-123")
  - team_id and team_key
  - state_name and state_type
  - priority and priority_label
- Proper state mapping (open/closed)

## Quick Start

### Configuration

Set environment variables:
```bash
export WORKTREE_LINEAR_API_KEY="lin_api_..."
export WORKTREE_LINEAR_TEAM_ID="team-uuid"  # Optional
```

### Usage

```python
from worktree_flow.providers import LinearIssueProvider

provider = LinearIssueProvider(
    api_key="lin_api_...",
    team_id="team-uuid"
)

# Get issue by identifier
issue = await provider.get_issue("DEV-123")
print(f"{issue.title}: {issue.state}")
```

### CLI Usage

```bash
# Create worktree from Linear issue
worktree create issue DEV-123 --provider linear
```

## Testing

Run the comprehensive test suite:
```bash
pytest tests/test_linear_provider.py -v
```

**Test Coverage:**
- ✅ Rate limiting behavior
- ✅ Provider initialization
- ✅ Issue transformation
- ✅ All CRUD operations
- ✅ Error handling
- ✅ HTTP client fallback

## Documentation

See [docs/linear_provider.md](docs/linear_provider.md) for:
- Detailed configuration guide
- Complete API reference
- Usage examples
- Troubleshooting tips
- Advanced configuration

## Security

- ✅ CodeQL scan passed (0 alerts)
- ✅ No vulnerabilities detected
- ✅ Secure API key handling
- ✅ Safe error messages

## Architecture

The Linear provider follows the same pattern as the GitHub provider:

```
LinearIssueProvider (implements IssueProvider)
    ├── _make_request() - GraphQL API calls with rate limiting
    ├── _transform_linear_issue_to_internal() - Model transformation
    ├── get_issue() - Retrieve by ID
    ├── list_issues() - List with filters
    ├── create_issue() - Create new
    ├── update_issue() - Update existing
    └── close_issue() - Close/complete
```

## Known Limitations

- Labels and assignees cannot be set during creation (requires ID lookups)
- No support for comments or attachments
- No support for sub-issues or parent issues
- Basic pagination (cursor-based not implemented)
- No custom fields support

These may be addressed in future versions.

## Integration

The Linear provider is fully integrated with the worktree-flow system:

1. **Provider Registry** - Registered as `ProviderType.LINEAR`
2. **Configuration** - Supports `linear_api_key` and `linear_team_id` settings
3. **CLI** - Works with `--provider linear` flag
4. **API** - Available through REST API endpoints
5. **MCP** - Accessible via MCP server

## Contributing

To extend the Linear provider:
1. Add new methods to `LinearIssueProvider`
2. Follow GraphQL query patterns
3. Add comprehensive tests
4. Update documentation

## Resources

- [Linear API Documentation](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
- [GraphQL Explorer](https://studio.apollographql.com/public/Linear-API/variant/current/home)
- [Linear Python SDK](https://github.com/linear/linear-sdk) (not used, but good reference)

## Support

For issues or questions:
1. Check [docs/linear_provider.md](docs/linear_provider.md) troubleshooting section
2. Review test examples in `tests/test_linear_provider.py`
3. Open an issue on GitHub
