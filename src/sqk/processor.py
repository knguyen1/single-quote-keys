# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

"""High-level processing: parse -> transform -> emit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import libcst as cst
from libcst.metadata import MetadataWrapper

from .transformer import QuoteKeysTransformer

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ProcessResult:
    """Result of processing a single file."""

    path: Path
    changed: bool
    code: str


def transform_code(code: str) -> tuple[str, bool]:
    """Transform ``code`` and return ``(new_code, changed)``."""
    module = cst.parse_module(code)
    wrapper = MetadataWrapper(module)
    new_module = wrapper.visit(QuoteKeysTransformer(source_code=code))
    new_code = new_module.code
    return new_code, new_code != code


def process_file(path: Path) -> ProcessResult:
    """Read ``path``, transform its contents, and return a ``ProcessResult``."""
    original = path.read_text()
    new_code, changed = transform_code(original)
    return ProcessResult(path=path, changed=changed, code=new_code)
