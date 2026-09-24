#!/usr/bin/env python3
"""Generate a branded header image for each post.

Every post shipped with the same flat gradient placeholder, which is fine for
one post and looks automated across seventy. These headers are generated from
the post's own front matter, so a DC Ranch bank statement post and a Desert
Mountain asset depletion post are visibly different pages at a glance, in the
index, in a Google result and in a shared link.

Deliberately deterministic: the same slug always produces the same image, so
re-running this never churns the repo. And deliberately generated rather than
stock-photographed, because a real photograph of a golf course we do not have
rights to is a liability, and a generic stock desert is worse than a mark that
says what the page is.

Design is taken from the site's own CSS variables, not invented:
    --char  #1b1e24   --orange #F36B24   --orange-d #d55913

Usage:
    python gen/make_header.py content/posts/2026-09-12-foo.md ...
    python gen/make_header.py --all
"""

from __future__ import annotations

import argparse
import hashlib
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "content" / "posts"
OUT = ROOT / "site" / "assets" / "images" / "headers"

# 1200x630 is the Open Graph standard. Social platforms crop anything else.
W, H = 1200, 630

CHAR = (0x1B, 0x1E, 0x24)
INK = (0x0E, 0x10, 0x13)
ORANGE = (0xF3, 0x6B, 0x24)
ORANGE_D = (0xD5, 0x59, 0x13)
WHITE = (0xFF, 0xFF, 0xFF)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
REG = FONT_DIR / "DejaVuSans.ttf"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def seed_of(slug: str) -> int:
    return int(hashlib.sha256(slug.encode()).hexdigest()[:8], 16)


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
    return meta


def gradient(img: Image.Image, seed: int) -> None:
    """Diagonal wash from charcoal to orange. The angle shifts per post so the
    set does not read as one template, but the two endpoints never change."""
    d = ImageDraw.Draw(img)
    tilt = 0.35 + ((seed >> 3) % 50) / 100.0
    for y in range(H):
        for_x = y / H
        for x in range(0, W, 8):
            t = min(1.0, max(0.0, (x / W) * tilt + for_x * (1 - tilt)))
            # ease so the orange stays a highlight rather than half the frame
            t = t ** 1.9
            c = (
                int(CHAR[0] + (ORANGE[0] - CHAR[0]) * t),
                int(CHAR[1] + (ORANGE[1] - CHAR[1]) * t),
                int(CHAR[2] + (ORANGE[2] - CHAR[2]) * t),
            )
            d.rectangle([x, y, x + 8, y + 1], fill=c)


def ridges(img: Image.Image, seed: int) -> None:
    """Layered desert ridgelines. This is Scottsdale against the McDowells, and
    it gives each post a silhouette of its own without needing a photograph."""
    d = ImageDraw.Draw(img, "RGBA")
    rnd = seed
    for layer in range(4):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        base = H * (0.62 + layer * 0.09)
        amp = 42 - layer * 7
        freq = 0.0038 + ((rnd >> 5) % 22) / 10000.0
        phase = ((rnd >> 11) % 628) / 100.0
        alpha = 38 + layer * 16
        pts = []
        for x in range(0, W + 12, 12):
            y = base - amp * math.sin(x * freq + phase) - amp * 0.45 * math.sin(
                x * freq * 2.3 + phase * 1.7
            )
            pts.append((x, y))
        pts += [(W, H), (0, H)]
        d.polygon(pts, fill=(*INK, alpha))


