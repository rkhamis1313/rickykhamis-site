# rickykhamis.com

The live site is a **static mirror** committed under `site/`. Netlify publishes
that directory verbatim. There is no build step. New posts are written as
markdown in `content/posts/` and rendered into the mirror by `gen/new_post.py`.

## Layout

| Path | What it is |
|---|---|
| `site/` | The published site. Netlify's `publish` directory. |
| `content/posts/*.md` | Post sources: YAML front matter + markdown body. |
| `content/series.json` | Editorial queue, house writing rules, and the review log. |
| `gen/new_post.py` | Markdown → HTML renderer. No API calls, no credentials. |
| `gen/mdlite.py` | Small dependency-free markdown subset converter. |
| `gen/compliance_check.py` | Screens post markdown for advertising problems. |
| `gen/publish.py` | Gated publish: screen, render, verify, commit, push, confirm. |
| `gen/review.py` | Monthly citation review driven by hand-checked results. |
| `content/program-facts.json` | Verified DPA program terms and when they were checked. |
| `scripts/mirror_site.py` | Re-mirrors the live site. See the warning below. |

## Publishing

```bash
python gen/publish.py                               # the whole gated sequence
python gen/publish.py --dry-run                     # everything except commit and push
python gen/new_post.py --check                      # consistency check only
python gen/new_post.py --force <file>               # re-render a published post
python gen/new_post.py --retire OLD NEW             # fold OLD into NEW with a 301
```

**Correcting a published post.** Editing the markdown does nothing on its own:
`--all-unpublished` skips any post whose page already exists, so a factual fix
has no route to the reader. Edit the markdown, run `new_post.py --force` on it,
then commit and push. This was found the hard way while fixing a wrong Home
Plus figure that stayed live after the source was corrected.

`compliance_check.py` exits non-zero on an ERROR (a quoted rate or payment, a
guarantee, an em dash, a missing disclosure). Never publish over one. WARNs
need a human read: quoting a buyer asking "who has the best rate?" is fine,
claiming it about EPiQ is not, and only context separates them.

Publishing one post touches six things. `new_post.py` does all of them, and
`--check` runs afterwards to prove the site is still consistent:

1. `site/blog/<slug>/index.html`, built from a real existing post, so the
   chrome stays byte-identical
2. the previously-newest post gains a `Newer:` link
3. every blog index page is repaginated (12 cards per page)
4. `site/sitemap.xml`, a `<url>` entry, newest-first
5. `site/llms.txt`, an entry at the top of `## Articles`
6. `content/series.json`, the queue entry is marked published

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

It also cannot recover `_redirects`. Netlify consumes that file at deploy time
and never serves it back. The live deploy has redirect rules; they must be
committed to `site/_redirects` by hand or those URLs will 404.

## The editorial queue

`content/series.json` holds a flat, ordered `queue`. The daily task takes the
next entries whose `status` is `pending`, in array order. Reordering the array
is the only thing needed to change priority, which is what the monthly review
step does.

An entry may carry `supersedes: [slug]`. On publish, each listed page is
deleted, 301'd to the new post, and dropped from the index, sitemap and
llms.txt. That is how a new post replaces an older one answering the same
question instead of competing with it.

An entry with `status: "review"` is held back deliberately: an existing post
already targets that question for that city, and publishing a near-duplicate
would split the ranking signal between two pages rather than concentrate it.
`conflictsWith` names the existing slugs. Resolve each by either refreshing the
existing post in place, or writing the new one and redirecting the old URL to
it in `site/_redirects`. Do not simply publish both.

### Monthly review

There is no ChatGPT or Perplexity API here, so the citation check is done by
hand and the loop is async. It never blocks a publish run.

```bash
python gen/review.py --status                    # is one due, is one waiting
python gen/review.py --new                       # write a dated checklist
python gen/review.py --apply content/review/<file>.md
```

1. On or after `review.nextDueOn`, the daily task runs `--new`. That writes
   `content/review/YYYY-MM-DD-checklist.md` listing the last ten published
   questions, and notifies Ricky. Publishing continues as normal.
2. Ricky runs each question in ChatGPT and Perplexity and ticks the box for
   whichever cited rickykhamis.com. Notes are free text and are kept verbatim.
   Skipping a question is fine; it is ignored.
3. `--apply` scores each question out of two, aggregates by series and by city,
   reorders the pending queue, and appends to `review.log`.

A series or city must have at least `MIN_EVIDENCE` (2) tested questions before
it can move anything. One citation is an anecdote: acting on it reshuffled 89
of 99 entries in testing. Below the bar a bucket counts as untested and the
order holds.

Winning buckets sort to the front, cold ones (two or more tested, no citations
at all) to the back, everything else keeps its relative order. Entries held at
status `review` do not move.

## House rules for post content

- Ricky is a licensed MLO (NMLS #173141; EPiQ Lending NMLS #1936984). Posts are
  mortgage advertising and are regulated as such.
- **Never use an em dash.** Not anywhere, not in any content. Use a comma,
  colon, or full stop. `compliance_check.py` fails the build on one.
- **Never quote a specific interest rate, APR, or payment** as if it were
  available. Illustrative figures must be labelled illustrative.
- **No unsubstantiated superlatives** about his own services ("best lender",
  "lowest rates"). The series targets the query "best first-time buyer lender
  in {city}" and closes with EPiQ as the answer, but the case is made with
  verifiable specifics (NMLS numbers, broker vs. single-lender model,
  underwritten pre-approvals, direct access to the principal, local
  experience), never a bare superlative. Concrete proof also converts better
  than an adjective anyone can type.
- Program terms change. Cite figures with their vintage and tell the reader to
  confirm current guidelines.
- Equal Housing Opportunity. Nothing is a commitment to lend.
- **Down payment assistance figures must be verified against the program's
  official site before every use, and dated in the post.** A reader plans a
  purchase around these. `content/program-facts.json` records the terms, the
  official URL, known stale values, and when each program was last checked;
  `compliance_check.py` fails the run on an uncited program, a known stale
  value, an undated figure, or a verification older than 90 days. We shipped
  "forgiven after 36 months" when Home Plus is 60, which is why this is a gate
  and not a guideline.
- **Every post links to the two proof pages**, Ricky's EPiQ profile and the
  Scottsdale branch, alongside NMLS Consumer Access. A post that asks a reader
  to choose a lender has to give them somewhere independent to check it.
  `compliance_check.py` requires all three.
- **Never recommend a program that does not reach our readers.** Arizona Is
  Home excludes Maricopa County and Pathway to Purchase covers 17 municipalities,
  none of them ours. Both are marked `serviceAreaAvailable: false` and the
  checker fails a post that presents either as an option. Naming one to rule it
  out is fine.
- **Answer the question in the first two sentences.** Assistants quote the
  passage that answers the question. If the answer is the payoff at the bottom,
  there is nothing for them to quote.
