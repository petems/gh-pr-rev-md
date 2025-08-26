Testing
=======

This guide covers how to run tests, write new tests, and understand the testing strategy for ``gh-pr-rev-md``.

Running Tests
-------------

**Prerequisites:**
Ensure you have development dependencies installed::

    uv pip install -e .[dev]

**Basic test commands:**

Run all tests::

    python -m pytest

Run tests with coverage reporting::

    python -m pytest --cov=gh_pr_rev_md --cov-report=term

Run tests in verbose mode::

    python -m pytest -v

Run specific test file::

    python -m pytest tests/test_cli.py

Run specific test function::

    python -m pytest tests/test_cli.py::test_main_with_valid_url

**Advanced options:**

Run tests in parallel (if you have pytest-xdist installed)::

    python -m pytest -n auto

Stop on first failure::

    python -m pytest -x

Run only failed tests from last run::

    python -m pytest --lf

Generate HTML coverage report::

    python -m pytest --cov=gh_pr_rev_md --cov-report=html
    open htmlcov/index.html

Test Structure
--------------

The test suite is organized into several files:

::

    tests/
    ├── conftest.py          # Shared fixtures and configuration  
    ├── test_cli.py          # Command-line interface tests
    ├── test_formatter.py    # Markdown formatting tests
    ├── test_github_client.py # GitHub API client tests
    ├── test_git_utils.py    # Git utilities tests
    └── test_config.py       # Configuration loading tests

**Test categories:**

1. **Unit tests** - Test individual functions in isolation
2. **Integration tests** - Test component interactions
3. **CLI tests** - Test command-line interface end-to-end
4. **Mock tests** - Test with external dependencies mocked

Test Fixtures
-------------

Common fixtures are defined in ``conftest.py``:

**``mock_github_client``**
  Mock GitHub API client with predefined responses

**``sample_pr_data``**
  Realistic PR and comment data for testing

**``temp_config_file``**
  Temporary configuration file for testing config loading

**``mock_git_repo``**
  Mock git repository with branch and remote information

**Example usage:**
::

    def test_format_comments(sample_pr_data):
        result = format_comments_as_markdown(sample_pr_data)
        assert "# PR Review Comments" in result

Writing Tests
-------------

**Test naming conventions:**

- Test files: ``test_<module_name>.py``
- Test functions: ``test_<function>_<scenario>()``
- Test classes: ``Test<ClassName>``

**Example test structure:**
::

    def test_function_name_success_case():
        """Test successful execution of function_name."""
        # Arrange
        input_data = {...}
        expected_output = {...}
        
        # Act
        result = function_name(input_data)
        
        # Assert
        assert result == expected_output

    def test_function_name_error_case():
        """Test error handling in function_name."""
        # Arrange
        invalid_input = {...}
        
        # Act & Assert
        with pytest.raises(ExpectedError):
            function_name(invalid_input)

**Mocking external dependencies:**

