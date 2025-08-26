"""Formatter for converting GitHub PR comments to markdown."""

from datetime import datetime
from typing import List, Dict, Any, Optional


def format_comments_as_markdown(
    comments: List[Dict[str, Any]], owner: str, repo: str, pr_number: int
) -> str:
    """Format GitHub PR review comments as markdown."""
    if not comments:
        return f"# {owner}/{repo} - PR #{pr_number} Review Comments\n\nNo review comments found for this pull request."

    markdown_lines = [
        f"# {owner}/{repo} - PR #{pr_number} Review Comments",
        f"**Repository:** {owner}/{repo}",
        f"**Pull Request:** https://github.com/{owner}/{repo}/pull/{pr_number}",
        f"**Total Comments:** {len(comments)}",
        "",
        "---",
        "",
    ]

    for i, comment in enumerate(comments, 1):
        user = comment.get("user", {})
        username = user.get("login", "Unknown")
        created_at = comment.get("created_at", "")
        updated_at = comment.get("updated_at", "")
        body = comment.get("body", "")
        path = comment.get("path", "Unknown file")
        diff_hunk = comment.get("diff_hunk", "")
        line = comment.get("line") or comment.get("original_line", "Unknown")

        # Format timestamps
        created_date = format_timestamp(created_at)
        updated_date = (
            format_timestamp(updated_at) if updated_at != created_at else None
        )

        markdown_lines.extend(
            [
                f"## Comment #{i}",
                f"**Author:** @{username}",
                f"**File:** `{path}`",
                f"**Line:** {line}",
                f"**Created:** {created_date}",
            ]
        )

        if updated_date:
            markdown_lines.append(f"**Updated:** {updated_date}")

        markdown_lines.extend(
            [
                "",
                "### Code Context",
                "```diff",
                diff_hunk,
                "```",
                "",
                "### Comment",
                body,
                "",
                "---",
                "",
            ]
        )

    return "\n".join(markdown_lines)


def format_timestamp(timestamp_str: Optional[str]) -> str:
    """Format ISO timestamp to human-readable format."""
    if not timestamp_str:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        return timestamp_str
