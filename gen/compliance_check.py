#!/usr/bin/env python3
"""Screen post markdown for mortgage-advertising problems before publishing.

Ricky is a licensed MLO (NMLS #173141; EPiQ Lending NMLS #1936984), so these
posts are regulated advertising. This is a coarse net, not legal review. It
catches the mistakes an automated writer actually makes.

  ERROR  exits non-zero. Never publish over one. Covers house style too:
         em dashes are banned outright in Ricky's content.
  WARN   needs a human look. Quoting what a buyer says ("who has the best
         rate?") is fine; claiming it about EPiQ is not, and only context
         separates them.

Usage:  python gen/compliance_check.py content/posts/*.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ERRORS: list[tuple[str, str]] = [
    # House style, not compliance, but non-negotiable: Ricky does not use em
    # dashes. Rewrite the sentence with a comma, colon, or full stop rather
    # than swapping in another dash.
    ("\u2014", "uses an em dash"),
    ("\u2015", "uses a horizontal bar"),
    (r"\s\u2013\s", "uses a spaced en dash as punctuation"),
    (r"\b\d+(?:\.\d+)?\s*%\s*(?:APR|interest\s+rate|rate)\b", "quotes a specific rate or APR"),
    (r"\bAPR\s+of\s+\d", "quotes a specific APR"),
    (r"\bguarante\w*\s+(?:approval|rate|savings|closing)", "promises a guarantee"),
    (r"\byou\s+will\s+(?:save|qualify|be\s+approved)\b", "promises an outcome"),
    (r"\bno\s+(?:closing\s+)?costs?\b(?!\s*\?)", "claims no costs"),
    (r"\$\d[\d,]*\s*(?:/|per\s+)mo(?:nth)?\b", "quotes a specific monthly payment"),
]

WARNINGS: list[tuple[str, str]] = [
    (r"\b(?:best|lowest|cheapest|top|#1|number\s+one)\s+(?:lender|rate|rates|mortgage|broker|loan)\b",
     "superlative: fine when quoting a buyer, not as our own claim"),
    (r"\b(?:always|never)\s+(?:cheaper|better|worse)\b", "absolute comparison"),
    (r"\bpre-?qualif", "mentions pre-qualification: make sure the distinction is drawn"),
]

REQUIRED: list[tuple[str, str]] = [
    ("Equal Housing Opportunity", "Equal Housing Opportunity disclosure"),
    ("not a commitment to lend", "'not a commitment to lend' disclaimer"),
    ("173141", "Ricky's NMLS number"),
]


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def check(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    errors = warnings = 0

    for pattern, label in ERRORS:
        for match in re.finditer(pattern, text, re.I):
            print(f"  ERROR {path.name}:{line_of(text, match.start())}  {label}: {match.group(0)!r}")
            errors += 1

    for pattern, label in WARNINGS:
        for match in re.finditer(pattern, text, re.I):
            print(f"  WARN  {path.name}:{line_of(text, match.start())}  {label}: {match.group(0)!r}")
            warnings += 1

    for needle, label in REQUIRED:
        if needle not in text:
            print(f"  ERROR {path.name}  missing {label}")
            errors += 1

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    total_errors = total_warnings = 0
    for path in args.paths:
        errors, warnings = check(path)
        total_errors += errors
        total_warnings += warnings

    print(
        f"Screened {len(args.paths)} file(s): "
        f"{total_errors} error(s), {total_warnings} warning(s)."
    )
    if total_warnings and not total_errors:
        print("Warnings need a human read. Check the context before publishing.")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
