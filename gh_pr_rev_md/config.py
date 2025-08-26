"""XDG YAML configuration loader for gh-pr-rev-md.

This module loads configuration following the XDG Base Directory specification:
- User config: $XDG_CONFIG_HOME/gh-pr-rev-md/config.yaml (or config.yml)
- System config: each dir in $XDG_CONFIG_DIRS/gh-pr-rev-md/config.yaml (or config.yml)

Config keys (all optional):
- token: str
- include_resolved: bool
- include_outdated: bool
- output: bool
- output_file: str
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import os

import yaml


_APP_DIR_NAME = "gh-pr-rev-md"
_CONFIG_FILENAMES = ("config.yaml", "config.yml")


def _xdg_config_home() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser()
    return Path.home() / ".config"


def _xdg_config_dirs() -> List[Path]:
    raw = os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg")
    return [Path(p) for p in raw.split(":") if p]


def _candidate_files() -> List[Path]:
    """Return config file candidates in increasing precedence order.

    Lower precedence first (system), higher precedence last (user). Within each
    directory, prefer config.yaml over config.yml by ordering.
    """
    candidates: List[Path] = []

    # System-wide directories (lowest precedence)
    for base in _xdg_config_dirs():
        app_dir = base / _APP_DIR_NAME
        for name in _CONFIG_FILENAMES:
            candidates.append(app_dir / name)

    # User config directory (highest precedence)
    user_dir = _xdg_config_home() / _APP_DIR_NAME
    for name in _CONFIG_FILENAMES:
        candidates.append(user_dir / name)

    return candidates


def _safe_yaml_load(path: Path) -> Dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if data is None:
            return {}
        if not isinstance(data, dict):
            # Non-mapping configs are ignored
            return {}
        return data
    except FileNotFoundError:
        return {}
    except Exception as exc:  # YAML error or IO error
        raise RuntimeError(f"Failed to load config file {path}: {exc}")


def load_config() -> Dict[str, Any]:
    """Load configuration by merging all candidate files.

    Later files override earlier ones. Only known keys are kept.
    """
    merged: Dict[str, Any] = {}
    allowed_keys = {
        "token",
        "include_resolved",
        "include_outdated",
        "output",
        "output_file",
    }

    for path in _candidate_files():
        if path.is_file():
            loaded = _safe_yaml_load(path)
            for key, value in loaded.items():
                if key in allowed_keys:
                    merged[key] = value

    return merged
