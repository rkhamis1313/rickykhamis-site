#!/usr/bin/env python3
"""Render the market-stats block a post asks for with <!-- MARKET:Name -->.

Why a placeholder instead of writing numbers into the markdown: sale prices go
stale in weeks. A post that hardcodes "the average sale is X" is wrong by the
next quarter and stays wrong forever, which on a licensed originator's site is
worse than publishing no number at all. The marker stays in the source, and the
figures are injected at render time from content/neighborhoods.json, so
refreshing the whole site is one data edit rather than seventy post edits.

If a community has no market data yet, the block renders an honest line saying
so rather than a fabricated range. Nothing here ever estimates.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "neighborhoods.json"
STALE_DAYS = 75


def load() -> dict:
    if not DATA.exists():
        return {}
    return json.loads(DATA.read_text(encoding="utf-8")).get("neighborhoods", {})


def money(v) -> str:
    if v is None:
        return "n/a"
    return f"${v:,.0f}"


def render(name: str) -> str:
    """Return the HTML block for one community, or an honest placeholder."""
    hood = load().get(name)
    market = (hood or {}).get("market")

    if not market or not market.get("asOf"):
        return (
            '<aside class="card" style="padding:18px 20px;margin:28px 0">'
            f"<p style='margin:0'><strong>{name} market data.</strong> "
            "I quote current figures from a dated subdivision report rather than "
            "from memory, so nothing on this page is a number I estimated. "
            "Call me for the current report on this community: "
            '<a href="tel:+14809999842">(480) 999-9842</a>.</p></aside>'
        )

    as_of = datetime.strptime(market["asOf"], "%Y-%m-%d").date()
    age = (date.today() - as_of).days
    rows = [
        ("Median sale price", money(market.get("medianSalePrice"))),
        ("Average sale price", money(market.get("averageSalePrice"))),
        ("Price per square foot", money(market.get("pricePerSqFt"))),
        ("Sales, trailing 12 months", market.get("twelveMonthSales") or "n/a"),
        ("Median days on market", market.get("medianDaysOnMarket") or "n/a"),
        ("Active listings", market.get("activeListings") or "n/a"),
    ]
    last = market.get("lastSale") or {}
    if last.get("price"):
        rows.append(("Most recent recorded sale",
                     f"{money(last['price'])} on {last.get('date', 'n/a')}"))

    body = "".join(
        f"<tr><td>{label}</td><td><strong>{value}</strong></td></tr>"
        for label, value in rows if value not in ("n/a", None)
    )

    warn = ""
    if age > STALE_DAYS:
        # Say it out loud rather than let a reader assume it is current.
        warn = (
            f"<p style='margin:8px 0 0;font-size:.85rem'><em>This report is "
            f"{age} days old. Ask me for the current one before you rely on it."
            "</em></p>"
        )

    return (
        f'<div style="overflow-x:auto"><table><caption style="text-align:left;'
        f'font-weight:600;padding-bottom:8px">{name} market snapshot</caption>'
        f"<tbody>{body}</tbody></table></div>"
        f"<p style='margin:6px 0 0;font-size:.85rem;color:var(--muted)'>"
        f"Source: {market.get('source', 'unstated')}. Figures as of "
        f"{as_of.strftime('%B %-d, %Y')}. Market data changes; confirm current "
        f"figures before relying on them.</p>{warn}"
    )


def expand(html: str) -> str:
    """Replace every [[MARKET:Name]] marker in a rendered page.

    An HTML comment was the obvious marker and the wrong one: the markdown
    converter escapes it, so it reached the page as visible text. A bracket
    token passes through untouched. Matches it with or without the wrapping
    paragraph the converter puts around a line on its own.
    """
    import re

    def sub(m):
        return render(m.group(1).strip())

    html = re.sub(r"<p>\s*\[\[MARKET:([^\]]+?)\]\]\s*</p>", sub, html)
    return re.sub(r"\[\[MARKET:([^\]]+?)\]\]", sub, html)


if __name__ == "__main__":
    import sys
    print(render(sys.argv[1] if len(sys.argv) > 1 else "Troon North"))
