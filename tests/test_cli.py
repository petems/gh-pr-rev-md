"""Comprehensive tests for CLI functionality, focusing on file output features."""

import pytest
import subprocess
from click.testing import CliRunner
from unittest import mock
from pathlib import Path
from datetime import datetime
import yaml

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
    with mock.patch(
        "gh_pr_rev_md.cli.format_comments_as_markdown"
    ) as mock_formatter_func:
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


@pytest.mark.parametrize(
    "extra_args,expected_filename",
    [
        (["--output"], "owner-repo-20230115-123045-pr123.md"),
        (["--output-file", "my_custom_pr_review.md"], "my_custom_pr_review.md"),
    ],
)
def test_main_output_creates_expected_file(
    runner,
    mock_github_client,
    mock_formatter,
    mock_datetime_now,
    extra_args,
    expected_filename,
):
    """Test that output flags create files with correct names and content."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.main,
            [
                "https://github.com/owner/repo/pull/123",
                "--token",
                "test_token",
                *extra_args,
            ],
        )

        assert result.exit_code == 0
        assert Path(expected_filename).exists()

        content = Path(expected_filename).read_text(encoding="utf-8")
        assert content == "# PR #123 Review Comments\n\nMocked markdown output"

        assert "Output saved to:" in result.output
        assert expected_filename in result.output


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


def test_main_file_write_nested_directory_with_create_dirs(
    runner, mock_github_client, mock_formatter
):
    """Test file output to nested directory path when --create-dirs is used."""
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
                "--create-dirs",
            ],
        )

        assert result.exit_code == 0
        assert Path(nested_filename).exists()


def test_main_include_flags_integration(runner, mock_github_client, mock_formatter):
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


def test_main_no_pr_url_shows_help(runner):
    """Test that CLI shows help and exits cleanly when no PR_URL is given."""
    result = runner.invoke(cli.main, [])

    assert result.exit_code == 0
    assert "Usage: main [OPTIONS] [PR_URL]" in result.output
    assert "--help" in result.output


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

    # Ensure no token is set via environment variable or config file
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("gh_pr_rev_md.cli.load_config", lambda: {})

    result = runner.invoke(cli.main, ["https://github.com/owner/repo/pull/123"])

    assert result.exit_code == 0
    # In Click testing, stderr is often captured along with stdout in result.output
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
include_outdated: true
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
        # Verify include_outdated from config reached client
        mock_github_client.get_pr_review_comments.assert_called_once_with(
            "owner", "repo", 123, True, False
        )
        assert config_module is not None


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


# --- Tests for hybrid git detection functionality ---


def test_get_current_branch_pr_url_native_success():
    """Test native git parsing successfully finding PR."""
    with mock.patch("gh_pr_rev_md.cli.GitRepository") as mock_repo_class:
        mock_repo = mock_repo_class.return_value
        mock_repo.get_repository_info.return_value = (
            "github.com",
            "owner",
            "repo",
            "feature-branch",
        )

        with mock.patch("gh_pr_rev_md.cli.GitHubClient") as mock_client:
            mock_instance = mock.MagicMock()
            mock_instance.find_pr_by_branch.return_value = 123
            mock_client.return_value = mock_instance

            result = cli.get_current_branch_pr_url_native("fake-token")
            assert result == "https://github.com/owner/repo/pull/123"


def test_get_current_branch_pr_url_native_github_enterprise():
    """Test native git parsing with GitHub Enterprise."""
    with mock.patch("gh_pr_rev_md.cli.GitRepository") as mock_repo_class:
        mock_repo = mock_repo_class.return_value
        mock_repo.get_repository_info.return_value = (
            "github.enterprise.com",
            "company",
            "project",
            "main",
        )

        with mock.patch("gh_pr_rev_md.cli.GitHubClient") as mock_client:
            mock_instance = mock.MagicMock()
            mock_instance.find_pr_by_branch.return_value = 456
            mock_client.return_value = mock_instance

            result = cli.get_current_branch_pr_url_native("fake-token")
            assert result == "https://github.enterprise.com/company/project/pull/456"


def test_get_current_branch_pr_url_native_no_repo_info():
    """Test native git parsing when repository info cannot be determined."""
    with mock.patch("gh_pr_rev_md.cli.GitRepository") as mock_repo_class:
        mock_repo = mock_repo_class.return_value
        mock_repo.get_repository_info.return_value = None

        with pytest.raises(
            cli.GitParsingError, match="Unable to extract repository information"
        ):
            cli.get_current_branch_pr_url_native()


def test_get_current_branch_pr_url_hybrid_fallback():
    """Test hybrid approach falls back to subprocess when native parsing fails."""
    # Mock native parsing to fail
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        # Mock subprocess approach to succeed
        with mock.patch(
            "gh_pr_rev_md.cli.get_current_branch_pr_url_subprocess"
        ) as mock_subprocess:
            mock_subprocess.return_value = "https://github.com/owner/repo/pull/999"

            result = cli.get_current_branch_pr_url()
            assert result == "https://github.com/owner/repo/pull/999"
            mock_native.assert_called_once()
            mock_subprocess.assert_called_once()


def test_get_current_branch_pr_url_hybrid_native_success():
    """Test hybrid approach uses native parsing when it succeeds."""
    # Mock native parsing to succeed
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.return_value = "https://github.com/owner/repo/pull/123"

        # Mock subprocess approach (should not be called)
        with mock.patch(
            "gh_pr_rev_md.cli.get_current_branch_pr_url_subprocess"
        ) as mock_subprocess:
            result = cli.get_current_branch_pr_url()
            assert result == "https://github.com/owner/repo/pull/123"
            mock_native.assert_called_once()
            mock_subprocess.assert_not_called()


# --- Tests for "." argument functionality ---


def test_cli_with_period_argument_success(runner, mock_github_client, mock_formatter):
    """Test CLI with "." argument to use current branch PR."""
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url") as mock_get_pr_url:
        mock_get_pr_url.return_value = "https://github.com/owner/repo/pull/456"

        result = runner.invoke(cli.main, ["."])

        assert result.exit_code == 0
        mock_get_pr_url.assert_called_once()
        mock_github_client.get_pr_review_comments.assert_called_once_with(
            "owner", "repo", 456, False, False
        )


def test_cli_with_period_argument_error(runner):
    """Test CLI with "." argument when git operations fail."""
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url") as mock_get_pr_url:
        mock_get_pr_url.side_effect = cli.click.BadParameter("Not in a git repository")

        result = runner.invoke(cli.main, ["."])

        assert result.exit_code == 1
        assert "Not in a git repository" in result.output


def test_get_current_branch_pr_url_not_git_repo():
    """Test get_current_branch_pr_url when not in a git repository."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")

            with pytest.raises(cli.click.BadParameter) as exc_info:
                cli.get_current_branch_pr_url()
            assert "Git is not installed" in str(exc_info.value)


