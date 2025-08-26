# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important: Always Use uv

**ALWAYS use `uv run` for Python commands instead of bare `python` or `python3`.**
This ensures consistent environment and dependency management.

## Project Overview

This is `gh-pr-rev-md`, a Python CLI tool that fetches GitHub pull request review comments and formats them as markdown output. The tool uses the GitHub API to retrieve PR review comments and presents them in a structured markdown format for easy reading.

## Architecture

The codebase follows a simple modular structure:

- `gh_pr_rev_md/cli.py` - Click-based CLI interface, handles argument parsing and orchestrates the workflow
- `gh_pr_rev_md/github_client.py` - GitHub GraphQL API client with pagination support and error handling
- `gh_pr_rev_md/formatter.py` - Converts GitHub API responses to formatted markdown output

The main flow: CLI parses PR URL → GitHub client fetches comments → Formatter generates markdown → Output to stdout.

## Development Commands

**Install the package locally:**
```bash
uv pip install .
```

**Run the CLI during development:**
```bash
uv run python -m gh_pr_rev_md.cli <pr_url>
```

**Authentication:**
Set `GITHUB_TOKEN` environment variable or use `--token` flag. Token needs repository access permissions.

**Linting, Testing, and Security:**
```bash
# Run linting (auto-fix issues)
uv run ruff check --fix .

# Run security scanning
uv run bandit -r gh_pr_rev_md -f txt

# Run tests
uv run python -m pytest -q

# Run tests with coverage
uv run python -m pytest -q --cov=gh_pr_rev_md --cov-report=term
```

## Key Implementation Details

- PR URL parsing uses regex pattern: `https://github\.com/([^/]+)/([^/]+)/pull/(\d+)`
- GitHub API pagination is handled automatically in `get_pr_review_comments()`
- Error handling covers common API scenarios (404, 403, rate limiting)
- Timestamps are formatted from ISO to human-readable format
- Diff hunks are preserved in markdown code blocks with diff syntax highlighting