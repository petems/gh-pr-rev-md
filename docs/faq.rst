Frequently Asked Questions
==========================

Installation and Setup
-----------------------

**Q: What Python versions are supported?**

A: Python 3.9 or higher is required. We test against Python 3.9, 3.10, 3.11, and 3.12.

**Q: How do I install gh-pr-rev-md?**

A: The recommended installation method is::

    uv tool install gh-pr-rev-md

You can also try it without installing::

    uvx gh-pr-rev-md https://github.com/owner/repo/pull/123

See the :doc:`usage/installation` guide for all installation options.

**Q: Do I need to install git or the GitHub CLI?**

A: No external tools are required. ``gh-pr-rev-md`` uses Python libraries to interact with Git repositories and the GitHub API directly.

GitHub Authentication
---------------------

**Q: Why am I hitting GitHub API rate limits?**

A: Without authentication, GitHub limits you to ~60 requests per hour. With a token, you get 5,000 requests per hour. Create a token at https://github.com/settings/tokens and set it via:

- Environment variable: ``export GITHUB_TOKEN=ghp_your_token``
- Command line: ``--token ghp_your_token``  
- Config file: ``token: ghp_your_token`` in ``~/.config/gh-pr-rev-md/config.yaml``

**Q: What GitHub token scopes are needed?**

A: For public repositories, no scopes are required (but a token is still recommended for higher rate limits).

For private repositories:
- ``repo`` - Full control of private repositories
- ``read:org`` - Read access to organization membership (for private org repos)

**Q: My token isn't working. What's wrong?**

A: Check that:
- Token starts with ``ghp_`` (classic tokens) or ``github_pat_`` (fine-grained tokens)
- Token hasn't expired (check at https://github.com/settings/tokens)
- Token has appropriate scopes for the repository
- You're using the token correctly (environment variable, CLI flag, or config file)

**Q: Can I use fine-grained personal access tokens?**

A: Yes, fine-grained tokens work. Make sure to grant access to the specific repositories you want to query and include the "Pull requests" permission with read access.

Usage Issues
------------

**Q: "Invalid GitHub PR URL format" error**

A: The URL must be in the exact format: ``https://github.com/<owner>/<repo>/pull/<number>``

Valid examples:
- ``https://github.com/octocat/Hello-World/pull/42``
- ``https://github.com/microsoft/vscode/pull/12345``