def test_get_current_branch_pr_url_no_git_dir():
    """Test get_current_branch_pr_url when not in a git repository."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git rev-parse")

            with pytest.raises(cli.click.BadParameter) as exc_info:
                cli.get_current_branch_pr_url()
            assert "Not in a git repository" in str(exc_info.value)


def _mock_subprocess_calls(*calls):
    """Helper to create subprocess mock with git config fallback added."""
    # Insert git config failure after git branch call for most tests
    if len(calls) >= 2 and calls[0].returncode == 0 and hasattr(calls[1], "stdout"):
        # Insert git config failure after first two successful calls (rev-parse, branch)
        calls_with_config = [
            calls[0],  # git rev-parse
            calls[1],  # git branch
            subprocess.CalledProcessError(
                1, "git config"
            ),  # git config fails (fallback to origin)
            *calls[2:],  # remaining calls
        ]
        return calls_with_config
    return calls


def test_get_current_branch_pr_url_no_origin_remote():
    """Test get_current_branch_pr_url when no origin remote is configured."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = _mock_subprocess_calls(
                mock.MagicMock(returncode=0),  # git rev-parse succeeds
                mock.MagicMock(returncode=0, stdout="main"),  # git branch succeeds
                subprocess.CalledProcessError(
                    1, "git remote get-url"
                ),  # git remote get-url fails
            )

            with pytest.raises(cli.click.BadParameter) as exc_info:
                cli.get_current_branch_pr_url()
            assert "No 'origin' remote found" in str(exc_info.value)


