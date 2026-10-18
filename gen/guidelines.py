#!/usr/bin/env python3
"""Render a citable loan-program rule from a [[RULE:key]] marker.

Why a marker rather than prose: a guideline is the volatile half of an
educational page. Hardcode "FHA requires X" into forty posts and a handbook
update means forty edits, which means it never happens, which means a licensed
originator's site carries stale rules under his NMLS number. The rule lives in
content/guidelines.json, the posts carry markers, and a refresh is one edit.

Why it refuses to state an unverified rule: the failure mode here is not an
ugly page, it is a reader acting on a number nobody checked. So the default
state prints no number at all. A post can publish before anyone opens the
handbook, and it says honestly that the requirement is confirmed per file.
When the rule is verified the same page starts citing the section and the date.

Three states, matching market_block.py's pattern:

  verifiedOn is null          -> honest placeholder, no number, phone number
  verifiedOn recent           -> the rule, the citation, the date
  verifiedOn past STALE_DAYS  -> the rule plus a visible age notice

The overlay distinction is deliberate and load-bearing. `handbookFloor` is the
published rule. `overlayReality` is what investors actually do, which is an
observation rather than a published requirement, and it renders under a label
that says so. Never merge the two.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "guidelines.json"

# A guideline goes stale slower than a sale price but faster than a founding
# year. Agency handbooks see meaningful updates a few times a year, so half a
# year is the point at which a reader deserves to be told the age.
STALE_DAYS = 180

PHONE = '<a href="tel:+14809999842">(480) 999-9842</a>'

DOC_NAMES = {
    "FHA": "HUD Handbook 4000.1",
    "VA": "VA Lenders Handbook M26-7",
    "USDA": "USDA Technical Handbook HB-1-3555",
}


def load() -> dict:
    if not DATA.exists():
        return {}
    return json.loads(DATA.read_text(encoding="utf-8")).get("rules", {})


def _aside(inner: str) -> str:
    """A cited guideline, rendered as a raised panel with an orange edge.

    The visual separation is doing real work: it marks the sourced, dated
    claim apart from the surrounding prose, which is the distinction the
    whole citation system exists to make. Styles live in site.css under
    .bevel and .rule rather than inline, so the treatment can be changed in
    one place across every page that cites a rule.
    """
    return f'<aside class="bevel rule">{inner}</aside>' 


def _overlay(rule: dict) -> str:
    """What lenders actually do, clearly marked as observation not rule."""
    overlay = (rule.get("overlayReality") or "").strip()
    if not overlay:
        return ""
    return (
        '<span class="ovl"><b>What lenders actually do.</b> '
        f"{overlay} That is my observation from running these files, not a "
        "published requirement, and it varies by investor.</span>"
    )


def render(key: str) -> str:
    """Return the HTML block for one rule, or an honest placeholder."""
    rule = load().get(key)

    if rule is None:
        # An unknown key is a content bug, not a borrower-facing situation.
        # Say so in the page rather than failing the build silently.
        return _aside(
            "<p style='margin:0'><strong>Missing rule reference.</strong> "
            f"No rule is registered under <code>{key}</code>. "
            "This is a site error; please call and I will answer directly: "
            f"{PHONE}.</p>"
        )

    program = rule.get("program", "This program")
    question = rule.get("question", "").strip()
    heading = f"<strong>{question}</strong> " if question else ""
    floor = (rule.get("handbookFloor") or "").strip()
    section = (rule.get("section") or "").strip()
    verified = rule.get("verifiedOn")

    # State 1: not verified. Print no number. This is the safe default and it
    # is what every rule starts as.
    if not verified or not floor or not section:
        doc = DOC_NAMES.get(program, "the program guidelines")
        return _aside(
            f"<p style='margin:0'>{heading}I quote {program} requirements from "
            f"{doc} with the section and the date I checked it, rather than "
            "from memory, because a stale guideline on a lender's site is worse "
            "than no guideline. This one is not yet stamped, so rather than "
            "publish a number I have not re-verified, call me and I will give "
            f"you the current requirement and what it means for your file: "
            f"{PHONE}.</p>" + _overlay(rule)
        )

    as_of = datetime.strptime(verified, "%Y-%m-%d").date()
    age = (date.today() - as_of).days

    warn = ""
    if age > STALE_DAYS:
        warn = (
            '<span class="age">This was verified '
            f"{age} days ago. Guidelines change; confirm the current "
            "requirement before you rely on it.</span>"
        )

    return _aside(
        f"<p style='margin:0'>{heading}{floor}</p>"
        + _overlay(rule)
        + f'<span class="src">'
        f"Source: {section}. Verified "
        f"{as_of.strftime('%B %-d, %Y')}. Guidelines change and investor "
        "requirements are frequently stricter than the published floor; this "
        "is general information, not a commitment to lend.</span>" + warn
    )


def expand(html: str) -> str:
    """Replace every [[RULE:key]] marker in a rendered page.

    Matches the marker with or without the wrapping paragraph the markdown
    converter puts around a line on its own, exactly as market_block does.
    """
    def sub(m):
        return render(m.group(1).strip())

    html = re.sub(r"<p>\s*\[\[RULE:([^\]]+?)\]\]\s*</p>", sub, html)
    return re.sub(r"\[\[RULE:([^\]]+?)\]\]", sub, html)


def audit() -> int:
    """Report verification coverage. Used by the publish workflow."""
    rules = load()
    if not rules:
        print("no rules registered")
        return 0

    verified, unverified, stale = [], [], []
    for key, r in sorted(rules.items()):
        v = r.get("verifiedOn")
        if not v or not (r.get("handbookFloor") or "").strip():
            unverified.append(key)
            continue
        age = (date.today() - datetime.strptime(v, "%Y-%m-%d").date()).days
        (stale if age > STALE_DAYS else verified).append((key, age))

    print(f"Guidelines: {len(rules)} registered, {len(verified)} verified, "
          f"{len(stale)} stale, {len(unverified)} unverified.")
    for key, age in stale:
        print(f"  STALE      {key}  ({age} days)")
    for key in unverified:
        print(f"  unverified {key}")
    if unverified:
        print("\nUnverified rules render an honest placeholder and no number, "
              "so this is safe to publish. Verify with gen/verify_guideline.py.")
    return 0


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--audit":
        raise SystemExit(audit())
    print(render(sys.argv[1] if len(sys.argv) > 1 else "fha-min-credit-score"))
