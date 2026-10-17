#!/usr/bin/env python3
"""Guard the guideline citation system against numbers written straight into prose.

The whole point of [[RULE:key]] markers is that a guideline figure lives in one
dated, cited data file instead of in forty posts. That only holds if nobody
writes "FHA requires a 580 score" into a paragraph, where it bypasses the
citation, bypasses the staleness notice, and goes stale silently under a
licensed originator's NMLS number.

So this checks two things across the guideline-bearing posts:

  1. Every [[RULE:key]] marker names a rule that is actually registered. An
     unregistered key renders a visible site error, which is better than
     silence but worse than catching it here.
  2. No guideline threshold is asserted in prose. A threshold is a number sat
     next to requirement language: "requires 580", "minimum of 620",
     "43 percent debt-to-income", "three years after a foreclosure".

What it deliberately does NOT flag is a number describing a real closed file,
such as "credit work moved him to a 770 FICO". That is an outcome, not a
published requirement, and it is the most valuable content on the site. An
earlier version of this check matched any three-digit score and flagged
exactly that sentence, which is the same mistake the British-spelling screen
made with the word "analyses": blocking correct content is the more expensive
error, so the patterns below require requirement language nearby.

Usage:
    python gen/check_guideline_prose.py content/posts/*.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "guidelines.json"

# Requirement language. A figure only becomes a guideline assertion when it
# sits next to one of these; on its own it is probably a real file's outcome.
REQ = (
    r"(?:requires?|required|requirement|minimum|minimums|at\s+least|"
    r"no\s+less\s+than|floor|must\s+(?:be|have)|need(?:s)?\s+(?:a|to)|"
    r"allows?|permits?|caps?\s+at|limited\s+to|eligible\s+(?:at|with))"
)

PATTERNS: list[tuple[str, str]] = [
    # Credit score thresholds stated as a requirement.
    (rf"{REQ}\D{{0,40}}(?<![$\d.,])\b[3-8]\d\d\b(?![\d,.])(?!\s*(?:sq|square))",
     "credit score threshold"),
    (r"(?<![$\d.,])\b[3-8]\d\d\b(?![\d,.])\s*(?:or\s+(?:higher|above|better)|and\s+above)",
     "credit score threshold"),
    # Down payment percentages stated as a requirement.
    (rf"{REQ}\D{{0,30}}\b\d{{1,2}}(?:\.\d+)?\s*(?:percent|%)\s*(?:down|minimum)",
     "down payment requirement"),
    (r"\b\d{1,2}(?:\.\d+)?\s*(?:percent|%)\s+down\s+payment\s+(?:is\s+)?"
     r"(?:required|minimum)", "down payment requirement"),
    # Ratio limits.
    (r"\b(?:debt-to-income|DTI)\D{0,30}\b\d{2}(?:\.\d+)?\s*(?:percent|%)",
     "debt-to-income threshold"),
    (rf"{REQ}\D{{0,30}}\b\d{{2}}(?:\.\d+)?\s*(?:percent|%)\D{{0,20}}"
     r"(?:debt-to-income|DTI)", "debt-to-income threshold"),
    # Seasoning and waiting periods.
    (r"\b(?:one|two|three|four|five|six|seven|\d{1,2})\s*(?:year|month)s?\s+"
     r"(?:after|from|following|since)\s+(?:a\s+|the\s+)?"
     r"(?:bankruptcy|discharge|foreclosure|short\s+sale|deed\s+in\s+lieu)",
     "waiting period"),
    (rf"{REQ}\D{{0,25}}\b(?:one|two|three|four|five|\d{{1,2}})\s*"
     r"(?:year|month)s?\s+(?:of\s+)?(?:seasoning|wait)", "waiting period"),
    # Loan limits and premium rates.
    (r"\bloan\s+limit\D{0,30}\$[\d,]{4,}", "loan limit figure"),
    (rf"(?:upfront|annual)\s+(?:mortgage\s+insurance|premium|MIP)\D{{0,30}}"
     r"\b\d(?:\.\d+)?\s*(?:percent|%)", "mortgage insurance rate"),
    # Concession caps.
    (r"\bseller\D{0,25}\b\d{1,2}(?:\.\d+)?\s*(?:percent|%)\D{0,25}"
     r"(?:contribut|concession|credit)", "seller concession cap"),
]

COMPILED = [(re.compile(p, re.I), label) for p, label in PATTERNS]
MARKER = re.compile(r"\[\[RULE:([^\]]+?)\]\]")


def registered() -> set[str]:
    if not DATA.exists():
        return set()
    return set(json.loads(DATA.read_text(encoding="utf-8")).get("rules", {}))


def body_of(text: str) -> str:
    """Everything after the front matter, so tags and titles are not scanned."""
    parts = text.split("---\n", 2)
    return parts[2] if len(parts) > 2 else text


def strip_markers(body: str) -> str:
    """Remove the markers themselves so a key like fha-203k is not a match."""
    return MARKER.sub(" ", body)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument(
        "--all", action="store_true",
        help="also screen posts that carry no rule markers. Those predate the "
             "citation system and currently hold program parameters inline, so "
             "this reports a known backlog rather than a build failure.")
    args = ap.parse_args()

    keys = registered()
    errors: list[str] = []
    checked = cited = 0
    used: set[str] = set()

    for path in args.paths:
        if not path.exists():
            errors.append(f"{path}: no such file")
            continue
        text = path.read_text(encoding="utf-8")
        body = body_of(text)
        markers = [m.group(1).strip() for m in MARKER.finditer(body)]
        # Default scope is the posts this system actually governs: the ones
        # that cite a rule. Screening everything would fail the build over
        # content written before the system existed, and a check that breaks
        # publishing is a check somebody disables.
        if not markers and not args.all:
            continue
        checked += 1
        if markers:
            cited += 1
        for key in markers:
            used.add(key)
            if key not in keys:
                errors.append(
                    f"{path.name}: [[RULE:{key}]] is not registered in "
                    "content/guidelines.json"
                )

        scan = strip_markers(body)
        for rx, label in COMPILED:
            for m in rx.finditer(scan):
                line = scan[: m.start()].count("\n") + 1
                errors.append(
                    f"{path.name}:{line}: {label} written into prose: "
                    f"{m.group(0).strip()[:70]!r}. Put it behind a "
                    "[[RULE:key]] marker so it carries a citation and a date."
                )

    scope = "all posts" if args.all else "posts citing rules"
    print(f"Screened {checked} post(s) ({scope}), {cited} carrying rule "
          f"markers, {len(used)} distinct rule(s) cited.")
    if errors:
        print(f"\n{len(errors)} problem(s):", file=sys.stderr)
        for e in errors:
            print(f"  ! {e}", file=sys.stderr)
        return 1
    print("No guideline figures written into prose.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
