#!/usr/bin/env python3
"""Build the four cluster hub pages.

A cluster of forty articles with no hub is forty orphans. Search engines and
answer engines both work out what a site is authoritative about from structure,
and the structure has to exist: one page per topic that links every article in
it, and every article linking back.

These are static pages under site/, built the same way new_post.py builds a
post: take a rendered post as the chrome template, swap the title, description,
canonical and structured data, and replace everything between <main> and
</main>. No new layout, no new CSS, nothing to keep in sync.

Post titles and descriptions are read from the markdown front matter rather
than repeated here, so a retitled post cannot leave a stale link label behind.

Only posts that have actually rendered are linked. The series is written weeks
ahead, so linking everything in the plan would put dozens of 404s on the four
pages search engines are most likely to crawl first. The daily publish job
reruns this after rendering, so each hub grows on the morning its next article
goes live.

Usage:  python gen/build_hubs.py
"""

import io
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path('/home/user/rickykhamis-site')
POSTS = ROOT / 'content' / 'posts'
SITE = ROOT / 'site'
TEMPLATE = SITE / 'blog' / 'mortgage-rate-buydowns-scottsdale-arizona' / 'index.html'
BASE = 'https://rickykhamis.com'

sys.path.insert(0, str(ROOT / 'gen'))
import lead_form  # noqa: E402


def front_matter(path: Path) -> dict:
    text = io.open(path, encoding='utf-8').read()
    m = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
    if not m:
        raise ValueError(f'no front matter: {path}')
    meta = {}
    for line in m.group(1).splitlines():
        if re.match(r'^\s', line) or ':' not in line:
            continue
        k, _, v = line.partition(':')
        meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta


def load(slug: str) -> dict | None:
    """Front matter for a slug, or None if the post has not rendered yet."""
    if not (SITE / 'blog' / slug / 'index.html').exists():
        return None
    hits = [h for h in sorted(POSTS.glob(f'*-{slug}.md')) if h.name[11:-3] == slug]
    if not hits:
        return None
    meta = front_matter(hits[-1])
    meta['url'] = f'/blog/{slug}/'
    return meta