def test_get_current_branch_pr_url_invalid_remote_url():
    """Test get_current_branch_pr_url with invalid remote URL."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = _mock_subprocess_calls(
                mock.MagicMock(returncode=0),  # git rev-parse succeeds
                mock.MagicMock(returncode=0, stdout="main"),  # git branch succeeds
                mock.MagicMock(
                    returncode=0, stdout="https://gitlab.com/owner/repo.git"
                ),  # invalid remote
            )

            with pytest.raises(cli.click.BadParameter) as exc_info:
                cli.get_current_branch_pr_url()
            assert "Could not parse remote URL" in str(exc_info.value)


def test_get_current_branch_pr_url_success_with_api():
    """Test get_current_branch_pr_url successfully finding PR via GitHub API."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = _mock_subprocess_calls(
                mock.MagicMock(returncode=0),  # git rev-parse succeeds
                mock.MagicMock(
                    returncode=0, stdout="feature-branch"
                ),  # git branch succeeds
                mock.MagicMock(
                    returncode=0, stdout="https://github.com/owner/repo.git"
                ),  # remote URL
            )

            with mock.patch("gh_pr_rev_md.cli.GitHubClient") as mock_client:
                mock_instance = mock.MagicMock()
                mock_instance.find_pr_by_branch.return_value = 123
                mock_client.return_value = mock_instance

                result = cli.get_current_branch_pr_url("fake-token")
                assert result == "https://github.com/owner/repo/pull/123"


def test_get_current_branch_pr_url_success_with_gh_cli():
    """Test get_current_branch_pr_url successfully finding PR via GitHub CLI."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = _mock_subprocess_calls(
                mock.MagicMock(returncode=0),  # git rev-parse succeeds
                mock.MagicMock(
                    returncode=0, stdout="feature-branch"
                ),  # git branch succeeds
                mock.MagicMock(
                    returncode=0, stdout="https://github.com/owner/repo.git"
                ),  # remote URL
                mock.MagicMock(
                    returncode=0, stdout="https://github.com/owner/repo/pull/456"
                ),  # gh pr view succeeds
            )

            result = cli.get_current_branch_pr_url()
            assert result == "https://github.com/owner/repo/pull/456"


def test_get_current_branch_pr_url_no_pr_found():
    """Test get_current_branch_pr_url when no PR is found for the branch."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = _mock_subprocess_calls(
                mock.MagicMock(returncode=0),  # git rev-parse succeeds
                mock.MagicMock(
                    returncode=0, stdout="feature-branch"
                ),  # git branch succeeds
                mock.MagicMock(
                    returncode=0, stdout="https://github.com/owner/repo.git"
                ),  # remote URL
                subprocess.CalledProcessError(1, "gh pr view"),  # gh pr view fails
            )

            with pytest.raises(cli.click.BadParameter) as exc_info:
                cli.get_current_branch_pr_url()
            assert "No open pull request found" in str(exc_info.value)


def test_get_current_branch_pr_url_detached_head():
    """Test get_current_branch_pr_url when in detached HEAD state."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                mock.MagicMock(returncode=0),  # git rev-parse succeeds
                mock.MagicMock(
                    returncode=0, stdout=""
                ),  # git branch returns empty (detached HEAD)
            ]

            with pytest.raises(cli.click.BadParameter) as exc_info:
                cli.get_current_branch_pr_url()
            assert "Could not determine current branch" in str(exc_info.value)


def test_get_current_branch_pr_url_ssh_remote():
    """Test get_current_branch_pr_url with SSH remote URL."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = _mock_subprocess_calls(
                mock.MagicMock(returncode=0),  # git rev-parse succeeds
                mock.MagicMock(
                    returncode=0, stdout="feature-branch"
                ),  # git branch succeeds
                mock.MagicMock(
                    returncode=0, stdout="git@github.com:owner/repo.git"
                ),  # SSH remote URL
            )

            with mock.patch("gh_pr_rev_md.cli.GitHubClient") as mock_client:
                mock_instance = mock.MagicMock()
                mock_instance.find_pr_by_branch.return_value = 789
                mock_client.return_value = mock_instance

                result = cli.get_current_branch_pr_url("fake-token")
                assert result == "https://github.com/owner/repo/pull/789"


