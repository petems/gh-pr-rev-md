"""CLI interface for GitHub PR review comments tool."""

import os
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import click
import yaml

from .config import load_config
from .formatter import format_comments_as_markdown
from .github_client import GitHubAPIError, GitHubClient

GITHUB_TOKEN_URL = (
    "https://github.com/settings/tokens/new?scopes=repo,read:org"  # nosec B105
    "&description=gh-pr-rev-md%20CLI%20"  # nosec B105
    "(read%20PR%20comments)"  # nosec B105
)


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


def resolve_config_value(name: str, current_value, config: dict, default):
    """Resolve a config value with precedence: CLI/env > config file > default."""
    ctx = click.get_current_context(silent=True)
    get_source = getattr(ctx, "get_parameter_source", None)
    if get_source is not None:
        src = ctx.get_parameter_source(name)
        if str(src) in {"ParameterSource.COMMANDLINE", "ParameterSource.ENVIRONMENT"}:
            return current_value
    # Fallback precedence
    if current_value not in (None, False, ""):
        return current_value
    return config.get(name, default)


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
    token = resolve_config_value("token", token, config, None)
    include_resolved = bool(
        resolve_config_value("include_resolved", include_resolved, config, False)
    )
    include_outdated = bool(
        resolve_config_value("include_outdated", include_outdated, config, False)
    )
    output = bool(resolve_config_value("output", output, config, False))
    output_file = resolve_config_value("output_file", output_file, config, None)

    if not token:
        click.echo(
            "Warning: no GitHub token provided. Unauthenticated requests are limited to ~60/hour and may hit rate limits.",
            err=True,
        )

    if not pr_url:
        click.echo("Error: PR_URL is required unless using --config-set.", err=True)
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
