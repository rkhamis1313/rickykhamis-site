#!/usr/bin/env python3
"""Build /reviews/ from content/reviews.json.

The page Ricky supplied was a self-contained document with its own fonts,
its own colour system and its own header. Dropped in as-is it would have
read as a different website that happens to share a domain, so the content
is rebuilt here in the site's own components: the same dark page hero the
hubs and blog use, the same .quote cards the old reviews page used, the same
buttons and bands.

All 206 reviews are written into the HTML rather than injected by script.
A reviews page whose reviews exist only in a JavaScript array is a reviews
page search engines cannot read, and it breaks entirely for anyone whose
script fails. Filtering and paging are layered on top: without JavaScript
every review is simply visible.

Usage:  python gen/build_reviews.py
"""

from __future__ import annotations

import html
import io
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DATA = ROOT / "content" / "reviews.json"
TARGET = SITE / "reviews" / "index.html"
TEMPLATE = SITE / "blog" / "mortgage-rate-buydowns-scottsdale-arizona" / "index.html"
BASE = "https://rickykhamis.com"

# Shown before the reader has to ask for more. Three rows of the g3 grid.
PAGE = 18

TITLE = "Client Reviews | Ricky Khamis, EPiQ Lending"
DESC = ("206 five-star reviews from clients and Realtor partners of Ricky Khamis, "
        "Certified Mortgage Planner and President of EPiQ Lending. Search them by "
        "situation, or read the files other lenders turned down first.")

FILTERS = [
    ("all", "All reviews"),
    ("first", "First-time buyers"),
    ("refi", "Refinance"),
    ("rescue", "Rescued deals"),
    ("realtor", "From Realtors"),
    ("investor", "Investors"),
]

RESCUES = [
    ("A big online lender said approved for $1.3M. Then, after inspection and appraisal, said no.",
     "He had to work some serious magic with these clients and their crazy finances to make it "
     "happen but he never gave up and fought till the end. My clients were able to close on their "
     "dream home at $1.25mm.",
     "Shaun Marion, Realtor"),
    ("The first lender tapped out 14 days before close of escrow.",
     "He even took a loan over from an incompetent lender, that tapped out 14 days before close of "
     "escrow, and closed the loan two days early!",
     "Marc Slavin, Realtor"),
    ("Five weeks into contract, the lender said it could not get the loan done.",
     "My wife and I came to Mr. Khamis in a complete panic. We are first time home buyers, and had "
     "no idea what we were doing.",
     "Donald Skinner, first-time buyer"),
    ("Turned down by a few lenders. On the verge of giving up.",
     "He kept me informed of what was happening in the process and was always honest and up front. "
     "He did exactly what he said he was going to do.",
     "Albert Smith, client"),
]

STATS = [
    ("Top 1%", "of loan officers nationally for funded loans"),
    ("206", "five-star client reviews"),
    ("82nd Airborne", "veteran, U.S. Army"),
    ("Since 1999", "originating mortgages"),
]

BIO = [
    "Ricky Khamis has been in the mortgage business since 1999. As President of EPiQ Lending he "
    "leads a team of loan officers and still originates loans himself.",
    "His edge is making complicated things simple. Rates, bond markets, loan structure, credit, "
    "down payment strategy. He breaks it down so clients, Realtors and loan officers can make "
    "confident decisions and move.",
    "He is also a real estate investor, across long-term rentals, short-term rentals, commercial "
    "and flips, and has helped hundreds of investors buy single-family rentals, luxury short-term "
    "rentals and small apartment buildings.",
    "Before mortgages he served in the U.S. Army as an infantryman with the 3-505th, 82nd Airborne "
    "Division at Fort Bragg. He earned the Army Achievement Medal and four Army Commendation "
    "Medals, and was named Soldier of the Month. He runs his business the same way: disciplined, "
    "prepared, and accountable for the outcome.",
]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def review_card(r: dict) -> str:
    """One review, fully visible.

    Nothing is hidden or clamped in the markup. The script does the hiding
    after it loads, so what ships is a complete, readable list.
    """
    tags = " ".join(r.get("g") or [])
    text = esc(r["t"].strip())
    name = esc(r["n"].strip())
    long_cls = " rk-long" if len(r["t"]) > 320 else ""
    return (
        f'<figure class="quote rk-review{long_cls}" data-tags="{tags}">'
        f'<div class="stars" aria-label="5 out of 5 stars">★★★★★</div>'
        f'<blockquote class="rk-text"><p>{text}</p></blockquote>'
        f'<figcaption class="who">{name}</figcaption>'
        f'</figure>'
    )