GitHub API calls::

    @patch('gh_pr_rev_md.github_client.requests.post')
    def test_api_call(mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'data': {...}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = GitHubClient(token="test-token")
        result = client.get_pr_review_comments("owner", "repo", 123)
        
        assert result is not None
        mock_post.assert_called_once()

File system operations::

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.open')
    def test_config_loading(mock_open, mock_exists):
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "token: test"
        
        config = load_config()
        
        assert config['token'] == 'test'

Git operations::

    @patch('subprocess.run')
    def test_git_command(mock_run):
        mock_run.return_value.stdout = 'main'
        mock_run.return_value.returncode = 0
        
        branch = get_current_branch()
        
        assert branch == 'main'

CLI Testing
-----------

CLI tests use Click's testing utilities:

**Basic CLI test:**
::

    from click.testing import CliRunner
    from gh_pr_rev_md.cli import main

    def test_cli_help():
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output

**CLI test with arguments:**
::

    @patch('gh_pr_rev_md.cli.GitHubClient')
    def test_cli_with_url(mock_client):
        mock_instance = mock_client.return_value
        mock_instance.get_pr_review_comments.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(main, [
            'https://github.com/owner/repo/pull/123'
        ])
        
        assert result.exit_code == 0

**CLI test with config file:**
::

    def test_cli_with_config():
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create config file
            config_dir = Path('.config/gh-pr-rev-md')
            config_dir.mkdir(parents=True)
            config_file = config_dir / 'config.yaml'
            config_file.write_text('token: test-token')
            
            # Set XDG_CONFIG_HOME to current directory
            result = runner.invoke(main, 
                ['https://github.com/owner/repo/pull/123'],
                env={'XDG_CONFIG_HOME': str(Path.cwd())}
            )

**Testing error conditions:**
::

    def test_cli_invalid_url():
        runner = CliRunner()
        result = runner.invoke(main, ['invalid-url'])
        
        assert result.exit_code != 0
        assert 'Invalid GitHub PR URL' in result.output

API Client Testing
------------------

**Mock successful API response:**
::

    @patch('requests.post')
    def test_get_pr_comments_success(mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'repository': {
                    'pullRequest': {
                        'reviewThreads': {
                            'nodes': [
                                {
                                    'comments': {
                                        'nodes': [{
                                            'author': {'login': 'reviewer'},
                                            'body': 'Test comment',
                                            'createdAt': '2023-01-01T00:00:00Z'
                                        }]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = GitHubClient(token="test-token")
        comments = client.get_pr_review_comments("owner", "repo", 123)
        
        assert len(comments) == 1
        assert comments[0]['author']['login'] == 'reviewer'

**Mock API error response:**
::

    @patch('requests.post')
    def test_get_pr_comments_api_error(mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'errors': [{'message': 'Not found'}]
        }
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        
        client = GitHubClient(token="test-token")
        
        with pytest.raises(GitHubAPIError):
            client.get_pr_review_comments("owner", "repo", 123)

Formatter Testing
-----------------

**Test Markdown output structure:**
::

    def test_format_comments_structure():
        sample_comments = [{
            'author': {'login': 'reviewer'},
            'body': 'Test comment',
            'createdAt': '2023-01-01T00:00:00Z',
            'path': 'test.py',
            'line': 42,
            'diffHunk': '@@ -1,3 +1,3 @@\n-old\n+new'
        }]
        
        result = format_comments_as_markdown(
            sample_comments, 
            "owner/repo", 
            "Test PR", 
            123
        )
        
        # Check header
        assert "# PR Review Comments: owner/repo #123" in result
        
        # Check comment structure
        assert "## Comment #1" in result
        assert "**Author:** @reviewer" in result
        assert "**File:** `test.py`" in result
        assert "**Line:** 42" in result
        
        # Check code context
        assert "```diff" in result
        assert "-old" in result
        assert "+new" in result
        
        # Check comment content
        assert "Test comment" in result

**Test timestamp formatting:**
::

    def test_format_timestamp():
        iso_timestamp = "2023-12-01T14:30:52Z"
        result = format_timestamp(iso_timestamp)
        assert result == "2023-12-01 14:30:52 UTC"

Configuration Testing
---------------------

**Test config file loading:**
::

    def test_load_config_from_file(tmp_path):
        config_dir = tmp_path / ".config" / "gh-pr-rev-md"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("""
        token: "test-token"
        include_resolved: true
        output: true
        """)
        
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(tmp_path)}):
            config = load_config()
        
        assert config['token'] == 'test-token'
        assert config['include_resolved'] is True
        assert config['output'] is True

**Test config precedence:**
::

    def test_config_precedence(tmp_path):
        # Create config file
        config_dir = tmp_path / ".config" / "gh-pr-rev-md"  
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("token: file-token")
        
        # Test environment variable override
        with patch.dict(os.environ, {
            'XDG_CONFIG_HOME': str(tmp_path),
            'GITHUB_TOKEN': 'env-token'
        }):
            config = load_config()
        
        assert config['token'] == 'env-token'  # Env overrides file

Coverage Goals
--------------

**Target coverage:**
- Overall: >90%
- Critical paths (API client, CLI): >95%
- New features: 100%

**Coverage exclusions:**
- Error handling for truly exceptional cases
- Platform-specific code paths
- Development/debugging code

**Checking coverage:**
::

    # Generate coverage report
    python -m pytest --cov=gh_pr_rev_md --cov-report=term-missing
    
    # Identify uncovered lines
    python -m pytest --cov=gh_pr_rev_md --cov-report=html
    open htmlcov/index.html

**Coverage configuration** (in ``pyproject.toml``)::

    [tool.coverage.run]
    source = ["gh_pr_rev_md"]
    omit = [
        "tests/*",
        "setup.py",
    ]

    [tool.coverage.report]
    exclude_lines = [
        "pragma: no cover",
        "def __repr__",
        "raise AssertionError",
        "raise NotImplementedError",
    ]

Continuous Integration
----------------------

Tests run automatically on:

- **Pull requests** - All tests must pass before merge
- **Main branch commits** - Ensures main stays stable  
- **Release tags** - Full test suite before publishing

**GitHub Actions workflow:**
- Python 3.9, 3.10, 3.11, 3.12 compatibility
- Multiple operating systems (Linux, macOS, Windows)
- Security scanning with bandit
- Code quality checks with ruff
- Documentation building

**Local pre-commit checks:**
::

    # Run the same checks as CI
    python -m pytest
    ruff check .
    ruff format --check .
    bandit -r gh_pr_rev_md

Debugging Test Failures
-----------------------

**Common issues and solutions:**

**Import errors:**
- Ensure package is installed in editable mode: ``pip install -e .``
- Check PYTHONPATH includes project directory

**Mock-related errors:**
- Verify mock patches target the correct module path
- Check that mock return values match expected data structures
- Ensure mocks are properly configured before calling tested functions

**Flaky tests:**
- Look for timing dependencies or random data
- Check for shared state between tests
- Consider using ``pytest-randomly`` to detect order dependencies

**API-related test failures:**
- Ensure all external API calls are mocked
- Check that mock data matches real API response structure
- Verify error conditions are properly tested

**Debugging tools:**
::

    # Run with Python debugger
    python -m pytest --pdb
    
    # Print debug output
    python -m pytest -s
    
    # Run specific failing test with verbose output
    python -m pytest -vvv tests/test_module.py::test_function

This comprehensive testing approach ensures reliability, maintainability, and confidence in the codebase.