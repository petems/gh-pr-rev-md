"""CLI interface for GitHub PR review comments tool."""

import os
import re
import sys
import webbrowser
import subprocess  # nosec B404  # Required for git/gh CLI integration
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import click
import yaml

from .config import load_config
from .formatter import format_comments_as_markdown
from .git_utils import GitParsingError, GitRepository
from .github_client import GitHubAPIError, GitHubClient

GITHUB_TOKEN_URL = "https://github.com/settings/tokens/new?scopes=repo,read:org&description=gh-pr-rev-md%20CLI%20(read%20PR%20comments)"  # nosec B105  # URL for token creation, not a password


def get_version() -> str:
    """Get version information for the application.
    
    Returns version information in priority order:
    1. Git tag if on a tagged commit
    2. Git commit hash + branch if in git repository
    3. Package version from pyproject.toml as fallback
    
    Returns:
        Formatted version string
    """
    try:
        # Try git-based version detection first
        repo = GitRepository()
        git_version = repo.get_version_info()
        
        if git_version != "unknown":
            return git_version
            
    except GitParsingError:
        # Not in a git repository or git parsing failed
        pass
    
    # Fallback to package version
    try:
        # Try to get version from package metadata
        import importlib.metadata
        package_version = importlib.metadata.version("gh-pr-rev-md")
        return f"{package_version} (from package)"
    except (ImportError, importlib.metadata.PackageNotFoundError):
        # Final fallback if package metadata not available
        return "0.1.0 (from package)"


