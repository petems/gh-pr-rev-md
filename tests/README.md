# Test Suite for gh-pr-rev-md

This directory contains comprehensive tests for the gh-pr-rev-md CLI tool, with particular focus on the file output functionality.

## Test Structure

- `test_cli.py` - Tests for CLI functionality, including file output features
- `test_github_client.py` - Tests for GitHub API client 
- `test_formatter.py` - Tests for markdown formatting
- `conftest.py` - Shared pytest fixtures

## Running Tests

### Install test dependencies
```bash
pip install pytest pytest-cov
```

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test modules
```bash
pytest tests/test_cli.py -v          # CLI tests only
pytest tests/test_formatter.py -v    # Formatter tests only
pytest tests/test_github_client.py -v # GitHub client tests only
```

### Run tests with coverage
```bash
pytest tests/ --cov=gh_pr_rev_md --cov-report=html
```

## Test Coverage

The test suite covers:

### CLI Functionality (test_cli.py)
- ✅ URL parsing with valid and invalid formats
- ✅ Filename generation with auto-timestamps  
- ✅ File output with `--output` flag (auto-generated filename)
- ✅ File output with `--output-file` flag (custom filename)
- ✅ File precedence (`--output-file` over `--output`)
- ✅ UTF-8 encoding for files
- ✅ Error handling (permissions, invalid paths)
- ✅ Integration with `--include-resolved` flag
- ✅ Stdout output when no file flags provided
- ✅ Absolute path reporting in success messages

### GitHub Client (test_github_client.py) 
- ✅ API client initialization
- ✅ Successful PR comment retrieval
- ✅ Pagination handling
- ✅ Error handling (404, 403, 500)
- ✅ Resolved comment filtering logic

### Formatter (test_formatter.py)
- ✅ Markdown formatting for comments
- ✅ Timestamp formatting edge cases
- ✅ Unicode character handling
- ✅ Missing field handling
- ✅ Empty comment list handling

## Key Test Features

- **Mocking**: External dependencies (GitHub API, file system) are mocked
- **Isolation**: Tests use Click's `isolated_filesystem()` for safe file operations
- **Edge Cases**: Comprehensive coverage of error conditions and boundary cases
- **Deterministic**: Fixed timestamps and predictable outputs for reliable testing

## Adding New Tests

When adding new functionality:

1. Add unit tests for individual functions
2. Add integration tests for CLI commands
3. Use appropriate fixtures from `conftest.py`
4. Mock external dependencies
5. Test both success and failure scenarios