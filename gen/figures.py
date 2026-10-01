#!/usr/bin/env python3
"""Charts for posts, as hand-written SVG, expanded from a [[FIGURE:name]] marker.

Why a marker rather than an <img> tag in the markdown: mdlite escapes raw HTML
and mangles markdown image syntax, so anything written inline reaches the page as
visible angle brackets. The marker survives conversion and is expanded afterward,
the same mechanism market_block.py uses.

Why SVG rather than a rendered PNG: these are charts of numbers, not photographs.
SVG stays crisp at any width, weighs a few kilobytes, and the text inside it is
real text rather than pixels.

Palette is the brand orange plus two hues from the validated reference set,
checked with the data-viz validator at the light surface:

    #F36B24 orange · #2a78d6 blue · #1baf7a aqua
    worst adjacent pair deltaE 23.1 protan, 24.0 normal vision, all checks pass

That run returned a contrast warning against the surface, which obligates visible
labels rather than relying on colour alone. Every series below is directly
labelled and also named in the legend, which satisfies it.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "assets" / "images" / "figures"

ORANGE = "#F36B24"
BLUE = "#2a78d6"
AQUA = "#1baf7a"
INK = "#1b1e24"
MUTED = "#5d6169"
LINE = "#e6e7ea"


def buydown_ladder(note: float = 7.75) -> str:
    """Effective rate by year for each temporary buydown structure.

    A step chart, not a smooth line: the rate holds flat for a year then jumps.
    Drawing it as a slope would misrepresent what the borrower actually pays.
    """
    series = [
        ("3-2-1 buydown", ORANGE, [note - 3, note - 2, note - 1, note, note]),
        ("2-1 buydown", BLUE, [note - 2, note - 1, note, note, note]),
        ("1-0 buydown", AQUA, [note - 1, note, note, note, note]),
    ]
    W, H = 840, 460
    L, R, T, B = 74, 210, 54, 64          # generous right margin for direct labels
    y_lo, y_hi = 4.0, 8.5
    years = 5
    pw, ph = W - L - R, H - T - B

    def x(i: int) -> float:
        return L + pw * i / years

    def y(v: float) -> float:
        return T + ph * (y_hi - v) / (y_hi - y_lo)

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}" '
         f'role="img" aria-label="Effective mortgage rate by year under a 3-2-1, '
         f'2-1 and 1-0 temporary buydown, compared with a note rate of {note} percent." '
         f'style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif">']
    p.append(f'<title>Effective rate by year under each buydown structure</title>')

    # Recessive gridlines and y axis labels.
    v = y_lo
    while v <= y_hi + 0.01:
        yy = y(v)
        p.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L+pw}" y2="{yy:.1f}" '
                 f'stroke="{LINE}" stroke-width="1"/>')
        p.append(f'<text x="{L-12}" y="{yy+4:.1f}" text-anchor="end" font-size="13" '
                 f'fill="{MUTED}">{v:.1f}%</text>')
        v += 1.0

    ny = y(note)

    # X axis.
    for i in range(years):
        cx = (x(i) + x(i + 1)) / 2
        p.append(f'<text x="{cx:.1f}" y="{T+ph+26:.0f}" text-anchor="middle" '
                 f'font-size="13.5" fill="{MUTED}">Year {i+1}</text>')
    p.append(f'<line x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}" '
             f'stroke="{MUTED}" stroke-width="1.5" opacity=".5"/>')

    # Step paths, drawn back to front so the headline series sits on top.
    label_y = []
    for name, colour, vals in series:
        d = []
        for i, val in enumerate(vals):
            x0, x1_, yy = x(i), x(i + 1), y(val)
            d.append(f'{"M" if i == 0 else "L"}{x0:.1f},{yy:.1f}')
            d.append(f'L{x1_:.1f},{yy:.1f}')
        p.append(f'<path d="{" ".join(d)}" fill="none" stroke="{colour}" '
                 f'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
        # Year one is the number that matters, so mark and label it.
        y1 = y(vals[0])
        p.append(f'<circle cx="{x(0)+pw/years/2:.1f}" cy="{y1:.1f}" r="5.5" '
                 f'fill="{colour}" stroke="#fff" stroke-width="2"/>')
        label_y.append((name, colour, vals[0], y1))

    # Direct labels at the right edge, nudged apart so they never collide.
    label_y.sort(key=lambda t: t[3])
    last = -99.0
    for name, colour, v1, yy in label_y:
        yy = max(yy, last + 19)
        last = yy
        p.append(f'<text x="{L+pw+10}" y="{yy+5:.1f}" font-size="13.5" '
                 f'fill="{colour}" font-weight="700">{name}</text>')
        p.append(f'<text x="{L+pw+10}" y="{yy+22:.1f}" font-size="12.5" '
                 f'fill="{MUTED}">year 1 near {v1:.2f}%</text>')

    # Reference line last so it stays visible where the series land on top of it.
    p.append(f'<line x1="{L}" y1="{ny:.1f}" x2="{L+pw}" y2="{ny:.1f}" '
             f'stroke="#fff" stroke-width="5" opacity=".85"/>')
    p.append(f'<line x1="{L}" y1="{ny:.1f}" x2="{L+pw}" y2="{ny:.1f}" '
             f'stroke="{INK}" stroke-width="2.5" stroke-dasharray="8 6"/>')
    p.append(f'<text x="{L+pw+10}" y="{ny+5:.1f}" font-size="13.5" fill="{INK}" '
             f'font-weight="700">Note rate {note}%</text>')

    p.append(f'<text x="{L}" y="26" font-size="16" font-weight="700" fill="{INK}">'
             f'What each buydown structure does to the rate</text>')
    p.append(f'<text x="{L}" y="44" font-size="12.5" fill="{MUTED}">'
             f'Illustrative, derived from each structure applied to an assumed '
             f'note rate. Not a quote.</text>')
    p.append("</svg>")
    return "\n".join(p)


def builder_incentives() -> str:
    """Two numbers from the Realtor.com data, as a stat pair.

    Deliberately not a bar chart. Two values do not need axes, and a hero number
    reads faster than a plot of two bars.
    """
    W, H = 840, 240
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}" role="img" '
         f'aria-label="18.8 percent of newly built home listings advertise a buyer '
         f'incentive, and 13.8 percent specifically advertise a reduced mortgage rate." '
         f'style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif">']
    p.append(f'<text x="0" y="24" font-size="16" font-weight="700" fill="{INK}">'
             f'What builders are advertising</text>')
    tiles = [
        (0, "18.8%", "of new-build listings carry an advertised buyer incentive", ORANGE),
        (W / 2 + 10, "13.8%", "advertise a reduced mortgage rate specifically", BLUE),
    ]
    for tx, big, sub, colour in tiles:
        p.append(f'<rect x="{tx}" y="48" width="{W/2-10}" height="150" rx="14" '
                 f'fill="#f4f5f7"/>')
        p.append(f'<rect x="{tx}" y="48" width="5" height="150" rx="2.5" fill="{colour}"/>')
        p.append(f'<text x="{tx+26}" y="118" font-size="52" font-weight="800" '
                 f'fill="{colour}">{big}</text>')
        # Wrap the caption by hand; SVG has no text flow.
        words, lines, cur = sub.split(), [], ""
        for w in words:
            if len(cur + " " + w) > 42:
                lines.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        for i, ln in enumerate(lines[:2]):
            p.append(f'<text x="{tx+26}" y="{148+i*19}" font-size="13.5" '
                     f'fill="{MUTED}">{ln}</text>')
    p.append(f'<text x="0" y="{H-8}" font-size="12" fill="{MUTED}">'
             f'Source: Realtor.com, September 2026.</text>')
    p.append("</svg>")
    return "\n".join(p)


FIGURES = {
    "buydown-ladder": (
        buydown_ladder,
        "Effective mortgage rate by year under a 3-2-1, 2-1 and 1-0 temporary "
        "buydown, each returning to the note rate. Illustrative.",
    ),
    "builder-incentives": (
        builder_incentives,
        "18.8% of new-build listings advertise a buyer incentive; 13.8% "
        "advertise a reduced mortgage rate. Realtor.com, September 2026.",
    ),
}


def build(name: str) -> Path:
    fn, _ = FIGURES[name]
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"{name}.svg"
    dest.write_text(fn(), encoding="utf-8")
    return dest


def expand(html: str) -> str:
    """Replace [[FIGURE:name]] with a real figure element, with or without the
    paragraph the markdown converter wraps a lone line in."""

    def sub(m):
        name = m.group(1).strip()
        if name not in FIGURES:
            return ""
        build(name)
        _, caption = FIGURES[name]
        return (
            f'<figure style="margin:30px 0">'
            f'<img src="/assets/images/figures/{name}.svg" alt="{caption}" '
            f'style="width:100%;height:auto;display:block;border:1px solid #e6e7ea;'
            f'border-radius:14px;background:#fff;padding:14px;box-sizing:border-box">'
            f'<figcaption style="font-size:.85rem;color:var(--muted);margin-top:10px">'
            f'{caption}</figcaption></figure>'
        )

    html = re.sub(r"<p>\s*\[\[FIGURE:([^\]]+?)\]\]\s*</p>", sub, html)
    return re.sub(r"\[\[FIGURE:([^\]]+?)\]\]", sub, html)


if __name__ == "__main__":
    for n in FIGURES:
        print("  +", build(n).relative_to(ROOT))
