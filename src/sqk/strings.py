# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

"""Helpers for safe Python string literal quote conversions.

This module contains utilities to convert Python ``libcst.SimpleString``
nodes from double quotes to single quotes while preserving semantics and
prefixes, and to quickly detect string literal properties.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass

import libcst as cst


@dataclass(frozen=True)
class ParsedStringPrefix:
    """Parsed information about a string literal's prefix (e.g., r, b, u)."""

    has_raw: bool
    has_bytes: bool
    has_unicode: bool
    raw_prefix: str


def _split_prefix_and_quoting(text: str) -> tuple[str, str]:
    """Split a literal token into ``(prefix, rest)``.

    ``text`` must be the raw token from ``cst.SimpleString.value``.
    """
    i = 0
    while i < len(text) and text[i] not in ("'", '"'):
        i += 1
    return text[:i], text[i:]


def parse_prefix(text: str) -> ParsedStringPrefix:
    """Parse and return the prefix details of a literal token ``text``."""
    prefix, _ = _split_prefix_and_quoting(text)
    lower = prefix.lower()
    return ParsedStringPrefix(
        has_raw="r" in lower,
        has_bytes="b" in lower,
        has_unicode="u" in lower,
        raw_prefix=prefix,
    )


def is_triple_quoted(text: str) -> bool:
    """Return True if the literal is triple-quoted."""
    _, rest = _split_prefix_and_quoting(text)
    return rest.startswith(("'''", '"""'))


def is_single_quoted(text: str) -> bool:
    """Return True if the literal uses single quotes (not triple)."""
    _, rest = _split_prefix_and_quoting(text)
    return (not is_triple_quoted(text)) and rest.startswith("'")


def to_single_quoted_string(simple: cst.SimpleString) -> cst.SimpleString | None:
    """Return a new ``SimpleString`` with single quotes, or ``None`` if unchanged.

    Rules:
    - Skip raw strings (``r"..."``) and byte strings (``b"..."``)
    - Skip triple-quoted strings
    - Only transform strings currently using double quotes
    - Preserve ``u`` prefix if present
    - Use Python's ``repr`` to produce a canonical single-quoted literal
    """
    original = simple.value
    if is_single_quoted(original):
        return None
    if is_triple_quoted(original):
        return None
    prefix = parse_prefix(original)
    if prefix.has_raw or prefix.has_bytes:
        return None

    try:
        value = ast.literal_eval(original)
    except (SyntaxError, ValueError):
        # Be conservative: if we cannot evaluate, do not change.
        return None

    # repr() prefers single quotes unless it needs to escape them.
    new_token = repr(value)

    if prefix.has_unicode and not prefix.raw_prefix:
        # If original used bare 'u', re-add it (choose lowercase for consistency)
        new_token = "u" + new_token
    elif prefix.has_unicode and prefix.raw_prefix:
        # Preserve exact prefix casing/ordering if any
        # Replace the quote portion of the original with repr-produced token quotes
        # by simply prefixing with the original prefix.
        new_token = prefix.raw_prefix + new_token

    # If there was an original prefix and we didn't preserve it above, but it
    # didn't include raw/bytes (already excluded), keep it as-is.
    if prefix.raw_prefix and not (
        prefix.has_unicode
        and prefix.raw_prefix
        and new_token.startswith(prefix.raw_prefix)
    ):
        # Avoid duplicating 'u' handled above
        kept = prefix.raw_prefix
        if "u" in kept.lower():
            kept = kept.replace("u", "").replace("U", "")
        new_token = kept + new_token

    if new_token == original:
        return None
    return cst.SimpleString(new_token)


def to_double_quoted_string(simple: cst.SimpleString) -> cst.SimpleString | None:
    """Return a new ``SimpleString`` using double quotes, or ``None`` if unchanged.

    Skips raw/bytes and triple-quoted strings. Preserves content and prefixes.
    """
    original = simple.value
    if is_triple_quoted(original):
        return None
    prefix = parse_prefix(original)
    if prefix.has_raw or prefix.has_bytes:
        return None

    _, rest = _split_prefix_and_quoting(original)
    if rest.startswith('"') and not rest.startswith('"""'):
        return None

    try:
        value = ast.literal_eval(original)
    except (SyntaxError, ValueError):
        return None

    dq = json.dumps(value)
    if prefix.has_unicode and not prefix.raw_prefix:
        dq = "u" + dq
    elif prefix.raw_prefix:
        dq = prefix.raw_prefix + dq

    if dq == original:
        return None
    return cst.SimpleString(dq)
