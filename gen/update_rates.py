#!/usr/bin/env python3
"""Record Ricky's published EPiQ rate sheet into site/assets/rates.json.

Why this exists: /cash-out-refinance-calculator/ used the Freddie Mac survey
average, which is a national purchase number and has nothing to do with what
this shop actually prices. epiqrates.com/rates/rickykhamis is the real sheet and
it updates daily. It also publishes an APR next to every rate, which is what
makes it safe to republish: a rate advertised without its APR is the thing
Reg Z 1026.24(c) is about.

So this takes rate AND APR together, or it takes neither. A row missing its APR
is dropped rather than published bare. The page then shows both with equal
prominence and carries the sheet's own APR assumptions verbatim.

Note for whoever reads this next: the sheet publishes no cash-out refinance
scenario. Every row is a purchase. The calculator says so and defaults to the
lowest-leverage primary residence row as the closest available proxy, which
still understates a real cash-out. Replace that default the day a cash-out row
appears on the sheet.

A failed fetch or an unparseable page exits 0 and leaves the previous file
alone. update_pmms.py still runs, so the page always has something to fall back
to, and the page itself handles having neither.

    python gen/update_rates.py             # fetch and write
    python gen/update_rates.py --selftest  # parse fixtures, touch no network
    python gen/update_rates.py --print     # fetch and show, write nothing
"""

from __future__ import annotations

import argparse
import html as H
import json
import re
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

URL = "https://www.epiqrates.com/rates/rickykhamis"
OUT = Path(__file__).resolve().parent.parent / "site" / "assets" / "rates.json"

# A mortgage rate lives in this band. Anything outside it means the wrong number
# was picked up, not that pricing moved.
RATE_MIN, RATE_MAX = 2.0, 20.0
# The sheet is daily. Past this it is not today's pricing and must not be shown
# as if it were.
MAX_AGE_DAYS = 10

# "Conventional 30-Year" then "25% down . Primary Residence" then rate then APR.
# Rates carry two or three decimals; the down payments on the same line ("25%",
# "3.5%") carry none or one, which is what keeps them out of this match.
ROW = re.compile(
    r"\b(FHA|VA|Conventional|Jumbo)\s+(\d{2})-Year\b\s*(.*?)\s*"
    r"(\d{1,2}\.\d{2,3})\s*%\s*(\d{1,2}\.\d{2,3})\s*%",
    re.I,
)
AS_OF = re.compile(
    r"(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,\s*"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(\d{1,2}),\s*(\d{4})",
    re.I,
)
APR_NOTE = re.compile(
    r"(The Annual Percentage Rate \(APR\).*?index fluctuations\.)", re.I | re.S
)


def visible_text(html: str) -> str:
    stripped = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", stripped))).strip()


def parse(html_or_text: str) -> dict | None:
    text = visible_text(html_or_text) if "<" in html_or_text else html_or_text

    rows = []
    for m in ROW.finditer(text):
        product, term, scenario, rate_s, apr_s = m.groups()
        rate, apr = float(rate_s), float(apr_s)
        if not (RATE_MIN <= rate <= RATE_MAX and RATE_MIN <= apr <= RATE_MAX):
            continue
        # APR includes financed cost, so it sits at or above the note rate. A row
        # where it does not means the two columns were read in the wrong order.
        if apr < rate - 0.01:
            continue
        scenario = re.sub(r"\s+", " ", scenario).strip(" ·-")
        rows.append(
            {
                "product": f"{product.upper() if product.upper() in ('FHA', 'VA') else product.title()} {term}-Year",
                "scenario": scenario,
                "label": f"{product.upper() if product.upper() in ('FHA', 'VA') else product.title()} {term}-Year, {scenario}" if scenario else f"{product} {term}-Year",
                "term": int(term),
                "rate": rate,
                "apr": apr,
            }
        )
    if not rows:
        return None

    as_of = None
    m = AS_OF.search(text)
    if m:
        try:
            as_of = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").date()
        except ValueError:
            as_of = None

    note = None
    m = APR_NOTE.search(text)
    if m:
        note = re.sub(r"\s+", " ", m.group(1)).strip()

    return {"rows": rows, "asOf": as_of, "aprNote": note}


def choose_default(rows: list[dict]) -> int:
    """Pick the row that least misrepresents a cash-out refinance.

    The sheet is all purchase pricing. A primary residence 30-year conventional
    at the largest down payment on the sheet is the lowest-leverage, closest
    comparison available. It is still a purchase rate and the page says so.
    """
    def score(r: dict) -> tuple:
        s = (r.get("scenario") or "").lower()
        return (
            0 if "conventional" in r["label"].lower() else 1,
            0 if r["term"] == 30 else 1,
            0 if "primary" in s else 1,
            -_down_pct(s),
        )
    return min(range(len(rows)), key=lambda i: score(rows[i]))


def _down_pct(scenario: str) -> float:
    m = re.search(r"(\d{1,2}(?:\.\d)?)\s*%\s*down", scenario, re.I)
    return float(m.group(1)) if m else 0.0


