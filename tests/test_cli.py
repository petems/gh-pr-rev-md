"""Comprehensive tests for CLI functionality, focusing on file output features."""

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
            },
            {
                "id": 2,
                "user": {"login": "anotheruser"},
                "body": "Test comment 2",
                "created_at": "2023-01-01T11:00:00Z",
                "updated_at": "2023-01-01T11:00:00Z",
                "path": "file2.js",
                "diff_hunk": "@@ -5,2 +5,3 @@",
                "line": 20,
            },
        ]
        yield mock_instance


@pytest.fixture
def mock_formatter():
    """Mocks the format_comments_as_markdown function."""
    with mock.patch("gh_pr_rev_md.cli.format_comments_as_markdown") as mock_formatter_func:
        mock_formatter_func.return_value = (
            "# PR #123 Review Comments\n\nMocked markdown output"
        )
        yield mock_formatter_func


@pytest.fixture
def mock_datetime_now():
    """Mocks datetime.now() for deterministic timestamp generation."""
    with mock.patch("gh_pr_rev_md.cli.datetime") as mock_dt:
        fixed_time = datetime(2023, 1, 15, 12, 30, 45)
        mock_dt.now.return_value = fixed_time
        yield mock_dt


# --- Tests for parse_pr_url function ---


def test_parse_pr_url_valid():
    """Test that parse_pr_url correctly extracts components from valid URLs."""
    test_cases = [
        ("https://github.com/owner/repo/pull/123", ("owner", "repo", 123)),
        (
            "https://github.com/microsoft/vscode/pull/999999",
            ("microsoft", "vscode", 999999),
        ),
        ("https://github.com/a/b/pull/1", ("a", "b", 1)),
        (
            "https://github.com/owner-dash/repo_under/pull/456",
            ("owner-dash", "repo_under", 456),
        ),
    ]

    for url, expected in test_cases:
        owner, repo, pr_number = cli.parse_pr_url(url)
        assert (owner, repo, pr_number) == expected


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://github.com/owner/repo/pull/123",  # HTTP instead of HTTPS
        "https://github.com/owner/repo/pull/",  # Missing PR number
        "https://github.com/owner/pull/123",  # Missing repo
        "https://github.com/owner/repo/issues/123",  # Issues instead of pull
        "https://gitlab.com/owner/repo/pull/123",  # Wrong domain
        "invalid-url",  # Completely invalid
        "",  # Empty string
        "https://github.com/owner/repo/pull/abc",  # Non-numeric PR number
    ],
)
def test_parse_pr_url_invalid(invalid_url):
    """Test that parse_pr_url raises click.BadParameter for invalid URLs."""
    with pytest.raises(cli.click.BadParameter):
        cli.parse_pr_url(invalid_url)


# --- Tests for generate_filename function ---


def test_generate_filename_format(mock_datetime_now):
    """Test that generate_filename produces the expected format."""
    filename = cli.generate_filename("owner", "repo", 123)
    expected = "owner-repo-20230115-123045-pr123.md"
    assert filename == expected


def test_generate_filename_edge_cases(mock_datetime_now):
    """Test generate_filename with edge case inputs."""
    test_cases = [
        ("", "repo", 123, "-repo-20230115-123045-pr123.md"),
        ("owner", "", 456, "owner--20230115-123045-pr456.md"),
        ("UPPER", "MixedCase", 1, "UPPER-MixedCase-20230115-123045-pr1.md"),
        ("owner.dot", "repo@symbol", 0, "owner.dot-repo@symbol-20230115-123045-pr0.md"),
    ]

    for owner, repo, pr_number, expected in test_cases:
        filename = cli.generate_filename(owner, repo, pr_number)
        assert filename == expected


# --- Tests for main CLI command file output functionality ---


def test_main_output_flag_auto_filename(
    runner, mock_github_client, mock_formatter, mock_datetime_now
):
    """Test --output flag creates file with auto-generated filename."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                "--output",
            ],
        )

        assert result.exit_code == 0
        expected_filename = "owner-repo-20230115-123045-pr123.md"
        assert Path(expected_filename).exists()

        content = Path(expected_filename).read_text(encoding="utf-8")
        assert content == "# PR #123 Review Comments\n\nMocked markdown output"

        assert "Output saved to:" in result.output
        assert expected_filename in result.output


def test_main_output_file_flag_custom_filename(
    runner, mock_github_client, mock_formatter
):
    """Test --output-file flag creates file with custom filename."""
    with runner.isolated_filesystem():
        custom_filename = "my_custom_pr_review.md"
        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                "--output-file",
                custom_filename,
            ],
        )

        assert result.exit_code == 0
        assert Path(custom_filename).exists()

        content = Path(custom_filename).read_text(encoding="utf-8")
        assert content == "# PR #123 Review Comments\n\nMocked markdown output"

        assert "Output saved to:" in result.output
        assert custom_filename in result.output


def test_main_output_file_precedence(
    runner, mock_github_client, mock_formatter, mock_datetime_now
):
    """Test that --output-file takes precedence over --output when both are provided."""
    with runner.isolated_filesystem():
        custom_filename = "explicit_file.md"
        auto_filename = "owner-repo-20230115-123045-pr123.md"

        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                "--output",
                "--output-file",
                custom_filename,
            ],
        )

        assert result.exit_code == 0
        assert Path(custom_filename).exists()
        assert not Path(auto_filename).exists()  # Auto-generated file should NOT exist

        assert custom_filename in result.output
        assert auto_filename not in result.output


def test_main_no_output_flags_stdout(runner, mock_github_client, mock_formatter):
    """Test that output goes to stdout when no output flags are provided."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            ["https://github.com/owner/repo/pull/123", "--token", "test_token"],
        )

        assert result.exit_code == 0
        # Verify no files were created
        assert list(Path(".").glob("*.md")) == []

        # Verify output contains the markdown content directly
        assert "# PR #123 Review Comments" in result.output
        assert "Mocked markdown output" in result.output


