"""FastAPI endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from worktree_flow.api.app import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Worktree Flow API"
    assert "version" in data


def test_health():
    """Test health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_docs_available():
    """Test OpenAPI docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_available():
    """Test ReDoc is available."""
    response = client.get("/redoc")
    assert response.status_code == 200
