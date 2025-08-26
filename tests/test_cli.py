"""Comprehensive tests for CLI functionality."""

import pytest
from click.testing import CliRunner
from unittest import mock
from pathlib import Path
from datetime import datetime

from gh_pr_rev_md import cli
from gh_pr_rev_md import github_client
from gh_pr_rev_md import config as config_module


# --- Fixtures ---


@pytest.fixture
def runner():
    """Fixture for Click's CliRunner to invoke CLI commands."""
    return CliRunner()


@pytest.fixture
def mock_github_client():
    """Mocks the GitHubClient to control API responses."""
    with mock.patch("gh_pr_rev_md.cli.GitHubClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_pr_review_comments.return_value = [
            {
                "id": 1,
                "user": {"login": "testuser"},
                "body": "Test comment 1",
                "created_at": "2023-01-01T10:00:00Z",
                "updated_at": "2023-01-01T10:00:00Z",
                "path": "file1.py",
                "diff_hunk": "@@ -1,3 +1,3 @@",
                "line": 10,
            }
        ]
        mock_instance.get_authenticated_user.return_value = "testuser"
        yield mock_instance


@pytest.fixture
def mock_formatter():
    """Mocks the format_comments_as_markdown function."""
    with mock.patch(
        "gh_pr_rev_md.cli.format_comments_as_markdown"
    ) as mock_formatter_func:
        mock_formatter_func.return_value = "Mocked markdown output"
        yield mock_formatter_func


@pytest.fixture
def mock_datetime_now():
    """Mocks datetime.now() for deterministic timestamp generation."""
    with mock.patch("gh_pr_rev_md.cli.datetime") as mock_dt:
        fixed_time = datetime(2023, 1, 15, 12, 30, 45)
        mock_dt.now.return_value = fixed_time
        yield mock_dt


@pytest.fixture
def mock_config_file(tmp_path, monkeypatch):
    """Fixture to create a temporary config file and set XDG_CONFIG_HOME."""
    xdg_home = tmp_path / ".config"
    app_dir = xdg_home / "gh-pr-rev-md"
    app_dir.mkdir(parents=True)
    config_file = app_dir / "config.yaml"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))
    return config_file


# --- Tests for helper functions ---


def test_parse_pr_url_valid():
    """Test that parse_pr_url correctly extracts components from valid URLs."""
    owner, repo, pr_number = cli.parse_pr_url(
        "https://github.com/owner/repo/pull/123"
    )
    assert (owner, repo, pr_number) == ("owner", "repo", 123)


def test_parse_pr_url_invalid(runner):
    """Test that parse_pr_url raises click.BadParameter for invalid URLs."""
    with pytest.raises(cli.click.BadParameter):
        cli.parse_pr_url("invalid-url")


def test_generate_filename_format(mock_datetime_now):
    """Test that generate_filename produces the expected format."""
    filename = cli.generate_filename("owner", "repo", 123)
    assert filename == "owner-repo-20230115-123045-pr123.md"


# --- Tests for 'fetch' command ---


