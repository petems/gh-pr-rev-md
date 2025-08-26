Contributing
============

We welcome contributions to ``gh-pr-rev-md``! This guide will help you set up your development environment and understand our development workflow.

Development Environment Setup
-----------------------------

**Prerequisites:**

- Python 3.9 or higher
- ``git`` for version control
- ``uv`` for Python package management (recommended)

**Clone the repository:**
::

    git clone https://github.com/petems/gh-pr-rev-md.git
    cd gh-pr-rev-md

**Install development dependencies:**
::

    # Using uv (recommended)
    uv venv
    uv pip install -e .[dev]

    # Or using pip
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -e .[dev]

**Verify installation:**
::

    gh-pr-rev-md --help
    python -m pytest --version

Development Dependencies
------------------------

The ``[dev]`` extra includes:

- **pytest** - Test framework
- **pytest-cov** - Test coverage reporting
- **ruff** - Linting and formatting
- **bandit** - Security analysis
- **sphinx** - Documentation generation
- **sphinx-rtd-theme** - Documentation theme

Code Style and Linting
-----------------------

We use ``ruff`` for both linting and formatting.

**Check code style:**
::

    ruff check .

**Auto-fix issues:**
::

    ruff check --fix .

**Format code:**
::

    ruff format .

**Configuration:**
Ruff configuration is in ``pyproject.toml`` under ``[tool.ruff]``.

Running Tests
-------------

**Run all tests:**
::

    python -m pytest

**Run with coverage:**
::

    python -m pytest --cov=gh_pr_rev_md --cov-report=term

**Run specific test file:**
::

    python -m pytest tests/test_cli.py

**Run tests in verbose mode:**
::

    python -m pytest -v

**Test coverage target:** Aim for >90% coverage on new code.

Security Analysis
-----------------

We use ``bandit`` for security analysis:

**Run security scan:**
::

    uv run bandit -r gh_pr_rev_md -f txt

**Address security issues:**
- Fix any high or medium severity issues
- Document any intentional ``# nosec`` suppressions
- Keep security dependencies up to date

Documentation
-------------

**Generate complete documentation:**
::

    make docs-generate

**Serve documentation locally:**
::

    make docs-serve
    # Opens http://localhost:8000

**Clean documentation:**
::

    make docs-clean

**Alternative manual steps:**
::

    # Update API documentation
    uv run sphinx-apidoc -f -o docs/api gh_pr_rev_md
    
    # Build HTML documentation
    uv run sphinx-build -b html docs docs/_build/html

Development Workflow
--------------------

**1. Create a feature branch:**
::

    git checkout -b feature/your-feature-name

**2. Make your changes:**
- Write code following existing patterns
- Add tests for new functionality
- Update documentation if needed
- Follow code style guidelines

**3. Test your changes:**
::

    # Run tests
    python -m pytest
    
    # Check code style  
    ruff check --fix .
    
    # Security scan
    uv run bandit -r gh_pr_rev_md -f txt
    
    # Build docs
    make docs-generate

**4. Commit your changes:**
::

    git add .
    git commit -m "feat: add new feature description"

**5. Push and create pull request:**
::

    git push origin feature/your-feature-name

Then create a pull request on GitHub.

Commit Message Guidelines
-------------------------

We follow conventional commit format:

- ``feat:`` New feature
- ``fix:`` Bug fix  
- ``docs:`` Documentation changes
- ``test:`` Adding or updating tests
- ``refactor:`` Code refactoring
- ``style:`` Code style changes
- ``chore:`` Maintenance tasks

**Examples:**
::

    feat: add support for draft pull requests
    fix: handle rate limit errors gracefully  
    docs: update CLI options documentation
    test: add integration tests for GitHub API

Testing Guidelines
------------------

**Test types:**

1. **Unit tests** - Test individual functions/methods
2. **Integration tests** - Test component interactions
3. **CLI tests** - Test command-line interface
4. **API tests** - Test GitHub API integration (with mocks)

**Writing tests:**

- Use descriptive test names
- Test both success and error cases
- Mock external dependencies (GitHub API, git commands)
- Use fixtures for common test data
- Follow existing test patterns

**Test file structure:**
::

    tests/
    ├── conftest.py          # Test fixtures and configuration
    ├── test_cli.py          # CLI interface tests
    ├── test_formatter.py    # Markdown formatting tests
    ├── test_github_client.py # GitHub API client tests
    ├── test_git_utils.py    # Git utilities tests
    └── test_config.py       # Configuration loading tests

**Mock examples:**
::

    # Mock GitHub API calls
    @patch('gh_pr_rev_md.github_client.requests.post')
    def test_api_call(mock_post):
        mock_post.return_value.json.return_value = {...}
        # Test your function
    
    # Mock file system
    @patch('pathlib.Path.exists')
    def test_config_loading(mock_exists):
        mock_exists.return_value = True
        # Test config loading

Adding New Features
-------------------

**Before adding a feature:**

1. Open an issue to discuss the feature
2. Ensure it aligns with project goals
3. Consider backward compatibility
4. Plan the API design

**Implementation checklist:**

- [ ] Add the feature implementation
- [ ] Add comprehensive tests
- [ ] Update CLI help text if needed
- [ ] Update configuration documentation
- [ ] Add usage examples
- [ ] Update API documentation
- [ ] Test with real GitHub repositories
- [ ] Check performance impact

**Feature guidelines:**

- Keep the CLI interface simple
- Follow existing patterns and conventions
- Handle errors gracefully with helpful messages
- Support configuration via CLI, env vars, and config file
- Add appropriate logging for debugging

Common Issues and Solutions
---------------------------

**Import errors during development:**
::

    # Ensure you installed in editable mode
    pip install -e .

**Tests failing with GitHub API:**
- Ensure tests use mocks, not real API calls
- Check that fixtures provide realistic test data
- Verify authentication is properly mocked

**Documentation build errors:**
- Check for RST syntax errors
- Ensure all referenced files exist
- Update ``toctree`` when adding new files

**Ruff/linting errors:**
- Run ``ruff check --fix .`` to auto-fix
- Some errors may require manual fixes
- Check ``pyproject.toml`` for configuration

Getting Help
------------

**Resources:**

- GitHub Issues: Report bugs and feature requests
- Discussions: Ask questions and share ideas
- Documentation: https://gh-pr-rev-md.readthedocs.io
- Code review: Submit pull requests for feedback

**Development questions:**

1. Check existing issues and discussions
2. Look at similar implementations in the codebase
3. Ask in a new discussion or issue
4. Reference relevant code and error messages

Thank you for contributing to ``gh-pr-rev-md``!