def fit(draw, text: str, path: Path, size: int, max_w: int):
    """Shrink until it fits. Long neighborhood names must not run off frame."""
    while size > 22:
        f = font(path, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(path, size)


def wrap(draw, text: str, f, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def mark(d: ImageDraw.ImageDraw, kind: str, cx: int, cy: int, r: int) -> None:
    """Draw a loan-type mark on the right of the frame.

    The neighborhood series is identified by place, so a place name carries the
    header. A product series is identified by the product, and ten pages that
    all say Scottsdale would be ten pages that look identical. These are drawn
    rather than stock, for the same reason the ridgelines are: a licensed photo
    of a stethoscope is a cost and a liability, and a geometric mark in the
    site's own accent reads as deliberate at thumbnail size.
    """
    glow = (*WHITE, 26)
    line = (*WHITE, 62)
    hot = (*ORANGE, 70)

    if kind == "physician":
        # Medical cross inside a ring.
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=line, width=9)
        a = r * 0.46
        b = r * 0.16
        d.rectangle([cx - b, cy - a, cx + b, cy + a], fill=hot)
        d.rectangle([cx - a, cy - b, cx + a, cy + b], fill=hot)

    elif kind == "graduate":
        # Mortarboard: a diamond cap over a short tassel.
        w = r * 1.05
        d.polygon([(cx, cy - r * 0.62), (cx + w, cy - r * 0.1),
                   (cx, cy + r * 0.42), (cx - w, cy - r * 0.1)], fill=hot)
        d.line([(cx + w * 0.62, cy - r * 0.28), (cx + w * 0.62, cy + r * 0.5)],
               fill=line, width=8)
        d.line([(cx - r * 0.5, cy + r * 0.1), (cx - r * 0.5, cy + r * 0.62)], fill=line, width=8)
        d.line([(cx + r * 0.5, cy + r * 0.1), (cx + r * 0.5, cy + r * 0.62)], fill=line, width=8)
        d.arc([cx - r * 0.5, cy + r * 0.34, cx + r * 0.5, cy + r * 0.9], 0, 180, fill=line, width=8)

    elif kind == "statements":
        # Stacked statement pages with ruled lines.
        for i, off in enumerate((r * 0.5, r * 0.1, -r * 0.3)):
            x0, y0 = cx - r * 0.72 + i * 10, cy - r * 0.8 + off
            x1, y1 = x0 + r * 1.2, y0 + r * 1.25
            d.rectangle([x0, y0, x1, y1], outline=line, width=7,
                        fill=(glow if i < 2 else (*ORANGE, 34)))
            for k in range(3):
                ly = y0 + r * 0.32 + k * r * 0.26
                d.line([(x0 + r * 0.18, ly), (x1 - r * 0.22, ly)], fill=line, width=6)

    elif kind == "assets":
        # Stacked reserves, tallest at the back.
        bw = r * 0.44
        for i, h in enumerate((0.55, 0.95, 1.35)):
            x0 = cx - r * 0.85 + i * (bw + 10)
            d.rectangle([x0, cy + r * 0.62 - r * h, x0 + bw, cy + r * 0.62],
                        fill=(hot if i == 2 else glow), outline=line, width=6)

    elif kind == "dscr":
        # Rent over payment: a bar pair with the coverage line above it.
        d.line([(cx - r, cy + r * 0.72), (cx + r, cy + r * 0.72)], fill=line, width=7)
        d.rectangle([cx - r * 0.68, cy - r * 0.42, cx - r * 0.16, cy + r * 0.72],
                    fill=hot, outline=line, width=6)
        d.rectangle([cx + r * 0.16, cy + r * 0.06, cx + r * 0.68, cy + r * 0.72],
                    fill=glow, outline=line, width=6)
        d.line([(cx - r * 0.42, cy - r * 0.72), (cx + r * 0.42, cy - r * 0.72)],
               fill=line, width=7)

    elif kind == "rental":
        # A roof over a clock face: short-term rental, income by the night.
        d.polygon([(cx, cy - r), (cx + r, cy - r * 0.16), (cx - r, cy - r * 0.16)], fill=hot)
        d.ellipse([cx - r * 0.5, cy - r * 0.06, cx + r * 0.5, cy + r * 0.94],
                  outline=line, width=8)
        d.line([(cx, cy + r * 0.44), (cx, cy + r * 0.12)], fill=line, width=7)
        d.line([(cx, cy + r * 0.44), (cx + r * 0.3, cy + r * 0.44)], fill=line, width=7)

    elif kind == "condo":
        # A tower with a lit grid, for project eligibility.
        d.rectangle([cx - r * 0.62, cy - r, cx + r * 0.62, cy + r], outline=line, width=8)
        for row in range(4):
            for col in range(3):
                x0 = cx - r * 0.42 + col * r * 0.34
                y0 = cy - r * 0.76 + row * r * 0.42
                d.rectangle([x0, y0, x0 + r * 0.2, y0 + r * 0.24],
                            fill=(hot if (row + col) % 3 == 0 else glow))

    else:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=line, width=9)


