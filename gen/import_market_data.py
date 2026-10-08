#!/usr/bin/env python3
"""Load market figures into content/neighborhoods.json from a CSV export.

Why this exists: every neighborhood post carries a [[MARKET:Name]] marker, and
until real figures are supplied that marker renders an honest placeholder
asking the reader to call. Filling it in by hand across a growing number of
communities is error prone, and the one error that matters here is publishing
a wrong number on a licensed originator's site. So the data arrives as a CSV
pulled from a real report, gets validated hard, and is written mechanically.

The design rule, inherited from neighborhoods.json: `facts` are stable and
sourced, `market` is volatile and carries asOf plus source. This script only
ever touches `market`. It will not invent a figure, it will not estimate a
missing one, and it refuses a row that cannot say where it came from or when.

Usage:
    python gen/import_market_data.py report.csv            # dry run, prints a diff
    python gen/import_market_data.py report.csv --apply    # writes the file

See content/market-data-template.csv for the columns, and the README section
"Refreshing market data" for the workflow.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "neighborhoods.json"

# Generous bounds. These are not a view on the market, they are a guard against
# a transposed digit or a figure typed in thousands. A number outside them is
# far more likely a typo than a real Scottsdale sale.
BOUNDS = {
    "medianSalePrice": (50_000, 50_000_000),
    "averageSalePrice": (50_000, 50_000_000),
    "pricePerSqFt": (50, 5_000),
    "activeListings": (0, 10_000),
    "medianDaysOnMarket": (0, 2_000),
    "twelveMonthSales": (0, 10_000),
}

MONEY_FIELDS = {"medianSalePrice", "averageSalePrice", "pricePerSqFt"}
INT_FIELDS = {"activeListings", "medianDaysOnMarket", "twelveMonthSales"}

# A source naming the MLS triggers a licensing reminder. Republishing MLS data
# on a public site carries IDX obligations from ARMLS; county records do not.
MLS_HINTS = ("mls", "armls", "flexmls", "matrix", "paragon")


class RowError(Exception):
    """A row that cannot be trusted. Never published, always reported."""


def clean(raw: str | None) -> str:
    return (raw or "").strip()


def parse_money(field: str, raw: str) -> float | None:
    """Accept 1234567, 1,234,567, $1,234,567 and 1234567.00. Reject the rest."""
    s = clean(raw).replace("$", "").replace(",", "").replace("_", "")
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        raise RowError(f"{field}: {raw!r} is not a number")
    if v != v or v in (float("inf"), float("-inf")):
        raise RowError(f"{field}: {raw!r} is not a finite number")
    lo, hi = BOUNDS[field]
    if not lo <= v <= hi:
        raise RowError(
            f"{field}: {v:,.0f} is outside {lo:,} to {hi:,}. "
            "Check for a transposed digit or a figure entered in thousands."
        )
    return v


def parse_int(field: str, raw: str) -> int | None:
    s = clean(raw).replace(",", "").replace("_", "")
    if not s:
        return None
    try:
        v = int(float(s))
    except ValueError:
        raise RowError(f"{field}: {raw!r} is not a whole number")
    lo, hi = BOUNDS[field]
    if not lo <= v <= hi:
        raise RowError(f"{field}: {v:,} is outside {lo:,} to {hi:,}")
    return v


def parse_day(field: str, raw: str, *, required: bool) -> date | None:
    s = clean(raw)
    if not s:
        if required:
            raise RowError(f"{field} is required and empty")
        return None
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise RowError(f"{field}: {raw!r} is not YYYY-MM-DD")
    if d > date.today():
        raise RowError(f"{field}: {s} is in the future")
    return d


def build_market(row: dict[str, str]) -> dict:
    """Turn one validated CSV row into a `market` object, or raise."""
    as_of = parse_day("asOf", row.get("asOf", ""), required=True)
    age = (date.today() - as_of).days
    if age > 365:
        raise RowError(
            f"asOf is {age} days old. Pull a current report rather than "
            "publishing a year-old figure."
        )

    source = clean(row.get("source"))
    if not source:
        raise RowError("source is required. Name the report, not 'MLS'.")
    if len(source) < 8:
        raise RowError(f"source {source!r} is too vague to cite")

    market: dict = {"asOf": as_of.isoformat(), "source": source}

    for f in sorted(MONEY_FIELDS):
        market[f] = parse_money(f, row.get(f, ""))
    for f in sorted(INT_FIELDS):
        market[f] = parse_int(f, row.get(f, ""))

    # Last sale is optional but must be complete if either half is present.
    ls_date_raw = clean(row.get("lastSaleDate"))
    ls_price_raw = clean(row.get("lastSalePrice"))
    if ls_date_raw or ls_price_raw:
        if not (ls_date_raw and ls_price_raw):
            raise RowError("lastSaleDate and lastSalePrice must both be set")
        d = parse_day("lastSaleDate", ls_date_raw, required=True)
        p = parse_money("medianSalePrice", ls_price_raw)  # same bounds
        ls: dict = {"date": d.isoformat(), "price": p}
        if note := clean(row.get("lastSaleNote")):
            ls["note"] = note
        market["lastSale"] = ls

    lo_raw, hi_raw = clean(row.get("priceRangeLow")), clean(row.get("priceRangeHigh"))
    if lo_raw or hi_raw:
        if not (lo_raw and hi_raw):
            raise RowError("priceRangeLow and priceRangeHigh must both be set")
        lo = parse_money("medianSalePrice", lo_raw)
        hi = parse_money("medianSalePrice", hi_raw)
        if lo > hi:
            raise RowError(f"priceRangeLow {lo:,.0f} exceeds high {hi:,.0f}")
        market["priceRange"] = {"low": lo, "high": hi}

    # A row of nothing but provenance publishes an empty table. Reject it so
    # the post keeps its honest placeholder instead.
    if not any(market.get(f) is not None for f in MONEY_FIELDS | INT_FIELDS) \
            and "lastSale" not in market:
        raise RowError("every figure is blank. Nothing to publish.")

    return market


def sanity_notes(name: str, market: dict) -> list[str]:
    """Non-fatal observations worth a human glance before publishing."""
    notes = []
    med, ppsf = market.get("medianSalePrice"), market.get("pricePerSqFt")
    if med and ppsf:
        sqft = med / ppsf
        if not 500 <= sqft <= 20_000:
            notes.append(
                f"{name}: median / price-per-sqft implies {sqft:,.0f} sqft, "
                "which looks like a unit mismatch"
            )
    avg, med = market.get("averageSalePrice"), market.get("medianSalePrice")
    if avg and med and (avg > med * 3 or med > avg * 3):
        notes.append(f"{name}: average and median differ by more than 3x")
    if any(h in market["source"].lower() for h in MLS_HINTS):
        notes.append(
            f"{name}: source names the MLS. Republishing MLS data publicly "
            "carries ARMLS IDX obligations. Confirm the agreement permits it."
        )
    return notes


def money(v) -> str:
    return "none" if v is None else f"${v:,.0f}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--apply", action="store_true",
                    help="write the file; without it this is a dry run")
    args = ap.parse_args()

    if not args.csv_path.exists():
        print(f"no such file: {args.csv_path}", file=sys.stderr)
        return 2

    doc = json.loads(DATA.read_text(encoding="utf-8"))
    hoods = doc["neighborhoods"]

    with args.csv_path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        print("the CSV has no data rows", file=sys.stderr)
        return 2
    if "neighborhood" not in (rows[0].keys() | set()):
        print("the CSV needs a 'neighborhood' column", file=sys.stderr)
        return 2

    staged: dict[str, dict] = {}
    errors: list[str] = []
    notes: list[str] = []
    unknown: list[str] = []

    for i, row in enumerate(rows, start=2):  # row 1 is the header
        name = clean(row.get("neighborhood"))
        if not name:
            errors.append(f"row {i}: neighborhood is blank")
            continue
        if name not in hoods:
            unknown.append(name)
            errors.append(
                f"row {i}: {name!r} is not in neighborhoods.json. Add the "
                "community with its sourced facts first."
            )
            continue
        try:
            market = build_market(row)
        except RowError as e:
            errors.append(f"row {i} ({name}): {e}")
            continue
        staged[name] = market
        notes.extend(sanity_notes(name, market))

    for name, market in sorted(staged.items()):
        before = hoods[name].get("market")
        verb = "replace" if before else "set"
        print(f"  {verb} {name}")
        print(f"      asOf   {market['asOf']}   source: {market['source']}")
        print(f"      median {money(market.get('medianSalePrice'))}"
              f"   avg {money(market.get('averageSalePrice'))}"
              f"   psf {money(market.get('pricePerSqFt'))}")
        if before:
            print(f"      (was asOf {before.get('asOf')},"
                  f" median {money(before.get('medianSalePrice'))})")

    if notes:
        print("\nWorth a look before you publish:")
        for n in notes:
            print(f"  ~ {n}")

    if errors:
        print(f"\n{len(errors)} row(s) rejected:", file=sys.stderr)
        for e in errors:
            print(f"  ! {e}", file=sys.stderr)

    if not staged:
        print("\nNothing valid to import.", file=sys.stderr)
        return 1

    if not args.apply:
        print(f"\nDry run. {len(staged)} community(ies) would be updated. "
              "Re-run with --apply to write.")
        return 1 if errors else 0

    for name, market in staged.items():
        hoods[name]["market"] = market

    DATA.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"\nWrote {len(staged)} community(ies) to {DATA.relative_to(ROOT)}.")
    print("Next: python gen/new_post.py --force <the affected posts>  "
          "to re-render pages that already published.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
