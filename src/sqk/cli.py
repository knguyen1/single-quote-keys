# Copyright (c) 2025 kynguyen and contributors. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.

"""CLI entrypoint for single-quote-keys pre-commit hook."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Config
from .processor import process_file


def build_parser() -> argparse.ArgumentParser:
    """Create and return the CLI argument parser for the tool."""
    p = argparse.ArgumentParser(
        prog="single-quote-keys", description="Normalize key strings to single quotes"
    )
    p.add_argument("paths", nargs="*", help="Files to process")
    p.add_argument(
        "--fix",
        action="store_true",
        help="Apply fixes in-place; exits non-zero if any changes were applied",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """Run the CLI with ``argv``; returns process exit code.

    If ``--fix`` is provided, changes are written in-place. Otherwise, prints the
    file paths that would change and returns non-zero.
    """
    argv = argv if argv is not None else sys.argv[1:]
    args = build_parser().parse_args(argv)
    config = Config.discover(Path.cwd())

    any_changed = False
    for raw in args.paths:
        path = Path(raw)
        if not path.exists() or path.suffix != ".py":
            continue
        if config.is_excluded(path):
            continue
        result = process_file(path)
        if result.changed:
            any_changed = True
            if args.fix:
                path.write_text(result.code)
            else:
                # Print unified diff-like output (filename only) for pre-commit to mark failure
                sys.stdout.write(f"{path}\n")

    # In both dry-run and --fix modes, if changes were (or would be) made, exit non-zero
    return 1 if any_changed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
