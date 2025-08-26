# AGENTS.md

This file is for AI agents. For human-readable documentation, see README.md.

## Project Overview

This project provides a command-line tool named `gh-pr-rev-md` (alias: `gh-pr-rev-md`) to fetch GitHub pull request review comments and format them as markdown. It's designed to be used in CI/CD pipelines or by developers to easily get a summary of review feedback.

## Getting Started

To get started, you need Python 3.9+ and `uv`.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/owner/repo.git
    cd repo
    ```

2.  **Install dependencies:**
    ```bash
    uv pip install .
    ```

3.  **Set up your GitHub token:**
    The tool requires a GitHub token with repository access. You can set it as an environment variable:
    ```bash
    export GITHUB_TOKEN=your_github_token_here
    ```

## Usage

To use the tool, run it with a GitHub pull request URL:

```bash
gh-pr-rev-md https://github.com/owner/repo/pull/123
```

You can also pass the token directly as an argument:

```bash
gh-pr-rev-md --token your_token https://github.com/owner/repo/pull/123
```

The output will be a markdown formatted list of all review comments on the pull request, printed to standard output.

## Code Style

This project uses Ruff for linting and formatting.

Format and lint before committing:

```bash
uv run ruff format .
uv run ruff check .
```

## Architecture

The project is structured as a Python package with a command-line interface.

-   `gh_pr_rev_md/cli.py`: The main entry point for the command-line tool. It uses `click` to handle command-line arguments.
-   `gh_pr_rev_md/github_client.py`: Handles all interactions with the GitHub GraphQL API. It uses the `requests` library to make API calls.
-   `gh_pr_rev_md/formatter.py`: Takes the review comments fetched from the GitHub API and formats them into markdown.
-   `pyproject.toml`: Defines the project metadata and dependencies.
