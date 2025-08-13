from __future__ import annotations

# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def test_cli_dry_run_lists_files(run_cli, write_file) -> None:  # type: ignore[no-untyped-def]
    src = 'hasattr(obj, "key")\n'
    file_path = write_file("a.py", src)
    # Dry run: expect non-zero exit and file name printed
    rc = run_cli([str(file_path)])
    assert rc == 1


def test_cli_fix_writes_changes(run_cli, write_file) -> None:  # type: ignore[no-untyped-def]
    src = 'hasattr(obj, "key")\n'
    file_path = write_file("a.py", src)
    rc = run_cli(["--fix", str(file_path)])
    assert rc == 1
    assert file_path.read_text() == "hasattr(obj, 'key')\n"


def test_cli_respects_exclude_in_pyproject(run_cli, write_file, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.single-quote-keys]
exclude = ["a.py"]
"""
    )
    src = 'hasattr(obj, "key")\n'
    file_path = write_file("a.py", src)
    rc = run_cli(["--fix", str(file_path)])
    assert rc == 0
    assert file_path.read_text() == src
