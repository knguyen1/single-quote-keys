from __future__ import annotations

# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
import pytest

from sqk.processor import transform_code


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("var123 = 'myvar'", 'var123 = "myvar"'),
        ('var456 = "myvar"', 'var456 = "myvar"'),
        # Prefer single quotes if the content contains a double quote
        ('s = "foo\\"bar"', "s = 'foo\"bar'"),
        # Prefer double quotes if the content contains a single quote
        ("s = 'foo\\'bar'", 's = "foo\'bar"'),
    ],
)
def test_textual_strings_are_double_quoted(code: str, expected: str) -> None:
    out, _ = transform_code(code)
    assert out == expected
