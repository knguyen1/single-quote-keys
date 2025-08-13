from __future__ import annotations

# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
from typing import TYPE_CHECKING

from sqk.config import Config
from sqk.filesystem import is_path_excluded, read_pyproject_excludes

if TYPE_CHECKING:
    from pathlib import Path


def test_read_pyproject_excludes(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.single-quote-keys]
exclude = ["tests/*", "**/generated_*.py"]
"""
    )
    excludes = read_pyproject_excludes(tmp_path)
    assert "tests/*" in excludes
    assert "**/generated_*.py" in excludes


def test_is_path_excluded(tmp_path: Path) -> None:
    patterns = {"**/ignore_me.py"}
    path = tmp_path / "pkg" / "ignore_me.py"
    assert is_path_excluded(path, patterns) is True
    assert is_path_excluded(tmp_path / "pkg" / "keep.py", patterns) is False


def test_config_exclusion(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.single-quote-keys]
exclude = ["**/skip.py"]
"""
    )
    cfg = Config.discover(tmp_path)
    assert cfg.is_excluded(tmp_path / "a" / "skip.py") is True
    assert cfg.is_excluded(tmp_path / "a" / "keep.py") is False
