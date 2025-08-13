# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

"""Runtime configuration model for single-quote-keys."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .filesystem import read_pyproject_excludes

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Resolved configuration for the tool."""

    project_root: Path
    excludes: tuple[str, ...]

    @classmethod
    def discover(cls, start: Path) -> Config:
        """Build configuration by reading ``pyproject.toml`` near ``start``."""
        excludes = tuple(sorted(read_pyproject_excludes(start)))
        return cls(project_root=start, excludes=excludes)

    def is_excluded(self, path: Path) -> bool:
        """Return True if ``path`` is excluded by config patterns."""
        from .filesystem import is_path_excluded

        return is_path_excluded(path, self.excludes)
