#!/usr/bin/env python3
"""Mirror the live rickykhamis.com into site/ for Netlify to publish.

This runs in GitHub Actions, which can reach rickykhamis.com. It:

  1. reads /sitemap.xml (following sitemap-index files),
  2. downloads every page listed there,
  3. scrapes same-origin asset references out of those pages and out of every
     stylesheet it mirrors (repeating until no new assets turn up, so fonts and
     images referenced from inside CSS are picked up too),
  4. writes everything under site/ in Netlify's clean-URL layout.

Pages are mirrored byte-for-byte. URLs are deliberately not rewritten: the
mirror is served from the same origin it was copied from, so absolute links
keep resolving to the right place.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SITE = "https://rickykhamis.com"
ORIGIN = urllib.parse.urlsplit(SITE).netloc
OUT = Path("site")

USER_AGENT = "rickykhamis-site-mirror/1.0 (+https://rickykhamis.com)"
WORKERS = 8
RETRIES = 3
TIMEOUT = 45

# Fetched even when the sitemap does not list them.
EXTRA_PATHS = ["/sitemap.xml", "/robots.txt", "/llms.txt", "/favicon.ico", "/404.html"]

# Same-origin files worth mirroring wherever they live in the URL space.
ASSET_SUFFIXES = {
    ".css", ".js", ".mjs",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico",
    ".mp4", ".webm", ".mp3", ".pdf", ".json", ".txt", ".xml",
}

ATTR_RE = re.compile(
    r"""(?:href|src|poster|content|data-src)\s*=\s*["']([^"']+)["']""", re.I
)
SRCSET_RE = re.compile(r"""srcset\s*=\s*["']([^"']+)["']""", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""", re.I)


def log(msg: str) -> None:
    print(msg, flush=True)


def fetch(url: str) -> tuple[bytes, str]:
    """GET a URL, returning (body, content_type). Retries transient failures."""
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                body = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return body, response.headers.get_content_type()
        except urllib.error.HTTPError as error:
            # 4xx will not fix itself; stop early.
            if 400 <= error.code < 500:
                raise
            last_error = error
        except Exception as error:  # noqa: BLE001 - network is best-effort
            last_error = error
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{url}: {last_error}")


def absolutize(url: str, base: str) -> str:
    joined = urllib.parse.urljoin(base, url.strip())
    return urllib.parse.urldefrag(joined)[0]


def same_origin(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    return parts.scheme in ("http", "https") and parts.netloc == ORIGIN


def local_path(url: str) -> Path:
    """Map a URL onto its file inside site/, using Netlify's clean-URL layout."""
    path = urllib.parse.urlsplit(url).path
    if path in ("", "/"):
        return OUT / "index.html"
    relative = path.lstrip("/")
    if path.endswith("/"):
        return OUT / relative / "index.html"
    if Path(relative).suffix:
        return OUT / relative
    # Extensionless page URL: /foo -> site/foo/index.html, which Netlify serves at /foo.
    return OUT / relative / "index.html"


def read_sitemap(url: str, seen: set[str]) -> list[str]:
    """Return every page URL in a sitemap, recursing through sitemap indexes."""
    if url in seen:
        return []
    seen.add(url)

    body, _ = fetch(url)
    if url.endswith(".gz"):
        body = gzip.decompress(body)

    root = ET.fromstring(body)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    nested = [
        element.text.strip()
        for element in root.findall(".//sm:sitemap/sm:loc", namespace)
        if element.text
    ]
    if nested:
        pages: list[str] = []
        for child in nested:
            log(f"  sitemap index -> {child}")
            pages.extend(read_sitemap(child, seen))
        return pages

    return [
        element.text.strip()
        for element in root.findall(".//sm:url/sm:loc", namespace)
        if element.text
    ]


def candidate_links(text: str, base: str) -> set[str]:
    """Pull every same-origin URL reference out of an HTML or CSS document."""
    found: set[str] = set()

    for match in ATTR_RE.findall(text):
        found.add(match)
    for match in CSS_URL_RE.findall(text):
        found.add(match)
    for srcset in SRCSET_RE.findall(text):
        for entry in srcset.split(","):
            candidate = entry.strip().split()
            if candidate:
                found.add(candidate[0])

    resolved: set[str] = set()
    for raw in found:
        if not raw or raw.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = absolutize(raw, base)
        if same_origin(absolute):
            resolved.add(absolute)
    return resolved


def is_asset(url: str) -> bool:
    path = urllib.parse.urlsplit(url).path
    if path.startswith("/assets/"):
        return True
    return Path(path).suffix.lower() in ASSET_SUFFIXES


def write(url: str, body: bytes) -> Path:
    target = local_path(url)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return target


def download_all(urls: list[str], label: str) -> dict[str, str]:
    """Download URLs in parallel. Returns {url: text} for text-ish responses."""
    text_bodies: dict[str, str] = {}
    failures: list[str] = []

    def task(url: str) -> tuple[str, bytes, str] | None:
        try:
            body, content_type = fetch(url)
            return url, body, content_type
        except Exception as error:  # noqa: BLE001
            log(f"  !! {url}: {error}")
            failures.append(url)
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for result in pool.map(task, urls):
            if result is None:
                continue
            url, body, content_type = result
            target = write(url, body)
            log(f"  {url} -> {target}")
            if content_type.startswith("text/") or content_type in (
                "application/javascript",
                "application/xml",
                "image/svg+xml",
            ):
                text_bodies[url] = body.decode("utf-8", errors="replace")

    log(f"{label}: {len(urls) - len(failures)} ok, {len(failures)} failed")
    if failures:
        log("failed: " + ", ".join(failures))
    return text_bodies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expect-min",
        type=int,
        default=100,
        help="fail if the sitemap yields fewer pages than this (guards against "
        "committing a truncated mirror over a good one)",
    )
    args = parser.parse_args()

    log(f"Reading {SITE}/sitemap.xml")
    pages = read_sitemap(f"{SITE}/sitemap.xml", set())
    pages = sorted({p for p in pages if same_origin(p)})
    log(f"Sitemap lists {len(pages)} pages")

    if len(pages) < args.expect_min:
        log(
            f"ERROR: only {len(pages)} pages found, expected at least "
            f"{args.expect_min}. Refusing to overwrite the mirror."
        )
        return 1

    log("\n== Pages ==")
    page_text = download_all(pages, "pages")

    log("\n== Extra top-level files ==")
    extras = [urllib.parse.urljoin(SITE, path) for path in EXTRA_PATHS]
    extra_text = download_all(extras, "extras")

    # Assets referenced by the pages, then assets referenced by those assets
    # (fonts and images reached from inside CSS), until nothing new appears.
    discovered: set[str] = set()
    for url, text in {**page_text, **extra_text}.items():
        discovered |= {link for link in candidate_links(text, url) if is_asset(link)}

    fetched: set[str] = set()
    round_number = 1
    while discovered:
        pending = sorted(discovered - fetched)
        if not pending:
            break
        log(f"\n== Assets, round {round_number} ({len(pending)}) ==")
        asset_text = download_all(pending, f"assets round {round_number}")
        fetched |= set(pending)

        next_round: set[str] = set()
        for url, text in asset_text.items():
            next_round |= {
                link for link in candidate_links(text, url) if is_asset(link)
            }
        discovered = next_round - fetched
        round_number += 1

    total = sum(1 for _ in OUT.rglob("*") if _.is_file())
    log(f"\nMirror complete: {total} files under {OUT}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
