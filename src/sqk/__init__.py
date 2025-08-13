# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

"""single-quote-keys public API."""

from .processor import transform_code
from .transformer import QuoteKeysTransformer

__all__ = ["QuoteKeysTransformer", "transform_code"]
