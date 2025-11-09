"""Linear provider implementation."""

import json
from datetime import datetime
from typing import Optional, Any
import time

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    # Fallback to requests if httpx is not available
    try:
        import requests
        REQUESTS_AVAILABLE = True
    except ImportError:
        REQUESTS_AVAILABLE = False

from ..models import Issue, IssueCreate
from .base import IssueProvider


class LinearRateLimiter:
    """Simple rate limiter for Linear API."""
    
    def __init__(self, requests_per_minute: int = 50):
        self.requests_per_minute = requests_per_minute
        self.request_times: list[float] = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.requests_per_minute:
            # Wait until the oldest request is more than 1 minute old
            sleep_time = 60 - (now - self.request_times[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
                # Clean up again after waiting
                now = time.time()
                self.request_times = [t for t in self.request_times if now - t < 60]
        
        self.request_times.append(time.time())


class LinearIssueProvider(IssueProvider):
    """Linear issues provider using GraphQL API."""

    def __init__(self, api_key: str, team_id: Optional[str] = None):
        """Initialize Linear provider.
        
        Args:
            api_key: Linear API key
            team_id: Optional team ID to filter issues
        """
        if not HTTPX_AVAILABLE and not REQUESTS_AVAILABLE:
            raise ImportError("Either httpx or requests library is required for Linear provider")
        
        self.api_key = api_key
        self.team_id = team_id
        self.api_url = "https://api.linear.app/graphql"
        self.rate_limiter = LinearRateLimiter()
        
        # Use httpx if available, otherwise fall back to requests
        self.use_httpx = HTTPX_AVAILABLE
        if self.use_httpx:
            self.client = httpx.Client(
                headers={
                    "Authorization": f"{api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        else:
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"{api_key}",
                "Content-Type": "application/json",
            })

    def _make_request(self, query: str, variables: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Make GraphQL request to Linear API with rate limiting.
        
        Args:
            query: GraphQL query string
            variables: Optional variables for the query
            
        Returns:
            Response data dictionary
            
        Raises:
            Exception: If the request fails
        """
        self.rate_limiter.wait_if_needed()
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        if self.use_httpx:
            response = self.client.post(self.api_url, json=payload)
            response.raise_for_status()
            result = response.json()
        else:
            response = self.session.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
        
        if "errors" in result:
            errors = result["errors"]
            error_msg = "; ".join([e.get("message", str(e)) for e in errors])
            raise Exception(f"Linear API error: {error_msg}")
        
        return result.get("data", {})

    def _transform_linear_issue_to_internal(self, linear_issue: dict[str, Any]) -> Issue:
        """Transform Linear issue to internal Issue model.
        
        Args:
            linear_issue: Linear issue data from GraphQL
            
        Returns:
            Internal Issue model
        """
        # Extract state information
        state_name = "open"
        if linear_issue.get("state"):
            state_type = linear_issue["state"].get("type", "").lower()
            # Linear state types: "triage", "backlog", "unstarted", "started", "completed", "canceled"
            if state_type in ["completed", "canceled"]:
                state_name = "closed"
        
        # Extract assignee
        assignees = []
        if linear_issue.get("assignee"):
            assignee_name = linear_issue["assignee"].get("name") or linear_issue["assignee"].get("email", "")
            if assignee_name:
                assignees.append(assignee_name)
        
        # Extract labels
        labels = []
        if linear_issue.get("labels") and linear_issue["labels"].get("nodes"):
            labels = [label["name"] for label in linear_issue["labels"]["nodes"]]
        
        # Parse dates
        created_at = datetime.fromisoformat(linear_issue["createdAt"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(linear_issue["updatedAt"].replace("Z", "+00:00"))
        
        # Extract identifier number (e.g., "DEV-123" -> 123)
        identifier = linear_issue.get("identifier", "")
        try:
            number = int(identifier.split("-")[-1]) if "-" in identifier else int(linear_issue.get("number", 0))
        except (ValueError, TypeError):
            number = 0
        
        return Issue(
            id=linear_issue["id"],
            number=number,
            title=linear_issue["title"],
            body=linear_issue.get("description", ""),
            state=state_name,
            labels=labels,
            assignees=assignees,
            url=linear_issue["url"],
            created_at=created_at,
            updated_at=updated_at,
            metadata={
                "linear_identifier": identifier,
                "team_id": linear_issue.get("team", {}).get("id"),
                "team_key": linear_issue.get("team", {}).get("key"),
                "state_name": linear_issue.get("state", {}).get("name"),
                "state_type": linear_issue.get("state", {}).get("type"),
                "priority": linear_issue.get("priority"),
                "priority_label": linear_issue.get("priorityLabel"),
            },
        )

    async def get_issue(self, issue_id: str) -> Issue:
        """Get Linear issue by ID or identifier.
        
        Args:
            issue_id: Linear issue UUID or identifier (e.g., "DEV-123")
            
        Returns:
            Issue model
        """
        # Check if issue_id is an identifier (e.g., "DEV-123") or UUID
        if "-" in issue_id and not issue_id.count("-") >= 4:
            # Looks like an identifier (e.g., "DEV-123"), need to query by identifier
            query = """
            query GetIssueByIdentifier($identifier: String!) {
                issue(filter: { identifier: { eq: $identifier } }) {
                    id
                    identifier
                    title
                    description
                    url
                    state {
                        id
                        name
                        type
                    }
                    assignee {
                        id
                        name
                        email
                    }
                    labels {
                        nodes {
                            id
                            name
                        }
                    }
                    team {
                        id
                        key
                    }
                    priority
                    priorityLabel
                    number
                    createdAt
                    updatedAt
                }
            }
            """
            variables = {"identifier": issue_id}
        else:
            # Assume it's a UUID
            query = """
            query GetIssue($id: String!) {
                issue(id: $id) {
                    id
                    identifier
                    title
                    description
                    url
                    state {
                        id
                        name
                        type
                    }
                    assignee {
                        id
                        name
                        email
                    }
                    labels {
                        nodes {
                            id
                            name
                        }
                    }
                    team {
                        id
                        key
                    }
                    priority
                    priorityLabel
                    number
                    createdAt
                    updatedAt
                }
            }
            """
            variables = {"id": issue_id}
        
        data = self._make_request(query, variables)
        linear_issue = data.get("issue")
        
        if not linear_issue:
            raise ValueError(f"Issue not found: {issue_id}")
        
        return self._transform_linear_issue_to_internal(linear_issue)

    async def list_issues(
        self,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[Issue]:
        """List Linear issues.
        
        Args:
            state: Filter by state ("open", "closed")
            labels: Filter by labels
            limit: Maximum number of issues to return
            
        Returns:
            List of Issue models
        """
        # Build filter
        filters = []
        
        if self.team_id:
            filters.append(f'team: {{ id: {{ eq: "{self.team_id}" }} }}')
        
        if state:
            if state.lower() == "open":
                filters.append('state: { type: { nin: ["completed", "canceled"] } }')
            elif state.lower() == "closed":
                filters.append('state: { type: { in: ["completed", "canceled"] } }')
        
        if labels:
            # Linear uses label names for filtering
            label_filters = [f'{{ name: {{ eq: "{label}" }} }}' for label in labels]
            filters.append(f'labels: {{ some: {{ or: [{", ".join(label_filters)}] }} }}')
        
        filter_str = ", ".join(filters) if filters else ""
        
        query = f"""
        query ListIssues($first: Int!) {{
            issues(first: $first{', filter: { ' + filter_str + ' }' if filter_str else ''}) {{
                nodes {{
                    id
                    identifier
                    title
                    description
                    url
                    state {{
                        id
                        name
                        type
                    }}
                    assignee {{
                        id
                        name
                        email
                    }}
                    labels {{
                        nodes {{
                            id
                            name
                        }}
                    }}
                    team {{
                        id
                        key
                    }}
                    priority
                    priorityLabel
                    number
                    createdAt
                    updatedAt
                }}
            }}
        }}
        """
        
        variables = {"first": limit}
        data = self._make_request(query, variables)
        
        issues = data.get("issues", {}).get("nodes", [])
        return [self._transform_linear_issue_to_internal(issue) for issue in issues]

    async def create_issue(self, issue: IssueCreate) -> Issue:
        """Create Linear issue.
        
        Args:
            issue: Issue creation data
            
        Returns:
            Created Issue model
        """
        if not self.team_id:
            raise ValueError("team_id is required to create issues in Linear")
        
        # Build the input
        input_fields = [
            f'teamId: "{self.team_id}"',
            f'title: {json.dumps(issue.title)}',
        ]
        
        if issue.body:
            input_fields.append(f'description: {json.dumps(issue.body)}')
        
        # Note: Linear label and assignee handling requires looking up IDs
        # For simplicity, we'll create the issue without labels/assignees
        # A full implementation would query for label/user IDs first
        
        input_str = ", ".join(input_fields)
        
        query = f"""
        mutation CreateIssue {{
            issueCreate(input: {{ {input_str} }}) {{
                success
                issue {{
                    id
                    identifier
                    title
                    description
                    url
                    state {{
                        id
                        name
                        type
                    }}
                    assignee {{
                        id
                        name
                        email
                    }}
                    labels {{
                        nodes {{
                            id
                            name
                        }}
                    }}
                    team {{
                        id
                        key
                    }}
                    priority
                    priorityLabel
                    number
                    createdAt
                    updatedAt
                }}
            }}
        }}
        """
        
        data = self._make_request(query)
        result = data.get("issueCreate", {})
        
        if not result.get("success"):
            raise Exception("Failed to create issue in Linear")
        
        linear_issue = result.get("issue")
        if not linear_issue:
            raise Exception("No issue returned from Linear API")
        
        return self._transform_linear_issue_to_internal(linear_issue)

    async def update_issue(self, issue_id: str, **kwargs) -> Issue:
        """Update Linear issue.
        
        Args:
            issue_id: Linear issue UUID
            **kwargs: Fields to update (title, description, state, etc.)
            
        Returns:
            Updated Issue model
        """
        # Build update input
        input_fields = []
        
        if "title" in kwargs:
            input_fields.append(f'title: {json.dumps(kwargs["title"])}')
        
        if "body" in kwargs or "description" in kwargs:
            desc = kwargs.get("body") or kwargs.get("description")
            input_fields.append(f'description: {json.dumps(desc)}')
        
        # Note: Updating state, labels, assignees requires additional ID lookups
        # For a full implementation, we'd need to query for state/label/user IDs
        
        if not input_fields:
            # Nothing to update, just return current issue
            return await self.get_issue(issue_id)
        
        input_str = ", ".join(input_fields)
        
        query = f"""
        mutation UpdateIssue($id: String!) {{
            issueUpdate(id: $id, input: {{ {input_str} }}) {{
                success
                issue {{
                    id
                    identifier
                    title
                    description
                    url
                    state {{
                        id
                        name
                        type
                    }}
                    assignee {{
                        id
                        name
                        email
                    }}
                    labels {{
                        nodes {{
                            id
                            name
                        }}
                    }}
                    team {{
                        id
                        key
                    }}
                    priority
                    priorityLabel
                    number
                    createdAt
                    updatedAt
                }}
            }}
        }}
        """
        
        variables = {"id": issue_id}
        data = self._make_request(query, variables)
        result = data.get("issueUpdate", {})
        
        if not result.get("success"):
            raise Exception("Failed to update issue in Linear")
        
        linear_issue = result.get("issue")
        if not linear_issue:
            raise Exception("No issue returned from Linear API")
        
        return self._transform_linear_issue_to_internal(linear_issue)

    async def close_issue(self, issue_id: str) -> Issue:
        """Close Linear issue.
        
        Args:
            issue_id: Linear issue UUID
            
        Returns:
            Closed Issue model
        """
        # To close an issue in Linear, we need to set it to a "completed" or "canceled" state
        # This requires querying for a state with type "completed"
        # For simplicity, we'll use a mutation that completes the issue
        
        query = """
        query GetCompletedState($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                    }
                }
            }
        }
        """
        
        # First get the issue to find its team
        issue = await self.get_issue(issue_id)
        team_id = issue.metadata.get("team_id")
        
        if not team_id:
            raise ValueError("Could not determine team ID for issue")
        
        # Get completed state
        data = self._make_request(query, {"teamId": team_id})
        states = data.get("team", {}).get("states", {}).get("nodes", [])
        completed_state = next(
            (s for s in states if s.get("type") == "completed"),
            None
        )
        
        if not completed_state:
            raise Exception("Could not find completed state for team")
        
        # Update issue to completed state
        query = f"""
        mutation CloseIssue($id: String!, $stateId: String!) {{
            issueUpdate(id: $id, input: {{ stateId: $stateId }}) {{
                success
                issue {{
                    id
                    identifier
                    title
                    description
                    url
                    state {{
                        id
                        name
                        type
                    }}
                    assignee {{
                        id
                        name
                        email
                    }}
                    labels {{
                        nodes {{
                            id
                            name
                        }}
                    }}
                    team {{
                        id
                        key
                    }}
                    priority
                    priorityLabel
                    number
                    createdAt
                    updatedAt
                }}
            }}
        }}
        """
        
        variables = {"id": issue_id, "stateId": completed_state["id"]}
        data = self._make_request(query, variables)
        result = data.get("issueUpdate", {})
        
        if not result.get("success"):
            raise Exception("Failed to close issue in Linear")
        
        linear_issue = result.get("issue")
        if not linear_issue:
            raise Exception("No issue returned from Linear API")
        
        return self._transform_linear_issue_to_internal(linear_issue)

    def __del__(self):
        """Clean up HTTP client."""
        if self.use_httpx and hasattr(self, 'client'):
            self.client.close()