def test_get_current_branch_pr_url_api_fallback_to_gh_cli():
    """Test get_current_branch_pr_url falls back to GitHub CLI when API fails."""
    # Mock native parsing to fail, triggering subprocess fallback
    with mock.patch("gh_pr_rev_md.cli.get_current_branch_pr_url_native") as mock_native:
        mock_native.side_effect = cli.GitParsingError("Native parsing failed")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = _mock_subprocess_calls(
                mock.MagicMock(returncode=0),  # git rev-parse succeeds
                mock.MagicMock(
                    returncode=0, stdout="feature-branch"
                ),  # git branch succeeds
                mock.MagicMock(
                    returncode=0, stdout="https://github.com/owner/repo.git"
                ),  # remote URL
                mock.MagicMock(
                    returncode=0, stdout="https://github.com/owner/repo/pull/999"
                ),  # gh pr view succeeds
            )

            with mock.patch("gh_pr_rev_md.cli.GitHubClient") as mock_client:
                mock_instance = mock.MagicMock()
                mock_instance.find_pr_by_branch.side_effect = (
                    github_client.GitHubAPIError("API failed")
                )
                mock_client.return_value = mock_instance

                result = cli.get_current_branch_pr_url("fake-token")
                assert result == "https://github.com/owner/repo/pull/999"


def test_get_current_branch_pr_url_subprocess_branch_error(monkeypatch):
    """Branch retrieval errors should raise a helpful Click exception."""

    def run_side_effect(
        cmd, capture_output=True, text=True, check=True
    ):  # pragma: no cover - type annotated
        if cmd[:3] == ["git", "rev-parse", "--git-dir"]:
            return subprocess.CompletedProcess(cmd, 0, stdout=".git\n")
        raise subprocess.CalledProcessError(1, cmd, "error")

    monkeypatch.setattr(cli.subprocess, "run", run_side_effect)

    with pytest.raises(cli.click.BadParameter, match="Failed to get current branch"):
        cli.get_current_branch_pr_url_subprocess()


def test_get_current_branch_pr_url_subprocess_no_pr(monkeypatch):
    """When no PR is found, a helpful error is raised."""

    responses = [
        subprocess.CompletedProcess(["git"], 0, stdout=".git\n"),
        subprocess.CompletedProcess(["git"], 0, stdout="feature\n"),
        subprocess.CompletedProcess(["git"], 0, stdout="origin\n"),
        subprocess.CompletedProcess(
            ["git"], 0, stdout="https://github.com/owner/repo.git\n"
        ),
        subprocess.CalledProcessError(1, ["gh"], "no pr"),
    ]

    def run_side_effect(
        cmd, capture_output=True, text=True, check=True
    ):  # pragma: no cover - type annotated
        result = responses.pop(0)
        if isinstance(result, subprocess.CalledProcessError):
            raise result
        return result

    monkeypatch.setattr(cli.subprocess, "run", run_side_effect)

    with pytest.raises(cli.click.BadParameter, match="No open pull request found"):
        cli.get_current_branch_pr_url_subprocess()


def test_get_current_branch_pr_url_native_fallback(monkeypatch):
    """Native parser falls back to subprocess and surfaces errors."""

    mock_repo = mock.MagicMock()
    mock_repo.get_repository_info.return_value = (
        "github.com",
        "owner",
        "repo",
        "main",
    )
    monkeypatch.setattr(cli, "GitRepository", lambda: mock_repo)

    mock_client = mock.MagicMock()
    mock_client.find_pr_by_branch.side_effect = github_client.GitHubAPIError("boom")
    monkeypatch.setattr(cli, "GitHubClient", lambda token: mock_client)

    def run_side_effect(
        cmd, capture_output=True, text=True, check=True
    ):  # pragma: no cover - type annotated
        raise subprocess.CalledProcessError(1, cmd, "error")

    monkeypatch.setattr(cli.subprocess, "run", run_side_effect)

    with pytest.raises(cli.click.BadParameter, match="No open pull request found"):
        cli.get_current_branch_pr_url_native("token")