class TestFetchCommand:
    """Tests for the 'fetch' subcommand."""

    def test_fetch_output_flag(
        self, runner, mock_github_client, mock_formatter, mock_datetime_now
    ):
        """Test 'fetch --output' creates file with auto-generated name."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli.main,
                ["fetch", "https://github.com/owner/repo/pull/123", "--output"],
            )
            assert result.exit_code == 0
            expected_filename = "owner-repo-20230115-123045-pr123.md"
            assert Path(expected_filename).exists()
            assert "Output saved to" in result.output

    def test_fetch_output_file_flag(self, runner, mock_github_client, mock_formatter):
        """Test 'fetch --output-file' creates file with custom name."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli.main,
                [
                    "fetch",
                    "https://github.com/owner/repo/pull/123",
                    "--output-file",
                    "custom.md",
                ],
            )
            assert result.exit_code == 0
            assert Path("custom.md").exists()

    def test_fetch_no_output_flags_stdout(
        self, runner, mock_github_client, mock_formatter
    ):
        """Test fetch output goes to stdout when no output flags are provided."""
        result = runner.invoke(
            cli.main, ["fetch", "https://github.com/owner/repo/pull/123"]
        )
        assert result.exit_code == 0
        assert "Mocked markdown output" in result.output

    def test_fetch_include_flags(self, runner, mock_github_client):
        """Test that --include-resolved and --include-outdated flags are passed."""
        runner.invoke(
            cli.main,
            [
                "fetch",
                "https://github.com/owner/repo/pull/123",
                "--include-resolved",
                "--include-outdated",
            ],
        )
        mock_github_client.get_pr_review_comments.assert_called_once_with(
            "owner", "repo", 123, True, True
        )

    def test_fetch_api_error(self, runner, mock_github_client):
        """Test 'fetch' handles GitHub API errors gracefully."""
        mock_github_client.get_pr_review_comments.side_effect = (
            github_client.GitHubAPIError("API Error")
        )
        result = runner.invoke(
            cli.main, ["fetch", "https://github.com/owner/repo/pull/123"]
        )
        assert result.exit_code == 1
        assert "Error fetching data from GitHub: API Error" in result.output


# --- Tests for 'config' subcommands ---


class TestConfigCommands:
    """Tests for the 'config' subcommands."""

    def test_config_get_no_config(self, runner, monkeypatch):
        """Test 'config get' when no config file exists."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/nonexistent-dir")
        result = runner.invoke(cli.main, ["config", "get"])
        assert result.exit_code == 0
        assert "No configuration found." in result.output

    def test_config_get_redacts_token(self, runner, mock_config_file):
        """Test that 'config get' redacts the token by default."""
        mock_config_file.write_text("token: my-secret-token", encoding="utf-8")
        result = runner.invoke(cli.main, ["config", "get"])
        assert result.exit_code == 0
        assert "token: '********'" in result.output

    def test_config_get_show_token(self, runner, mock_config_file):
        """Test 'config get --show-token' displays the token."""
        mock_config_file.write_text("token: my-secret-token", encoding="utf-8")
        result = runner.invoke(cli.main, ["config", "get", "--show-token"])
        assert result.exit_code == 0
        assert "token: my-secret-token" in result.output

    def test_config_check_no_token(self, runner, monkeypatch):
        """Test 'config check' when no token is configured."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr("gh_pr_rev_md.cli.load_config", lambda: {})
        result = runner.invoke(cli.main, ["config", "check"])
        assert result.exit_code == 1
        assert "FAILED: GitHub token is not configured" in result.output

    def test_config_check_valid_token(self, runner, mock_github_client):
        """Test 'config check' with a valid token."""
        result = runner.invoke(cli.main, ["--token", "valid-token", "config", "check"])
        assert result.exit_code == 0
        assert "Token is valid" in result.output

    def test_config_check_invalid_token(self, runner, mock_github_client):
        """Test 'config check' with an invalid token."""
        mock_github_client.get_authenticated_user.side_effect = (
            github_client.GitHubAPIError("Bad credentials")
        )
        result = runner.invoke(
            cli.main, ["--token", "invalid-token", "config", "check"]
        )
        assert result.exit_code == 1
        assert "FAILED: Token is invalid" in result.output


# --- Tests for default command and argument passing ---


def test_default_command_is_fetch(runner, mock_github_client):
    """Test that running the CLI without a command defaults to 'fetch'."""
    result = runner.invoke(cli.main, ["https://github.com/owner/repo/pull/123"])
    assert result.exit_code == 0
    mock_github_client.get_pr_review_comments.assert_called_once()


def test_no_pr_url_error(runner):
    """Test that 'fetch' command exits if no PR_URL is provided."""
    result = runner.invoke(cli.main, ["fetch"])
    assert result.exit_code == 2  # click.UsageError
    assert "Missing argument 'PR_URL'" in result.output


def test_no_command_error(runner):
    """Test that running the CLI with no args shows help for the main command."""
    result = runner.invoke(cli.main, [])
    assert result.exit_code == 2
    assert "Usage: main [OPTIONS] COMMAND [ARGS]..." in result.output
