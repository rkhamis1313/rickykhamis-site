#!/usr/bin/env python3
"""Render markdown posts into the mirrored rickykhamis.com static site.

This is a pure renderer: it writes no prose of its own and calls no APIs, so it
needs no credentials. The scheduled Claude task writes the markdown; this turns
it into HTML that is indistinguishable from the rest of the site.

Publishing one post touches six things, and skipping any of them leaves the
site inconsistent:

  1. site/blog/<slug>/index.html      the post itself, built from a real post
  2. the previous newest post          gains a "Newer:" link
  3. site/blog/index.html + page/N/    every index page is repaginated
  4. site/sitemap.xml                  a <url> entry, newest-first
  5. site/llms.txt                     an entry at the top of ## Articles
  6. content/series.json               the queue entry is marked published

Usage:
    python gen/new_post.py content/posts/2026-09-05-tempe.md [...more]
    python gen/new_post.py --all-unpublished
    python gen/new_post.py --check          # verify site consistency only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mdlite  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
BLOG = SITE / "blog"
POSTS_DIR = ROOT / "content" / "posts"
SERIES_FILE = ROOT / "content" / "series.json"

BASE_URL = "https://rickykhamis.com"
PER_PAGE = 12
WORDS_PER_MINUTE = 250
DEFAULT_IMAGE = "/assets/images/og-default.jpg"
TITLE_SUFFIX = " | Ricky Khamis, EPiQ Lending"
NEIGHBOUR_TITLE_CAP = 48

CARD_RE = re.compile(
    r'<div class="card post"><a href="(?P<url>/blog/[^"]+/)">'
    r'(?P<thumb>.*?)</a>'
    r'<div class="b"><div class="d">(?P<date>[^<·]+)· (?P<minutes>\d+) min read</div>'
    r'<h3><a href="[^"]*">(?P<title>.*?)</a></h3></div></div>',
    re.S,
)

# Posts with no hero image use this gradient block as their card thumbnail.
GRADIENT_THUMB = (
    '<div style="aspect-ratio:16/9;'
    'background:linear-gradient(135deg,#1b1e24,#F36B24)"></div>'
)


# --------------------------------------------------------------------------- io
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def log(message: str) -> None:
    print(message, flush=True)


# ---------------------------------------------------------------- front matter
def parse_front_matter(text: str) -> tuple[dict, str]:
    """Parse the small YAML subset the posts use: scalars and `- ` lists."""
    if not text.startswith("---"):
        raise ValueError("post is missing front matter")
    _, block, body = text.split("---", 2)

    meta: dict = {}
    key: str | None = None
    for raw in block.strip().split("\n"):
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith(("  - ", "- ")):
            if key is None:
                raise ValueError("list item before any key")
            meta.setdefault(key, []).append(line.split("- ", 1)[1].strip())
            continue
        if ":" not in line:
            raise ValueError(f"cannot parse front matter line: {line!r}")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value:
            meta[key] = value.strip('"').strip("'")
        else:
            meta[key] = []
    return meta, body.strip()


def require(meta: dict, field: str, source: Path) -> str:
    value = meta.get(field)
    if not value:
        raise ValueError(f"{source.name}: front matter is missing '{field}'")
    return value


# ------------------------------------------------------------------- utilities
def long_date(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def count_words(html_text: str) -> int:
    stripped = re.sub(r"<[^>]+>", " ", html_text)
    return len([w for w in stripped.split() if w.strip()])


def read_minutes(words: int) -> int:
    # Calibrated against the existing posts: 1042 and 1046 words render as
    # "4 min read", 387 as "1 min read", floor division, not rounding.
    return max(1, words // WORDS_PER_MINUTE)


def clip_title(title: str) -> str:
    plain = re.sub(r"<[^>]+>", "", title)
    if len(plain) <= NEIGHBOUR_TITLE_CAP:
        return plain
    return plain[:NEIGHBOUR_TITLE_CAP].rstrip() + "…"


def escape_attr(text: str) -> str:
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def escape_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ------------------------------------------------------------- existing posts
def load_post_index() -> list[dict]:
    """Read every blog index page and return posts in display order."""
    pages = [BLOG / "index.html"]
    n = 2
    while (BLOG / "page" / str(n) / "index.html").exists():
        pages.append(BLOG / "page" / str(n) / "index.html")
        n += 1

    posts: list[dict] = []
    seen: set[str] = set()
    for page in pages:
        for match in CARD_RE.finditer(read(page)):
            url = match.group("url")
            if url in seen:
                continue
            seen.add(url)
            posts.append(
                {
                    "url": url,
                    "slug": url.strip("/").split("/")[-1],
                    "thumb": match.group("thumb"),
                    "date": match.group("date").strip(),
                    "minutes": int(match.group("minutes")),
                    "title": match.group("title"),
                }
            )
    return posts


def find_template() -> Path:
    """Any existing post works, only its chrome is reused. Prefer a stable,
    structurally complete one, then fall back to whatever is present."""
    preferred = BLOG / "mortgage-rate-buydowns-scottsdale-arizona" / "index.html"
    if preferred.exists():
        return preferred
    for candidate in sorted(BLOG.glob("*/index.html")):
        if candidate.parent.name not in ("page",):
            return candidate
    raise FileNotFoundError("no existing blog post to use as a template")


# ------------------------------------------------------------------- rendering
def render_card(post: dict) -> str:
    return (
        f'<div class="card post"><a href="{post["url"]}">'
        f'{post["thumb"]}</a>'
        f'<div class="b"><div class="d">{post["date"]} · {post["minutes"]} min read</div>'
        f'<h3><a href="{post["url"]}">{post["title"]}</a></h3></div></div>'
    )


def render_pager(current: int, total_pages: int) -> str:
    parts = []
    for n in range(1, total_pages + 1):
        if n == current:
            parts.append(f"<span>{n}</span>")
        else:
            href = "/blog/" if n == 1 else f"/blog/page/{n}/"
            parts.append(f'<a href="{href}">{n}</a>')
    return '<div class="pager">' + "".join(parts) + "</div>"


def build_jsonld(document: str, meta: dict, published: date, image: str,
                 words: int) -> str:
    """Rewrite the BlogPosting node inside the page's JSON-LD @graph."""
    match = re.search(
        r'(<script type="application/ld\+json">)(.*?)(</script>)', document, re.S
    )
    if not match:
        raise ValueError("template has no JSON-LD block")

    graph = json.loads(match.group(2))
    url = f"{BASE_URL}/blog/{meta['slug']}/"
    for node in graph.get("@graph", []):
        if node.get("@type") == "BlogPosting":
            node.update(
                {
                    "headline": meta["title"],
                    "description": meta["description"],
                    "datePublished": published.isoformat(),
                    "dateModified": published.isoformat(),
                    "mainEntityOfPage": url,
                    "image": f"{BASE_URL}{image}",
                    "wordCount": words,
                }
            )
            break
    else:
        raise ValueError("template JSON-LD has no BlogPosting node")

    rebuilt = match.group(1) + json.dumps(graph, ensure_ascii=False) + match.group(3)
    return document[: match.start()] + rebuilt + document[match.end() :]


