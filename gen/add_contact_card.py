#!/usr/bin/env python3
"""Add the Save My Contact link to the nav on every page, and the card block
to the homepage.

The site is a static mirror with the nav baked into all 176 HTML files, so this
edits them in place. Idempotent on purpose: it checks for the marker class
before inserting, so running it after every publish is safe and re-running it
never produces two links.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

MARK = "js-save-contact"

NAV_LINK = (
    f'<li><a class="{MARK}" href="/assets/ricky-khamis.vcf" download="Ricky-Khamis.vcf">'
    "Save My Contact</a></li>"
)

CARD = f"""
<section class="sec" id="save-contact">
  <div class="wrap">
    <div class="card" style="padding:32px;display:flex;gap:32px;flex-wrap:wrap;align-items:center">
      <div style="flex:1 1 320px;min-width:280px">
        <span class="eyebrow">Contact</span>
        <h2 style="margin:.3rem 0 .6rem">Save my contact card</h2>
        <p style="margin:0 0 20px;color:var(--muted)">
          One tap puts my name, direct line, email, office and NMLS straight
          into your phone. No form, no signup. Scan the code instead if you are
          reading this on a computer.
        </p>
        <a class="btn btn-primary {MARK}" href="/assets/ricky-khamis.vcf"
           download="Ricky-Khamis.vcf"
           style="display:inline-flex;align-items:center;gap:10px">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2.5" stroke-linecap="round"
               stroke-linejoin="round" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Download My Contact Card
        </a>
        <p style="margin:14px 0 0;font-size:.85rem;color:var(--muted)">
          Ricky Khamis · President, EPiQ Lending · NMLS #173141 ·
          <a href="tel:+14809999842">(480) 999-9842</a>
        </p>
      </div>
      <div style="flex:0 0 auto;text-align:center">
        <img src="/assets/images/contact-qr.png" alt="QR code to save Ricky Khamis contact card"
             width="180" height="180"
             style="border-radius:12px;background:#fff;padding:10px;display:block">
        <p style="margin:10px 0 0;font-size:.8rem;color:var(--muted)">Scan to save</p>
      </div>
    </div>
  </div>
</section>
"""


def add_nav_link() -> int:
    """Insert the link as the last nav item, on every page that has a nav."""
    changed = 0
    for page in SITE.rglob("*.html"):
        html = page.read_text(encoding="utf-8", errors="replace")
        if MARK in html or "</ul></nav>" not in html:
            continue
        page.write_text(html.replace("</ul></nav>", NAV_LINK + "</ul></nav>", 1),
                        encoding="utf-8")
        changed += 1
    return changed


def add_homepage_card() -> bool:
    home = SITE / "index.html"
    html = home.read_text(encoding="utf-8")
    if 'id="save-contact"' in html:
        return False
    # Sit it just above the footer so it is the last thing before contact info.
    marker = "<footer"
    i = html.rfind(marker)
    if i == -1:
        return False
    home.write_text(html[:i] + CARD + html[i:], encoding="utf-8")
    return True


if __name__ == "__main__":
    n = add_nav_link()
    print(f"  nav link added to {n} page(s)")
    print(f"  homepage card: {'added' if add_homepage_card() else 'already present'}")
