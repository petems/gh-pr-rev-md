"""Tests for GitHub API client functionality."""

import pytest
from unittest import mock
import requests

from gh_pr_rev_md.github_client import GitHubAPIError, GitHubClient


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


def _resp(status_code=200, json_body=None, text=""):
    m = mock.MagicMock()
    m.status_code = status_code
    if json_body is None:
        json_body = {}
    m.json.return_value = json_body
    m.text = text
    return m


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


@mock.patch("requests.Session.post")
def test_retries_then_success(mock_post):
    """Client retries on transient 5xx then succeeds."""
    threads = [
        {
            "isResolved": False,
            "comments": {
                "nodes": [
                    {
                        "id": "1",
                        "author": {"login": "u"},
                        "body": "ok",
                        "createdAt": "2023-01-01T00:00:00Z",
                        "updatedAt": "2023-01-01T00:00:00Z",
                        "path": "f",
                        "diffHunk": "",
                        "position": 1,
                        "url": "u",
                        "line": 1,
                    }
                ]
            },
        }
    ]
    ok_json = mock_graphql_response(threads)
    mock_post.side_effect = [
        _resp(500, text="Server Error"),
        _resp(502, text="Bad Gateway"),
        _resp(200, ok_json),
    ]

    client = GitHubClient("t", max_retries=3, backoff_factor=0)
    comments = client.get_pr_review_comments("owner", "repo", 1)
    assert len(comments) == 1
    assert mock_post.call_count == 3


@mock.patch("requests.Session.post")
def test_retries_exhaust_then_error(mock_post):
    """Client raises after exhausting retries."""
    mock_post.side_effect = [
        _resp(500, text="Server Error"),
        _resp(503, text="Service Unavailable"),
        _resp(504, text="Gateway Timeout"),
    ]

    client = GitHubClient("t", max_retries=3, backoff_factor=0)
    with pytest.raises(GitHubAPIError):
        client.get_pr_review_comments("owner", "repo", 1)


@mock.patch("requests.Session.post")
def test_retries_on_exception_then_success(mock_post):
    """Client retries on transient exceptions then succeeds."""
    threads = [
        {
            "isResolved": False,
            "comments": {
                "nodes": [
                    {
                        "id": "1",
                        "author": {"login": "u"},
                        "body": "ok",
                        "createdAt": "2023-01-01T00:00:00Z",
                        "updatedAt": "2023-01-01T00:00:00Z",
                        "path": "f",
                        "diffHunk": "",
                        "position": 1,
                        "url": "u",
                        "line": 1,
                    }
                ]
            },
        }
    ]
    ok_json = mock_graphql_response(threads)
    mock_post.side_effect = [
        requests.Timeout("Timed out"),
        requests.ConnectionError("Connection failed"),
        _resp(200, ok_json),
    ]

    client = GitHubClient("t", max_retries=3, backoff_factor=0)
    comments = client.get_pr_review_comments("owner", "repo", 1)
    assert len(comments) == 1
    assert mock_post.call_count == 3


@mock.patch("requests.Session.post")
def test_retries_on_exception_exhaust_then_error(mock_post):
    """Client raises after exhausting retries on exceptions."""
    mock_post.side_effect = [
        requests.Timeout("Timed out"),
        requests.ConnectionError("Connection failed"),
        requests.Timeout("Timed out again"),
    ]

    client = GitHubClient("t", max_retries=3, backoff_factor=0)
    with pytest.raises(GitHubAPIError) as exc_info:
        client.get_pr_review_comments("owner", "repo", 1)
    assert "Request failed after 3 retries" in str(exc_info.value)
    assert mock_post.call_count == 3


# --- Tests for find_pr_by_branch method ---


@mock.patch("requests.Session.post")
def test_find_pr_by_branch_success(mock_post, github_client):
    """Test successful finding of PR by branch name."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {
                            "number": 123,
                            "headRefName": "feature-branch",
                            "state": "OPEN",
                        },
                        {
                            "number": 456,
                            "headRefName": "another-branch",
                            "state": "OPEN",
                        },
                    ]
                }
            }
        }
    }

    pr_number = github_client.find_pr_by_branch("owner", "repo", "feature-branch")
    assert pr_number == 123


@mock.patch("requests.Session.post")
def test_find_pr_by_branch_no_match(mock_post, github_client):
    """Test finding PR by branch name when no matching PR exists."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {
                            "number": 123,
                            "headRefName": "different-branch",
                            "state": "OPEN",
                        },
                    ]
                }
            }
        }
    }

    pr_number = github_client.find_pr_by_branch("owner", "repo", "feature-branch")
    assert pr_number is None


@mock.patch("requests.Session.post")
def test_get_pr_review_comments_pr_not_found(mock_post, github_client):
    """PR absence triggers a specific API error."""

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {"repository": {"pullRequest": None}}
    }

    with pytest.raises(GitHubAPIError):
        github_client.get_pr_review_comments("o", "r", 1)


@mock.patch("requests.Session.post")
def test_get_pr_review_comments_thread_pagination(mock_post, github_client):
    """Thread pagination is followed using cursors."""

    def make_response(data):
        resp = mock.Mock()
        resp.status_code = 200
        resp.json.return_value = data
        return resp

    first_page = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": True, "endCursor": "t1"},
                        "nodes": [],
                    }
                }
            }
        }
    }

    second_page = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [],
                    }
                }
            }
        }
    }

    mock_post.side_effect = [make_response(first_page), make_response(second_page)]

    comments = github_client.get_pr_review_comments("o", "r", 1)
    assert comments == []
    assert mock_post.call_count == 2


