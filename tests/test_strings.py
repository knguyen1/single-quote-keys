from __future__ import annotations

# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
import libcst as cst
import pytest

from sqk.strings import is_single_quoted, is_triple_quoted, to_single_quoted_string


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("'a'", True),
        ('"a"', False),
        ("r'a'", True),
        ('u"a"', False),
        ("'''a'''", False),
        ('"""a"""', False),
    ],
)
def test_is_single_quoted(token: str, expected: bool) -> None:
    assert is_single_quoted(token) is expected


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("'''a'''", True),
        ('"""a"""', True),
        ("'a'", False),
        ('"a"', False),
    ],
)
def test_is_triple_quoted(token: str, expected: bool) -> None:
    assert is_triple_quoted(token) is expected


@pytest.mark.parametrize(
    ("token", "changed"),
    [
        ('"a"', True),
        ("'a'", False),
        ('r"a"', False),
        ('b"a"', False),
        ('"""a"""', False),
    ],
)
def test_to_single_quoted_string_behavior(token: str, changed: bool) -> None:
    node = cst.SimpleString(token)
    new = to_single_quoted_string(node)
    assert (new is not None) is changed
    if new is not None:
        assert new.value.startswith("'")