def build_main(reviews: list[dict]) -> str:
    counts = {"all": len(reviews)}
    for r in reviews:
        for t in r.get("g") or []:
            counts[t] = counts.get(t, 0) + 1

    chips = "".join(
        f'<button type="button" class="rk-chip{" is-on" if key == "all" else ""}" '
        f'data-filter="{key}"{" aria-pressed=true" if key == "all" else " aria-pressed=false"}>'
        f'{esc(label)} <span class="rk-n">{counts.get(key, 0)}</span></button>'
        for key, label in FILTERS
        if counts.get(key)
    )

    rescue_cards = "".join(
        f'<article class="card rk-rescue">'
        f'<h3>{esc(head)}</h3>'
        f'<p>&ldquo;{esc(body)}&rdquo;</p>'
        f'<div class="rk-src">{esc(who)}</div>'
        f'</article>'
        for head, body, who in RESCUES
    )

    stat_items = "".join(
        f'<div class="rk-stat"><strong>{esc(big)}</strong><span>{esc(small)}</span></div>'
        for big, small in STATS
    )

    cards = "".join(review_card(r) for r in reviews)
    bio = "".join(f"<p>{esc(p)}</p>" for p in BIO)

    return f"""<main id="main">

<section class="phero rk-hero">
<div class="wrap">
<div class="crumbs"><a href="/">Home</a> / Reviews</div>
<div class="rk-hero-grid">
<div>
<span class="eyebrow">Certified Mortgage Planner</span>
<h1>Ricky Khamis</h1>
<p>President of EPiQ Lending. In the mortgage business since 1999. NMLS #173141.</p>
<blockquote class="rk-pull">
<p>&ldquo;When all the other lenders said no, Ricky Khamis said &lsquo;we can do this!&rsquo;&rdquo;</p>
<cite>Albert Smith, client</cite>
</blockquote>
<div class="btns">
<a class="btn btn-primary" href="tel:+16027587425">Call Ricky</a>
<a class="btn btn-ghost" href="#reviews">Read 206 reviews</a>
</div>
</div>
<img class="rk-portrait" src="/assets/images/ricky-portrait.webp" width="1024" height="1536"
 alt="Ricky Khamis, Certified Mortgage Planner and President of EPiQ Lending" loading="eager">
</div>
</div>
</section>

<section class="rk-statbar"><div class="wrap"><div class="rk-stats">{stat_items}</div></div></section>

<section class="section">
<div class="wrap">
<span class="eyebrow">Rescued files</span>
<h2>When the deal was in trouble</h2>
<p class="rk-lede">Other lenders backed out, ran out of time, or said no. These are the files that
landed on Ricky&rsquo;s desk next.</p>
<div class="grid g2 rk-rescues">{rescue_cards}</div>
</div>
</section>

<section class="section soft" id="reviews">
<div class="wrap">
<span class="eyebrow">In their words</span>
<h2>What clients say</h2>
<p class="rk-lede">Every review below is from a real client or Realtor partner. Search for your
situation, or filter by the kind of loan you are working on.</p>

<div class="rk-tools">
<label class="rk-search">
<span class="sr-only">Search reviews</span>
<input type="search" id="rk-q" placeholder="Search reviews (try: refinance)" autocomplete="off">
</label>
<div class="rk-chips" role="group" aria-label="Filter reviews">{chips}</div>
</div>

<p class="rk-count" id="rk-count" aria-live="polite">Showing all {len(reviews)} reviews</p>
<div class="grid g3 rk-grid" id="rk-grid">{cards}</div>
<p class="rk-none" id="rk-none" hidden>No reviews match that search. Try a different word.</p>
<div class="rk-more"><button type="button" class="btn btn-outline" id="rk-more">Show more reviews</button></div>
</div>
</section>

<section class="section">
<div class="wrap two rk-bio">
<div class="prose">
<span class="eyebrow">More than a mortgage</span>
<h2>Who you are actually working with</h2>
{bio}
<p><a class="btn btn-outline btn-sm" href="/about/">The longer version</a></p>
</div>
<div class="aside">
<img class="rk-bio-img" src="/assets/images/ricky-portrait-crop.webp" width="716" height="1024"
 alt="Ricky Khamis" loading="lazy">
</div>
</div>
</section>

<section class="section dark rk-contact">
<div class="wrap">
<span class="eyebrow">Let&rsquo;s run your numbers</span>
<h2>Buying, refinancing, or investing</h2>
<p class="rk-lede">Call or text and you will get a straight answer on what is possible.</p>
<div class="grid g3 rk-lines">
<div><span>Direct line</span><a href="tel:+16027587425">(602) 758-7425</a></div>
<div><span>Team line</span><a href="tel:+14809999842">(480) 999-9842</a></div>
<div><span>Email</span><a href="mailto:ricky.khamis@epiqlending.com">ricky.khamis@epiqlending.com</a></div>
</div>
<div class="btns">
<a class="btn btn-primary" href="/assets/ricky-khamis.vcf" download="Ricky-Khamis.vcf">Save my contact</a>
<a class="btn btn-ghost" href="sms:+16027587425">Text Ricky</a>
<a class="btn btn-ghost" href="/book-appointment/">Book a call</a>
</div>
<p class="rk-fine">Reviews reflect individual client experiences with Ricky Khamis, including at
prior companies, and do not guarantee a specific outcome. This is not a commitment to lend. All
loans are subject to credit approval. Equal Housing Opportunity.</p>
</div>
</section>

</main>"""