def render_post(meta: dict, body_html: str, template: str, newer: dict | None,
                older: dict | None, related: list[dict]) -> str:
    published = datetime.strptime(meta["date"], "%Y-%m-%d").date()
    image = meta.get("image") or DEFAULT_IMAGE
    words = count_words(body_html)
    minutes = read_minutes(words)
    url = f"{BASE_URL}/blog/{meta['slug']}/"
    title_attr = escape_attr(meta["title"])
    title_text = escape_text(meta["title"])
    desc_attr = escape_attr(meta["description"])

    document = template

    document = re.sub(
        r"<title>.*?</title>",
        f"<title>{title_text}{TITLE_SUFFIX}</title>",
        document,
        count=1,
        flags=re.S,
    )
    document = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{desc_attr}">',
        document,
        count=1,
    )
    document = re.sub(
        r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="{url}">',
        document,
        count=1,
    )
    document = build_jsonld(document, meta, published, image, words)
    document = re.sub(
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{title_attr}{TITLE_SUFFIX}">',
        document,
        count=1,
    )
    document = re.sub(
        r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="{desc_attr}">',
        document,
        count=1,
    )
    document = re.sub(
        r'<meta property="og:url" content="[^"]*">',
        f'<meta property="og:url" content="{url}">',
        document,
        count=1,
    )

    phero = (
        '<section class="phero"><div class="wrap">'
        '<div class="crumbs"><a href="/">Home</a> / <a href="/blog/">Blog</a> / Article</div>'
        '<span class="eyebrow">Blog</span>'
        f"<h1>{title_text}</h1>"
        f"<p>By Ricky Khamis · {long_date(published)} · {minutes} min read</p>"
        "</div></section>"
    )
    document = re.sub(
        r'<section class="phero">.*?</section>', lambda _: phero, document,
        count=1, flags=re.S,
    )

    hero_img = ""
    if meta.get("image"):
        hero_img = (
            f'<img src="{image}" alt="{title_attr}" '
            'style="border-radius:18px;margin-bottom:32px;aspect-ratio:16/9;'
            'object-fit:cover;width:100%">'
        )
    citation = (
        '<p style="margin-top:32px;font-size:.85rem;color:var(--muted)">'
        "Written by Ricky Khamis, President of EPiQ Lending, NMLS #173141, "
        f"Scottsdale, Arizona. Cite as: Khamis, R. ({published.year}). "
        f'"{title_text}." rickykhamis.com.</p>'
    )

    buttons = []
    if older:
        buttons.append(
            f'<a class="btn btn-outline btn-sm" href="{older["url"]}">'
            f'← Older: {clip_title(older["title"])}</a>'
        )
    if newer:
        buttons.append(
            f'<a class="btn btn-outline btn-sm" href="{newer["url"]}">'
            f'Newer: {clip_title(newer["title"])} →</a>'
        )
    nav = (
        f'<div class="btns" style="margin-top:40px">{"".join(buttons)}</div>'
        if buttons
        else ""
    )

    article = (
        f'<article class="prose">{hero_img}{body_html}{citation}{nav}</article>'
    )
    document = re.sub(
        r'<article class="prose">.*?</article>', lambda _: article, document,
        count=1, flags=re.S,
    )

    if related:
        grid = "".join(render_card(p) for p in related)
        document = re.sub(
            r'(<h2 style="margin-bottom:24px">Keep reading</h2><div class="grid g3">).*?(</div></div></section>)',
            lambda m: m.group(1) + grid + m.group(2),
            document,
            count=1,
            flags=re.S,
        )

    return document