def esc(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


# --------------------------------------------------------------- cluster data
HUBS = [
 dict(
  path='physician-home-loans',
  title='Physician Home Loans in Arizona: The Complete Guide for Doctors, Dentists and Medical Professionals',
  h1='Physician and medical professional home loans',
  eyebrow='Loan programs',
  form='physician',
  description=('Everything a physician, dentist, veterinarian, pharmacist, CRNA or nurse '
               'practitioner needs to know about doctor loan programs in Arizona. Eligibility, '
               'leverage, student loan treatment, employment contracts, reserves and the rules '
               'that decide your file.'),
  intro=[
   ('You are being told no by people reading the wrong rulebook.',
    'Physician loan programs finance up to 100% of a primary residence with no mortgage insurance '
    'at any loan-to-value, and they let a qualifying borrower use future income from a fully '
    'executed employment contract instead of pay history. The designation list is wider than '
    '"doctor" and the rules that actually decide a file are narrower than the marketing.'),
   ('Three things almost nobody tells you first.',
    'There is a <strong>minimum</strong> loan-to-value of 90.01%, so a large down payment makes you '
    'ineligible rather than preferred. The student loan exclusion applies only during residency or '
    'clinical fellowship training, not afterwards. And moving from 100% to 95% financing raises the '
    'debt-to-income ceiling by five points, which for most attendings buys more house than the down '
    'payment costs.'),
   ('Everything below is sourced.',
    'Each article cites the guideline document and revision date behind every figure. Program terms '
    'change without notice, so confirm current eligibility on your own file before you plan around '
    'any of it.'),
  ],
  groups=[
   ('Start here', [
     'physician-home-loans-scottsdale',
     'physician-home-loan-faq',
     'physician-loan-vs-conventional',
     'physician-loan-mistakes',
   ]),
   ('By profession', [
     'dentist-home-loans-dds-dmd',
     'veterinarian-home-loans-dvm',
     'pharmacist-home-loans-pharmd',
     'crna-nurse-practitioner-home-loans',
     'graduate-professional-home-loans-scottsdale',
   ]),
   ('Structuring the loan', [
     'physician-loan-down-payment-options',
     'physician-loan-credit-score-requirements',
     'physician-loan-reserves-requirements',
     'physician-jumbo-loans-arizona',
   ]),
   ('Income, contracts and timing', [
     'medical-residents-student-loans-mortgage',
     'physician-loan-before-start-date',
     '1099-locum-tenens-physician-loans',
     'second-year-attending-mortgage',
   ]),
   ('Buying in the Valley', [
     'physician-loans-phoenix-chandler-gilbert',
     'physician-loan-refinance',
     'non-warrantable-condo-financing-scottsdale',
   ]),
  ],
 ),
 dict(
  path='self-employed-home-loans',
  title='Self-Employed Home Loans in Arizona: Qualifying Without Two Years of Tax Returns',
  h1='Self-employed and business owner home loans',
  eyebrow='Loan programs',
  form='self-employed',
  description=('Bank statement loans, third-party P&L documentation, written verification of '
               'employment and streamline documentation, explained from the guidelines. The '
               'expense factor table, co-mingling, large deposits, business age and the tier '
               'rules that decide which options you get.'),
  intro=[
   ('Your tax return is not your income and a lender knows it.',
    'It just does not have a field for the difference. Several documentation routes exist that never '
    'open a tax return, and the same business can produce qualifying income that differs by multiples '
    'depending on which one the file goes down.'),
   ('The expense factor is the whole game.',
    'A bank statement loan does not count your deposits. It applies a percentage set by what your '
    'business does and how many people it employs: 15%, 30% or 50% for a service business, 25%, 50% '
    'or 85% for a product business. Same deposits, five and a half times the spread in qualifying '
    'income, before anyone looks at your actual expenses.'),
   ('Your options are assigned, not chosen.',
    'Housing event history and mortgage lates put you in a program tier, and the tier decides whether '
    'the third-party P&L, asset depletion and written verification of employment routes exist for you '
    'at all. One late payment can remove the structure your business needs.'),
  ],
  groups=[
   ('Start here', [
     'self-employed-home-loan-faq',
     'bank-statement-loans-how-income-is-calculated',
     'expense-factor-by-business-type',
     'housing-history-tiers-non-qm',
   ]),
   ('Choosing a documentation route', [
     'personal-vs-business-bank-statements',
     '12-vs-24-month-bank-statements',
     'profit-and-loss-wvoe-loans-self-employed',
     'business-owner-write-offs-mortgage',
   ]),
   ('By situation', [
     'realtor-commission-income-mortgage',
     '1099-contractor-gig-mortgage',
     'restaurant-hospitality-owner-mortgage',
     'recently-self-employed-mortgage',
   ]),
   ('Bigger loans and pulling equity', [
     'self-employed-jumbo-loans',
     'self-employed-cash-out-refinance',
     'large-deposits-nsf-bank-statements',
   ]),
  ],
 ),
 dict(
  path='dscr-investor-loans',
  title='DSCR and Investor Property Loans in Arizona: Qualifying on the Property, Not Your Tax Returns',
  h1='DSCR and investor property loans',
  eyebrow='Loan programs',
  form='investor',
  description=('DSCR loans qualify the property rather than the borrower. The calculation, the '
               'leverage grid, No Ratio structures, LLC vesting, cash-out seasoning, short-term '
               'rentals, multi-unit caps and how to sequence a portfolio so the fourth loan still '
               'closes.'),
  intro=[
   ('Your ratio is the reason the fifth deal died, not the deal.',
    'Conventional investment lending counts every mortgage you hold at full weight and gives partial, '
    'delayed credit for the rent that pays them. It degrades with every acquisition even when every '
    'property cash flows. That is a consumer formula pointed at a business.'),
   ('DSCR replaces you with the property.',
    'Gross rental income divided by PITIA, qualified at the original note rate. No personal income, '
    'no tax returns, no debt-to-income test, and borrowers who do not provide employment verification '
    'are still eligible.'),
   ('One line makes portfolios possible.',
    'Additional financed properties require no reserves on this program. On most investment lending '
    'each property you own adds months of reserves to the next file, which is exactly what stalls '
    'investors at three or four properties.'),
  ],
  groups=[
   ('Start here', [
     'dscr-loans-scottsdale-investors',
     'dscr-loan-faq',
     'how-to-calculate-dscr',
     'dscr-credit-reserves-requirements',
   ]),
   ('Structuring the loan', [
     'no-ratio-dscr-loans',
     'dscr-llc-vesting',
     'dscr-vs-conventional-investment',
     'first-time-investor-dscr',
   ]),
   ('By property type', [
     'dscr-2-4-unit-properties',
     'short-term-rental-dscr-scottsdale',
     'non-warrantable-condo-financing-scottsdale',
   ]),
   ('Growing the portfolio', [
     'dscr-cash-out-refinance',
     'building-a-rental-portfolio-dscr',
   ]),
  ],
 ),
 dict(
  path='asset-based-home-loans',
  title='Asset Based Home Loans in Arizona: Qualifying With a Portfolio Instead of a Paycheck',
  h1='Asset based and no-income home loans',
  eyebrow='Loan programs',
  form='self-employed',
  description=('Asset depletion and asset qualifier programs convert a portfolio into qualifying '
               'income without selling anything. The haircut schedule, the 84 month divisor, the '
               'residual income test, trust and crypto treatment, and the five things these loans '
               'will not do.'),
  intro=[
   ('Your net worth went up and your qualifying income went to zero.',
    'Retirement, a business sale or a portfolio built over decades all produce the same result in an '
    'underwriting system with no field for wealth. Asset based programs exist for exactly that file.'),
   ('Qualifying assets divided by 84 months.',
    'That is the mechanic. The complication is that "qualifying assets" is not your balance: checking '
    'and savings count at 100%, stocks, bonds and mutual funds at 80%, vested retirement at 70%, and '
    'cryptocurrency at 60%. Money used for closing comes out before any of it is calculated.'),
   ('Two programs, two different tests.',
    'Asset depletion converts assets to income and runs a debt-to-income ratio. Asset qualifier '
    'subtracts your monthly debt and tests the residual against a floor. A file that fails one '
    'frequently clears the other, and most lenders run only one.'),
  ],
  groups=[
   ('Start here', [
     'asset-based-home-loan-faq',
     'asset-depletion-asset-qualifier-loans',
     'asset-depletion-vs-asset-qualifier',
   ]),
   ('By situation', [
     'retiree-mortgage-no-paycheck',
     'post-liquidity-event-mortgage',
     'trust-and-inherited-assets-mortgage',
   ]),
   ('Getting the calculation right', [
     'reserves-vs-depletion-double-count',
   ]),
  ],
 ),
]

CALCS = [
  ('/cash-out-refinance-calculator/', 'Cash-Out Refinance Calculator',
   'Enter every loan on the home and every debt to pay off. Returns the blended rate you carry '
   'today, the new loan amount and loan-to-value, and a new payment priced at the latest Freddie '
   'Mac survey average, refreshed daily and shown dated.'),
  ('/buydown-calculator/', 'Rate Buydown Calculator',
   'Compares 3-2-1, 2-1 and 1-1 temporary buydowns against a 30-year fixed and a permanent '
   'buydown funded with the same seller concession, and shows the month one passes the other.'),
  ('/calculator/', 'Mortgage Calculator',
   'Payment, taxes, insurance and mortgage insurance on a straightforward purchase.'),
]


def build_main(hub: dict) -> tuple[str, list[dict]]:
    """Return the <main> contents and the flat list of posts linked."""
    out = [f'<main id="main">']
    out.append(
      '<section class="phero"><div class="wrap">'
      '<div class="crumbs"><a href="/">Home</a> / <a href="/loan-programs/">Loan Programs</a> / '
      f'{esc(hub["h1"])}</div>'
      f'<span class="eyebrow">{esc(hub["eyebrow"])}</span>'
      f'<h1>{esc(hub["h1"])}</h1>'
      f'<p>{esc(hub["description"])}</p>'
      '</div></section>'
    )

    out.append('<section class="section"><div class="wrap"><article class="prose">')
    for heading, body in hub['intro']:
        out.append(f'<h2>{esc(heading)}</h2><p>{body}</p>')
    out.append('</article></div></section>')

    linked: list[dict] = []
    out.append('<section class="section soft"><div class="wrap">')
    for group, slugs in hub['groups']:
        live = [m for m in (load(s) for s in slugs) if m]
        if not live:
            continue
        out.append(f'<h2>{esc(group)}</h2><div class="grid g3">')
        for meta in live:
            linked.append(meta)
            out.append(
              '<div class="card post"><div class="b">'
              f'<h3><a href="{meta["url"]}">{esc(meta["title"])}</a></h3>'
              f'<div class="d">{esc(meta["description"])}</div>'
              f'<p><a class="btn btn-sm" href="{meta["url"]}">Read this</a></p>'
              '</div></div>'
            )
        out.append('</div>')
    out.append('</div></section>')

    out.append('<section class="section"><div class="wrap"><h2>Run the numbers yourself</h2>'
               '<div class="grid g3">')
    for url, name, blurb in CALCS:
        out.append(
          '<div class="card"><div class="b">'
          f'<h3><a href="{url}">{esc(name)}</a></h3><div class="d">{esc(blurb)}</div></div></div>'
        )
    out.append('</div></div></section>')

    out.append('<section class="section soft"><div class="wrap">')
    out.append(lead_form.render(hub['form']))
    out.append('</div></section>')

    out.append(
      '<section class="band"><div class="wrap">'
      '<h2>Talk to the principal, not a call center</h2>'
      '<p>Ricky Khamis is President of EPiQ Lending and a Certified Mortgage Planner, NMLS #173141, '
      'originating mortgages since 1999. EPiQ Lending is NMLS #1936984, at 7975 N. Hayden Road, '
      'Suite A-101 in Scottsdale. Verify all of it before you trust any of it: '
      '<a href="https://www.epiqlending.com/mysite/Ricky-Khamis">the EPiQ Lending profile</a>, the '
      '<a href="https://www.epiqlending.com/branch/1936984/7975-N-Hayden-Rd-Ste-A101-Scottsdale-AZ-85258">'
      'Scottsdale branch</a>, and the license itself at '
      '<a href="https://www.nmlsconsumeraccess.org/">NMLS Consumer Access</a>.</p>'
      '<div class="btns"><a class="btn btn-primary" href="/contact/">Start a conversation</a>'
      '<a class="btn" href="tel:+14809999842">(480) 999-9842</a></div>'
      '</div></section>'
    )
    out.append('</main>')
    return '\n'.join(out), linked


def build(hub: dict, template: str) -> Path:
    url = f'{BASE}/{hub["path"]}/'
    doc = template

    doc = re.sub(r'<title>.*?</title>',
                 f'<title>{esc(hub["title"])} | Ricky Khamis, EPiQ Lending</title>',
                 doc, count=1, flags=re.S)
    doc = re.sub(r'<meta name="description" content="[^"]*">',
                 f'<meta name="description" content="{esc(hub["description"])}">',
                 doc, count=1)
    doc = re.sub(r'<link rel="canonical" href="[^"]*">',
                 f'<link rel="canonical" href="{url}">', doc, count=1)
    doc = re.sub(r'(<meta property="og:title" content=")[^"]*(">)',
                 lambda m: m.group(1) + esc(hub['title']) + m.group(2), doc)
    doc = re.sub(r'(<meta property="og:description" content=")[^"]*(">)',
                 lambda m: m.group(1) + esc(hub['description']) + m.group(2), doc)
    doc = re.sub(r'(<meta property="og:url" content=")[^"]*(">)',
                 lambda m: m.group(1) + url + m.group(2), doc)
    doc = re.sub(r'(<meta name="twitter:title" content=")[^"]*(">)',
                 lambda m: m.group(1) + esc(hub['title']) + m.group(2), doc)
    doc = re.sub(r'(<meta name="twitter:description" content=")[^"]*(">)',
                 lambda m: m.group(1) + esc(hub['description']) + m.group(2), doc)

    main_html, linked = build_main(hub)

    # Structured data: keep the business, person and website nodes, drop the
    # article node this chrome came with, and describe the hub as what it is.
    def swap_jsonld(m):
        data = json.loads(m.group(1))
        graph = [n for n in data.get('@graph', [])
                 if n.get('@type') not in ('BlogPosting', 'Article', 'NewsArticle')]
        graph.append({
          '@type': 'CollectionPage',
          '@id': url,
          'url': url,
          'name': hub['title'],
          'description': hub['description'],
          'isPartOf': {'@id': f'{BASE}/#website'},
          'about': {'@id': f'{BASE}/#business'},
          'mainEntity': {
            '@type': 'ItemList',
            'numberOfItems': len(linked),
            'itemListElement': [
              {'@type': 'ListItem', 'position': i + 1,
               'url': BASE + p['url'], 'name': p['title']}
              for i, p in enumerate(linked)
            ],
          },
        })
        data['@graph'] = graph
        return ('<script type="application/ld+json">'
                + json.dumps(data, ensure_ascii=False) + '</script>')

    doc, n = re.subn(r'<script type="application/ld\+json">(.*?)</script>',
                     swap_jsonld, doc, count=1, flags=re.S)
    if n != 1:
        raise ValueError('json-ld block not found in template')

    doc, n = re.subn(r'<main id="main">.*?</main>', lambda _: main_html,
                     doc, count=1, flags=re.S)
    if n != 1:
        raise ValueError('<main> block not found in template')

    target = SITE / hub['path'] / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    io.open(target, 'w', encoding='utf-8').write(doc)
    print(f'  /{hub["path"]}/  {len(linked)} posts  {len(doc)//1024} KB')
    return target


def update_sitemap(paths):
    p = SITE / 'sitemap.xml'
    s = io.open(p, encoding='utf-8').read()
    today = date.today().isoformat()
    added = 0
    for path in paths:
        loc = f'{BASE}/{path}/'
        if loc in s:
            continue
        entry = f'<url><loc>{loc}</loc><lastmod>{today}</lastmod></url>\n'
        s = s.replace('</urlset>', entry + '</urlset>')
        added += 1
    io.open(p, 'w', encoding='utf-8').write(s)
    print(f'  sitemap: +{added}')


def update_llms(hubs):
    p = SITE / 'llms.txt'
    s = io.open(p, encoding='utf-8').read()
    if '## Topic guides' in s:
        s = re.sub(r'\n## Topic guides\n.*?(?=\n## |\Z)', '', s, flags=re.S)
    lines = ['', '## Topic guides', '']
    for h in hubs:
        lines.append(f'- [{h["h1"]}]({BASE}/{h["path"]}/): {h["description"]}')
    block = '\n'.join(lines) + '\n'
    # Sit above the article list, which is long and changes every day.
    s = s.replace('\n## Articles', block + '\n## Articles', 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  llms.txt: topic guides section written')


def main() -> int:
    template = io.open(TEMPLATE, encoding='utf-8').read()
    print('Hubs:')
    for hub in HUBS:
        build(hub, template)
    update_sitemap([h['path'] for h in HUBS])
    update_llms(HUBS)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
