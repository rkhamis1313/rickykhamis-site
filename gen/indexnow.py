#!/usr/bin/env python3
"""Tell Bing about new or changed pages the moment they are live.

Search engines find new pages by crawling, on their own schedule. IndexNow
inverts that: the site pings a shared endpoint with a list of URLs and the
participating engines fetch them instead of waiting to stumble across them.
Bing, Yandex, Seznam and Naver all consume the same feed, and a single
submission reaches all of them. Google does not participate.

That matters here more than it usually would. Bing's index is what Copilot
answers from, and what ChatGPT's search uses, so getting into Bing quickly is
the difference between an article existing and an article being quotable.

Authentication is a public key. A file named <key>.txt sits at the site root
containing exactly that key, which proves whoever is submitting controls the
domain. There is no secret to store and nothing to rotate on a schedule, which
is why this needs no repository secret and cannot leak anything.

This never fails a publish. A search engine being unreachable is not a reason
to break the site's deploy, so network problems are logged and the run still
exits 0. Pass --strict when running by hand and you want the real exit code.

Usage:
    python gen/indexnow.py                 # everything stamped with today's date
    python gen/indexnow.py --date 2026-09-26
    python gen/indexnow.py --all           # every URL in the sitemap
    python gen/indexnow.py --url https://rickykhamis.com/reviews/
    python gen/indexnow.py --dry-run       # show the payload, send nothing
    python gen/indexnow.py --selftest      # offline checks, exits non-zero on failure
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SITEMAP = SITE / "sitemap.xml"
HOST = "rickykhamis.com"
BASE = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

# The spec allows 8 to 128 characters from a-z, A-Z, 0-9 and dashes.
KEY_RE = re.compile(r"^[A-Za-z0-9-]{8,128}$")
# One request carries at most ten thousand URLs.
BATCH = 10_000
TIMEOUT = 30


def log(msg: str) -> None:
    print(msg, flush=True)


def find_key() -> tuple[str, str]:
    """Return (key, keyLocation), discovered from the key file on disk.

    Looked up rather than hardcoded so rotating the key is one file swap. A
    valid key file is named <key>.txt and contains exactly that key, which is
    also the test the search engine itself performs.
    """
    candidates = []
    for path in sorted(SITE.glob("*.txt")):
        stem = path.stem
        if not KEY_RE.match(stem):
            continue
        if path.read_text(encoding="utf-8").strip() == stem:
            candidates.append(stem)
    if not candidates:
        raise SystemExit(
            "IndexNow: no key file found. Expected site/<key>.txt containing "
            "exactly <key>, using 8-128 characters from A-Za-z0-9-."
        )
    if len(candidates) > 1:
        raise SystemExit(f"IndexNow: more than one key file present: {candidates}")
    key = candidates[0]
    return key, f"{BASE}/{key}.txt"


def sitemap_urls(when: str | None) -> list[str]:
    """URLs from the sitemap, optionally only those stamped with a given date."""
    root = ET.parse(SITEMAP).getroot()
    out = []
    for url in root.iter(f"{NS}url"):
        loc = url.findtext(f"{NS}loc")
        if not loc:
            continue
        if when is not None:
            mod = (url.findtext(f"{NS}lastmod") or "").strip()
            if mod != when:
                continue
        out.append(loc.strip())
    return out


def check_urls(urls: list[str]) -> list[str]:
    """Drop anything not on this host. A mixed list is rejected wholesale by
    the endpoint with a 422, so one stray URL would lose the entire batch."""
    good, bad = [], []
    for u in urls:
        (good if u.startswith(BASE + "/") else bad).append(u)
    for u in bad:
        log(f"  ! skipping, not on {HOST}: {u}")
    return good


def payload(key: str, key_location: str, urls: list[str]) -> dict:
    return {
        "host": HOST,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }


def submit(body: dict, strict: bool) -> bool:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = resp.status
    except urllib.error.HTTPError as exc:
        code = exc.code
    except Exception as exc:  # noqa: BLE001 - never break a deploy over this
        log(f"  ! IndexNow unreachable: {exc}")
        return not strict
    # 200 accepted, 202 accepted with the key still being validated.
    if code in (200, 202):
        log(f"  submitted {len(body['urlList'])} URL(s), HTTP {code}")
        return True
    meaning = {
        400: "bad request, the payload was malformed",
        403: "forbidden, the key file did not validate",
        422: "unprocessable, URLs do not match the host or the key is wrong",
        429: "too many requests, slow down",
    }.get(code, "unexpected response")
    log(f"  ! IndexNow returned HTTP {code}: {meaning}")
    return not strict


def selftest() -> int:
    """Offline checks. Network access is not required and is not used."""
    failures = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        log(f"  {'ok  ' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
        if not ok:
            failures.append(name)

    try:
        key, loc = find_key()
        check("key file found and self-consistent", True, key)
        check("key matches the permitted character set", bool(KEY_RE.match(key)))
        check("keyLocation points at the key file", loc == f"{BASE}/{key}.txt", loc)
    except SystemExit as exc:
        check("key file found", False, str(exc))
        key, loc = "x" * 16, f"{BASE}/x.txt"

    everything = sitemap_urls(None)
    check("sitemap parses and is not empty", len(everything) > 0, f"{len(everything)} URLs")
    check("every sitemap URL is on this host", all(u.startswith(BASE + "/") for u in everything))

    mixed = ["https://example.com/nope/", f"{BASE}/reviews/"]
    check("off-host URLs are dropped", check_urls(mixed) == [f"{BASE}/reviews/"])

    body = payload(key, loc, [f"{BASE}/reviews/"])
    check("payload has the four required fields",
          set(body) == {"host", "key", "keyLocation", "urlList"})
    check("payload serialises to JSON", isinstance(json.dumps(body), str))

    batches = [everything[i:i + BATCH] for i in range(0, len(everything), BATCH)]
    check("batching respects the 10,000 URL limit", all(len(b) <= BATCH for b in batches),
          f"{len(batches)} batch(es)")

    today = date.today().isoformat()
    check("date filter runs", isinstance(sitemap_urls(today), list),
          f"{len(sitemap_urls(today))} stamped {today}")

    log(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="every URL in the sitemap")
    ap.add_argument("--date", help="only URLs with this lastmod (default: today)")
    ap.add_argument("--url", action="append", default=[], help="submit an explicit URL")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when the submission fails")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        log("IndexNow selftest:")
        return selftest()

    key, key_location = find_key()

    if args.url:
        urls = args.url
    elif args.all:
        urls = sitemap_urls(None)
    else:
        urls = sitemap_urls(args.date or date.today().isoformat())

    urls = check_urls(urls)
    if not urls:
        log("IndexNow: nothing to submit today. This is a normal no-op.")
        return 0

    log(f"IndexNow: {len(urls)} URL(s) via {ENDPOINT}")
    if args.dry_run:
        body = payload(key, key_location, urls[:BATCH])
        log(json.dumps({**body, "urlList": body["urlList"][:5]}, indent=2))
        log(f"  ...{len(urls)} URL(s) total, {(len(urls) - 1) // BATCH + 1} batch(es)")
        return 0

    ok = True
    for i in range(0, len(urls), BATCH):
        ok = submit(payload(key, key_location, urls[i:i + BATCH]), args.strict) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