SCRIPT = """
<script>
/* Search, filter and paging for the review archive.
   Every review is already in the HTML. This only hides and shows, so a
   reader without JavaScript sees all of them rather than none. */
(function () {
  var grid = document.getElementById('rk-grid');
  if (!grid) return;
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.rk-review'));
  var q = document.getElementById('rk-q');
  var more = document.getElementById('rk-more');
  var count = document.getElementById('rk-count');
  var none = document.getElementById('rk-none');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.rk-chip'));
  var PAGE = %(page)d, shown = PAGE, filter = 'all', term = '';

  grid.classList.add('is-enhanced');
  cards.forEach(function (c) { c.dataset.text = c.textContent.toLowerCase(); });

  function matches(c) {
    if (filter !== 'all' && (' ' + c.dataset.tags + ' ').indexOf(' ' + filter + ' ') < 0) return false;
    if (term && c.dataset.text.indexOf(term) < 0) return false;
    return true;
  }

  function render() {
    var hits = 0, visible = 0;
    cards.forEach(function (c) {
      if (!matches(c)) { c.hidden = true; return; }
      hits++;
      var show = visible < shown;
      c.hidden = !show;
      if (show) visible++;
    });
    none.hidden = hits !== 0;
    more.hidden = hits <= visible;
    count.textContent = hits === 0 ? 'No reviews match'
      : (visible >= hits ? 'Showing all ' + hits + (hits === 1 ? ' review' : ' reviews')
                         : 'Showing ' + visible + ' of ' + hits + ' reviews');
  }

  chips.forEach(function (b) {
    b.addEventListener('click', function () {
      chips.forEach(function (o) { o.classList.remove('is-on'); o.setAttribute('aria-pressed', 'false'); });
      b.classList.add('is-on'); b.setAttribute('aria-pressed', 'true');
      filter = b.dataset.filter; shown = PAGE; render();
    });
  });

  var timer;
  q.addEventListener('input', function (e) {
    clearTimeout(timer);
    var v = e.target.value.trim().toLowerCase();
    timer = setTimeout(function () { term = v; shown = PAGE; render(); }, 120);
  });

  more.addEventListener('click', function () { shown += PAGE; render(); });

  /* Long reviews are clamped. Give each one its own toggle. */
  grid.querySelectorAll('.rk-long').forEach(function (c) {
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'rk-toggle'; b.textContent = 'Read more';
    b.setAttribute('aria-expanded', 'false');
    b.addEventListener('click', function () {
      var open = c.classList.toggle('is-open');
      b.textContent = open ? 'Read less' : 'Read more';
      b.setAttribute('aria-expanded', String(open));
    });
    c.querySelector('.rk-text').insertAdjacentElement('afterend', b);
  });

  render();
})();
</script>
""" % {"page": PAGE}