def test_main_file_write_permission_error(runner, mock_github_client, mock_formatter):
    """Test error handling when file write fails due to permissions."""
    with runner.isolated_filesystem():
        # Create a directory with the same name as our intended file
        restricted_filename = "restricted.md"
        Path(restricted_filename).mkdir()  # This will cause write to fail

        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                "--output-file",
                restricted_filename,
            ],
        )

        assert result.exit_code == 1
        assert "Error writing to file" in result.output
        assert restricted_filename in result.output


def test_main_file_write_nested_directory(runner, mock_github_client, mock_formatter):
    """Test file output to nested directory path."""
    with runner.isolated_filesystem():
        nested_filename = "nested/dir/output.md"

        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                "--output-file",
                nested_filename,
            ],
        )

        # This should fail because parent directories don't exist
        assert result.exit_code == 1
        assert "Error writing to file" in result.output


def test_main_include_flags_integration(
    runner, mock_github_client, mock_formatter
):
    """Test that --include-resolved and --include-outdated flags work."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                "--include-resolved",
                "--include-outdated",
                "--output",
            ],
        )

        assert result.exit_code == 0
        # Verify flags were passed to GitHub client
        mock_github_client.get_pr_review_comments.assert_called_once_with(
            "owner", "repo", 123, True, True
        )


def test_main_utf8_encoding(runner, mock_github_client, mock_formatter):
    """Test that files are written with UTF-8 encoding."""
    # Mock formatter to return content with unicode characters
    mock_formatter.return_value = "# PR Review\n\n👍 Looks good! 中文测试"

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                "--output-file",
                "unicode_test.md",
            ],
        )

        assert result.exit_code == 0
        content = Path("unicode_test.md").read_text(encoding="utf-8")
        assert "👍" in content
        assert "中文测试" in content


# --- Tests for error conditions ---


def test_main_no_token_warning_allows_run(runner, monkeypatch):
    """When no token is provided, CLI warns but proceeds (unauthenticated)."""
    # Prevent real network calls by mocking GitHubClient.get_pr_review_comments
    from gh_pr_rev_md import cli as cli_module

    monkeypatch.setattr(
        cli_module.GitHubClient,
        "get_pr_review_comments",
        lambda self, owner, repo, pr, include_outdated=None, include_resolved=None: [],
        raising=True,
    )

    result = runner.invoke(cli.main, ["https://github.com/owner/repo/pull/123"])

    assert result.exit_code == 0
    assert "Unauthenticated requests are limited" in result.output


def test_main_invalid_url_error(runner):
    """Test CLI exits with error for invalid PR URL."""
    result = runner.invoke(cli.main, ["invalid-url", "--token", "test_token"])

    assert result.exit_code == 1
    assert "Invalid GitHub PR URL format" in result.output


def test_main_github_api_error(runner, mock_github_client):
    """Test CLI handles GitHub API errors gracefully."""
    mock_github_client.get_pr_review_comments.side_effect = (
        github_client.GitHubAPIError("PR not found")
    )

    result = runner.invoke(
        cli.main, ["https://github.com/owner/repo/pull/123", "--token", "test_token"]
    )

    assert result.exit_code == 1
    assert "Error fetching data from GitHub: PR not found" in result.output


def test_main_github_api_generic_error(runner, mock_github_client):
    """Test CLI handles unexpected exceptions during API calls."""
    mock_github_client.get_pr_review_comments.side_effect = Exception("Network timeout")

    result = runner.invoke(
        cli.main, ["https://github.com/owner/repo/pull/123", "--token", "test_token"]
    )

    assert result.exit_code == 1
    assert "An unexpected error occurred: Network timeout" in result.output


def test_main_absolute_path_reporting(runner, mock_github_client, mock_formatter):
    """Test that success message shows absolute path of created file."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                "--output-file",
                "test.md",
            ],
        )

        assert result.exit_code == 0
        # Check that absolute path is shown in output
        assert str(Path("test.md").absolute()) in result.output


def test_config_applies_when_cli_missing(
    runner, mock_github_client, mock_formatter, tmp_path, monkeypatch
):
    """If CLI flags are not provided, values from XDG YAML config are used."""
    xdg_home = tmp_path / ".config"
    app_dir = xdg_home / "gh-pr-rev-md"
    app_dir.mkdir(parents=True)
    (app_dir / "config.yaml").write_text(
        """
output_file: config_output.md
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
            ],
        )

        assert result.exit_code == 0
        assert Path("config_output.md").exists()
        config_module  # reference to avoid unused import warnings


def test_cli_overrides_config(
    runner, mock_github_client, mock_formatter, tmp_path, monkeypatch
):
    """CLI options should override configuration file values."""
    xdg_home = tmp_path / ".config"
    app_dir = xdg_home / "gh-pr-rev-md"
    app_dir.mkdir(parents=True)
    (app_dir / "config.yaml").write_text(
        """
output_file: from_config.md
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "cli_token",
                "--include-outdated",
                "--output-file",
                "from_cli.md",
            ],
        )

        assert result.exit_code == 0
        assert Path("from_cli.md").exists()
        assert not Path("from_config.md").exists()
