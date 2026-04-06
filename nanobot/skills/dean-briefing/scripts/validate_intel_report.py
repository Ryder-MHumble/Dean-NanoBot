#!/usr/bin/env python3
"""
Lightweight report validator for intelligence-style markdown output.

Checks:
- optional P1/P2/P3 presence
- optional URL presence
- max character budget
"""

from __future__ import annotations

import argparse
import re
import sys

PRIORITY_RE = re.compile(r"\bP[123]\b")
URL_RE = re.compile(r"https?://[^\s)]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate intel report quality gates")
    parser.add_argument("--file", default="-", help="Input file path, or '-' for stdin")
    parser.add_argument("--require-priority", default="false", choices=["true", "false"])
    parser.add_argument("--require-links", default="true", choices=["true", "false"])
    parser.add_argument("--max-chars", type=int, default=6000)
    parser.add_argument("--allow-missing-links", type=int, default=0)
    return parser.parse_args()


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> int:
    args = parse_args()
    text = read_text(args.file).strip()

    if not text:
        print("FAIL: empty report")
        return 1

    errors: list[str] = []

    char_count = len(text)
    priorities = PRIORITY_RE.findall(text)
    urls = URL_RE.findall(text)

    if char_count > args.max_chars:
        errors.append(f"char_count={char_count} exceeds max={args.max_chars}")

    if args.require_priority == "true" and not priorities:
        errors.append("missing priority labels P1/P2/P3")

    if args.require_links == "true":
        if not urls:
            errors.append("missing source links")
        if priorities and len(urls) + args.allow_missing_links < len(priorities):
            errors.append(
                f"links({len(urls)}) + allow_missing({args.allow_missing_links}) < priorities({len(priorities)})"
            )

    if errors:
        print("FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("PASS")
    print(f"char_count={char_count}")
    print(f"priority_labels={len(priorities)}")
    print(f"urls={len(urls)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