def test_get_current_branch_pr_url_native_gh_cli_success(monkeypatch):
    """Native git parsing uses gh CLI when API fails."""

    mock_repo = mock.MagicMock()
    mock_repo.get_repository_info.return_value = (
        "github.com",
        "owner",
        "repo",
        "main",
    )
    monkeypatch.setattr(cli, "GitRepository", lambda: mock_repo)

    mock_client = mock.MagicMock()
    mock_client.find_pr_by_branch.side_effect = github_client.GitHubAPIError("boom")
    monkeypatch.setattr(cli, "GitHubClient", lambda token: mock_client)

    responses = [
        subprocess.CompletedProcess(
            ["gh"], 0, stdout="https://github.com/owner/repo/pull/5\n"
        ),
    ]

    def run_side_effect(
        cmd, capture_output=True, text=True, check=True
    ):  # pragma: no cover - type annotated
        return responses.pop(0)

    monkeypatch.setattr(cli.subprocess, "run", run_side_effect)

    result = cli.get_current_branch_pr_url_native("token")
    assert result == "https://github.com/owner/repo/pull/5"


def test_interactive_config_setup_new_config(tmp_path, monkeypatch):
    """Interactive config setup handles browser errors and chmod failures."""

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_dir = tmp_path / "gh-pr-rev-md"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_bytes(b"\xff")

    confirms = iter([True, True, True])
    monkeypatch.setattr(cli.click, "confirm", lambda *a, **k: next(confirms))
    monkeypatch.setattr(cli.click, "prompt", lambda *a, **k: "new_token")
    monkeypatch.setattr(
        cli.webbrowser,
        "open",
        lambda *a, **k: (_ for _ in ()).throw(OSError("no browser")),
    )
    monkeypatch.setattr(
        cli.os,
        "chmod",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError("no chmod")),
    )

    cli._interactive_config_setup()
    assert (config_dir / "config.yaml").exists()


def test_interactive_config_setup_existing_token(tmp_path, monkeypatch):
    """Existing config is loaded and token can be replaced."""

    config_dir = tmp_path / "gh-pr-rev-md"
    config_dir.mkdir(parents=True)
    (config_dir / "config.yaml").write_text(yaml.safe_dump({"token": "old"}))

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    confirms = iter([False, False, False, False])
    monkeypatch.setattr(cli.click, "confirm", lambda *a, **k: next(confirms))
    monkeypatch.setattr(cli.click, "prompt", lambda *a, **k: "replacement")
    monkeypatch.setattr(cli.webbrowser, "open", lambda *a, **k: None)
    monkeypatch.setattr(cli.os, "chmod", lambda *a, **k: None)

    cli._interactive_config_setup()

    data = yaml.safe_load((config_dir / "config.yaml").read_text())
    assert data["token"] == "replacement"


def test_interactive_config_setup_open_success(tmp_path, monkeypatch):
    """Browser launch path runs without errors."""

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    confirms = iter([True, True, True])
    monkeypatch.setattr(cli.click, "confirm", lambda *a, **k: next(confirms))
    monkeypatch.setattr(cli.click, "prompt", lambda *a, **k: "token")
    monkeypatch.setattr(cli.webbrowser, "open", lambda *a, **k: None)
    monkeypatch.setattr(cli.os, "chmod", lambda *a, **k: None)

    cli._interactive_config_setup()
    assert (tmp_path / "gh-pr-rev-md" / "config.yaml").exists()


def test_main_config_set_success(runner, monkeypatch):
    """--config-set exits cleanly on success."""

    monkeypatch.setattr(cli, "_interactive_config_setup", lambda: None)
    result = runner.invoke(cli.main, ["--config-set"])
    assert result.exit_code == 0


def test_main_config_set_error(runner, monkeypatch):
    """Errors during config setup exit with status 1."""

    def bad_setup():
        raise yaml.YAMLError("bad")

    monkeypatch.setattr(cli, "_interactive_config_setup", bad_setup)
    result = runner.invoke(cli.main, ["--config-set"])
    assert result.exit_code == 1
    assert "Error during config setup" in result.output


def test_main_missing_pr_url_shows_help(runner, monkeypatch):
    """Running without PR URL shows help and exits cleanly (new behavior)."""

    monkeypatch.setattr(cli, "load_config", lambda: {})
    result = runner.invoke(cli.main, [])
    assert result.exit_code == 0
    assert "Usage: main [OPTIONS] [PR_URL]" in result.output
