from __future__ import annotations

# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
import pytest

from sqk.processor import transform_code


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('hasattr(obj, "key")', "hasattr(obj, 'key')"),
        ('getattr(obj, "key")', "getattr(obj, 'key')"),
        ('setattr(obj, "key", 1)', "setattr(obj, 'key', 1)"),
        ('delattr(obj, "key")', "delattr(obj, 'key')"),
    ],
)
def test_attr_builtins(code: str, expected: str) -> None:
    out, changed = transform_code(code)
    assert out == expected
    assert changed is True


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('d.get("a")', "d.get('a')"),
        ('d.pop("a")', "d.pop('a')"),
        ('d.setdefault("a", 1)', "d.setdefault('a', 1)"),
    ],
)
def test_mapping_first_key_methods(code: str, expected: str) -> None:
    out, changed = transform_code(code)
    assert out == expected
    assert changed is True


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('operator.attrgetter("a")', "operator.attrgetter('a')"),
        ('operator.itemgetter("a")', "operator.itemgetter('a')"),
        ('operator.methodcaller("a")', "operator.methodcaller('a')"),
    ],
)
def test_operator_getters(code: str, expected: str) -> None:
    out, changed = transform_code(code)
    assert out == expected
    assert changed is True


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('{"a": 1}', "{'a': 1}"),
        ('dict({"a": 1})', "dict({'a': 1})"),
        ('dict([("a", 1), ("b", 2)])', "dict([('a', 1), ('b', 2)])"),
    ],
)
def test_dict_construction(code: str, expected: str) -> None:
    out, changed = transform_code(code)
    assert out == expected
    assert changed is True


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('d["a"]', "d['a']"),
        ('obj.__getitem__("a")', "obj.__getitem__('a')"),
        ('obj.__setitem__("a", 1)', "obj.__setitem__('a', 1)"),
    ],
)
def test_subscript_and_dunder_key_methods(code: str, expected: str) -> None:
    out, changed = transform_code(code)
    assert out == expected
    assert changed is True


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('type.__getattr__(obj, "a")', "type.__getattr__(obj, 'a')"),
        ('obj.__setattr__("a", 1)', "obj.__setattr__('a', 1)"),
        ('obj.__delattr__("a")', "obj.__delattr__('a')"),
    ],
)
def test_dunder_attr_methods(code: str, expected: str) -> None:
    out, changed = transform_code(code)
    assert out == expected
    assert changed is True


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('dict.fromkeys(["a", "b"])', "dict.fromkeys(['a', 'b'])"),
        ('d.fromkeys(("a", "b"))', "d.fromkeys(('a', 'b'))"),
        ('d.fromkeys({"a", "b"})', "d.fromkeys({'a', 'b'})"),
    ],
)
def test_fromkeys(code: str, expected: str) -> None:
    out, changed = transform_code(code)
    assert out == expected
    assert changed is True


def test_noqa_inline() -> None:
    code = 'hasattr(obj, "key")  # noqa: quote-keys'
    out, changed = transform_code(code)
    assert out == code
    assert changed is False


@pytest.mark.parametrize(
    "code",
    [
        'hasattr(obj, r"a")',
        'd["""a"""]',
        "{r'k': 1}",
    ],
)
def test_raw_and_triple_are_unchanged(code: str) -> None:
    out, changed = transform_code(code)
    assert out == code
    assert changed is False


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ('[kvp["foo"] for kvp in items]', "[kvp['foo'] for kvp in items]"),
        (
            '{kvp["foo"]: "bar" for kvp in items}',
            "{kvp['foo']: \"bar\" for kvp in items}",
        ),
    ],
)
def test_comprehensions(code: str, expected: str) -> None:
    out, changed = transform_code(code)
    assert out == expected
    assert changed is True
