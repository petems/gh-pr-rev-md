# Project Overview

This project provides a command-line tool named `gh-pr-rev-md` to fetch review comments from a GitHub Pull Request and format them into a clean Markdown document. It's written in Python and uses the `click` library for its command-line interface, `requests` for interacting with the GitHub GraphQL API, and `PyYAML` for handling configuration.

The tool is designed to be flexible, allowing users to provide a GitHub token via command-line options, environment variables, or a YAML configuration file. It supports both printing the output to the console and saving it to a file.

## Building and Running

### Installation

To install the necessary dependencies, run the following command:

```bash
uv pip install .
```

To include the development dependencies for testing and linting, use:

```bash
uv pip install .[dev]
```

### Running the tool

To run the tool, you need to provide a GitHub PR URL. You can also provide a GitHub token to avoid rate limiting.

```bash
# Using an environment variable for the token
export GITHUB_TOKEN=your_github_token_here
gh-pr-rev-md https://github.com/owner/repo/pull/123

# Passing the token as an option
gh-pr-rev-md --token your_token https://github.com/owner/repo/pull/123
```

### Running Tests

The project uses `pytest` for testing. To run the tests, first install the development dependencies and then run `pytest`:

```bash
uv pip install .[dev]
pytest
```

The `README.md` also suggests running tests in parallel with randomized order:

```bash
PYTEST_ADDOPTS="--randomly-seed=$(date +%s)" pytest -n auto -q
```

## Development Conventions

### Code Style

The project uses `ruff` for linting. While the specific configuration is not detailed in the files I've read, it's a good practice to run `ruff check .` to ensure your changes adhere to the project's style.

### Testing

The project has a `tests/` directory with tests for the CLI, formatter, and GitHub client. This indicates a convention of writing unit tests for new functionality.

### Configuration

The application follows the XDG Base Directory Specification for configuration files, looking for `config.yaml` in `~/.config/gh-pr-rev-md/`. This is the preferred way to configure the tool for regular use.
