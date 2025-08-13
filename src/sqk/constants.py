# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

"""Constants for single-quote-keys tool."""

NOQA_TAG = "quote-keys"
NOQA_PATTERN = "#noqa: quote-keys"

# Tool configuration keys in pyproject.
PYPROJECT_TOOL_SECTION = "tool.single-quote-keys"
OPT_OUT_KEY = "exclude"
TEXTUAL_DOUBLE_QUOTED = True

# Supported call names for key-arg transformations
ATTR_FUNCS = {"getattr", "hasattr", "setattr", "delattr"}
MAPPING_FIRST_KEY_METHODS = {"get", "pop", "setdefault"}
OPERATOR_GETTERS = {"attrgetter", "itemgetter", "methodcaller"}
FROM_KEYS = {"fromkeys"}
DICT_CONSTRUCTORS = {"dict", "OrderedDict", "collections.OrderedDict"}

# Dunder methods
DUUNDER_KEY = {"__getitem__", "__setitem__"}
DUUNDER_ATTR = {"__getattr__", "__setattr__", "__delattr__", "__getattribute__"}