# ------------------------------------------------------------ site-wide updates
def rewrite_index_pages(posts: list[dict]) -> list[Path]:
    """Repaginate every blog index page from the full ordered post list."""
    template = read(BLOG / "index.html")
    total_pages = max(1, (len(posts) + PER_PAGE - 1) // PER_PAGE)
    written: list[Path] = []

    for page_number in range(1, total_pages + 1):
        chunk = posts[(page_number - 1) * PER_PAGE : page_number * PER_PAGE]
        document = template

        cards = "".join(render_card(p) for p in chunk)
        document = re.sub(
            r'(<div class="grid g3">).*?(</div>\s*<div class="pager">.*?</div>)',
            lambda m: m.group(1) + cards + "</div>" + render_pager(page_number, total_pages),
            document,
            count=1,
            flags=re.S,
        )

        if page_number == 1:
            target = BLOG / "index.html"
            title, canonical = "Blog", f"{BASE_URL}/blog/"
        else:
            target = BLOG / "page" / str(page_number) / "index.html"
            title = f"Blog, page {page_number}"
            canonical = f"{BASE_URL}/blog/page/{page_number}/"

        document = re.sub(
            r"<title>.*?</title>", f"<title>{title}{TITLE_SUFFIX}</title>",
            document, count=1, flags=re.S,
        )
        document = re.sub(
            r'<link rel="canonical" href="[^"]*">',
            f'<link rel="canonical" href="{canonical}">', document, count=1,
        )
        document = re.sub(
            r'<meta property="og:url" content="[^"]*">',
            f'<meta property="og:url" content="{canonical}">', document, count=1,
        )

        write(target, document)
        written.append(target)

    # Drop index pages that are no longer needed.
    stale = total_pages + 1
    while (BLOG / "page" / str(stale) / "index.html").exists():
        (BLOG / "page" / str(stale) / "index.html").unlink()
        (BLOG / "page" / str(stale)).rmdir()
        stale += 1

    return written


def update_sitemap(new_posts: list[dict], today: date) -> None:
    path = SITE / "sitemap.xml"
    text = read(path)
    stamp = today.isoformat()

    # Re-rendering a post must not add a second <url> for it. Drop any existing
    # entry for these slugs first, then insert one each.
    for post in new_posts:
        text = re.sub(
            rf"^<url><loc>{re.escape(BASE_URL + post['url'])}</loc>[^\n]*\n?",
            "",
            text,
            flags=re.M,
        )

    entries = "\n".join(
        f"<url><loc>{BASE_URL}{p['url']}</loc><lastmod>{stamp}</lastmod></url>"
        for p in new_posts
    )

    # Blog posts are listed newest-first, immediately after the paginated
    # index entries. Anchor on the last /blog/page/N/ line.
    page_lines = list(
        re.finditer(r"^<url><loc>[^<]*/blog/page/\d+/</loc>[^\n]*$", text, re.M)
    )
    if not page_lines:
        raise ValueError("sitemap has no /blog/page/N/ entries to anchor on")
    at = page_lines[-1].end()
    write(path, text[:at] + "\n" + entries + text[at:])


def update_llms(new_posts: list[dict]) -> None:
    path = SITE / "llms.txt"
    text = read(path)

    # Same rule as the sitemap: one line per post, no matter how often it is
    # re-rendered.
    for post in new_posts:
        text = re.sub(
            rf"^- \[[^\]]*\]\({re.escape(BASE_URL + post['url'])}\):[^\n]*\n?",
            "",
            text,
            flags=re.M,
        )

    entries = "\n".join(
        f"- [{p['title']}]({BASE_URL}{p['url']}): {p['description']}"
        for p in new_posts
    )
    marker = "## Articles\n"
    if marker not in text:
        raise ValueError("llms.txt has no '## Articles' section")
    at = text.index(marker) + len(marker)
    write(path, text[:at] + entries + "\n" + text[at:])


def add_newer_link(post: dict, newer: dict) -> None:
    """Give the previously-newest post a forward link to the new one."""
    path = BLOG / post["slug"] / "index.html"
    if not path.exists():
        log(f"  ! {path} missing; skipping its Newer link")
        return
    text = read(path)
    link = (
        f'<a class="btn btn-outline btn-sm" href="{newer["url"]}">'
        f'Newer: {clip_title(newer["title"])} →</a>'
    )
    if 'Newer:' in text:
        text = re.sub(
            r'<a class="btn btn-outline btn-sm" href="[^"]*">Newer:.*?</a>',
            lambda _: link, text, count=1, flags=re.S,
        )
    elif '<div class="btns" style="margin-top:40px">' in text:
        text = text.replace("</div></article>", f"{link}</div></article>", 1)
    else:
        text = text.replace(
            "</article>",
            f'<div class="btns" style="margin-top:40px">{link}</div></article>',
            1,
        )
    write(path, text)


def mark_published(meta: dict) -> None:
    """Move this post's queue entry into `published`, matching on slug."""
    if not SERIES_FILE.exists():
        return
    data = json.loads(read(SERIES_FILE))
    queue = data.get("queue", [])

    published = data.setdefault("published", [])
    if any(p.get("slug") == meta["slug"] for p in published):
        # Already recorded; a re-render is not a second publication.
        data["queue"] = [q for q in queue if q.get("slug") != meta["slug"]]
        write(SERIES_FILE, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        return

    match = next((q for q in queue if q.get("slug") == meta["slug"]), None)
    if match is None:
        # Published outside the queue (a one-off). Still record it so the
        # review step sees the full history.
        published.append(
            {
                "city": meta.get("city"),
                "series": meta.get("series"),
                "slug": meta["slug"],
                "date": meta["date"],
                "offQueue": True,
            }
        )
    else:
        data["queue"] = [q for q in queue if q is not match]
        published.append(
            {
                "city": match.get("city"),
                "series": match.get("series"),
                "question": match.get("question"),
                "slug": meta["slug"],
                "date": meta["date"],
            }
        )
    write(SERIES_FILE, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------------ check
def check() -> int:
    posts = load_post_index()
    problems: list[str] = []

    for post in posts:
        if not (BLOG / post["slug"] / "index.html").exists():
            problems.append(f"index lists {post['url']} but the page is missing")

    seen: dict[str, int] = {}
    for page in [BLOG / "index.html"] + sorted(BLOG.glob("page/*/index.html")):
        for match in CARD_RE.finditer(read(page)):
            url = match.group("url")
            seen[url] = seen.get(url, 0) + 1
    for url, count in sorted(seen.items()):
        if count > 1:
            problems.append(f"{url} is listed {count} times across the index pages")

    on_disk = {
        p.parent.name
        for p in BLOG.glob("*/index.html")
        if p.parent.name != "page"
    }
    listed = {p["slug"] for p in posts}
    for slug in sorted(on_disk - listed):
        problems.append(f"site/blog/{slug}/ exists but no index page links to it")

    sitemap = read(SITE / "sitemap.xml")
    locs = re.findall(r"<loc>([^<]*)</loc>", sitemap)
    for loc in sorted({l for l in locs if locs.count(l) > 1}):
        problems.append(f"{loc} appears {locs.count(loc)} times in sitemap.xml")
    for post in posts:
        if f"{BASE_URL}{post['url']}" not in sitemap:
            problems.append(f"{post['url']} is missing from sitemap.xml")

    llms = read(SITE / "llms.txt")
    links = re.findall(r"^- \[[^\]]*\]\(([^)]*)\):", llms, re.M)
    for link in sorted({l for l in links if links.count(l) > 1}):
        problems.append(f"{link} appears {links.count(link)} times in llms.txt")
    for post in posts:
        if f"{BASE_URL}{post['url']}" not in llms:
            problems.append(f"{post['url']} is missing from llms.txt")

    log(f"Checked {len(posts)} posts.")
    for problem in problems:
        log(f"  FAIL {problem}")
    if not problems:
        log("  All consistent.")
    return 1 if problems else 0


# ------------------------------------------------------------------------- main
def publish(paths: list[Path], force: bool = False) -> None:
    sources = sorted(paths, key=lambda p: p.name)
    existing = load_post_index()
    template = read(find_template())
    log(f"{len(existing)} posts already published.")

    rendered: list[dict] = []
    for source in sources:
        meta, body = parse_front_matter(read(source))
        for field in ("title", "slug", "description", "date"):
            require(meta, field, source)

        if (BLOG / meta["slug"] / "index.html").exists() and not force:
            log(f"  = {meta['slug']} already published; skipping "
                "(use --force to re-render after an edit)")
            continue

        body_html = mdlite.convert(body)
        published_on = datetime.strptime(meta["date"], "%Y-%m-%d").date()
        words = count_words(body_html)

        entry = {
            "url": f"/blog/{meta['slug']}/",
            "slug": meta["slug"],
            "thumb": (
                f'<img src="{meta["image"]}" alt="" loading="lazy">'
                if meta.get("image")
                else GRADIENT_THUMB
            ),
            "date": long_date(published_on),
            "minutes": read_minutes(words),
            "title": escape_text(meta["title"]),
            "description": meta["description"],
            "meta": meta,
            "body_html": body_html,
        }
        rendered.append(entry)

    if not rendered:
        log("Nothing new to publish.")
        return

    # Newest first: the last source in the batch ends up at the top.
    rendered.reverse()

    # An index page may already list a post whose directory was removed (for
    # example when re-rendering after an edit). Drop those stale entries so the
    # freshly rendered one is the only card for that slug.
    fresh = {entry["slug"] for entry in rendered}
    ordered = rendered + [p for p in existing if p["slug"] not in fresh]

    # The post that gains a forward link is the newest one we are NOT
    # re-rendering. Taking existing[0] blindly gave the newest post on the site
    # a "Newer" link pointing back at an older post whenever that post was
    # itself part of the batch, which is exactly what a --force correction does.
    previous_newest = next((p for p in existing if p["slug"] not in fresh), None)

    for position, entry in enumerate(rendered):
        newer = ordered[position - 1] if position > 0 else None
        older = ordered[position + 1] if position + 1 < len(ordered) else None
        related = [p for p in ordered if p["slug"] != entry["slug"]][:3]
        document = render_post(
            entry["meta"], entry["body_html"], template, newer, older, related
        )
        target = BLOG / entry["slug"] / "index.html"
        write(target, document)
        log(f"  + {target.relative_to(ROOT)}  ({entry['minutes']} min read)")

    if previous_newest:
        add_newer_link(previous_newest, ordered[len(rendered) - 1])
        log(f"  ~ linked {previous_newest['slug']} forward")

    pages = rewrite_index_pages(ordered)
    log(f"  ~ repaginated {len(pages)} index page(s) for {len(ordered)} posts")

    update_sitemap(rendered, date.today())
    log("  ~ sitemap.xml")

    update_llms(rendered)
    log("  ~ llms.txt")

    for entry in rendered:
        mark_published(entry["meta"])
    log("  ~ series.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="*", type=Path)
    parser.add_argument(
        "--all-unpublished",
        action="store_true",
        help="publish every markdown post in content/posts/ that is not live yet",
    )
    parser.add_argument(
        "--check", action="store_true", help="verify site consistency and exit"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-render posts whose pages already exist. Needed to push a "
        "correction: editing the markdown alone does not touch the rendered "
        "HTML, so a factual fix would otherwise never reach the site.",
    )
    args = parser.parse_args()

    if args.check:
        return check()

    sources = list(args.sources)
    if args.all_unpublished:
        sources = sorted(POSTS_DIR.glob("*.md"))
    if not sources:
        parser.error("give one or more markdown files, or --all-unpublished")

    publish(sources, force=args.force)
    return check()


if __name__ == "__main__":
    sys.exit(main())
