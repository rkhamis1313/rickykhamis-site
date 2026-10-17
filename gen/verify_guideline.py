#!/usr/bin/env python3
"""Stamp a guideline rule as verified against its handbook section.

This is the only sanctioned way a rule gets a verifiedOn date. The point is
that the date means something: a human opened the cited section, read it, and
recorded what it said. A hand-edited date in the JSON means nothing, which is
why the file's own comment block says not to do it.

Usage:
    python gen/verify_guideline.py fha-min-credit-score \
        --section "Handbook 4000.1 II.A.4.b" \
        --text "Borrowers with a minimum decision credit score of ... " \
        [--overlay "Most investors overlay to ..."] \
        [--apply]

Without --apply it prints what it would write and changes nothing.

    python gen/verify_guideline.py --audit      # coverage report
    python gen/verify_guideline.py --list       # unverified keys, for a work list
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "guidelines.json"

# A citation has to name a section, not just a document. "Handbook 4000.1" is
# not a citation, it is a book. These are the shapes that count as specific.
VAGUE = {
    "handbook 4000.1", "4000.1", "hud handbook", "fha handbook", "the handbook",
    "m26-7", "va handbook", "selling guide", "fannie mae selling guide",
    "freddie mac guide", "hb-1-3555", "usda handbook", "guidelines", "hud",
}


def load_doc() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def cmd_audit() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import guidelines
    return guidelines.audit()


def cmd_list() -> int:
    rules = load_doc()["rules"]
    pending = [
        (k, r) for k, r in sorted(rules.items())
        if not r.get("verifiedOn") or not (r.get("handbookFloor") or "").strip()
    ]
    if not pending:
        print("Every registered rule is verified.")
        return 0
    print(f"{len(pending)} rule(s) awaiting verification:\n")
    by_topic: dict[str, list] = {}
    for k, r in pending:
        by_topic.setdefault(f"{r.get('program','?')} / {r.get('topic','?')}", []).append((k, r))
    for group in sorted(by_topic):
        print(f"  {group}")
        for k, r in by_topic[group]:
            print(f"    {k}")
            print(f"        {r.get('question','(no question set)')}")
            if note := r.get("judgmentNeeded"):
                print(f"        needs from Ricky: {note}")
        print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("key", nargs="?")
    ap.add_argument("--section", help="specific citation, e.g. 'Handbook 4000.1 II.A.4.b'")
    ap.add_argument("--text", help="what the section actually says")
    ap.add_argument("--overlay", help="what investors actually do, as an observation")
    ap.add_argument("--judgment", help="replace the judgmentNeeded note")
    ap.add_argument("--apply", action="store_true", help="write the file")
    ap.add_argument("--audit", action="store_true", help="coverage report")
    ap.add_argument("--list", action="store_true", help="list unverified rules")
    args = ap.parse_args()

    if args.audit:
        return cmd_audit()
    if args.list:
        return cmd_list()

    if not args.key:
        ap.error("give a rule key, or --audit, or --list")

    doc = load_doc()
    rules = doc["rules"]

    if args.key not in rules:
        print(f"no rule registered under {args.key!r}.", file=sys.stderr)
        print("Register it in content/guidelines.json first, so a rule can "
              "never arrive for a question no page asks.", file=sys.stderr)
        close = [k for k in rules if args.key.split("-")[0] in k][:6]
        if close:
            print("\nSimilar keys:", file=sys.stderr)
            for k in close:
                print(f"  {k}", file=sys.stderr)
        return 2

    rule = rules[args.key]
    stamping = bool(args.section or args.text)

    if stamping:
        if not (args.section and args.text):
            print("--section and --text must be given together. A rule without "
                  "a citation is a rule written from memory.", file=sys.stderr)
            return 2
        section = args.section.strip()
        text = args.text.strip()
        if section.lower().rstrip(".") in VAGUE:
            print(f"section {section!r} names a document, not a section. "
                  "Cite the subsection you actually read.", file=sys.stderr)
            return 2
        if len(section) < 12:
            print(f"section {section!r} is too short to be a real citation.",
                  file=sys.stderr)
            return 2
        if len(text) < 25:
            print("--text is too short to be the rule. Quote or paraphrase "
                  "what the section says.", file=sys.stderr)
            return 2
        rule["handbookFloor"] = text
        rule["section"] = section
        rule["verifiedOn"] = date.today().isoformat()

    if args.overlay is not None:
        rule["overlayReality"] = args.overlay.strip() or None
    if args.judgment is not None:
        rule["judgmentNeeded"] = args.judgment.strip() or None

    if not stamping and args.overlay is None and args.judgment is None:
        # Read-only: show the rule's current state.
        print(json.dumps({args.key: rule}, indent=2))
        return 0

    print(f"  {args.key}")
    print(f"      program  {rule.get('program')}  /  {rule.get('topic')}")
    print(f"      question {rule.get('question')}")
    if stamping:
        print(f"      section  {rule['section']}")
        print(f"      verified {rule['verifiedOn']}")
        print(f"      rule     {rule['handbookFloor'][:140]}"
              f"{'...' if len(rule['handbookFloor']) > 140 else ''}")
    if rule.get("overlayReality"):
        print(f"      overlay  {rule['overlayReality'][:140]}")

    if not args.apply:
        print("\nDry run. Re-run with --apply to write.")
        return 1

    DATA.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"\nWrote {DATA.relative_to(ROOT)}.")
    print("Pages already published that cite this rule need re-rendering:")
    print("  python gen/new_post.py --force content/posts/<post>.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
