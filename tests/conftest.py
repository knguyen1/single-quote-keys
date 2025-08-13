# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqk.processor import transform_code

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@pytest.fixture
def transform() -> Callable[[str], tuple[str, bool]]:
    def _run(code: str) -> tuple[str, bool]:
        return transform_code(code)

    return _run


@pytest.fixture
def write_file(tmp_path: Path) -> Callable[[str, str], Path]:
    def _write(rel: str, content: str) -> Path:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return target

    return _write


@pytest.fixture
def run_cli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Callable[[list[str]], int]:
    from sqk.cli import main as cli_main

    def _run(args: list[str]) -> int:
        monkeypatch.chdir(tmp_path)
        return cli_main(args)

    return _run
