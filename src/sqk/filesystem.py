# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

"""Filesystem utilities and pyproject configuration reading."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from .constants import OPT_OUT_KEY

if TYPE_CHECKING:
    from collections.abc import Iterable


def read_pyproject_excludes(start: Path) -> set[str]:
    """Read per-file opt-outs from ``pyproject.toml``.

    Looks for ``[tool.single-quote-keys]`` section and the ``exclude``
    array of globs. Returns a set of glob patterns; empty set if none.
    """
    proj = find_pyproject_toml(start)
    if proj is None:
        return set()
    raw = tomllib.loads(proj.read_text())
    section = raw.get("tool", {}).get("single-quote-keys", {})
    excludes = section.get(OPT_OUT_KEY, [])
    return set(excludes or [])


def is_path_excluded(path: Path, patterns: Iterable[str]) -> bool:
    """Return True if ``path`` matches any exclusion glob in ``patterns``."""
    as_posix = path.as_posix()
    return any(Path(as_posix).match(pat) for pat in patterns)


def find_pyproject_toml(start: Path) -> Path | None:
    """Find the nearest ``pyproject.toml`` starting at or above ``start``.

    Returns the path if found, otherwise ``None``.
    """
    cur = start
    for p in [cur, *cur.parents]:
        candidate = p / "pyproject.toml"
        if candidate.exists():
            return candidate
    return None
