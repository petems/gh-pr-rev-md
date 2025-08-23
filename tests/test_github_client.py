"""Tests for GitHub API client functionality."""

import pytest
from unittest import mock

from gh_pr_rev_md.github_client import GitHubClient, GitHubAPIError


@pytest.fixture
def github_client():
    """Create a GitHubClient instance for testing."""
    return GitHubClient("test_token")


def mock_graphql_response(threads):
    """Helper to create a mock GraphQL response."""
    return {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": threads,
                    }
                }
            }
        }
    }


def _comment_node(comment_id, body, position=1):
    """Helper to create a comment node for the mock response."""
    return {
        "id": comment_id,
        "author": {"login": "testuser"},
        "body": body,
        "createdAt": "2023-01-01T10:00:00Z",
        "updatedAt": "2023-01-01T10:00:00Z",
        "path": "file.py",
        "diffHunk": "...",
        "position": position,
        "url": "...",
        "line": 10,
    }


@mock.patch("requests.Session.post")
def test_get_pr_review_comments_success(mock_post, github_client):
    """Test successful retrieval of PR review comments with GraphQL."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_graphql_response(
        [
            {
                "isResolved": False,
                "comments": {"nodes": [_comment_node("1", "Comment 1")]},
            }
        ]
    )

    comments = github_client.get_pr_review_comments("owner", "repo", 123)
    assert len(comments) == 1
    assert comments[0]["body"] == "Comment 1"
    mock_post.assert_called_once()


@mock.patch("requests.Session.post")
def test_filter_resolved_comments(mock_post, github_client):
    """Test that resolved comments are filtered by default."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_graphql_response(
        [
            {
                "isResolved": True,
                "comments": {"nodes": [_comment_node("1", "Resolved")]},
            },
            {
                "isResolved": False,
                "comments": {"nodes": [_comment_node("2", "Not Resolved")]},
            },
        ]
    )

    comments = github_client.get_pr_review_comments("owner", "repo", 123)
    assert len(comments) == 1
    assert comments[0]["body"] == "Not Resolved"


@mock.patch("requests.Session.post")
def test_include_resolved_comments(mock_post, github_client):
    """Test that resolved comments are included when requested."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_graphql_response(
        [
            {
                "isResolved": True,
                "comments": {"nodes": [_comment_node("1", "Resolved")]},
            },
            {
                "isResolved": False,
                "comments": {"nodes": [_comment_node("2", "Not Resolved")]},
            },
        ]
    )

    comments = github_client.get_pr_review_comments(
        "owner", "repo", 123, include_resolved=True
    )
    assert len(comments) == 2


@mock.patch("requests.Session.post")
def test_filter_outdated_comments(mock_post, github_client):
    """Test that outdated comments are filtered by default."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_graphql_response(
        [
            {
                "isResolved": False,
                "comments": {
                    "nodes": [
                        _comment_node("1", "Outdated", position=None),
                        _comment_node("2", "Current", position=1),
                    ]
                },
            }
        ]
    )

    comments = github_client.get_pr_review_comments("owner", "repo", 123)
    assert len(comments) == 1
    assert comments[0]["body"] == "Current"


@mock.patch("requests.Session.post")
def test_include_outdated_comments(mock_post, github_client):
    """Test that outdated comments are included when requested."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_graphql_response(
        [
            {
                "isResolved": False,
                "comments": {
                    "nodes": [
                        _comment_node("1", "Outdated", position=None),
                        _comment_node("2", "Current", position=1),
                    ]
                },
            }
        ]
    )

    comments = github_client.get_pr_review_comments(
        "owner", "repo", 123, include_outdated=True
    )
    assert len(comments) == 2


@mock.patch("requests.Session.post")
def test_graphql_api_error(mock_post, github_client):
    """Test handling of GraphQL API errors."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"errors": "Something went wrong"}

    with pytest.raises(GitHubAPIError) as exc_info:
        github_client.get_pr_review_comments("owner", "repo", 123)
    assert "GitHub GraphQL API error" in str(exc_info.value)


@mock.patch("requests.Session.post")
def test_http_error(mock_post, github_client):
    """Test handling of HTTP errors."""
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "Server Error"

    with pytest.raises(GitHubAPIError) as exc_info:
        github_client.get_pr_review_comments("owner", "repo", 123)
    assert "GitHub API error: 500" in str(exc_info.value)