def test_get_all_thread_comments_paginates(monkeypatch, github_client):
    """_get_all_thread_comments should request additional pages when needed."""

    thread = {
        "id": "T1",
        "isResolved": False,
        "comments": {
            "nodes": [],
            "pageInfo": {"hasNextPage": True, "endCursor": "C1"},
        },
    }

    monkeypatch.setattr(
        github_client,
        "_get_additional_thread_comments",
        lambda thread_id, cursor, include_outdated: [
            {
                "id": "c2",
                "user": {"login": "u"},
                "body": "b",
                "created_at": "0",
                "updated_at": "0",
                "path": "p",
                "diff_hunk": "h",
                "line": 1,
                "position": 1,
                "html_url": "u",
                "side": "RIGHT",
            }
        ],
    )

    comments = github_client._get_all_thread_comments(
        thread, "o", "r", 1, include_outdated=True
    )
    assert len(comments) == 1


@mock.patch("requests.Session.post")
def test_get_additional_thread_comments_pagination_and_filter(mock_post, github_client):
    """Additional comments pagination continues until complete and filters outdated."""

    def make_response(data):
        resp = mock.Mock()
        resp.status_code = 200
        resp.json.return_value = data
        return resp

    first = {
        "data": {
            "node": {
                "comments": {
                    "pageInfo": {"hasNextPage": True, "endCursor": "C2"},
                    "nodes": [
                        {
                            "id": "c1",
                            "author": {"login": "u"},
                            "body": "old",
                            "createdAt": "0",
                            "updatedAt": "0",
                            "path": "p",
                            "diffHunk": "h",
                            "position": None,
                            "url": "u",
                            "line": 1,
                        }
                    ],
                }
            }
        }
    }

    second = {
        "data": {
            "node": {
                "comments": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "c2",
                            "author": {"login": "u"},
                            "body": "new",
                            "createdAt": "0",
                            "updatedAt": "0",
                            "path": "p",
                            "diffHunk": "h",
                            "position": 1,
                            "url": "u",
                            "line": 1,
                        }
                    ],
                }
            }
        }
    }

    mock_post.side_effect = [make_response(first), make_response(second)]

    comments = github_client._get_additional_thread_comments("T1", "C1", False)
    assert len(comments) == 1


@mock.patch("requests.Session.post")
def test_get_additional_thread_comments_http_error(mock_post, github_client):
    """HTTP errors in pagination raise GitHubAPIError."""

    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "boom"

    with pytest.raises(GitHubAPIError):
        github_client._get_additional_thread_comments("T1", "C1", True)


@mock.patch("requests.Session.post")
def test_get_additional_thread_comments_graphql_error(mock_post, github_client):
    """GraphQL errors in pagination raise GitHubAPIError."""

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"errors": "nope"}

    with pytest.raises(GitHubAPIError):
        github_client._get_additional_thread_comments("T1", "C1", True)


@mock.patch("requests.Session.post")
def test_find_pr_by_branch_closed_pr(mock_post, github_client):
    """Test finding PR by branch name ignores closed PRs."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {
                            "number": 123,
                            "headRefName": "feature-branch",
                            "state": "CLOSED",
                        },
                    ]
                }
            }
        }
    }

    pr_number = github_client.find_pr_by_branch("owner", "repo", "feature-branch")
    assert pr_number is None


@mock.patch("requests.Session.post")
def test_find_pr_by_branch_multiple_matches(mock_post, github_client):
    """Test finding PR by branch name returns first match when multiple exist."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {
                            "number": 123,
                            "headRefName": "feature-branch",
                            "state": "OPEN",
                        },
                        {
                            "number": 456,
                            "headRefName": "feature-branch",
                            "state": "OPEN",
                        },
                    ]
                }
            }
        }
    }

    pr_number = github_client.find_pr_by_branch("owner", "repo", "feature-branch")
    assert pr_number == 123  # Should return the first match


@mock.patch("requests.Session.post")
def test_find_pr_by_branch_api_error(mock_post, github_client):
    """Test handling of API errors in find_pr_by_branch."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"errors": "Something went wrong"}

    with pytest.raises(GitHubAPIError) as exc_info:
        github_client.find_pr_by_branch("owner", "repo", "feature-branch")
    assert "GitHub GraphQL API error" in str(exc_info.value)


@mock.patch("requests.Session.post")
def test_find_pr_by_branch_http_error(mock_post, github_client):
    """Test handling of HTTP errors in find_pr_by_branch."""
    mock_post.return_value.status_code = 403
    mock_post.return_value.text = "Forbidden"

    with pytest.raises(GitHubAPIError) as exc_info:
        github_client.find_pr_by_branch("owner", "repo", "feature-branch")
    assert "GitHub API error: 403" in str(exc_info.value)


@mock.patch("requests.Session.post")
def test_find_pr_by_branch_empty_response(mock_post, github_client):
    """Test finding PR by branch name with empty response."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": {"repository": {"pullRequests": {"nodes": []}}}
    }

    pr_number = github_client.find_pr_by_branch("owner", "repo", "feature-branch")
    assert pr_number is None