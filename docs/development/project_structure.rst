Project Structure
=================

This document provides an overview of the ``gh-pr-rev-md`` codebase structure and the role of each module.

Repository Layout
-----------------

::

    gh-pr-rev-md/
    ├── gh_pr_rev_md/           # Main Python package
    │   ├── __init__.py         # Package initialization
    │   ├── cli.py              # Command-line interface
    │   ├── github_client.py    # GitHub API client
    │   ├── formatter.py        # Markdown formatting
    │   ├── config.py           # Configuration loading
    │   └── git_utils.py        # Git repository utilities
    ├── tests/                  # Test suite
    │   ├── conftest.py         # Test fixtures
    │   ├── test_cli.py         # CLI tests
    │   ├── test_github_client.py # API client tests
    │   ├── test_formatter.py   # Formatter tests
    │   ├── test_config.py      # Configuration tests
    │   └── test_git_utils.py   # Git utilities tests
    ├── docs/                   # Sphinx documentation
    │   ├── conf.py             # Sphinx configuration
    │   ├── index.rst           # Documentation home
    │   ├── api/                # API documentation
    │   ├── usage/              # Usage guides
    │   ├── configuration/      # Configuration docs
    │   └── development/        # Developer guides
    ├── pyproject.toml          # Project configuration
    ├── uv.lock                 # Dependency lock file
    ├── README.md               # Project overview
    ├── LICENSE                 # MIT license
    └── Makefile                # Development tasks

Core Modules
------------

``cli.py`` - Command-Line Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Entry point for the command-line tool, handles argument parsing and orchestrates the workflow.

**Key components:**

- ``main()`` - Click-based CLI command definition
- ``get_current_branch_pr_url()`` - Auto-detects PR URL from current git branch
- ``_interactive_config_setup()`` - Interactive configuration wizard
- Error handling and user-friendly error messages

**Dependencies:**
- ``click`` for CLI framework
- ``subprocess`` for git/gh CLI integration
- Internal modules: ``config``, ``github_client``, ``formatter``, ``git_utils``

**Flow:**
1. Parse command-line arguments
2. Load configuration (CLI → env → config file → defaults)
3. Resolve PR URL (explicit URL or auto-detect from branch)
4. Create GitHub client and fetch review comments
5. Format comments as Markdown
6. Output to stdout or file

``github_client.py`` - GitHub API Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Handles all interactions with the GitHub GraphQL API.

**Key components:**

- ``GitHubClient`` class - Main API client
- ``get_pr_review_comments()`` - Fetches review comments with pagination
- ``find_pr_by_branch()`` - Finds PR for a given branch
- Error handling for API rate limits, authentication, and network issues

**Features:**
- GraphQL queries for efficient data fetching  
- Automatic pagination handling
- Configurable filtering (resolved/outdated comments)
- Robust error handling with user-friendly messages

**API Integration:**
- Uses GitHub GraphQL API v4
- Requires authentication token for higher rate limits
- Handles repository permissions and access control

``formatter.py`` - Markdown Formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Converts GitHub API responses into structured Markdown output.

**Key components:**

- ``format_comments_as_markdown()`` - Main formatting function
- ``format_timestamp()`` - Converts ISO timestamps to human-readable format
- Template-based output generation
- Diff context preservation

**Output structure:**

1. Header with PR metadata
2. Individual comment sections with:

   - Author, file, line information
   - Code context (diff hunks)
   - Comment content with preserved formatting

**Features:**
- Preserves original Markdown formatting from GitHub
- Includes surrounding code context
- Handles emoji, mentions, and GitHub-flavored Markdown
- Clean, readable output suitable for archiving or sharing

``config.py`` - Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Handles configuration loading following XDG Base Directory Specification.

**Key components:**

- ``load_config()`` - Main configuration loading function
- XDG-compliant directory discovery
- YAML configuration file parsing
- Configuration precedence handling

**Configuration sources (in precedence order):**
1. Command-line arguments (highest)
2. Environment variables
3. User config file (``~/.config/gh-pr-rev-md/config.yaml``)
4. System config files (``/etc/xdg/gh-pr-rev-md/config.yaml``)
5. Default values (lowest)

**Features:**
- Cross-platform config directory detection
- Graceful handling of missing or invalid config files
- Support for all CLI options via configuration file

``git_utils.py`` - Git Repository Utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Provides native Git repository introspection without external dependencies.

**Key components:**

- ``GitRepository`` class - Git repository operations
- ``find_pr_by_branch()`` - Maps branch to PR URL using remotes
- ``RemoteInfo`` data class - Remote repository information  
- ``GitParsingError`` - Custom exception for Git-related errors

**Features:**
- Pure Python Git operations (no git CLI dependency)
- Remote URL parsing and normalization
- Branch to PR URL mapping
- Error handling for invalid repositories

**Git operations:**
- Read ``.git/HEAD`` to get current branch
- Parse ``.git/config`` for remote information
- Extract owner/repo from remote URLs
- Support for both SSH and HTTPS Git remotes

Data Flow
---------

**High-level workflow:**

1. **Input processing** (``cli.py``)
   - Parse CLI arguments
   - Load configuration from multiple sources
   - Validate and normalize inputs

2. **PR URL resolution** (``cli.py`` + ``git_utils.py``)
   - If URL provided: validate format
   - If ``.`` provided: auto-detect from current branch
   - Use git utilities to find matching PR

3. **Data fetching** (``github_client.py``)
   - Authenticate with GitHub API
   - Execute GraphQL query to fetch PR review comments
   - Handle pagination and filtering
   - Return structured comment data

4. **Output generation** (``formatter.py``)
   - Process comment data into Markdown structure
   - Format timestamps and metadata
   - Preserve code context and diff information
   - Generate final Markdown document

5. **Output delivery** (``cli.py``)
   - Print to stdout or save to file
   - Handle file creation and error reporting

**Error handling flow:**

- Each module raises specific exceptions for different error conditions
- CLI layer catches exceptions and provides user-friendly error messages
- Graceful degradation for non-critical features
- Detailed error information for debugging

Architecture Principles
-----------------------

**Separation of concerns:**
- CLI handling separated from business logic
- GitHub API client isolated from formatting logic
- Configuration management centralized
- Git operations abstracted into utilities

**Dependency management:**
- Minimal external dependencies
- Optional dependencies clearly marked
- No runtime dependencies on external tools (git, gh CLI)

**Error handling:**
- Explicit error types for different failure modes
- User-friendly error messages with actionable guidance  
- Graceful degradation where possible
- Detailed logging for debugging

**Testability:**
- Pure functions where possible
- Clear module boundaries for mocking
- Separation of I/O operations from business logic
- Comprehensive test coverage

**Extensibility:**
- Modular design allows for easy feature additions
- Configuration system supports new options
- Output formatting can be extended
- API client can support new GitHub features

Development Patterns
--------------------

**Configuration pattern:**
All user-configurable options follow the same pattern:
1. Define in CLI with ``click.option()``
2. Add environment variable support
3. Include in config file schema
4. Set appropriate defaults
5. Document in all three places

**Error handling pattern:**
::

    try:
        # Operation that might fail
        result = risky_operation()
    except SpecificException as e:
        raise click.BadParameter(f"User-friendly error message: {e}")
    except Exception as e:
        raise click.ClickException(f"Unexpected error: {e}")

**Testing pattern:**
- Mock external dependencies (GitHub API, file system)
- Test both success and failure cases
- Use fixtures for common test data
- Follow naming convention: ``test_<function>_<scenario>()``

This modular architecture makes the codebase maintainable, testable, and extensible while keeping the user experience simple and reliable.