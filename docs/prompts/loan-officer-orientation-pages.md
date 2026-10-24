# Prompt: per-loan-officer Realty ONE Group orientation pages

Paste everything below the line into a Claude Code session on the
`rkhamis1313/rickykhamis-site` repo. It is written to be self-contained, so a
session with no memory of how this site works can still do the job correctly.

Keep this file updated when the facts in it change. A stale prompt produces a
confidently wrong page.

---

Build a personalized Realty ONE Group orientation landing page for each EPiQ
Lending loan officer, so a managing broker can send a new recruit straight to
*their* loan officer's page and book the orientation on *that* person's
calendar.

## The site you are working in

- Repo `rkhamis1313/rickykhamis-site`, branch
  `claude/rickykhamis-daily-blog-automation-dovt88`. Commit and push there.
- `site/` is a **static mirror published verbatim by Netlify. There is no build
  step.** What is in `site/` is what is served.
- Short links live in `site/_redirects`, one rule per line, first match wins.
  Rules do not override a real file at the same path.
- Deploy is automatic on push. Verify with the GitHub workflow
  `verify-live.yml` (it fetches every URL in `sitemap.xml` and fails on any
  non-200, and checks a sample of redirects). Trigger it with
  `gh api -X POST repos/rkhamis1313/rickykhamis-site/actions/workflows/verify-live.yml/dispatches -f ref=<branch>`
  and read the result before you tell anyone it works.
- **rickykhamis.com does not resolve from inside the container.** You cannot
  curl or fetch the live site. The workflow above is your only way to confirm
  anything is actually live. Never claim a page works because the file exists.

## The page you are copying

`site/epiq-orientation/index.html` is the master version, aimed at Ricky
Khamis. Read it first. It is a standalone page with its own `<style>` block
rather than the site chrome, and it is `noindex`.

Its section order, which works and which you should keep:

1. Hero: co-brand bar, headline, lede, meta chips, booking button **above the
   fold**
2. The half point benefit, full-width orange band
3. The partnership story, two founder cards with photos
4. What the 30 minutes covers, three numbered cards
5. The 2-24-48 service standard, a table of promises with times
6. What else the agent gets
7. The embedded Calendly, plus a text fallback link
8. A block for managing brokers with the link to copy
9. Footer: NMLS identifiers, Equal Housing, affiliated business disclosure

## Build it as a generator, not as copies

Do **not** hand-write one HTML file per loan officer. Follow the pattern
already in this repo:

- `gen/build_programs.py` builds pages from a config and `gen/program_content.py`
  holds the content. Read both before you start.
- Create `gen/build_lo_pages.py` plus `gen/lo_roster.py` holding one dict per
  loan officer. Re-running the builder must regenerate every page.
- Each page writes to `site/lo/<slug>/index.html`, and gets a short link in
  `site/_redirects`: `/<slug>/  /lo/<slug>/  301`. Confirm the slug does not
  collide with an existing path before you add it.
- Pages are `noindex, follow`, like the master. These are links handed out by
  managers, not search targets, and keeping another company's name out of the
  index is deliberate.
- The builder must refuse to write a page that fails the house rules below.
  `gen/build_programs.py` has a `screen()` function doing exactly this. Reuse
  the approach.

## What varies per loan officer

Ask the user for these. **Do not invent any of them, and do not guess a
Calendly URL.**

```
name                 full name as it should appear
title                e.g. Loan Officer, Senior Loan Officer, Branch Manager
nmls                 their individual NMLS number          REQUIRED
slug                 url segment, e.g. jane-smith
photo                path under site/assets/images/, or ask them to upload one
phone                direct line, digits only for the tel: link
email                their EPiQ address
calendly             the FULL orientation event URL for that person
offices              which Realty ONE Group offices they cover (see list below)
bio                  two or three sentences, specific, no filler
years                years in the business, if they want it shown
languages            if relevant
```

Verify each Calendly URL before shipping. If the Calendly MCP connector is
available, call `users-get_current_user` then `event_types-list_event_types`
and use the real `scheduling_url` of the orientation event. A booking link that
goes nowhere is worse than no page: three links on this site once pointed at a
Calendly slug that was not Ricky's, including the widget behind the "Book a
Call" button in the header of every page.

## What stays identical on every page

These are facts about the company, not about the person. Copy them from
`site/epiq-orientation/index.html` so they stay consistent:

- The half point: a lender credit worth half a percent of the loan amount on a
  Realty ONE Group agent's transaction, the buyer's choice of closing costs or
  a first-year rate buydown, $2,500 on a $500,000 loan.
- The partnership: CMG Financial and Christopher M. George, Founder, President
  and CEO, since 1993, former Chairman of the Mortgage Bankers Association,
  direct lender in all 50 states, home of the All In One Loan and HomeFundIt.
  Realty ONE Group and Kuba Jewgieniew, Founder and CEO, Las Vegas 2005, 400+
  offices, "every ONE matters", 4,700+ agents across Arizona and Nevada.
  Founder photos are already at `site/assets/images/chris-george.jpg` and
  `site/assets/images/kuba-jewgieniew.jpg`.
- The 2-24-48 standard: credit reviewed on a soft pull in 2 hours, signed AAR
  Pre-Qualification in 24, buyer consultation booked in 48, Loan Status Update
  every Tuesday at 9am, milestone updates same day, text replies within 1
  business hour.