Invalid examples:
- ``https://github.com/owner/repo/pulls/123`` (``pulls`` instead of ``pull``)
- ``github.com/owner/repo/pull/123`` (missing ``https://``)
- ``https://github.com/owner/repo/pull/123/files`` (extra path after number)

**Q: "No open PR found for branch" error**

A: When using ``.`` to auto-detect the PR URL, this error means:

1. You're not in a git repository, or
2. The current branch doesn't have an open PR, or  
3. The repository remote URL doesn't match any open PRs

Solutions:
- Ensure you're in the correct git repository
- Check that a PR is open for your current branch
- Use the explicit PR URL instead of ``.``
- Verify your git remotes match the GitHub repository

**Q: "Git is not installed" error**

A: This shouldn't happen since ``gh-pr-rev-md`` doesn't require git CLI. If you see this error, it's likely a bug. Please report it with:
- Your operating system
- Python version
- How you installed the tool
- The exact command that failed

**Q: Why are some comments missing?**

A: By default, the tool excludes:
- **Resolved comments** - Use ``--include-resolved`` to include them
- **Outdated comments** - Use ``--include-outdated`` to include them (from previous versions of the diff)

To get all comments::

    gh-pr-rev-md --include-resolved --include-outdated https://github.com/owner/repo/pull/123

**Q: Can I get comments from draft PRs?**

A: Yes, the tool works with draft pull requests as long as you have access to the repository.

Configuration
-------------

**Q: Where is the configuration file located?**

A: Following XDG Base Directory Specification:

- Linux/macOS: ``~/.config/gh-pr-rev-md/config.yaml``
- Windows: ``%APPDATA%\gh-pr-rev-md\config.yaml``
- Custom: ``$XDG_CONFIG_HOME/gh-pr-rev-md/config.yaml``

**Q: How do I create a configuration file?**

A: Use the interactive setup::

    gh-pr-rev-md --config-set

This will guide you through setting up your token and preferences.

**Q: What's the configuration file format?**

A: YAML format. Example::

    token: "ghp_your_token_here"
    include_resolved: true
    include_outdated: false
    output: true
    output_file: "~/pr-reviews/review.md"

See :doc:`configuration/config_file` for details.

**Q: Which configuration source takes precedence?**

A: Priority order (highest to lowest):
1. Command-line arguments
2. Environment variables
3. Configuration file
4. Default values

See :doc:`configuration/precedence` for examples.

Output and Files
----------------

**Q: How do I save output to a file?**

A: Three options:

1. Auto-generated filename::

    gh-pr-rev-md --output https://github.com/owner/repo/pull/123

2. Custom filename::

    gh-pr-rev-md --output-file review.md https://github.com/owner/repo/pull/123

3. Shell redirection::

    gh-pr-rev-md https://github.com/owner/repo/pull/123 > review.md

**Q: What's the auto-generated filename format?**

A: ``<owner>-<repo>-pr-<number>-<timestamp>.md``

Example: ``octocat-Hello-World-pr-42-20231201-143052.md``

**Q: Can I customize the output format?**

A: Currently, the Markdown format is fixed. If you need different formatting, you can:
- Process the Markdown output with other tools
- Parse the JSON data from the GitHub API directly
- Submit a feature request for additional output formats

**Q: Why is the diff context different from GitHub?**

A: The tool shows the original diff context from the review comment, which may differ from the current file state if:
- The PR has been updated since the comment was made
- Files have been renamed or moved
- Additional commits have changed the surrounding code

This is normal and preserves the context that was relevant when the comment was made.

Troubleshooting
---------------

**Q: The tool is running slowly**

A: Common causes:

- **Large PRs** - PRs with many comments take longer to process
- **API rate limits** - Use a token for faster API access
- **Network issues** - Check your internet connection
- **GitHub API performance** - Occasionally GitHub's API is slow

**Q: I'm getting SSL/certificate errors**

A: This usually indicates network configuration issues:

- Check if you're behind a corporate firewall
- Verify system date/time is correct
- Try updating your Python certificates
- Consider using a VPN if network restrictions apply

**Q: The tool crashes with "ModuleNotFoundError"**

A: This suggests an installation issue:

1. Reinstall the package::

    pip uninstall gh-pr-rev-md
    pip install gh-pr-rev-md

2. If using ``uv``::

    uv tool uninstall gh-pr-rev-md
    uv tool install gh-pr-rev-md

3. Check your Python environment and PATH

**Q: Output contains weird characters or encoding issues**

A: This can happen with:
- Non-ASCII characters in comments (emoji, Unicode text)
- Terminal encoding issues
- File encoding problems when saving to disk

Try:
- Using a UTF-8 capable terminal
- Saving to a file instead of printing to stdout
- Setting ``export PYTHONIOENCODING=utf-8``

Development and Contributing
----------------------------

**Q: How can I contribute to the project?**

A: See :doc:`development/contributing` for detailed instructions. In summary:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

**Q: How do I run the tests?**

A: After installing development dependencies::

    pip install -e .[dev]
    python -m pytest

See :doc:`development/testing` for comprehensive testing information.

**Q: Can I add support for other code hosting platforms?**

A: Currently, only GitHub is supported. Adding support for GitLab, Bitbucket, etc. would require significant changes to the API client. If there's sufficient demand, this could be considered for future versions.

**Q: How do I report bugs or request features?**

A: Use the GitHub issue tracker at https://github.com/petems/gh-pr-rev-md/issues

Include:
- Your operating system and Python version
- How you installed the tool
- The exact command you ran
- The full error message
- Steps to reproduce the issue

Getting Help
------------

**Q: Where can I get more help?**

A: Resources:

- **Documentation**: https://gh-pr-rev-md.readthedocs.io
- **GitHub Issues**: https://github.com/petems/gh-pr-rev-md/issues
- **GitHub Discussions**: For questions and community support

**Q: Is there a community forum or chat?**

A: Currently, GitHub Discussions and Issues are the primary support channels. For real-time help, you can:

- Check existing issues for similar problems
- Create a new issue with detailed information
- Start a discussion for general questions

**Q: How often is the tool updated?**

A: Updates depend on:
- Bug fixes (released as needed)
- Feature requests and community contributions
- GitHub API changes requiring updates
- Security updates (high priority)

Follow the repository to get notified of new releases.