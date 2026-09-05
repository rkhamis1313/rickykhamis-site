#!/usr/bin/env python3
"""Screen post markdown for mortgage-advertising problems before publishing.

Ricky is a licensed MLO (NMLS #173141; EPiQ Lending NMLS #1936984), so these
posts are regulated advertising. This is a coarse net, not legal review. It
catches the mistakes an automated writer actually makes.

  ERROR  exits non-zero. Never publish over one. Covers house style (no em
         dashes) and down payment assistance terms, which must be cited to the
         program's official site, dated, and verified recently. Program facts
         and their verification dates live in content/program-facts.json.
  WARN   needs a human look. Quoting what a buyer says ("who has the best
         rate?") is fine; claiming it about EPiQ is not, and only context
         separates them.

Usage:  python gen/compliance_check.py content/posts/*.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

FACTS_FILE = Path(__file__).resolve().parent.parent / "content" / "program-facts.json"

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
    # Proof pages. A post that asks the reader to choose a lender has to give
    # them somewhere independent to check the claim.
    ("epiqlending.com/mysite/Ricky-Khamis", "link to Ricky's EPiQ profile page"),
    ("epiqlending.com/branch/1936984", "link to the Scottsdale branch page"),
    ("nmlsconsumeraccess.org", "link to NMLS Consumer Access"),
]


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def load_facts() -> dict:
    if not FACTS_FILE.exists():
        return {}
    return json.loads(FACTS_FILE.read_text(encoding="utf-8"))


def check_dpa(path: Path, text: str) -> tuple[int, int]:
    """Down payment assistance terms are the figures most likely to go stale and
    the ones a reader will act on. A post that names a program must cite that
    program's official site, must not repeat a value known to be out of date,
    and must date any specific figure it states."""
    facts = load_facts()
    programs = facts.get("programs", {})
    max_age = int(facts.get("maxVerificationAgeDays", 90))
    errors = warnings = 0

    for name, program in programs.items():
        match = re.search(rf"\b{re.escape(name)}\b", text, re.I)
        if not match:
            continue
        line = line_of(text, match.start())

        # 1. Cite the official source.
        domain = program.get("citeDomain")
        if domain and domain.lower() not in text.lower():
            print(f"  ERROR {path.name}:{line}  names {name} without citing "
                  f"{program.get('officialUrl')}")
            errors += 1

        # 2. Never point a reader at a program they cannot use.
        if program.get("serviceAreaAvailable") is False:
            recommending = re.search(
                rf"(?:apply|qualify|eligible|available|consider|look into|check)"
                rf"[^.]{{0,80}}\b{re.escape(name)}\b"
                rf"|\b{re.escape(name)}\b[^.]{{0,80}}"
                rf"(?:is available|you can|may qualify|offers you)",
                text, re.I,
            )
            if recommending:
                print(f"  ERROR {path.name}:{line}  {name} is not available in "
                      f"our service area. {program.get('unavailableReason', '')}")
                errors += 1
            else:
                print(f"  WARN  {path.name}:{line}  {name} is not available in "
                      "our service area; mention it only to rule it out")
                warnings += 1

        # 3. Never repeat a value we know has changed.
        for stale in program.get("staleValues", []):
            for hit in re.finditer(re.escape(stale), text, re.I):
                print(f"  ERROR {path.name}:{line_of(text, hit.start())}  "
                      f"{name}: {stale!r} is a known stale value")
                errors += 1

        # 4. Any specific figure needs a date the reader can judge.
        program_facts = program.get("facts") or {}
        figures = [str(program_facts.get(k)) for k in
                   ("incomeLimit", "assistanceMax", "forgivenessMonths")
                   if program_facts.get(k)]
        states_figure = any(
            re.search(re.escape(f.replace("up to ", "").split(" of ")[0]), text, re.I)
            for f in figures
        )
        dated = re.search(
            r"as of \w+ \d{1,2},? \d{4}|verified against[^.]*\d{4}", text, re.I
        )
        if states_figure and not dated:
            print(f"  ERROR {path.name}:{line}  states {name} terms with no "
                  "'as of <date>' or 'verified against ... <year>' marker")
            errors += 1

        # 5. Our own verification has to be recent.
        verified_on = program.get("verifiedOn")
        if states_figure:
            if not verified_on:
                print(f"  ERROR {path.name}:{line}  {name} has no verifiedOn in "
                      f"content/program-facts.json. Read {program.get('officialUrl')}, "
                      "fill in the facts, set verifiedOn to today, then re-run")
                errors += 1
            else:
                age = (date.today() - datetime.strptime(verified_on, "%Y-%m-%d").date()).days
                if age > max_age:
                    print(f"  ERROR {path.name}:{line}  {name} terms were last "
                          f"verified {age} days ago (limit {max_age}). Re-check "
                          f"{program.get('officialUrl')} and update verifiedOn")
                    errors += 1
                elif age > max_age // 2:
                    print(f"  WARN  {path.name}:{line}  {name} verification is "
                          f"{age} days old; re-check soon")
                    warnings += 1

    return errors, warnings


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

    dpa_errors, dpa_warnings = check_dpa(path, text)
    errors += dpa_errors
    warnings += dpa_warnings

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
