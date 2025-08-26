gh-pr-rev-md documentation
===========================

Welcome to gh-pr-rev-md's documentation.

`gh-pr-rev-md` is a command-line tool to fetch GitHub Pull Request review comments and render them as Markdown.

Features:
- Fetches PR review comments via the GitHub GraphQL API
- Excludes resolved and outdated comments by default
- Provides flags (`--include-resolved`, `--include-outdated`) to include them
- Emits clean Markdown including per-comment metadata and diff context
- Can print to stdout or write to a timestamped file
- Configurable via CLI, environment variables, and an XDG config file
- Auto-detects PR URL from current git branch
- Works with both public and private repositories

Quick Start
-----------

Try it without installing::

    uvx gh-pr-rev-md https://github.com/octocat/Hello-World/pull/42

Or install as a global tool::

    uv tool install gh-pr-rev-md
    gh-pr-rev-md https://github.com/octocat/Hello-World/pull/42

For authentication and higher rate limits, set up a GitHub token::

    export GITHUB_TOKEN=ghp_your_token_here

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage/index
   configuration/index
   api/index
   development/index
   faq
   changelog
