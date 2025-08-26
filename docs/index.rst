gh-pr-rev-md documentation
===========================

Welcome to gh-pr-rev-md's documentation.

`gh-pr-rev-md` is a command-line tool to fetch GitHub Pull Request review comments and render them as Markdown.

Features:
- Fetches PR review comments via the GitHub GraphQL API.
- Excludes resolved and outdated comments by default.
- Provides flags (`--include-resolved`, `--include-outdated`) to include them.
- Emits clean Markdown including per-comment metadata and diff context.
- Can print to stdout or write to a file.
- Configurable via CLI, environment variables, and an XDG config file.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/modules
