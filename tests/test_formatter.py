"""Tests for markdown formatting functionality."""

from gh_pr_rev_md.formatter import format_comments_as_markdown, format_timestamp


def test_format_timestamp_valid():
    """Test formatting of valid ISO timestamps."""
    test_cases = [
        ("2023-01-01T10:00:00Z", "2023-01-01 10:00:00 UTC"),
        ("2023-12-25T23:59:59Z", "2023-12-25 23:59:59 UTC"),
        ("2023-06-15T12:30:45Z", "2023-06-15 12:30:45 UTC"),
        ("2023-01-01T00:00:00Z", "2023-01-01 00:00:00 UTC"),
    ]

    for input_timestamp, expected_output in test_cases:
        result = format_timestamp(input_timestamp)
        assert result == expected_output


def test_format_timestamp_edge_cases():
    """Test formatting of edge case timestamps."""
    # Empty string
    assert format_timestamp("") == "Unknown"

    # Invalid format should return original string
    assert format_timestamp("invalid-timestamp") == "invalid-timestamp"
    assert format_timestamp("2023-13-45") == "2023-13-45"

    # None should return "Unknown"
    assert format_timestamp(None) == "Unknown"


def test_format_comments_as_markdown_empty_list():
    """Test formatting when no comments are provided."""
    result = format_comments_as_markdown([], "owner", "repo", 123)

    assert "# owner/repo - PR #123 Review Comments" in result
    assert "No review comments found for this pull request." in result


def test_format_comments_as_markdown_single_comment(sample_pr_comments):
    """Test formatting of a single comment."""
    single_comment = [sample_pr_comments[0]]
    result = format_comments_as_markdown(single_comment, "owner", "repo", 123)

    # Check header information
    assert "# owner/repo - PR #123 Review Comments" in result
    assert "**Repository:** owner/repo" in result
    assert "**Pull Request:** https://github.com/owner/repo/pull/123" in result
    assert "**Total Comments:** 1" in result

    # Check comment details
    assert "## Comment #1" in result
    assert "**Author:** @reviewer1" in result
    assert "**File:** `src/main.py`" in result
    assert "**Line:** 12" in result
    assert "**Created:** 2023-01-01 10:00:00 UTC" in result
    assert "This looks good, but consider adding error handling." in result

    # Check code context
    assert "### Code Context" in result
    assert "```diff" in result
    assert "@@ -10,3 +10,4 @@ def main():" in result


def test_format_comments_as_markdown_multiple_comments(sample_pr_comments):
    """Test formatting of multiple comments."""
    result = format_comments_as_markdown(sample_pr_comments, "microsoft", "vscode", 999)

    # Check header shows correct count
    assert "**Total Comments:** 2" in result

    # Check both comments are present
    assert "## Comment #1" in result
    assert "## Comment #2" in result
    assert "@reviewer1" in result
    assert "@reviewer2" in result
    assert "src/main.py" in result
    assert "src/utils.py" in result


def test_format_comments_as_markdown_updated_timestamp(sample_pr_comments):
    """Test that updated timestamp is shown when different from created."""
    # Modify a comment to have different updated timestamp
    comment_with_update = sample_pr_comments[0].copy()
    comment_with_update["updated_at"] = "2023-01-01T15:30:00Z"

    result = format_comments_as_markdown([comment_with_update], "owner", "repo", 123)

    assert "**Created:** 2023-01-01 10:00:00 UTC" in result
    assert "**Updated:** 2023-01-01 15:30:00 UTC" in result


def test_format_comments_as_markdown_missing_fields():
    """Test formatting when comment has missing or None fields."""
    incomplete_comment = {
        "id": 1,
        "user": {},  # Missing login
        "body": "Comment text",
        "created_at": "",  # Empty timestamp
        "updated_at": "",
        "path": None,  # Missing path
        "diff_hunk": "",  # Empty diff
        "line": None,  # Missing line
    }

    result = format_comments_as_markdown([incomplete_comment], "owner", "repo", 123)

    # Should handle missing fields gracefully
    assert "**Author:** @Unknown" in result
    assert "**File:** `None`" in result  # None becomes "None" in f-string
    assert "**Line:** Unknown" in result
    assert "**Created:** Unknown" in result
    # Updated timestamp should not appear when same as created
    assert "**Updated:**" not in result


def test_format_comments_as_markdown_unicode_content():
    """Test formatting with unicode characters in comments."""
    unicode_comment = {
        "id": 1,
        "user": {"login": "developer"},
        "body": "这个看起来不错! 👍 Great work with émojis and ñ characters",
        "created_at": "2023-01-01T10:00:00Z",
        "updated_at": "2023-01-01T10:00:00Z",
        "path": "src/测试.py",
        "diff_hunk": "@@ unicode diff @@",
        "line": 42,
    }

    result = format_comments_as_markdown([unicode_comment], "owner", "repo", 123)

    assert "这个看起来不错! 👍" in result
    assert "émojis and ñ characters" in result
    assert "`src/测试.py`" in result


def test_format_comments_as_markdown_long_pr_number():
    """Test formatting with very large PR numbers."""
    result = format_comments_as_markdown([], "owner", "repo", 999999999)

    assert "# owner/repo - PR #999999999 Review Comments" in result
    assert "No review comments found for this pull request." in result


def test_format_comments_as_markdown_special_characters_in_repo():
    """Test formatting with special characters in owner/repo names."""
    result = format_comments_as_markdown([], "owner-dash", "repo_underscore", 123)

    assert "# owner-dash/repo_underscore - PR #123 Review Comments" in result
    assert "No review comments found for this pull request." in result


def test_format_comments_as_markdown_original_line_fallback():
    """Test that original_line is used when line is None."""
    comment_with_original_line = {
        "id": 1,
        "user": {"login": "reviewer"},
        "body": "Comment on original line",
        "created_at": "2023-01-01T10:00:00Z",
        "updated_at": "2023-01-01T10:00:00Z",
        "path": "file.py",
        "diff_hunk": "diff content",
        "line": None,
        "original_line": 25,
    }

    result = format_comments_as_markdown(
        [comment_with_original_line], "owner", "repo", 123
    )

    assert "**Line:** 25" in result
