#!/usr/bin/env python3
"""Monthly citation review, driven by results Ricky checks by hand.

There is no Perplexity or ChatGPT API here, so the loop is deliberately async
and never blocks a publish run:

    --new            write a checklist of the questions to test, then notify
    --apply FILE     read the filled-in checklist, reorder the queue, log it
    --status         report whether a review is due or a checklist is waiting

The checklist is plain markdown with tick boxes. Ricky runs each question in
ChatGPT and Perplexity, ticks whichever cited rickykhamis.com, and saves. This
script turns those ticks into a queue order.

Usage:
    python gen/review.py --status
    python gen/review.py --new
    python gen/review.py --apply content/review/2026-10-05-checklist.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERIES_FILE = ROOT / "content" / "series.json"
REVIEW_DIR = ROOT / "content" / "review"
BASE_URL = "https://rickykhamis.com"
SAMPLE = 10

# A question counts as winning if, on average across the assistants tested, it
# was cited at least once.
WINNING = 1.0

# A series or city needs this many tested questions before it is allowed to move
# the queue. One citation is an anecdote, and acting on it reshuffles almost the
# whole plan on noise. Below the bar a bucket is treated as untested.
MIN_EVIDENCE = 2


def load() -> dict:
    return json.loads(SERIES_FILE.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    SERIES_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def log(message: str) -> None:
    print(message, flush=True)


def relative_or_absolute(path: Path) -> str:
    """Repo-relative when the file lives here, absolute otherwise. A checklist
    pasted into /tmp is still a valid input and must not crash the run."""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


# ------------------------------------------------------------------ checklist
def write_checklist(data: dict, today: date) -> Path:
    published = [p for p in data.get("published", []) if p.get("question")]
    recent = published[-SAMPLE:]
    if not recent:
        raise SystemExit("No published posts carry a question yet; nothing to test.")

    path = REVIEW_DIR / f"{today.isoformat()}-checklist.md"
    lines = [
        f"# Citation check, {today.isoformat()}",
        "",
        "Run each question in ChatGPT and in Perplexity. Tick the box for any",
        "assistant that cited or linked rickykhamis.com in its answer. Leave a",
        "box unticked if it did not. Skip a question entirely and it is ignored.",
        "",
        "Add anything useful under notes: which competitor got cited, whether the",
        "answer was right, whether it named Ricky without linking. That text is",
        "kept verbatim in the review log.",
        "",
        "Save the file, then tell Claude it is ready.",
        "",
        "---",
        "",
    ]
    for n, entry in enumerate(recent, 1):
        lines += [
            f"### {n}. {entry['question']}",
            f"- url: {BASE_URL}/blog/{entry['slug']}/",
            f"- series: {entry.get('series', 'unknown')}  city: {entry.get('city', 'unknown')}",
            "- [ ] ChatGPT cited rickykhamis.com",
            "- [ ] Perplexity cited rickykhamis.com",
            "- notes:",
            "",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------- parse + apply
def parse_checklist(path: Path) -> list[dict]:
    """Read a filled-in checklist into per-question results."""
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"^### \d+\.\s*", text, flags=re.M)[1:]
    if not blocks:
        raise SystemExit(
            f"{path} has no '### N. question' blocks. Is it the checklist file?"
        )

    results = []
    for block in blocks:
        question = block.splitlines()[0].strip()
        slug_match = re.search(r"^- url:\s*\S+/blog/([^/\s]+)/", block, re.M)
        series_match = re.search(r"^- series:\s*(\S+)\s+city:\s*(.+)$", block, re.M)
        notes_match = re.search(r"^- notes:(.*)$", block, re.M)

        def ticked(label: str) -> bool:
            found = re.search(rf"^- \[( |x|X)\] {label}", block, re.M)
            return bool(found and found.group(1).lower() == "x")

        chatgpt = ticked("ChatGPT")
        perplexity = ticked("Perplexity")
        tested = bool(
            re.search(r"^- \[[xX]\]", block, re.M)
            or (notes_match and notes_match.group(1).strip())
        )

        results.append({
            "question": question,
            "slug": slug_match.group(1) if slug_match else None,
            "series": series_match.group(1) if series_match else None,
            "city": series_match.group(2).strip() if series_match else None,
            "chatgpt": chatgpt,
            "perplexity": perplexity,
            "tested": tested,
            "score": int(chatgpt) + int(perplexity),
            "notes": notes_match.group(1).strip() if notes_match else "",
        })
    return results


def rank(results: list[dict], key: str) -> dict[str, dict]:
    buckets: dict[str, dict] = {}
    for r in results:
        if not r["tested"] or not r.get(key):
            continue
        b = buckets.setdefault(r[key], {"tested": 0, "score": 0})
        b["tested"] += 1
        b["score"] += r["score"]
    for b in buckets.values():
        b["mean"] = b["score"] / b["tested"]
    return buckets


def band(buckets: dict[str, dict], name: str | None) -> int:
    """0 winning, 1 untested or not enough evidence, 2 cold. Lower sorts first."""
    b = buckets.get(name or "")
    if not b or b["tested"] < MIN_EVIDENCE:
        return 1
    if b["mean"] >= WINNING:
        return 0
    if b["mean"] == 0 and b["tested"] >= 2:
        return 2
    return 1


def apply_review(path: Path, today: date) -> int:
    data = load()
    results = parse_checklist(path)
    tested = [r for r in results if r["tested"]]

    log(f"Read {len(results)} question(s) from {path.name}; {len(tested)} marked.")
    if not tested:
        log("Nothing is ticked and no notes are filled in. Queue left unchanged.")
        log("Tick a box or write a note for at least one question, then re-run.")
        return 1

    for r in tested:
        marks = []
        if r["chatgpt"]:
            marks.append("ChatGPT")
        if r["perplexity"]:
            marks.append("Perplexity")
        log(f"  {r['score']}/2  {', '.join(marks) or 'no citations'}  {r['question']}")

    by_series = rank(results, "series")
    by_city = rank(results, "city")

    actionable = [n for n, b in {**by_series, **by_city}.items()
                  if b["tested"] >= MIN_EVIDENCE]

    log("\nBy series:")
    for name, b in sorted(by_series.items(), key=lambda kv: -kv[1]["mean"]):
        log(f"  {b['mean']:.2f} over {b['tested']} tested  {name}")
    log("By city:")
    for name, b in sorted(by_city.items(), key=lambda kv: -kv[1]["mean"]):
        log(f"  {b['mean']:.2f} over {b['tested']} tested  {name}")

    # Reorder pending entries among themselves. Entries held at status "review"
    # keep their positions, since the task never takes them anyway.
    queue = data["queue"]
    slots = [i for i, e in enumerate(queue) if e.get("status") == "pending"]
    pending = [queue[i] for i in slots]
    before = [e["slug"] for e in pending]

    ordered = sorted(
        enumerate(pending),
        key=lambda pair: (
            band(by_series, pair[1].get("series")),
            band(by_city, pair[1].get("city")),
            pair[0],
        ),
    )
    for slot, (_, entry) in zip(slots, ordered):
        queue[slot] = entry

    after = [queue[i]["slug"] for i in slots]
    moved = sum(1 for a, b in zip(before, after) if a != b)

    if not actionable:
        log(f"\nNo series or city has {MIN_EVIDENCE} tested questions yet, so "
            "there is nothing solid enough to reorder on.")
        log("Recorded the results; queue order left as it was.")
    log(f"\nReordered {moved} of {len(pending)} pending entries.")
    log("Next five:")
    for slug in after[:5]:
        log(f"  {slug}")

    review = data.setdefault("review", {})
    review.setdefault("log", []).append({
        "date": today.isoformat(),
        "checklist": relative_or_absolute(path),
        "questionsTested": len(tested),
        "bySeries": {k: round(v["mean"], 2) for k, v in by_series.items()},
        "byCity": {k: round(v["mean"], 2) for k, v in by_city.items()},
        "entriesMoved": moved,
        "newHead": after[:5],
        "notes": [
            {"question": r["question"], "note": r["notes"]}
            for r in tested if r["notes"]
        ],
    })
    review["lastRunOn"] = today.isoformat()
    review["nextDueOn"] = (
        today + timedelta(days=int(review.get("everyDays", 30)))
    ).isoformat()
    review.pop("pendingChecklist", None)
    save(data)

    log(f"\nLogged. Next review due {review['nextDueOn']}.")
    return 0


# ----------------------------------------------------------------------- status
def status(data: dict, today: date) -> int:
    review = data.get("review", {})
    due_on = review.get("nextDueOn")
    waiting = review.get("pendingChecklist")

    log(f"Today: {today.isoformat()}")
    log(f"Review due on: {due_on}  (last run: {review.get('lastRunOn') or 'never'})")
    if waiting:
        path = ROOT / waiting
        log(f"Checklist waiting: {waiting}"
            f"{'' if path.exists() else '  [MISSING ON DISK]'}")
    else:
        log("No checklist outstanding.")
    log(f"Review due now: {bool(due_on and today.isoformat() >= due_on)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--new", action="store_true")
    group.add_argument("--apply", metavar="FILE")
    group.add_argument("--status", action="store_true")
    args = parser.parse_args()

    today = date.today()
    data = load()

    if args.status:
        return status(data, today)

    if args.new:
        path = write_checklist(data, today)
        data.setdefault("review", {})["pendingChecklist"] = str(
            path.relative_to(ROOT)
        )
        save(data)
        log(f"Wrote {path.relative_to(ROOT)}")
        log("Ricky fills it in, then run --apply on it.")
        return 0

    return apply_review(Path(args.apply).resolve(), today)


if __name__ == "__main__":
    sys.exit(main())