def build() -> Path:
    reviews = json.loads(io.open(DATA, encoding="utf-8").read())
    doc = io.open(TEMPLATE, encoding="utf-8").read()
    url = f"{BASE}/reviews/"

    doc = re.sub(r"<title>.*?</title>", f"<title>{esc(TITLE)}</title>", doc, count=1, flags=re.S)
    doc = re.sub(r'<meta name="description" content="[^"]*">',
                 f'<meta name="description" content="{esc(DESC)}">', doc, count=1)
    doc = re.sub(r'<link rel="canonical" href="[^"]*">',
                 f'<link rel="canonical" href="{url}">', doc, count=1)
    for prop, val in (("og:title", TITLE), ("og:description", DESC), ("og:url", url),
                      ("twitter:title", TITLE), ("twitter:description", DESC)):
        attr = "property" if prop.startswith("og:") else "name"
        doc = re.sub(rf'(<meta {attr}="{prop}" content=")[^"]*(">)',
                     lambda m: m.group(1) + esc(val) + m.group(2), doc)

    # Structured data: describe the page, not an aggregate rating. Review and
    # rating markup a business collects about itself is self-serving and is not
    # eligible for rich results, so claiming it here would be noise at best.
    def swap_jsonld(m):
        data = json.loads(m.group(1))
        graph = [n for n in data.get("@graph", [])
                 if n.get("@type") not in ("BlogPosting", "Article", "NewsArticle")]
        graph.append({
            "@type": "ProfilePage",
            "@id": url,
            "url": url,
            "name": TITLE,
            "description": DESC,
            "isPartOf": {"@id": f"{BASE}/#website"},
            "about": {"@id": f"{BASE}/#ricky"},
            "primaryImageOfPage": f"{BASE}/assets/images/ricky-portrait.webp",
        })
        data["@graph"] = graph
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"

    doc, n = re.subn(r'<script type="application/ld\+json">(.*?)</script>',
                     swap_jsonld, doc, count=1, flags=re.S)
    if n != 1:
        raise ValueError("json-ld block not found in template")

    doc, n = re.subn(r"<main id=\"main\">.*?</main>", lambda _: build_main(reviews),
                     doc, count=1, flags=re.S)
    if n != 1:
        raise ValueError("<main> block not found in template")

    doc = doc.replace("</body>", SCRIPT + "</body>", 1)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    io.open(TARGET, "w", encoding="utf-8").write(doc)
    print(f"  /reviews/  {len(reviews)} reviews  {len(doc)//1024} KB")
    return TARGET


def touch_sitemap() -> None:
    """Keep /reviews/ in the sitemap and stamp it with today's date."""
    path = SITE / "sitemap.xml"
    xml = io.open(path, encoding="utf-8").read()
    loc = f"{BASE}/reviews/"
    today = date.today().isoformat()
    entry = f"<url><loc>{loc}</loc><lastmod>{today}</lastmod></url>"
    pattern = re.compile(rf"<url><loc>{re.escape(loc)}</loc><lastmod>[^<]*</lastmod></url>")
    if pattern.search(xml):
        xml = pattern.sub(entry, xml)
    else:
        xml = xml.replace("</urlset>", entry + "\n</urlset>")
    io.open(path, "w", encoding="utf-8").write(xml)
    print("  sitemap.xml stamped")


def update_llms(count: int) -> None:
    """One line under its own heading, above the long article list."""
    path = SITE / "llms.txt"
    txt = io.open(path, encoding="utf-8").read()
    block = (
        "\n## Reviews\n\n"
        f"- [Client reviews]({BASE}/reviews/): {count} five-star reviews from clients and Realtor "
        "partners of Ricky Khamis, searchable and filterable by situation (first-time buyers, "
        "refinance, rescued deals, Realtor partners, investors), alongside four files other "
        "lenders declined or abandoned before he closed them.\n"
    )
    txt = re.sub(r"\n## Reviews\n.*?(?=\n## )", "", txt, flags=re.S)
    anchor = "\n## Topic guides" if "## Topic guides" in txt else "\n## Articles"
    txt = txt.replace(anchor, block + anchor, 1)
    io.open(path, "w", encoding="utf-8").write(txt)
    print("  llms.txt updated")


if __name__ == "__main__":
    build()
    touch_sitemap()
    update_llms(len(json.loads(io.open(DATA, encoding="utf-8").read())))
