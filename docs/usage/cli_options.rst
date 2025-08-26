CLI Options
===========

Command Syntax
---------------

::

    gh-pr-rev-md [OPTIONS] PR_URL

Arguments
---------

``PR_URL``
~~~~~~~~~~

The GitHub pull request URL to fetch review comments from.

**Required format:** ``https://github.com/<owner>/<repo>/pull/<number>``

**Examples:**
  - ``https://github.com/octocat/Hello-World/pull/42``
  - ``https://github.com/microsoft/vscode/pull/12345``

**Special value:** ``.`` (dot) - Automatically detects the PR URL for the current git branch.

Options
-------

``--token TEXT``
~~~~~~~~~~~~~~~~

GitHub personal access token for API authentication.

- **Environment variable:** ``GITHUB_TOKEN``
- **Required scopes:** 
  - ``repo`` for private repositories
  - ``read:org`` for private organization repositories  
  - No scopes needed for public repositories (but recommended to avoid rate limits)
- **Rate limits:** 
  - Unauthenticated: ~60 requests/hour
  - Authenticated: 5,000 requests/hour

**Example:**
::

    gh-pr-rev-md --token ghp_your_token_here https://github.com/owner/repo/pull/123

**Token creation:** Visit https://github.com/settings/tokens to create a new token.

``--config-set``
~~~~~~~~~~~~~~~~

Launch interactive setup to create or update the XDG configuration file.

This will guide you through setting up:
- GitHub token
- Default include/exclude preferences  
- Default output settings

**Example:**
::

    gh-pr-rev-md --config-set

``--include-resolved``
~~~~~~~~~~~~~~~~~~~~~~

Include resolved review comments in the output.

By default, resolved comments are excluded to focus on active discussions.

**Example:**
::

    gh-pr-rev-md --include-resolved https://github.com/owner/repo/pull/123

``--include-outdated``  
~~~~~~~~~~~~~~~~~~~~~~

Include outdated review comments (from previous versions of the diff).

By default, outdated comments are excluded to focus on the current state.

**Example:**
::

    gh-pr-rev-md --include-outdated https://github.com/owner/repo/pull/123

``--output`` / ``-o``
~~~~~~~~~~~~~~~~~~~~~

Save output to an auto-generated filename instead of printing to stdout.

The filename format is: ``<owner>-<repo>-pr-<number>-<timestamp>.md``

**Example:**
::

    gh-pr-rev-md --output https://github.com/owner/repo/pull/123
    # Creates: owner-repo-pr-123-20231201-143052.md

``--output-file PATH``
~~~~~~~~~~~~~~~~~~~~~~

Save output to a specific file path instead of printing to stdout.

**Examples:**
::

    gh-pr-rev-md --output-file review.md https://github.com/owner/repo/pull/123
    gh-pr-rev-md --output-file /tmp/pr-review.md https://github.com/owner/repo/pull/123

``--help``
~~~~~~~~~~

Show the help message and exit.

::

    gh-pr-rev-md --help

Common Usage Patterns
----------------------

**Basic usage with token:**
::

    export GITHUB_TOKEN=ghp_your_token_here
    gh-pr-rev-md https://github.com/owner/repo/pull/123

**Include all comments and save to file:**
::

    gh-pr-rev-md --include-resolved --include-outdated --output https://github.com/owner/repo/pull/123

**Use current branch:**
::

    gh-pr-rev-md .

**One-time run without installation:**
::

    uvx gh-pr-rev-md https://github.com/owner/repo/pull/123