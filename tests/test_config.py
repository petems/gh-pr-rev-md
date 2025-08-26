import pytest
from pathlib import Path
from gh_pr_rev_md import config


def test_safe_yaml_load_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("", encoding="utf-8")
    assert config._safe_yaml_load(path) == {}


def test_safe_yaml_load_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("- item1\n- item2\n", encoding="utf-8")
    assert config._safe_yaml_load(path) == {}


def test_safe_yaml_load_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.yaml"
    assert config._safe_yaml_load(path) == {}


def test_safe_yaml_load_invalid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("[unclosed", encoding="utf-8")
    with pytest.raises(RuntimeError):
        config._safe_yaml_load(path)
