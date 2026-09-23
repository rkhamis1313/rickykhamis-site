#!/usr/bin/env python3
"""Record the latest Freddie Mac PMMS 30-year rate into site/assets/pmms.json.

Why this exists: /cash-out-refinance-calculator/ prices a new loan off "the last
Freddie Mac posted rate". The site is a static mirror with no build step and no
backend, so the page cannot go and look that up. A daily job can. This writes a
small JSON file next to the site assets and the page fetches it same-origin.

What it will not do is publish a number it is not sure about. Every value is
range checked and date checked before anything is written, and a failed fetch
leaves the previous file untouched and exits 0. A stale rate on a mortgage site
is worse than no rate, so the page is built to handle this file being missing,
and marks the figure stale on its own once the survey date is old enough.

PMMS posts on Thursdays. Running daily just means we pick it up the morning
after, whatever day the job happens to succeed.

    python gen/update_pmms.py             # fetch and write
    python gen/update_pmms.py --selftest  # parse fixtures, touch no network
    python gen/update_pmms.py --print     # fetch and show, write nothing
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "site" / "assets" / "pmms.json"

# Freddie Mac publishes the survey itself. FRED republishes the identical series
# as MORTGAGE30US and is a far more stable file format, so it stands in when the
# primary is unreachable or reformatted. Either way the number is Freddie Mac's
# and is attributed to the survey, not to the messenger.
SOURCES = [
    (
        "freddiemac",
        "https://www.freddiemac.com/pmms/docs/PMMS_history.csv",
    ),
    (
        "fred",
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US",
    ),
]

ATTRIBUTION = "Freddie Mac Primary Mortgage Market Survey"
ATTRIBUTION_URL = "https://www.freddiemac.com/pmms"

# A 30-year survey average outside this band means we parsed the wrong column,
# not that rates moved. PMMS has never printed below 2.5 or above 19 since 1971.
RATE_MIN, RATE_MAX = 1.0, 20.0
# The survey is weekly. Anything older than this and we are not looking at a
# current file, so refuse rather than publish something months out of date.
MAX_AGE_DAYS = 45

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d-%b-%y", "%b %d, %Y")


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip().strip('"')
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def pick_columns(header: list[str]) -> tuple[int, int] | None:
    """Find (date column, 30-year rate column) by name, then by position.

    Freddie Mac has renamed these columns more than once and may again. Match on
    what the names mean rather than on one exact spelling, and fall back to the
    first two columns, which both publishers have always used for date and the
    30-year fixed.
    """
    lowered = [h.strip().strip('"').lower() for h in header]
    date_i = rate_i = None
    for i, name in enumerate(lowered):
        if date_i is None and ("date" in name or name in ("week", "observation_date")):
            date_i = i
        if rate_i is None and (
            "mortgage30us" in name.replace(" ", "")
            or ("30" in name and "pts" not in name and "point" not in name and "p" != name[-1:])
        ):
            rate_i = i
    if date_i is None:
        date_i = 0
    if rate_i is None or rate_i == date_i:
        rate_i = 1
    if rate_i >= len(header):
        return None
    return date_i, rate_i


def latest_from_csv(text: str) -> tuple[date, float] | None:
    """Return the most recent (date, rate) row that survives validation."""
    rows = list(csv.reader(io.StringIO(text)))
    rows = [r for r in rows if r and any(c.strip() for c in r)]
    if len(rows) < 2:
        return None

    cols = pick_columns(rows[0])
    if cols is None:
        return None
    date_i, rate_i = cols

    best: tuple[date, float] | None = None
    for row in rows[1:]:
        if len(row) <= max(date_i, rate_i):
            continue
        when = parse_date(row[date_i])
        if when is None:
            continue
        raw = row[rate_i].strip().strip('"').rstrip("%")
        # FRED writes "." for a missing observation.
        if not raw or raw == ".":
            continue
        try:
            rate = float(raw)
        except ValueError:
            continue
        if not (RATE_MIN <= rate <= RATE_MAX):
            continue
        if best is None or when > best[0]:
            best = (when, rate)
    return best


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "rickykhamis.com PMMS updater (+https://rickykhamis.com/)",
            "Accept": "text/csv,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def collect() -> dict | None:
    today = date.today()
    for name, url in SOURCES:
        try:
            text = fetch(url)
        except Exception as exc:  # noqa: BLE001 - any failure just means try the next one
            print(f"  . {name}: unreachable ({exc.__class__.__name__})")
            continue
        found = latest_from_csv(text)
        if not found:
            print(f"  . {name}: reachable but no usable row, format may have changed")
            continue
        when, rate = found
        age = (today - when).days
        if when > today:
            print(f"  . {name}: survey date {when} is in the future, refusing")
            continue
        if age > MAX_AGE_DAYS:
            print(f"  . {name}: newest row is {when}, {age} days old, refusing")
            continue
        print(f"  . {name}: {rate:.2f}% surveyed {when} ({age} days old)")
        return {
            "rate": round(rate, 3),
            "surveyDate": when.isoformat(),
            "source": ATTRIBUTION,
            "sourceUrl": ATTRIBUTION_URL,
            "via": name,
            "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    return None


FIXTURES = [
    # Freddie Mac PMMS_history.csv, the long-standing shape.
    (
        "date,pmms30,pmms30p,pmms15,pmms15p\n"
        "04/02/1971,7.33,,,\n"
        "09/11/2026,6.35,0.6,5.60,0.6\n"
        "09/18/2026,6.13,0.7,5.42,0.6\n",
        "2026-09-18",
        6.13,
    ),
    # Same file after a plausible rename of the columns.
    (
        "Week,30-Yr FRM,30-Yr FRM Pts,15-Yr FRM,15-Yr FRM Pts\n"
        "09/18/2026,6.13,0.7,5.42,0.6\n",
        "2026-09-18",
        6.13,
    ),
    # FRED, current header.
    (
        "observation_date,MORTGAGE30US\n"
        "2026-09-04,6.50\n"
        "2026-09-11,.\n"
        "2026-09-18,6.13\n",
        "2026-09-18",
        6.13,
    ),
    # FRED, older header.
    ("DATE,MORTGAGE30US\n2026-09-18,6.13\n", "2026-09-18", 6.13),
    # Rows out of order: newest wins regardless of position in the file.
    (
        "date,pmms30\n09/18/2026,6.13\n09/11/2026,6.35\n",
        "2026-09-18",
        6.13,
    ),
]

BAD_FIXTURES = [
    "",
    "date,pmms30\n",
    "date,pmms30\nnot-a-date,6.13\n",
    "date,pmms30\n09/18/2026,999\n",  # out of range, wrong column
    "date,pmms30\n09/18/2026,.\n",
]


def selftest() -> int:
    failures = 0
    for text, want_date, want_rate in FIXTURES:
        got = latest_from_csv(text)
        if not got or got[0].isoformat() != want_date or abs(got[1] - want_rate) > 1e-9:
            print(f"FAIL parse: wanted {want_date} {want_rate}, got {got}")
            failures += 1
    for text in BAD_FIXTURES:
        got = latest_from_csv(text)
        if got is not None:
            print(f"FAIL reject: {text!r} should not parse, got {got}")
            failures += 1
    print(
        f"selftest: {len(FIXTURES)} formats parsed, {len(BAD_FIXTURES)} bad inputs "
        f"rejected, {failures} failure(s)."
    )
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true", help="parse fixtures, no network")
    ap.add_argument("--print", dest="show", action="store_true", help="fetch but do not write")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    print("Looking up the Freddie Mac 30-year survey rate:")
    data = collect()
    if data is None:
        # Deliberately not an error. A missed fetch leaves yesterday's file in
        # place and the page keeps working; failing here would fail the whole
        # daily publish run over a number that is nice to have.
        print("No source produced a usable rate. Leaving the existing file alone.")
        return 0

    if args.show:
        print(json.dumps(data, indent=2))
        return 0

    previous = None
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text())
        except Exception:  # noqa: BLE001 - a corrupt file is simply replaced
            previous = None

    if previous and previous.get("surveyDate") == data["surveyDate"] and previous.get("rate") == data["rate"]:
        print(f"Already current at {data['rate']}% for {data['surveyDate']}. Nothing to write.")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    was = f" (was {previous['rate']}% for {previous['surveyDate']})" if previous else ""
    print(f"Wrote {OUT.relative_to(OUT.parent.parent.parent)}: {data['rate']}% for {data['surveyDate']}{was}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
