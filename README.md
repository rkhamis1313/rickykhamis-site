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
| `content/author.json` | Ricky's credentials, awards and proof links. Renders into every post and into each page's Person schema. |
| `content/scenarios.json` | Real closed files, anonymized. The moat. Read the rules at the top before using one. |
| `scripts/mirror_site.py` | Re-mirrors the live site. See the warning below. |

## The scenario bank

`content/scenarios.json` holds real closed loan files, anonymized. Every
competitor can write "self-employed buyers need two years of returns". Nobody
else has these files, which is the entire reason the borrower by neighborhood
series is defensible.

Rules, which are also written into the file:

- No borrower names. No exact street numbers. Street or area level only.
- No loan amounts, no rates, no payments.
- Use a scenario only where it genuinely fits the post's borrower type or
  neighborhood. Check `fitsBorrowerTypes` and `fitsNeighborhoods`. A forced fit
  reads as filler and destroys the credibility the real detail buys you.
- Any post using one carries the file's `disclaimer` line verbatim.
- Append the post's slug to that scenario's `usedIn`.
- Never invent a client story. A fabricated file is the worst thing this system
  could produce, and it would be indistinguishable from the real ones to a
  reader. That is exactly why it must never happen.

The bank runs down as the series publishes. When it is thin, ask Ricky for two
more files rather than writing around it.

## How posts actually get published

Posts are written ahead of time and released on their own date by a GitHub
Action. No model runs on a schedule. This matters, because every version of
"a scheduled Claude session writes today's posts" failed the same way: the
fired session had no repository attached, so it could not push, and it failed
silently for days. A guard was added so it failed loudly instead, which saved
tokens and still published nothing.

The split that works:

- **Writing happens in a Claude session.** Posts go into `content/posts/` with
  a future `date` in the front matter. Nothing is rendered yet.
- **Releasing happens in `.github/workflows/daily-publish.yml`**, daily at
  13:00 UTC, which is 6am Phoenix year round since Arizona skips DST. It runs
  `gen/publish.py --due-only`, which renders only posts whose date has arrived,
  then commits and pushes with the automatic `GITHUB_TOKEN`.

There is no API key to manage and no credential to rotate. The scheduler runs
no model, so it cannot fail on model access, and a day with nothing due is a
healthy no-op rather than an error.

The one failure mode left is running out of runway. The workflow prints how
many days of posts remain and raises a warning annotation when none are
written ahead. When that fires, write the next batch.

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

### Series in the queue

The strategy is Scottsdale luxury lending, and the queue interleaves a pillar
post with a neighborhood post each day so every day ships a mechanic and an
application of it.

`qualification-mechanics` is the moat. A luxury borrower's problem is almost
never the rate, it is whether their income can be documented at all: K-1s,
business return add-backs, bank statement analysis, asset depletion, equity
comp, trust income, several entities, a recent liquidity event. Show the actual
mechanic, which line of the return and which months of statements. Generic
reassurance is worthless to this reader. Never state a guideline as universal;
investors differ and guidelines change, so attribute and date anything specific.

`luxury-products` covers the structures those files land in. Each post says who
the product suits AND who it does not. The All In One Loan gets its own gate in
compliance_check: every pound of its benefit comes from how the borrower parks
and spends their money, so a savings figure presented as an outcome is a promise
we cannot keep. Mark it illustrative, say what it depends on, and say who it
does not suit.



`scottsdale-neighborhoods` runs first. Scottsdale is already about two thirds of
the blog at city level and every mortgage topic is covered there, so the
unclaimed ground is geography inside the city, where there are currently zero
pages. Each entry carries an `angle` naming the financing mechanic that makes it
different. Six mechanics cover the twelve: condo project eligibility, property
condition, HOA depth, jumbo tiering, club membership as a recurring obligation,
and construction lending.

That `angle` is a quality gate, not a hint. Twelve near-identical neighborhood
pages are a doorway set and get treated as one. If a post could be produced by
swapping the name into another post in the series, it should not ship, and the
neighborhood should be cut from the queue instead.

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

## Header images

Every post gets its own generated header at `site/assets/images/headers/<slug>.jpg`,
1200x630 so it doubles as the Open Graph card. `gen/new_post.py` makes one
automatically at publish time; there is nothing to do by hand.

They are generated rather than photographed on purpose. A photograph of a golf
course we do not have rights to is a liability, and a generic stock desert is
worse than a mark that states what the page is. Each header takes its headline
from the post's `neighborhood` or `city`, its eyebrow from `borrowerType`, and
its ridgeline silhouette from a hash of the slug, so the set is visibly varied
but never off-brand and never random between runs.

Before this existed, every post shared one flat gradient thumbnail and one
default `og:image`, so seventy different articles produced the same preview
card when shared. Each post now points at its own.

    python gen/make_header.py --all              # every post with a markdown source
    python gen/make_header.py --all --force      # redraw after a design change
    python gen/make_header.py --page site/blog/<slug>/index.html   # mirrored posts

Generation needs Pillow. It is installed in the publish workflow, and a failure
falls back to the old gradient rather than blocking a post from going out.

## Neighborhood facts and market data

`content/neighborhoods.json` is what makes a post read as written by someone who
knows the community rather than someone who knows its name. It holds two kinds
of data, separated deliberately.

**`facts` are stable and sourced.** Developer, course architect, opening year,
acreage, villages, club structure. These do not change, every entry carries a
`sources` list, and nothing goes in without one. Troon North's Monument opened
in 1990 and the Pinnacle in 1995, both Weiskopf and Morrish, on 1,800 acres.
That is checkable, and it is the kind of detail a competitor writing generic
luxury copy cannot fake.

**`market` is volatile and starts null.** Average sale price, last sale, days
on market. Never populate this from memory or estimation. A stale figure on a
licensed originator's site is worse than no figure, and an invented one is
indefensible.

Posts reference market data with a marker rather than hardcoded numbers:

    [[MARKET:Troon North]]

`gen/market_block.py` expands it at render time. Refreshing every post on the
site is one edit to the data file, not seventy edits to markdown. Three
behaviours, all tested:

- **No data:** renders an honest line offering the current report by phone. It
  never invents a range.
- **Fresh data:** renders a sourced table with an `asOf` date and a reminder
  that market data changes.
- **Older than 75 days:** adds a visible notice saying exactly how old it is.

**Where market data may come from.** An MLS subdivision report pulled by a
licensed agent, or Maricopa County Assessor and Recorder public records. Note
that republishing MLS data on a public website carries IDX licensing
obligations from ARMLS, so confirm what the agreement permits before publishing
an MLS-derived figure. County records are public and carry no such restriction,
which makes them the safer source for last-sale data.
