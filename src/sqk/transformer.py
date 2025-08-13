# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

"""libcst transformer for converting key string literals to single quotes.

Rules:
- Convert double-quoted key strings to single quotes in:
  - builtins: getattr/hasattr/setattr/delattr
  - mapping methods where first arg is a key: get/pop/setdefault
  - operator getters: attrgetter/itemgetter/methodcaller
  - constructors from pairs: dict/OrderedDict
  - dunder key methods: __getitem__/__setitem__
  - dunder attr methods: __getattr__/__setattr__/__delattr__/__getattribute__
  - fromkeys
- Textual content in normal code should be double-quoted except raw strings.
  This transformer enforces single quotes only for keys. It does not rewrite
  other string literals.
- Honour inline opt-out ``#noqa: quote-keys`` on lines containing the literal.
"""

from __future__ import annotations

import ast

import libcst as cst
from libcst import matchers as m
from libcst.metadata import PositionProvider

from .constants import (
    ATTR_FUNCS,
    DUUNDER_ATTR,
    DUUNDER_KEY,
    FROM_KEYS,
    MAPPING_FIRST_KEY_METHODS,
    NOQA_TAG,
    OPERATOR_GETTERS,
)
from .strings import to_double_quoted_string, to_single_quoted_string


class QuoteKeysTransformer(cst.CSTTransformer):
    """Transform qualifying string literals used as keys to single quotes."""

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, source_code: str) -> None:
        self._lines = source_code.splitlines()
        self._source_has_noqa = "# noqa: quote-keys" in source_code

    def _has_noqa_comment(self, node: cst.CSTNode) -> bool:
        """Return True if the node's line contains the noqa tag."""
        try:
            code_range = self.get_metadata(PositionProvider, node)
        except KeyError:
            return False
        line_no = max(1, min(len(self._lines), code_range.end.line))
        line_text = self._lines[line_no - 1]
        return NOQA_TAG in line_text

    def _maybe_requote(
        self, node: cst.CSTNode, s: cst.BaseExpression
    ) -> cst.BaseExpression:
        if (
            self._source_has_noqa
            or self._has_noqa_comment(node)
            or self._has_noqa_comment(s)
        ):
            return s
        if isinstance(s, cst.SimpleString):
            new_s = to_single_quoted_string(s)
            return new_s or s
        return s

    def leave_Call(  # noqa: N802, C901
        self, _original_node: cst.Call, updated_node: cst.Call
    ) -> cst.BaseExpression:
        """Rewrite arguments to calls that treat the first string as a key."""
        func_name = None
        if m.matches(updated_node.func, m.Name() | m.Attribute()):
            # Extract dotted name best-effort
            parts: list[str] = []
            cur = updated_node.func
            while isinstance(cur, cst.Attribute):
                if isinstance(cur.attr, cst.Name):
                    parts.append(cur.attr.value)
                cur = cur.value
            if isinstance(cur, cst.Name):
                parts.append(cur.value)
            func_name = ".".join(reversed(parts))

        # builtins getattr/hasattr/setattr/delattr
        if (
            func_name
            and func_name.split(".")[-1] in ATTR_FUNCS
            and len(updated_node.args) >= 2
        ):
            key_arg = updated_node.args[1]
            new_value = self._maybe_requote(updated_node, key_arg.value)
            updated_args = list(updated_node.args)
            updated_args[1] = key_arg.with_changes(value=new_value)
            return updated_node.with_changes(args=tuple(updated_args))

        # mapping methods first arg: get/pop/setdefault
        if isinstance(updated_node.func, cst.Attribute) and isinstance(
            updated_node.func.attr, cst.Name
        ):
            meth = updated_node.func.attr.value
            if meth in MAPPING_FIRST_KEY_METHODS and updated_node.args:
                arg0 = updated_node.args[0]
                new_value = self._maybe_requote(updated_node, arg0.value)
                updated_args = list(updated_node.args)
                updated_args[0] = arg0.with_changes(value=new_value)
                return updated_node.with_changes(args=tuple(updated_args))

        # operator getters: attrgetter/itemgetter/methodcaller
        if (
            func_name
            and func_name.split(".")[-1] in OPERATOR_GETTERS
            and updated_node.args
        ):
            arg0 = updated_node.args[0]
            new_value = self._maybe_requote(updated_node, arg0.value)
            updated_args = list(updated_node.args)
            updated_args[0] = arg0.with_changes(value=new_value)
            return updated_node.with_changes(args=tuple(updated_args))

        # dict/OrderedDict constructors from pairs: dict([...])
        if (
            func_name
            and func_name.split(".")[-1] in {"dict", "OrderedDict"}
            and updated_node.args
        ):
            # Handle dict([("a", 1), ("b", 2)]) or dict({"a": 1})
            first = updated_node.args[0].value
            if isinstance(first, cst.Dict):
                new_elements = []
                for elt in first.elements or ():
                    if isinstance(elt, cst.DictElement) and elt.key is not None:
                        new_key = self._maybe_requote(first, elt.key)
                        new_elements.append(elt.with_changes(key=new_key))
                    else:
                        new_elements.append(elt)
                return updated_node.deep_replace(
                    first, first.with_changes(elements=new_elements)
                )
            if isinstance(first, (cst.List, cst.Tuple)):
                new_elts = []
                for elt in first.elements or ():
                    value = elt.value if isinstance(elt, cst.Element) else elt
                    if isinstance(value, (cst.Tuple, cst.List)) and value.elements:
                        # pair like (key, val)
                        pair_elts = list(value.elements)
                        if pair_elts:
                            pair0 = pair_elts[0]
                            new0_val = self._maybe_requote(value, pair0.value)
                            pair_elts[0] = pair0.with_changes(value=new0_val)
                            new_pair = value.with_changes(elements=tuple(pair_elts))
                            if isinstance(elt, cst.Element):
                                new_elts.append(elt.with_changes(value=new_pair))
                            else:
                                new_elts.append(new_pair)
                            continue
                    new_elts.append(elt)
                return updated_node.deep_replace(
                    first, first.with_changes(elements=new_elts)
                )

        # Handle fromkeys() with sequences of keys
        if (
            isinstance(updated_node.func, cst.Attribute)
            and isinstance(updated_node.func.attr, cst.Name)
            and updated_node.func.attr.value in FROM_KEYS
            and updated_node.args
        ):
            arg0 = updated_node.args[0]
            target = arg0.value
            if isinstance(target, (cst.List, cst.Tuple, cst.Set)):
                new_elts = []
                for elt in target.elements or ():
                    if isinstance(elt, cst.Element):
                        new_elts.append(
                            elt.with_changes(
                                value=self._maybe_requote(target, elt.value)
                            )
                        )
                    else:
                        new_elts.append(self._maybe_requote(target, elt))
                new_target = target.with_changes(elements=tuple(new_elts))
                new_args = list(updated_node.args)
                new_args[0] = arg0.with_changes(value=new_target)
                return updated_node.with_changes(args=tuple(new_args))

        # dunder key/attr methods when invoked as calls, e.g., obj.__getitem__("key")
        if isinstance(updated_node.func, cst.Attribute) and isinstance(
            updated_node.func.attr, cst.Name
        ):
            dunder = updated_node.func.attr.value
            if dunder in DUUNDER_KEY and updated_node.args:
                arg0 = updated_node.args[0]
                new_value = self._maybe_requote(updated_node, arg0.value)
                updated_args = list(updated_node.args)
                updated_args[0] = arg0.with_changes(value=new_value)
                return updated_node.with_changes(args=tuple(updated_args))
            if dunder in DUUNDER_ATTR and updated_node.args:
                # The attribute name is the first string among the first two args
                idx = None
                upto = min(2, len(updated_node.args))
                for i in range(upto):
                    if isinstance(updated_node.args[i].value, cst.SimpleString):
                        idx = i
                        break
                if idx is not None:
                    target_arg = updated_node.args[idx]
                    new_value = self._maybe_requote(updated_node, target_arg.value)
                    updated_args = list(updated_node.args)
                    updated_args[idx] = target_arg.with_changes(value=new_value)
                    return updated_node.with_changes(args=tuple(updated_args))

        return updated_node

    def leave_Dict(  # noqa: N802
        self, _original_node: cst.Dict, updated_node: cst.Dict
    ) -> cst.Dict:
        """Rewrite dict literal keys to single-quoted form where applicable."""
        new_elements = []
        changed = False
        for elt in updated_node.elements or ():
            if isinstance(elt, cst.DictElement) and elt.key is not None:
                new_key = self._maybe_requote(updated_node, elt.key)
                if new_key is not elt.key:
                    changed = True
                    new_elements.append(elt.with_changes(key=new_key))
                else:
                    new_elements.append(elt)
            else:
                new_elements.append(elt)
        return (
            updated_node.with_changes(elements=new_elements)
            if changed
            else updated_node
        )

    def leave_Subscript(  # noqa: N802
        self, _original_node: cst.Subscript, updated_node: cst.Subscript
    ) -> cst.Subscript:
        """Rewrite subscript keys like obj["a"] -> obj['a']."""
        # obj["key"] -> obj['key']
        current = updated_node.slice
        if current is None:
            return updated_node
        elements = current if isinstance(current, tuple) else (current,)
        new_elems: list[cst.SubscriptElement] = []
        changed = False
        for s in elements:
            if isinstance(s, cst.SubscriptElement) and isinstance(s.slice, cst.Index):
                target = s.slice.value
                new_target = self._maybe_requote(updated_node, target)
                if new_target is not target:
                    changed = True
                    new_elems.append(s.with_changes(slice=cst.Index(value=new_target)))
                else:
                    new_elems.append(s)
            else:
                new_elems.append(s)
        if not changed:
            return updated_node
        new_slice = tuple(new_elems) if isinstance(current, tuple) else new_elems[0]
        return updated_node.with_changes(slice=new_slice)

    # Dunder methods in class/function defs are covered via Call/Subscript; no special casing for FunctionDef needed.
    # Additionally, prefer double quotes for standalone textual strings outside key contexts.

    def leave_SimpleString(  # noqa: N802
        self, _original_node: cst.SimpleString, updated_node: cst.SimpleString
    ) -> cst.SimpleString:
        r"""Prefer quote style that minimizes escaping for textual strings.

        Rules for non-raw, non-bytes, non-triple-quoted strings:
        - If value contains an unescaped double quote and no single quotes,
          prefer single-quoted form: "foo\"bar" -> 'foo"bar'.
        - If value contains a single quote and no double quotes,
          prefer double-quoted form: 'foo\'bar' -> "foo'bar".
        - Otherwise, prefer double-quoted form.
        """
        token = updated_node.value
        try:
            value = ast.literal_eval(token)
        except (SyntaxError, ValueError):
            # Fall back to previous behavior
            new_node = to_double_quoted_string(updated_node)
            return new_node or updated_node

        has_single = "'" in value
        has_double = '"' in value

        if has_double and not has_single:
            preferred = to_single_quoted_string(updated_node)
            return preferred or updated_node

        preferred = to_double_quoted_string(updated_node)
        return preferred or updated_node