def get_current_branch_pr_url_subprocess(token: Optional[str] = None) -> str:
    """Get the PR URL for the current git branch.
    
    Returns the PR URL for the current branch, or raises an exception with a helpful message.
    """
    try:
        # Check if we're in a git repository
        result = subprocess.run(  # nosec B603 B607  # Safe: hardcoded git command with controlled args
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError:
        raise click.BadParameter(
            "Not in a git repository. Please run this command from within a git repository."
        )
    except FileNotFoundError:
        raise click.BadParameter(
            "Git is not installed or not available in PATH. Please install git and try again."
        )

    try:
        # Get the current branch name
        result = subprocess.run(  # nosec B603 B607  # Safe: hardcoded git command with controlled args
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = result.stdout.strip()
        
        if not current_branch:
            raise click.BadParameter(
                "Could not determine current branch. Are you in a detached HEAD state?"
            )
    except subprocess.CalledProcessError as e:
        raise click.BadParameter(f"Failed to get current branch: {e}")

    # Determine the remote name to use
    try:
        remote_name_result = subprocess.run(  # nosec B603 B607  # Safe: hardcoded git command with controlled args
            ["git", "config", f"branch.{current_branch}.remote"],
            capture_output=True, text=True, check=True
        )
        remote_name = remote_name_result.stdout.strip()
    except subprocess.CalledProcessError:
        remote_name = "origin"  # Fallback to origin

    try:
        # Get the remote URL to determine owner/repo
        result = subprocess.run(  # nosec B603 B607  # Safe: hardcoded git command with controlled args
            ["git", "remote", "get-url", remote_name],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        
        # Handle both SSH and HTTPS URLs
        if remote_url.startswith("git@"):
            # SSH format: git@github.com:owner/repo.git
            match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
        else:
            # HTTPS format: https://github.com/owner/repo.git
            match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
        
        if not match:
            raise click.BadParameter(
                f"Could not parse remote URL: {remote_url}. Expected GitHub repository."
            )
        
        owner, repo = match.groups()
        
    except subprocess.CalledProcessError:
        raise click.BadParameter(
            f"No '{remote_name}' remote found or it is misconfigured. Please ensure your repository has a valid GitHub remote."
        )

    # Try to find the PR for the current branch using GitHub API
    if token:
        try:
            client = GitHubClient(token)
            pr_number = client.find_pr_by_branch(owner, repo, current_branch)
            if pr_number:
                return f"https://github.com/{owner}/{repo}/pull/{pr_number}"
        except GitHubAPIError:
            # API call failed, continue to fallback methods
            pass

    # Try to find the PR for the current branch using GitHub CLI
    try:
        result = subprocess.run(  # nosec B603 B607  # Safe: hardcoded gh command with controlled args
            ["gh", "pr", "view", "--json", "url", "--jq", ".url"],
            capture_output=True,
            text=True,
            check=True
        )
        pr_url = result.stdout.strip()
        if pr_url:
            return pr_url
    except (subprocess.CalledProcessError, FileNotFoundError):
        # GitHub CLI not available or no PR found
        pass

    # If we get here, we couldn't find a PR for the current branch
    raise click.BadParameter(
        f"No open pull request found for branch '{current_branch}' in {owner}/{repo}. "
        "Please ensure there is an open PR for the current branch."
    )


def get_current_branch_pr_url(token: Optional[str] = None) -> str:
    """Get the PR URL for the current git branch using hybrid approach.
    
    Tries native git parsing first, falls back to subprocess calls if needed.
    
    Args:
        token: Optional GitHub token for API calls
        
    Returns:
        The PR URL for the current branch
        
    Raises:
        click.BadParameter: If unable to determine PR URL
    """
    try:
        # Try native git parsing first (fast path)
        return get_current_branch_pr_url_native(token)
    except GitParsingError:
        # Fall back to subprocess approach (compatibility path)
        return get_current_branch_pr_url_subprocess(token)


def get_current_branch_pr_url_native(token: Optional[str] = None) -> str:
    """Get the PR URL using native git parsing (no subprocess calls).
    
    Args:
        token: Optional GitHub token for API calls
        
    Returns:
        The PR URL for the current branch
        
    Raises:
        GitParsingError: If git parsing fails
        click.BadParameter: If unable to determine PR URL
    """
    try:
        # Initialize git repository parser
        repo = GitRepository()
        
        # Get repository information
        repo_info = repo.get_repository_info()
        if repo_info is None:
            raise GitParsingError("Unable to extract repository information")
        
        host, owner, repo_name, branch = repo_info
        
        # Try to find PR using GitHub API if token provided
        if token:
            try:
                client = GitHubClient(token)
                pr_number = client.find_pr_by_branch(owner, repo_name, branch)
                if pr_number:
                    return f"https://{host}/{owner}/{repo_name}/pull/{pr_number}"
            except GitHubAPIError:
                # API call failed, continue to fallback methods
                pass
        
        # Try to find PR using GitHub CLI
        try:
            result = subprocess.run(  # nosec B603 B607  # Safe: hardcoded gh command with controlled args
                ["gh", "pr", "view", "--json", "url", "--jq", ".url"],
                capture_output=True,
                text=True,
                check=True
            )
            pr_url = result.stdout.strip()
            if pr_url:
                return pr_url
        except (subprocess.CalledProcessError, FileNotFoundError):
            # GitHub CLI not available or no PR found
            pass
        
        # If we get here, we couldn't find a PR for the current branch
        raise click.BadParameter(
            f"No open pull request found for branch '{branch}' in {owner}/{repo_name}. "
            "Please ensure there is an open PR for the current branch."
        )
        
    except GitParsingError as e:
        # Re-raise as GitParsingError so the hybrid function can catch it
        raise GitParsingError(f"Native git parsing failed: {e}") from e


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Parse GitHub PR URL to extract owner, repo, and PR number."""
    pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url)
    if not match:
        raise click.BadParameter(
            "Invalid GitHub PR URL format. Expected: https://github.com/owner/repo/pull/123"
        )

    owner, repo, pr_number = match.groups()
    return owner, repo, int(pr_number)


def generate_filename(owner: str, repo: str, pr_number: int) -> str:
    """Generate default filename for PR review output."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{owner}-{repo}-{timestamp}-pr{pr_number}.md"




def _interactive_config_setup() -> None:
    """Interactively create or update the XDG config file."""
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    base_dir = Path(xdg_home).expanduser() if xdg_home else (Path.home() / ".config")
    app_dir = base_dir / "gh-pr-rev-md"
    config_path = app_dir / "config.yaml"

    existing: dict = {}
    if config_path.exists():
        try:
            existing = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError, UnicodeDecodeError):
            existing = {}

    click.echo(f"Config path: {config_path}")

    # Offer to open PAT creation page with recommended scopes for read-only repo access
    if click.confirm("Open GitHub token creation page in your browser?", default=True):
        try:
            webbrowser.open(GITHUB_TOKEN_URL, new=2)
            click.echo(
                "Opened browser. After creating the token, copy it and return here."
            )
        except OSError as exc:
            click.echo(f"Warning: failed to open browser automatically: {exc}")
            click.echo(f"You can open this URL manually: {GITHUB_TOKEN_URL}")
    else:
        click.echo(f"You can create a token here if needed: {GITHUB_TOKEN_URL}")

    # Token prompt
    token_value: Optional[str] = (
        existing.get("token") if isinstance(existing, dict) else None
    )
    if token_value:
        keep = click.confirm("Keep existing token (not shown)?", default=True)
        if not keep:
            token_value = click.prompt(
                "Enter new GitHub token",
                hide_input=True,
                confirmation_prompt=True,
            )
    else:
        token_value = click.prompt(
            "Enter GitHub token", hide_input=True, confirmation_prompt=True
        )

    # Optional prompts for other known settings
    include_resolved_default = (
        bool(existing.get("include_resolved", False))
        if isinstance(existing, dict)
        else False
    )
    include_resolved = click.confirm(
        "Include resolved review comments by default?",
        default=include_resolved_default,
    )
    include_outdated_default = (
        bool(existing.get("include_outdated", False))
        if isinstance(existing, dict)
        else False
    )
    include_outdated = click.confirm(
        "Include outdated review comments by default?",
        default=include_outdated_default,
    )

    # Build config dictionary with allowed keys only
    new_config = {
        "token": token_value,
        "include_resolved": include_resolved,
        "include_outdated": include_outdated,
    }

    # Ensure directory exists and write YAML
    app_dir.mkdir(parents=True, exist_ok=True)
    config_text = yaml.safe_dump(new_config, sort_keys=False)
    config_path.write_text(config_text, encoding="utf-8")
    try:
        os.chmod(config_path, 0o600)
    except (OSError, PermissionError) as e:
        click.echo(f"Warning: could not set permissions on config file: {e}", err=True)
    click.echo(f"Config written to: {config_path}")


@click.command()
@click.argument("pr_url", required=False)
@click.option(
    "--token",
    envvar="GITHUB_TOKEN",
    help="GitHub token (can also be set via GITHUB_TOKEN env var)",
)
@click.option(
    "--config-set",
    is_flag=True,
    default=False,
    help="Interactively create/update XDG config then exit",
)
@click.option(
    "--include-resolved",
    is_flag=True,
    default=None,
    help="Include resolved review comments in the output",
)
@click.option(
    "--include-outdated",
    is_flag=True,
    default=None,
    help="Include outdated review comments in the output",
)
@click.option(
    "--output",
    "-o",
    is_flag=True,
    default=None,
    help="Save output to file with auto-generated filename",
)
@click.option(
    "--output-file", type=str, default=None, help="Save output to specified file"
)
@click.option(
    "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="Show version information and exit",
    callback=lambda ctx, param, value: ctx.exit(click.echo(f"gh-pr-rev-md, version {get_version()}")) if value else None,
)
def main(
    pr_url: Optional[str],
    token: Optional[str],
    config_set: bool,
    include_resolved: Optional[bool],
    include_outdated: Optional[bool],
    output: Optional[bool],
    output_file: Optional[str],
):
    """Fetch GitHub PR review comments and output as markdown.

    By default, outdated and resolved review comments are excluded.
    Use --include-outdated and --include-resolved to include them.

    Output can be saved to file using --output (auto-generated filename) or
    --output-file (custom filename).

    PR_URL should be in the format: https://github.com/owner/repo/pull/123
    or "." to use the current git branch's PR.
    """
    # If requested, run interactive config setup and exit early
    if config_set:
        try:
            _interactive_config_setup()
            sys.exit(0)
        except (click.Abort, OSError, yaml.YAMLError) as e:
            click.echo(f"Error during config setup: {e}", err=True)
            sys.exit(1)

    # Load XDG YAML config and merge with CLI/env values (CLI/env > config > defaults)
    config = load_config()

    # Resolve final values from CLI/env, config file, then defaults
    token = token if token is not None else config.get("token")
    include_resolved = (
        include_resolved
        if include_resolved is not None
        else config.get("include_resolved", False)
    )
    include_outdated = (
        include_outdated
        if include_outdated is not None
        else config.get("include_outdated", False)
    )
    output = output if output is not None else config.get("output", False)
    output_file = output_file if output_file is not None else config.get("output_file")

    if not token:
        click.echo(
            "Warning: no GitHub token provided. Unauthenticated requests are limited to ~60/hour and may hit rate limits.",
            err=True,
        )

    if not pr_url:
        click.echo("Error: PR_URL is required unless using --config-set.", err=True)
        sys.exit(1)

    # Handle "." argument to use current branch's PR
    if pr_url == ".":
        try:
            pr_url = get_current_branch_pr_url(token)
        except click.BadParameter as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    try:
        owner, repo, pr_number = parse_pr_url(pr_url)
    except click.BadParameter as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    client = GitHubClient(token)

    try:
        comments = client.get_pr_review_comments(
            owner, repo, pr_number, include_outdated, include_resolved
        )
        markdown_output = format_comments_as_markdown(comments, owner, repo, pr_number)

        # Handle file output
        if output_file or output:
            filename = (
                output_file
                if output_file
                else generate_filename(owner, repo, pr_number)
            )
            file_path = Path(filename)

            try:
                file_path.write_text(markdown_output, encoding="utf-8")
                click.echo(f"Output saved to: {file_path.absolute()}")
            except (OSError, PermissionError) as e:
                click.echo(f"Error writing to file {filename}: {e}", err=True)
                sys.exit(1)
        else:
            click.echo(markdown_output)
    except GitHubAPIError as e:
        click.echo(f"Error fetching data from GitHub: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