- Entity identifiers: EVO Home Loans, LLC dba EPiQ Lending, NMLS #1936984,
  Equal Housing Lender, nmlsconsumeraccess.org.

## Hard rules. The page does not ship if it breaks one.

**Affiliated business.** Realty ONE Group's founder holds a **49% ownership
interest in EPiQ Lending**. Every page carries, in the footer: the affiliation
and the ownership interest named; that the owner may receive a financial
benefit from referred business; **that the reader is not required to use EPiQ
Lending**; that other providers are available and clients are free to shop; and
that the written affiliated business disclosure must reach a client at or
before the time of referral. Copy the wording from the master page. Never write
that the two companies are unaffiliated.

**No rates.** Do not print an interest rate, an APR, or a worked rate example
anywhere, including "7% becomes 6.5%". Naming a rate in an advertisement pulls
in Regulation Z trigger-term rules. Describe what the credit does, not what
rate it produces. Do not quote a monthly payment either.

**No presumption.** Never imply the agent has chosen EPiQ or that using EPiQ is
expected. Phrases like "your lender", "get your lender set up" and "one of
ours" contradict the not-required-to-use disclosure three screens below them.

**Only claim what is true for that office.** EPiQ shares Suite A-101 with
**Realty ONE Group Scottsdale only**. Do not write "in your building" on a page
for an officer covering Gilbert or Henderson. This is the main advantage of a
per-officer page: say the actual office by name, with its address, and the
claim becomes true and stronger. Get this wrong and the page is worse than the
generic one.

**American spelling, no em dashes.** House style, enforced by
`gen/compliance_check.py` on posts and by `screen()` in `build_programs.py`.

## Design requirements

- **The booking button is in the first screen.** Measured on two pages in this
  repo, the main action had drifted to 66% and 69% down. Both had to be fixed
  after the fact. Put it in the hero and again next to the calendar.
- Lead with what the reader gets, then prove it. Benefit, then story.
- The officer's photo, name, title and **NMLS number** are in the hero. An
  orientation page for a named originator that does not show their licence
  number is not finished.
- Name the specific office or offices, with addresses, as a short list.
- Embed that officer's Calendly inline, and always include a plain text link
  plus phone as a fallback for when the widget does not load.
- Responsive and measured, not eyeballed. Probe at 1280, 768, 390 and 320px
  with headless Chromium at `/opt/pw-browsers/chromium` over a local HTTP
  server. **Serve over HTTP, not `file://`:** the stylesheet is root-relative,
  so `file://` silently loads an unstyled page and every measurement is
  garbage. Assert zero horizontal overflow and the hero CTA above the fold.
  If Playwright will not install, say so plainly rather than claiming the
  layout was verified.
- No fixed or minimum widths above about 99px on anything inside the content
  column, or it will overflow a 320px phone.

## Managing broker block

Every page needs it, and it is the reason the page exists:

- The short link in a copy block, e.g. `rickykhamis.com/jane-smith`
- One line on when to send it: with the rest of the signup paperwork
- The officer's direct line for a broker who would rather call

Also build one index at `site/lo/index.html`, `noindex`, listing every officer
with their photo, office and link, so a broker who does not know which officer
covers their office can find the right page.

## Before you say it is done

1. `python3 gen/build_lo_pages.py` regenerates every page cleanly
2. The house-rule screen passes on every generated page
3. No broken internal links: walk every `href="/..."` in `site/` and confirm
   a file exists or a redirect covers it
4. Every short link resolves and collides with nothing
5. Each Calendly URL is the one the user gave you, character for character
6. Layout probed at four widths over HTTP, zero overflow, CTA above the fold
7. Pushed, then `verify-live.yml` run and **read**, green, on your commit SHA
8. Report the real numbers: pages built, word counts, what you could not verify

## Reference: Realty ONE Group offices

From the EPiQ Calendly event locations, correct as of 24 October 2026. Confirm
with the user before publishing, offices move.

```
AZ  Scottsdale        7975 N. Hayden Rd. #A-101, Scottsdale, AZ 85258
                      (EPiQ Lending shares this suite)
AZ  North Scottsdale  17550 N. Perimeter Dr., Ste 160, Scottsdale, AZ 85255
AZ  Phoenix           11211 N. Tatum Blvd., Ste 120, Phoenix, AZ 85028
AZ  Gilbert           3530 S. Val Vista Dr., #114, Gilbert, AZ 85297
AZ  Chandler          3100 W. Ray Rd., Suite 100, Chandler, AZ 85226
AZ  Glendale          17235 N. 75th Ave., C-190, Glendale, AZ 85308
AZ  Goodyear          2950 N. Litchfield Rd., Goodyear, AZ 85395
AZ  Surprise          14815 W. Bell Rd., #100, Surprise, AZ 85374
NV  Henderson         2831 St. Rose Pkwy., Suite 100, Henderson, NV 89052
NV  Summerlin         10750 W. Charleston Blvd., Suite 180, Las Vegas, NV 89135
NV  Northwest         5550 Painted Mirage Rd., Suite 140, Las Vegas, NV 89149
NV  Southwest         8395 W. Sunset Rd., Suite 190, Las Vegas, NV 89113
```

## Start by asking

Do not begin building until you have, for at least one officer: name, title,
NMLS, slug, phone, email, the exact Calendly orientation URL, which offices
they cover, and a photo. Build that one page completely, show it to the user,
get it approved, and only then roll out the rest of the roster. One approved
page beats twelve that all need the same correction.
