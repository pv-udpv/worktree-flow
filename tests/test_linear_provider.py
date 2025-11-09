"""Tests for Linear provider."""

import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest

from worktree_flow.models import Issue, IssueCreate
from worktree_flow.providers.linear import LinearIssueProvider, LinearRateLimiter


class TestLinearRateLimiter:
    """Tests for LinearRateLimiter."""
    
    def test_rate_limiter_allows_requests_under_limit(self):
        """Test that rate limiter allows requests under the limit."""
        limiter = LinearRateLimiter(requests_per_minute=10)
        
        # Should not block for requests under limit
        for _ in range(5):
            limiter.wait_if_needed()
        
        assert len(limiter.request_times) == 5
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = LinearRateLimiter(requests_per_minute=50)
        assert limiter.requests_per_minute == 50
        assert limiter.request_times == []


class TestLinearIssueProvider:
    """Tests for LinearIssueProvider."""
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client."""
        with patch('worktree_flow.providers.linear.HTTPX_AVAILABLE', True), \
             patch('worktree_flow.providers.linear.httpx.Client') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_requests_session(self):
        """Mock requests session."""
        with patch('worktree_flow.providers.linear.HTTPX_AVAILABLE', False), \
             patch('worktree_flow.providers.linear.REQUESTS_AVAILABLE', True), \
             patch('worktree_flow.providers.linear.requests.Session') as mock_session:
            mock_instance = Mock()
            mock_session.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def linear_issue_data(self):
        """Sample Linear issue data."""
        return {
            "id": "abc-123-def-456",
            "identifier": "DEV-42",
            "title": "Test Issue",
            "description": "Test description",
            "url": "https://linear.app/team/issue/DEV-42",
            "number": 42,
            "state": {
                "id": "state-1",
                "name": "In Progress",
                "type": "started"
            },
            "assignee": {
                "id": "user-1",
                "name": "John Doe",
                "email": "john@example.com"
            },
            "labels": {
                "nodes": [
                    {"id": "label-1", "name": "bug"},
                    {"id": "label-2", "name": "urgent"}
                ]
            },
            "team": {
                "id": "team-1",
                "key": "DEV"
            },
            "priority": 1,
            "priorityLabel": "High",
            "createdAt": "2024-01-01T10:00:00.000Z",
            "updatedAt": "2024-01-02T15:30:00.000Z"
        }
    
    def test_provider_initialization_with_httpx(self, mock_httpx_client):
        """Test provider initialization with httpx."""
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        assert provider.api_key == "test-key"
        assert provider.team_id == "team-123"
        assert provider.api_url == "https://api.linear.app/graphql"
        assert provider.use_httpx is True
    
    def test_provider_initialization_without_http_library(self):
        """Test provider initialization fails without http library."""
        with patch('worktree_flow.providers.linear.HTTPX_AVAILABLE', False), \
             patch('worktree_flow.providers.linear.REQUESTS_AVAILABLE', False):
            with pytest.raises(ImportError, match="Either httpx or requests library is required"):
                LinearIssueProvider(api_key="test-key")
    
    def test_transform_linear_issue_to_internal(self, mock_httpx_client, linear_issue_data):
        """Test transformation of Linear issue to internal model."""
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issue = provider._transform_linear_issue_to_internal(linear_issue_data)
        
        assert isinstance(issue, Issue)
        assert issue.id == "abc-123-def-456"
        assert issue.number == 42
        assert issue.title == "Test Issue"
        assert issue.body == "Test description"
        assert issue.state == "open"
        assert issue.labels == ["bug", "urgent"]
        assert issue.assignees == ["John Doe"]
        assert issue.url == "https://linear.app/team/issue/DEV-42"
        assert issue.metadata["linear_identifier"] == "DEV-42"
        assert issue.metadata["team_id"] == "team-1"
        assert issue.metadata["team_key"] == "DEV"
        assert issue.metadata["state_name"] == "In Progress"
        assert issue.metadata["priority"] == 1
    
    def test_transform_completed_issue(self, mock_httpx_client, linear_issue_data):
        """Test transformation of completed Linear issue."""
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        linear_issue_data["state"]["type"] = "completed"
        issue = provider._transform_linear_issue_to_internal(linear_issue_data)
        
        assert issue.state == "closed"
    
    def test_transform_canceled_issue(self, mock_httpx_client, linear_issue_data):
        """Test transformation of canceled Linear issue."""
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        linear_issue_data["state"]["type"] = "canceled"
        issue = provider._transform_linear_issue_to_internal(linear_issue_data)
        
        assert issue.state == "closed"
    
    def test_make_request_with_httpx(self, mock_httpx_client, linear_issue_data):
        """Test making a GraphQL request with httpx."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"issue": linear_issue_data}}
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        result = provider._make_request("query { test }")
        
        assert "issue" in result
        assert result["issue"]["identifier"] == "DEV-42"
        mock_httpx_client.post.assert_called_once()
    
    def test_make_request_handles_errors(self, mock_httpx_client):
        """Test error handling in GraphQL requests."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "errors": [
                {"message": "Invalid query"},
                {"message": "Authentication failed"}
            ]
        }
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        with pytest.raises(Exception, match="Linear API error: Invalid query; Authentication failed"):
            provider._make_request("query { test }")
    
    @pytest.mark.asyncio
    async def test_get_issue_by_identifier(self, mock_httpx_client, linear_issue_data):
        """Test getting issue by identifier."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"issue": linear_issue_data}}
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issue = await provider.get_issue("DEV-42")
        
        assert isinstance(issue, Issue)
        assert issue.number == 42
        assert issue.title == "Test Issue"
    
    @pytest.mark.asyncio
    async def test_get_issue_by_uuid(self, mock_httpx_client, linear_issue_data):
        """Test getting issue by UUID."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"issue": linear_issue_data}}
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issue = await provider.get_issue("abc-123-def-456-789")
        
        assert isinstance(issue, Issue)
        assert issue.id == "abc-123-def-456"
    
    @pytest.mark.asyncio
    async def test_get_issue_not_found(self, mock_httpx_client):
        """Test getting non-existent issue."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"issue": None}}
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        with pytest.raises(ValueError, match="Issue not found"):
            await provider.get_issue("DEV-999")
    
    @pytest.mark.asyncio
    async def test_list_issues(self, mock_httpx_client, linear_issue_data):
        """Test listing issues."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "issues": {
                    "nodes": [linear_issue_data]
                }
            }
        }
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issues = await provider.list_issues(limit=10)
        
        assert len(issues) == 1
        assert issues[0].number == 42
    
    @pytest.mark.asyncio
    async def test_list_issues_with_filters(self, mock_httpx_client, linear_issue_data):
        """Test listing issues with state and label filters."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "issues": {
                    "nodes": [linear_issue_data]
                }
            }
        }
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issues = await provider.list_issues(state="open", labels=["bug"], limit=20)
        
        assert len(issues) == 1
        assert issues[0].labels == ["bug", "urgent"]
    
    @pytest.mark.asyncio
    async def test_create_issue(self, mock_httpx_client, linear_issue_data):
        """Test creating an issue."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": linear_issue_data
                }
            }
        }
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issue_create = IssueCreate(
            title="New Issue",
            body="Issue description",
            labels=["feature"]
        )
        
        issue = await provider.create_issue(issue_create)
        
        assert isinstance(issue, Issue)
        assert issue.title == "Test Issue"
    
    @pytest.mark.asyncio
    async def test_create_issue_without_team_id(self, mock_httpx_client):
        """Test creating issue fails without team_id."""
        provider = LinearIssueProvider(api_key="test-key")
        
        issue_create = IssueCreate(title="New Issue")
        
        with pytest.raises(ValueError, match="team_id is required"):
            await provider.create_issue(issue_create)
    
    @pytest.mark.asyncio
    async def test_create_issue_failure(self, mock_httpx_client):
        """Test handling create issue failure."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": False
                }
            }
        }
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issue_create = IssueCreate(title="New Issue")
        
        with pytest.raises(Exception, match="Failed to create issue"):
            await provider.create_issue(issue_create)
    
    @pytest.mark.asyncio
    async def test_update_issue(self, mock_httpx_client, linear_issue_data):
        """Test updating an issue."""
        mock_response = Mock()
        updated_data = linear_issue_data.copy()
        updated_data["title"] = "Updated Title"
        mock_response.json.return_value = {
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": updated_data
                }
            }
        }
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issue = await provider.update_issue("abc-123", title="Updated Title")
        
        assert issue.title == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_update_issue_no_changes(self, mock_httpx_client, linear_issue_data):
        """Test updating issue with no changes returns current issue."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"issue": linear_issue_data}}
        mock_httpx_client.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issue = await provider.update_issue("abc-123")
        
        assert issue.title == "Test Issue"
    
    @pytest.mark.asyncio
    async def test_close_issue(self, mock_httpx_client, linear_issue_data):
        """Test closing an issue."""
        # Mock responses for get_issue, get states, and update
        get_response = Mock()
        get_response.json.return_value = {"data": {"issue": linear_issue_data}}
        
        states_response = Mock()
        states_response.json.return_value = {
            "data": {
                "team": {
                    "states": {
                        "nodes": [
                            {"id": "state-completed", "name": "Done", "type": "completed"}
                        ]
                    }
                }
            }
        }
        
        closed_data = linear_issue_data.copy()
        closed_data["state"] = {"id": "state-completed", "name": "Done", "type": "completed"}
        update_response = Mock()
        update_response.json.return_value = {
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": closed_data
                }
            }
        }
        
        mock_httpx_client.post.side_effect = [get_response, states_response, update_response]
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        issue = await provider.close_issue("abc-123")
        
        assert issue.state == "closed"
    
    @pytest.mark.asyncio
    async def test_close_issue_no_completed_state(self, mock_httpx_client, linear_issue_data):
        """Test closing issue when no completed state exists."""
        get_response = Mock()
        get_response.json.return_value = {"data": {"issue": linear_issue_data}}
        
        states_response = Mock()
        states_response.json.return_value = {
            "data": {
                "team": {
                    "states": {
                        "nodes": [
                            {"id": "state-1", "name": "Todo", "type": "unstarted"}
                        ]
                    }
                }
            }
        }
        
        mock_httpx_client.post.side_effect = [get_response, states_response]
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        with pytest.raises(Exception, match="Could not find completed state"):
            await provider.close_issue("abc-123")


class TestLinearProviderWithRequests:
    """Tests for Linear provider using requests library."""
    
    @pytest.fixture
    def mock_requests_session(self):
        """Mock requests session."""
        with patch('worktree_flow.providers.linear.HTTPX_AVAILABLE', False), \
             patch('worktree_flow.providers.linear.REQUESTS_AVAILABLE', True), \
             patch('worktree_flow.providers.linear.requests.Session') as mock_session_class:
            mock_instance = Mock()
            mock_instance.headers = {}
            mock_session_class.return_value = mock_instance
            yield mock_instance
    
    def test_provider_uses_requests_fallback(self, mock_requests_session):
        """Test that provider falls back to requests when httpx is unavailable."""
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        assert provider.use_httpx is False
        assert hasattr(provider, 'session')
    
    def test_make_request_with_requests(self, mock_requests_session):
        """Test making a GraphQL request with requests library."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_requests_session.post.return_value = mock_response
        
        provider = LinearIssueProvider(api_key="test-key", team_id="team-123")
        
        result = provider._make_request("query { test }")
        
        assert result == {"test": "value"}
        mock_requests_session.post.assert_called_once()
