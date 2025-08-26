Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

Added
~~~~~

- Comprehensive documentation with usage guides, API reference, and developer documentation
- FAQ section covering common issues and troubleshooting
- Configuration precedence documentation

Changed
~~~~~~~

- Improved README with modern uv installation instructions and uvx examples

[1.0.0] - 2023-12-01
--------------------

Added
~~~~~

- Initial release of gh-pr-rev-md
- Command-line interface for fetching GitHub PR review comments
- Support for GitHub GraphQL API with authentication
- Markdown formatting of review comments with code context
- Configuration via CLI arguments, environment variables, and XDG config file
- Auto-detection of PR URL from current git branch
- Filtering options for resolved and outdated comments
- Output to stdout or file (auto-generated or custom filename)
- Interactive configuration setup with ``--config-set``
- Support for both public and private repositories
- Comprehensive test suite with >90% coverage
- Sphinx documentation with API reference
- CI/CD with GitHub Actions
- Security scanning with bandit
- Code quality checks with ruff

Features
~~~~~~~~

**Core functionality:**
- Fetch PR review comments via GitHub GraphQL API
- Format comments as structured Markdown with metadata
- Include code context (diff hunks) for each comment
- Support pagination for PRs with many comments
- Handle GitHub API rate limits gracefully

**Configuration:**
- XDG Base Directory Specification compliance
- Multiple configuration sources with precedence
- Interactive setup wizard
- Environment variable support

**Output options:**
- Print to stdout (default)
- Save to auto-generated filename
- Save to custom file path
- Preserve original Markdown formatting from GitHub

**Filtering:**
- Exclude resolved comments (default)
- Exclude outdated comments (default)
- Options to include both types via CLI flags

**Git integration:**
- Auto-detect PR URL from current branch
- Support for SSH and HTTPS git remotes
- No external git CLI dependency

**Developer experience:**
- Comprehensive test suite
- Type hints throughout codebase
- Clear error messages
- Extensive documentation
- Modern Python packaging with pyproject.toml

Dependencies
~~~~~~~~~~~~

**Runtime dependencies:**
- click >= 8.0.0 - Command-line interface framework
- requests >= 2.25.0 - HTTP requests for GitHub API
- PyYAML >= 5.4.0 - YAML configuration file parsing

**Development dependencies:**
- pytest >= 6.0.0 - Testing framework
- pytest-cov >= 2.10.0 - Coverage reporting
- ruff >= 0.1.0 - Linting and formatting
- bandit >= 1.7.0 - Security analysis
- sphinx >= 4.0.0 - Documentation generation
- sphinx-rtd-theme >= 1.0.0 - Documentation theme

Python Support
~~~~~~~~~~~~~~

- Python 3.9+
- Tested on Linux, macOS, and Windows
- Compatible with CPython and PyPy

Known Issues
~~~~~~~~~~~~

None at release.

Security
~~~~~~~~

- No known security vulnerabilities
- Bandit security scanning integrated into CI
- GitHub token handling follows security best practices
- Configuration file permissions automatically set to 600

Migration Guide
~~~~~~~~~~~~~~~

This is the initial release, so no migration is needed.

---

**Release Process:**

Releases are published to PyPI when a new tag is pushed to the repository.
The version number follows semantic versioning:

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner  
- **PATCH** version for backwards compatible bug fixes

**Deprecation Policy:**

When features are deprecated:
1. They will be marked as deprecated in the documentation
2. Deprecation warnings will be added to the CLI/API
3. The feature will be removed in the next major version
4. Migration instructions will be provided

**Support Policy:**

- Latest major version: Full support (new features, bug fixes, security updates)
- Previous major version: Security updates only for 6 months after new major release
- Older versions: Community support only

**Contributing:**

See the :doc:`development/contributing` guide for information on how to contribute to gh-pr-rev-md.