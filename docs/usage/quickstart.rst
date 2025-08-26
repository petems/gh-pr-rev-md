Quickstart
==========

Basic Usage
-----------

Fetch review comments for a GitHub pull request::

    gh-pr-rev-md https://github.com/owner/repo/pull/123

This will print the formatted markdown to stdout.

Using Current Branch
--------------------

If you're in a git repository with a pull request open for the current branch::

    gh-pr-rev-md .

The tool will automatically detect the PR URL using the current branch.

Authentication
--------------

For higher rate limits and access to private repositories, set up a GitHub token:

1. Create a personal access token at https://github.com/settings/tokens
2. Grant ``repo`` scope for private repositories, or no scopes for public repositories only
3. Set the token as an environment variable::

    export GITHUB_TOKEN=ghp_your_token_here

Or use the ``--token`` flag::

    gh-pr-rev-md --token ghp_your_token_here https://github.com/owner/repo/pull/123

Initial Configuration
---------------------

Set up a configuration file interactively::

    gh-pr-rev-md --config-set

This will guide you through creating a configuration file in your XDG config directory.

Saving Output to File
---------------------

Save to an auto-generated filename::

    gh-pr-rev-md --output https://github.com/owner/repo/pull/123

Save to a specific file::

    gh-pr-rev-md --output-file review.md https://github.com/owner/repo/pull/123