def build(meta: dict) -> Image.Image:
    slug = meta.get("slug", "post")
    seed = seed_of(slug)
    img = Image.new("RGB", (W, H), CHAR)
    gradient(img, seed)
    ridges(img, seed)
    d = ImageDraw.Draw(img, "RGBA")

    pad = 72
    # Headline: the product on a product post, the place on a neighborhood post.
    # A reader searching "bank statement loan" is not searching "Scottsdale",
    # and ten product posts headlined Scottsdale would be ten identical cards.
    motif = (meta.get("motif") or "").strip().lower()
    program = (meta.get("program") or "").strip()
    place = program or meta.get("neighborhood") or meta.get("city") or "Scottsdale"
    # A mark needs room, so the headline gets a narrower column when one is drawn.
    head_w = W - pad * 2 - (300 if motif else 0)
    f_place = fit(d, place, BOLD, 92, head_w)
    # Eyebrow: who the page is for.
    kicker = (meta.get("borrowerType") or "").upper()
    if kicker in ("ALL", ""):
        kicker = (meta.get("city") or "SCOTTSDALE").upper()
    f_kick = font(BOLD, 27)

    y = pad + 6
    d.text((pad, y), kicker, font=f_kick, fill=(*ORANGE, 255))
    y += 46
    d.line([(pad, y), (pad + 74, y)], fill=(*ORANGE, 255), width=5)
    y += 34

    if motif:
        mark(d, motif, W - 250, int(H * 0.44), 118)
    for hline in wrap(d, place, f_place, head_w)[:2]:
        d.text((pad, y), hline, font=f_place, fill=WHITE)
        y += f_place.size + 6
    y += 16

    # Subhead: the actual subject, wrapped.
    title = meta.get("title", "")
    sub = re.sub(r"^.*?:\s*", "", title) if ":" in title else title
    sub = re.sub(r"\s*\(.*?\)\s*", " ", sub).strip()
    f_sub = font(REG, 34)
    for line in wrap(d, sub, f_sub, head_w - 20)[:2]:
        d.text((pad, y), line, font=f_sub, fill=(226, 228, 232, 255))
        y += 46

    # Footer mark. Entity signal, and it makes a screenshotted card attributable.
    f_name = font(BOLD, 30)
    f_meta = font(REG, 23)
    fy = H - pad - 44
    d.text((pad, fy), "Ricky Khamis", font=f_name, fill=WHITE)
    d.text((pad, fy + 40), "EPiQ Lending  ·  NMLS #173141  ·  Scottsdale, AZ",
           font=f_meta, fill=(198, 201, 207, 255))

    # Corner rule, tying it to the site's accent.
    d.rectangle([W - 10, 0, W, H], fill=(*ORANGE_D, 255))
    return img


def meta_from_html(page: Path) -> dict:
    """Build header fields from a rendered page.

    The site carries posts that predate the generator and have no markdown
    source. They still deserve a header, so read what the page already states
    about itself rather than leaving them on the flat gradient.
    """
    html = page.read_text(encoding="utf-8", errors="replace")
    slug = page.parent.name
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    title = re.sub(r"\s*\|.*$", "", t.group(1)).strip() if t else slug.replace("-", " ").title()
    place = "Scottsdale"
    for candidate in ("Paradise Valley", "Queen Creek", "Las Vegas", "Scottsdale",
                      "Gilbert", "Chandler", "Tempe", "Mesa", "Phoenix"):
        if re.search(rf"\b{re.escape(candidate)}\b", title, re.I):
            place = candidate
            break
    return {"slug": slug, "title": title, "city": place}


def render_page(page: Path, force: bool = False) -> str | None:
    """Generate a header for a rendered post that has no markdown source."""
    meta = meta_from_html(page)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"{meta['slug']}.jpg"
    if dest.exists() and not force:
        return f"= {dest.relative_to(ROOT)} (exists)"
    build(meta).save(dest, "JPEG", quality=86, optimize=True, progressive=True)
    return f"+ {dest.relative_to(ROOT)}  ({dest.stat().st_size / 1024:.0f} KB)"


def render(path: Path, force: bool = False) -> str | None:
    meta = front_matter(path)
    slug = meta.get("slug")
    if not slug:
        return None
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"{slug}.jpg"
    if dest.exists() and not force:
        return f"= {dest.relative_to(ROOT)} (exists)"
    build(meta).save(dest, "JPEG", quality=86, optimize=True, progressive=True)
    kb = dest.stat().st_size / 1024
    return f"+ {dest.relative_to(ROOT)}  ({kb:.0f} KB)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sources", nargs="*", type=Path)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--page",
        nargs="*",
        type=Path,
        default=[],
        help="rendered site/blog/<slug>/index.html files with no markdown source",
    )
    a = ap.parse_args()
    for page in a.page:
        line = render_page(page, a.force)
        if line:
            print(" ", line)
    srcs = sorted(POSTS.glob("*.md")) if a.all else a.sources
    if not srcs and not a.page:
        ap.error("give markdown files, --all, or --page")
    for s in srcs:
        line = render(s, a.force)
        if line:
            print(" ", line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
