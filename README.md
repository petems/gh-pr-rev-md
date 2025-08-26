# gh-pr-rev-md

`gh-pr-rev-md` is a Python based CLI to fetch GitHub Pull Request review comments and render them as Markdown.

## Features

- Fetches PR review comments via the GitHub GraphQL API
- Excludes resolved and outdated comments by default
- Toggle with `--include-resolved` and `--include-outdated`
- Emits clean Markdown including per-comment metadata and diff context
- Can print to stdout or write to a timestamped file
- Configurable via CLI, env, and XDG config file

## Installation

Requirements: Python >= 3.9

Recommended with uv (fast installer/runner):

```bash
uv pip install gh-pr-rev-md
```

Alternative (pipx):

```bash
pipx install gh-pr-rev-md
```

Or with pip:

```bash
python -m pip install gh-pr-rev-md
```

## Quickstart

```bash
gh-pr-rev-md https://github.com/<owner>/<repo>/pull/123
```

If you don’t set a token, unauthenticated requests are limited (~60/hour) and may hit rate limits. Set `GITHUB_TOKEN` or use `--token`.

## CLI Usage

```bash
gh-pr-rev-md [OPTIONS] PR_URL
```

Options:
- `--token` (env: `GITHUB_TOKEN`): GitHub token for higher rate limits
- `--config-set`: Interactive setup to write an XDG config file
- `--include-resolved`: Include resolved review comments
- `--include-outdated`: Include outdated review comments (on previous versions of the diff)
- `--output` / `-o`: Save to auto-generated file name
- `--output-file <path>`: Save to provided file path

URL format must be: `https://github.com/<owner>/<repo>/pull/<number>`

### Examples

Print to stdout:

```bash
gh-pr-rev-md https://github.com/octocat/Hello-World/pull/42
```

Include resolved comments and save to a generated file:

```bash
gh-pr-rev-md --include-resolved --output https://github.com/octocat/Hello-World/pull/42
```

Write to a specific file:

```bash
gh-pr-rev-md --output-file review.md https://github.com/octocat/Hello-World/pull/42
```

Provide token via env:

```bash
GITHUB_TOKEN=ghp_xxx gh-pr-rev-md https://github.com/octocat/Hello-World/pull/42
```

## Configuration

Follows XDG Base Directory spec.

- User config: `$XDG_CONFIG_HOME/gh-pr-rev-md/config.yaml` (or `~/.config/gh-pr-rev-md/config.yaml`)
- Supported keys:
  - `token: <str>`
  - `include_resolved: <bool>`
  - `include_outdated: <bool>`
  - `output: <bool>`
  - `output_file: <str>`

Create/update interactively:

```bash
gh-pr-rev-md --config-set
```

## Output format

The Markdown includes a header with repo/PR metadata, then one section per review comment with author, file, line, created/updated times, a `diff`-fenced code hunk, and the comment body.

Example snippet:

```markdown
## Comment #3
**Author:** @octocat
**File:** `app/main.py`
**Line:** 120
**Created:** 2025-08-23 10:05:30 UTC

### Code Context
```diff
@@ def handle():
- old
+ new
```

### Comment
Consider handling None here.
```

## Development

We use uv for local workflows and Sphinx for docs.

Setup:

```bash
uv venv
uv pip install .[dev]
```

Run tests:

```bash
uv run -m pytest -q --cov=gh_pr_rev_md
```

Lint:

```bash
uv run ruff check .
```

Docs:

```bash
make docs       # builds HTML into docs/_build/html
make docs-serve # serves on http://localhost:8000
make docs-clean
```

Local development commands:

```bash
# Install into a local venv with dev dependencies
make install

# Run the CLI without activating the venv
make run ARGS="https://github.com/owner/repo/pull/123"

# Start a shell with the venv on PATH
make activate

# Alternatively, call the binary directly
.venv/bin/gh-pr-rev-md https://github.com/owner/repo/pull/123

# Or run without installing (one-off)
uvx gh-pr-rev-md https://github.com/owner/repo/pull/123
```

### Project structure

- `gh_pr_rev_md/cli.py`: CLI entry point and option handling
- `gh_pr_rev_md/github_client.py`: GitHub API client (requests-based)
- `gh_pr_rev_md/formatter.py`: Markdown renderer
- `gh_pr_rev_md/config.py`: XDG YAML config loader

### GitHub token scopes

Read-only access is sufficient. Recommended scopes: `repo`, `read:org` for private org repos. For public repos, a token is optional but avoids rate limits.

## CI/CD

- GitHub Actions with uv (`astral-sh/setup-uv@v6`) and caching enabled
- Separate jobs for lint, tests, acceptance, security (Bandit), docs, and release
- Release: tagging `vX.Y.Z` triggers build/publish in `release.yml`

## Dependabot

Weekly updates for GitHub Actions and uv-managed dependencies via `.github/dependabot.yml`.

## License

MIT
