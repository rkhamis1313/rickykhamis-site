# rickykhamis.com

The live site is a **static mirror** committed under `site/`. Netlify publishes
that directory verbatim — there is no build step. New posts are written as
markdown in `content/posts/` and rendered into the mirror by `gen/new_post.py`.

## Layout

| Path | What it is |
|---|---|
| `site/` | The published site. Netlify's `publish` directory. |
| `content/posts/*.md` | Post sources: YAML front matter + markdown body. |
| `content/series.json` | Editorial queue and what has already been published. |
| `gen/new_post.py` | Markdown → HTML renderer. No API calls, no credentials. |
| `gen/mdlite.py` | Small dependency-free markdown subset converter. |
| `scripts/mirror_site.py` | Re-mirrors the live site. See the warning below. |

## Publishing

```bash
python gen/new_post.py content/posts/2026-09-05-tempe.md
python gen/new_post.py --all-unpublished
python gen/new_post.py --check          # consistency check only
```

Publishing one post touches six things. `new_post.py` does all of them, and
`--check` runs afterwards to prove the site is still consistent:

1. `site/blog/<slug>/index.html` — built from a real existing post, so the
   chrome stays byte-identical
2. the previously-newest post gains a `Newer:` link
3. every blog index page is repaginated (12 cards per page)
4. `site/sitemap.xml` — a `<url>` entry, newest-first
5. `site/llms.txt` — an entry at the top of `## Articles`
6. `content/series.json` — the queue entry is marked published

### Front matter

```yaml
---
title: "…"           # required
slug: …              # required, becomes /blog/<slug>/
description: "…"     # required, used for meta, og and llms.txt
date: 2026-09-05     # required, YYYY-MM-DD
city: Tempe          # optional, marks the series queue entry published
image: /assets/…     # optional; omitted posts get the site's gradient card
tags: [ … ]          # optional
---
```

## The mirror is not routine maintenance

`scripts/mirror_site.py` (and the `Mirror live site` workflow) rebuilds `site/`
from whatever rickykhamis.com currently serves and commits with `git add -A
site`. **Any generated post not yet present in the live sitemap would be
deleted.** The workflow is `workflow_dispatch` only, deliberately. Re-run it
only to re-baseline against a site that changed outside this repo, and expect
to re-publish anything newer afterwards.

It also cannot recover `_redirects` — Netlify consumes that file at deploy time
and never serves it back. The live deploy has redirect rules; they must be
committed to `site/_redirects` by hand or those URLs will 404.

## House rules for post content

- Ricky is a licensed MLO (NMLS #173141; EPiQ Lending NMLS #1936984). Posts are
  mortgage advertising and are regulated as such.
- **Never quote a specific interest rate, APR, or payment** as if it were
  available. Illustrative figures must be labelled illustrative.
- **No unsubstantiated superlatives** about his own services ("best lender",
  "lowest rates"). Answer the question the reader is asking instead.
- Program terms change. Cite figures with their vintage and tell the reader to
  confirm current guidelines.
- Equal Housing Opportunity. Nothing is a commitment to lend.