def fetch(url: str, timeout: int = 40) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; rickykhamis.com rate updater; +https://rickykhamis.com/)",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def collect() -> dict | None:
    try:
        html = fetch(URL)
    except Exception as exc:  # noqa: BLE001
        print(f"  . epiqrates unreachable ({exc.__class__.__name__})")
        return None

    parsed = parse(html)
    if not parsed:
        print("  . page reached but no rate row parsed. The sheet's layout may have changed.")
        return None

    rows, as_of = parsed["rows"], parsed["asOf"]
    today = date.today()
    if as_of is None:
        print("  . no 'as of' date found on the sheet, refusing rather than guess how old it is")
        return None
    age = (today - as_of).days
    if as_of > today:
        print(f"  . sheet is dated {as_of}, in the future, refusing")
        return None
    if age > MAX_AGE_DAYS:
        print(f"  . sheet is dated {as_of}, {age} days old, refusing")
        return None

    idx = choose_default(rows)
    print(f"  . {len(rows)} scenarios, sheet dated {as_of} ({age} day(s) old)")
    for i, r in enumerate(rows):
        print(f"      {'>' if i == idx else ' '} {r['label']}: {r['rate']}% / {r['apr']}% APR")

    return {
        "rows": rows,
        "defaultIndex": idx,
        "asOf": as_of.isoformat(),
        "aprNote": parsed["aprNote"],
        "source": "EPiQ Lending rate sheet",
        "sourceUrl": URL,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# Verbatim from the live sheet, captured 2026-09-23, so the parser is tested
# against the real thing rather than against something convenient.
FIXTURE = (
    "Ricky Khamis - Today's Rates | EPiQ Rate Sheet Today's Rates Wednesday, September 23, 2026 "
    "Current Mortgage Rates Scenario Rate APR Trending 1 Day 30 Day "
    "FHA 30-Year 3.5% down 6.625% 6.766% 0.13 % 0.42 % "
    "VA 30-Year 0% down 7.375% 7.516% 0.50 % 0.70 % "
    "Conventional 30-Year 5% down · Primary Residence 7.125% 7.286% 0.13 % 0.29 % "
    "Conventional 30-Year 25% down · Primary Residence 7.125% 7.261% 0.14 % 0.36 % "
    "Conventional 15-Year 25% down · Primary Residence 6.625% 6.873% 0% 0.27 % "
    "Conventional 30-Year 25% down · Investment 7.490% 7.628% 0.24 % 0.40 % "
    "Ricky Khamis EPiQ Lending™ NMLS# 173141 "
    "The Annual Percentage Rate (APR) is determined based on different loan amounts and types. "
    "For conforming, FHA, and VA loans, the APR is calculated based on a loan amount of $450,000. "
    "All rates are based on approximately 0.902 to 1.161 discount points paid by the borrower. "
    "The APR assumes no increase in the financial index. However, after a fixed period, your "
    "interest rate and monthly payment may increase based on market index fluctuations."
)


def selftest() -> int:
    fails = 0
    p = parse(FIXTURE)
    if not p:
        print("FAIL: fixture did not parse at all")
        return 1

    rows = p["rows"]
    if len(rows) != 6:
        print(f"FAIL: expected 6 scenarios, got {len(rows)}")
        fails += 1

    want = [
        ("FHA 30-Year", "3.5% down", 6.625, 6.766),
        ("VA 30-Year", "0% down", 7.375, 7.516),
        ("Conventional 30-Year", "5% down · Primary Residence", 7.125, 7.286),
        ("Conventional 30-Year", "25% down · Primary Residence", 7.125, 7.261),
        ("Conventional 15-Year", "25% down · Primary Residence", 6.625, 6.873),
        ("Conventional 30-Year", "25% down · Investment", 7.490, 7.628),
    ]
    for i, (prod, scen, rate, apr) in enumerate(want):
        if i >= len(rows):
            break
        r = rows[i]
        if r["product"] != prod or r["rate"] != rate or r["apr"] != apr or r["scenario"] != scen:
            print(f"FAIL row {i}: wanted {prod} | {scen} | {rate} | {apr}, got "
                  f"{r['product']} | {r['scenario']} | {r['rate']} | {r['apr']}")
            fails += 1

    if p["asOf"] != date(2026, 9, 23):
        print(f"FAIL: as-of date, wanted 2026-09-23, got {p['asOf']}")
        fails += 1

    if not p["aprNote"] or "450,000" not in p["aprNote"] or "discount points" not in p["aprNote"]:
        print(f"FAIL: APR note not captured: {p['aprNote']!r}")
        fails += 1

    idx = choose_default(rows)
    if rows[idx]["scenario"] != "25% down · Primary Residence" or rows[idx]["term"] != 30:
        print(f"FAIL: default should be the 30-year primary at the largest down payment, got {rows[idx]['label']}")
        fails += 1

    # A down payment must never be mistaken for a rate, and a row whose APR sits
    # below its rate means the columns were misread.
    bad = [
        "FHA 30-Year 3.5% down",                              # no rate pair at all
        "Conventional 30-Year 25% down 99.125% 99.200%",      # out of range
        "Conventional 30-Year 25% down 7.125% 6.900%",        # APR below rate
        "",
    ]
    for t in bad:
        got = parse(t)
        if got is not None:
            print(f"FAIL reject: {t!r} should not parse, got {got['rows']}")
            fails += 1

    print(f"selftest: {len(rows)} scenarios parsed from the live fixture, "
          f"{len(bad)} bad inputs rejected, {fails} failure(s).")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true", help="parse fixtures, no network")
    ap.add_argument("--print", dest="show", action="store_true", help="fetch but do not write")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    print("Reading the EPiQ rate sheet:")
    data = collect()
    if data is None:
        print("Nothing usable. Leaving the existing file alone; the page falls back to the survey rate.")
        return 0

    if args.show:
        print(json.dumps(data, indent=2))
        return 0

    previous = None
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text())
        except Exception:  # noqa: BLE001
            previous = None
    if previous and previous.get("asOf") == data["asOf"] and previous.get("rows") == data["rows"]:
        print(f"Already current for {data['asOf']}. Nothing to write.")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote site/assets/rates.json: {len(data['rows'])} scenarios, sheet dated {data['asOf']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
