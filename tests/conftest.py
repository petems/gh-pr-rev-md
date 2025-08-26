"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests that need file operations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_pr_comments():
    """Sample PR review comments data for testing."""
    return [
        {
            "id": 1,
            "user": {"login": "reviewer1"},
            "body": "This looks good, but consider adding error handling.",
            "created_at": "2023-01-01T10:00:00Z",
            "updated_at": "2023-01-01T10:00:00Z",
            "path": "src/main.py",
            "diff_hunk": "@@ -10,3 +10,4 @@ def main():\n     print('hello')\n+    return 0",
            "line": 12,
            "side": "RIGHT",
        },
        {
            "id": 2,
            "user": {"login": "reviewer2"},
            "body": "Could we use a more descriptive variable name here?",
            "created_at": "2023-01-01T11:30:00Z",
            "updated_at": "2023-01-01T11:30:00Z",
            "path": "src/utils.py",
            "diff_hunk": "@@ -5,2 +5,3 @@ def helper():\n     x = 1\n+    y = 2",
            "line": 7,
            "side": "RIGHT",
        },
    ]


@pytest.fixture
def empty_pr_comments():
    """Empty PR review comments for testing no-comments scenarios."""
    return []
