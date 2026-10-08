#!/usr/bin/env python3
"""Build the five core loan program pages.

Why this exists. The site shipped with six families of city landing pages:
fha-loans-mesa, va-loans-gilbert, conventional-loans-tempe and so on, eight
cities each, forty eight pages in total. Measured against each other they ran
79% to 84% identical and 549 to 681 words. They targeted the queries that
actually produce loans, and they were the weakest pages on the site, while the
blog ran a median of 1,439 words and was genuinely distinct. That is backwards.

So the forty eight were retired into 301s and the authority was consolidated
here: one deep page per program, each carrying the East Valley geography the
city pages were supposed to own, with something true and program specific to
say about each city rather than the same paragraph with the name swapped.

Every regulatory figure on these pages is sourced and dated in the page itself.
Nothing is asserted from memory. Where a number moves annually and could not be
confirmed against the issuing agency, the page explains the mechanism and sends
the reader to the agency, which is both more honest and does not go stale.

Built the same way build_hubs.py builds the cluster hubs: take a rendered post
as the chrome template, swap the head metadata and structured data, replace
everything between <main> and </main>. No new layout, no new CSS.

Usage:  python gen/build_programs.py
"""

import io
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
TEMPLATE = SITE / 'blog' / 'mortgage-rate-buydowns-scottsdale-arizona' / 'index.html'
BASE = 'https://rickykhamis.com'

sys.path.insert(0, str(ROOT / 'gen'))
import lead_form  # noqa: E402

# The eight cities the retired pages covered, in the order a reader in the
# East Valley would think of them.
CITIES = ['Mesa', 'Gilbert', 'Chandler', 'Tempe', 'Scottsdale',
          'Phoenix', 'Queen Creek', 'Paradise Valley']


def esc(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


# --------------------------------------------------------------- house style
# These pages are regulated advertising and they are not screened by
# compliance_check.py, which only reads content/posts. So the screen runs here,
# against the rendered prose, before anything is written.
BANNED = [
    (r'—', 'em dash'),
    (r'―', 'horizontal bar'),
    (r'\s–\s', 'spaced en dash as punctuation'),
    (r'\b\d+(?:\.\d+)?\s*%\s*(?:APR|interest\s+rate|rate)\b', 'a specific rate or APR'),
    (r'\bAPR\s+of\s+\d', 'a specific APR'),
    (r'\bguarante\w*\s+(?:approval|rate|savings|closing)', 'a guarantee'),
    (r'\byou\s+will\s+(?:save|qualify|be\s+approved)\b', 'a promised outcome'),
    (r'\bno\s+(?:closing\s+)?costs?\b(?!\s*\?)', 'a no-costs claim'),
    (r'\$\d[\d,]*\s*(?:/|per\s+)mo(?:nth)?\b', 'a specific monthly payment'),
    (r'\b\w*(?:neighbour|behaviour|favour|colour|centre|metre|licence|organis|'
     r'recognis|whilst|amongst)\w*\b', 'a British spelling'),
]

REQUIRED = [
    ('Equal Housing Opportunity', 'the Equal Housing Opportunity disclosure'),
    ('not a commitment to lend', 'the "not a commitment to lend" disclaimer'),
    ('173141', "Ricky's NMLS number"),
    ('nmlsconsumeraccess.org', 'the NMLS Consumer Access link'),
]


def screen(path: str, html: str) -> list[str]:
    """Return a list of problems with the rendered prose. Empty means clean."""
    text = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    problems = []
    for pattern, label in BANNED:
        m = re.search(pattern, text, re.I)
        if m:
            problems.append(f'{path}: contains {label}: {m.group(0)!r}')
    for needle, label in REQUIRED:
        if needle not in html:
            problems.append(f'{path}: missing {label}')
    return problems


# ------------------------------------------------------------------ building
DISCLAIMER = (
    '<p style="font-size:.85rem;color:var(--muted);margin-top:28px">'
    'Equal Housing Opportunity. This is general information, not a commitment to lend or an '
    'offer to extend credit. Program rules, agency limits and pricing change, and every file '
    'depends on credit approval, property appraisal, income and asset verification and other '
    'qualifying factors. Not all applicants will qualify. Figures attributed to an agency above '
    'are cited with the issuing agency and the date they were published; confirm the current '
    'figure on your own file before you plan around it. Ricky Khamis, NMLS #173141. EPiQ Lending, '
    'NMLS #1936984, 7975 N. Hayden Road, Suite A-101, Scottsdale, AZ 85258. Verify any of this at '
    '<a href="https://www.nmlsconsumeraccess.org/">NMLS Consumer Access</a>, the '
    '<a href="https://www.epiqlending.com/mysite/Ricky-Khamis">EPiQ Lending profile</a> or the '
    '<a href="https://www.epiqlending.com/branch/1936984/7975-N-Hayden-Rd-Ste-A101-Scottsdale-AZ-85258">'
    'Scottsdale branch page</a>.</p>'
)


def build_main(p: dict) -> str:
    out = ['<main id="main">']

    out.append(
      '<section class="phero"><div class="wrap">'
      '<div class="crumbs"><a href="/">Home</a> / <a href="/loan-programs/">Loan Programs</a> / '
      f'{esc(p["h1"])}</div>'
      '<span class="eyebrow">Loan program</span>'
      f'<h1>{esc(p["h1"])}</h1>'
      f'<p>{esc(p["lede"])}</p>'
      '</div></section>'
    )

    # The article: opening, then the substantive sections.
    body = [f'<p class="hook"><strong>{p["hook"]}</strong></p>']
    for heading, paras in p['sections']:
        body.append(f'<h2>{esc(heading)}</h2>')
        body.extend(f'<p>{t}</p>' for t in paras)

    # The geography the retired city pages were supposed to carry.
    body.append(f'<h2>{esc(p["geo_heading"])}</h2>')
    body.append(f'<p>{p["geo_intro"]}</p>')
    body.append('<ul>')
    for city in CITIES:
        body.append(f'<li><strong>{esc(city)}.</strong> {p["cities"][city]}</li>')
    body.append('</ul>')

    body.append('<h2>Common questions</h2>')
    for q, a in p['faq']:
        body.append(f'<p><strong>{esc(q)}</strong><br>{a}</p>')

    body.append('<h2>Why bring this file to us</h2>')
    body.append(
      '<ul>'
      '<li><strong>Broker model.</strong> Multiple investors rather than one bank\'s shelf, which '
      'is what a file needs when the first answer is no.</li>'
      '<li><strong>You talk to the principal.</strong> Ricky Khamis is President of EPiQ Lending '
      'and a Certified Mortgage Planner, NMLS #173141, originating mortgages since 1999. Direct '
      'line: <a href="tel:+14809999842">(480) 999-9842</a>.</li>'
      '<li><strong>We price the alternatives against each other.</strong> Most lenders quote the '
      'program you asked for. The comparison is the work.</li>'
      '</ul>'
    )
    body.append(
      '<p class="analyze-cta" style="margin-top:36px;padding:16px 18px;'
      'border-left:4px solid var(--orange);background:var(--soft);font-size:1.02rem">'
      'Looking at a specific home? Send me the address and I will run the numbers: '
      '<a href="/analyze/"><strong>rickykhamis.com/analyze</strong></a></p>'
    )
    body.append(DISCLAIMER)

    out.append('<section class="section"><div class="wrap"><article class="prose">'
               + ''.join(body) + '</article></div></section>')

    out.append('<section class="section soft"><div class="wrap">')
    out.append(lead_form.render(p['form']))
    out.append('</div></section>')

    if p['related']:
        out.append('<section class="section"><div class="wrap"><h2>Read further</h2>'
                   '<div class="grid g3">')
        for url, name, blurb in p['related']:
            out.append(
              '<div class="card"><div class="b">'
              f'<h3><a href="{url}">{esc(name)}</a></h3>'
              f'<div class="d">{esc(blurb)}</div></div></div>'
            )
        out.append('</div></div></section>')

    out.append(
      '<section class="band"><div class="wrap">'
      '<h2>Talk to the principal, not a call center</h2>'
      '<p>EPiQ Lending is NMLS #1936984, at 7975 N. Hayden Road, Suite A-101 in Scottsdale. '
      'Verify all of it before you trust any of it: '
      '<a href="https://www.epiqlending.com/mysite/Ricky-Khamis">the EPiQ Lending profile</a>, the '
      '<a href="https://www.epiqlending.com/branch/1936984/7975-N-Hayden-Rd-Ste-A101-Scottsdale-AZ-85258">'
      'Scottsdale branch</a>, and the license itself at '
      '<a href="https://www.nmlsconsumeraccess.org/">NMLS Consumer Access</a>.</p>'
      '<div class="btns"><a class="btn btn-primary" href="/contact/">Start a conversation</a>'
      '<a class="btn" href="tel:+14809999842">(480) 999-9842</a></div>'
      '</div></section>'
    )
    out.append('</main>')
    return '\n'.join(out)


def build(p: dict, template: str) -> tuple[Path, bool]:
    url = f'{BASE}/{p["path"]}/'
    doc = template

    doc = re.sub(r'<title>.*?</title>',
                 f'<title>{esc(p["title"])} | Ricky Khamis, EPiQ Lending</title>',
                 doc, count=1, flags=re.S)
    doc = re.sub(r'<meta name="description" content="[^"]*">',
                 f'<meta name="description" content="{esc(p["description"])}">', doc, count=1)
    doc = re.sub(r'<link rel="canonical" href="[^"]*">',
                 f'<link rel="canonical" href="{url}">', doc, count=1)
    for prop, val in (('og:title', p['title']), ('og:description', p['description']),
                      ('og:url', url), ('twitter:title', p['title']),
                      ('twitter:description', p['description'])):
        attr = 'property' if prop.startswith('og:') else 'name'
        doc = re.sub(rf'(<meta {attr}="{prop}" content=")[^"]*(">)',
                     lambda m: m.group(1) + esc(val) + m.group(2), doc)

    main_html = build_main(p)

    def swap_jsonld(m):
        data = json.loads(m.group(1))
        graph = [n for n in data.get('@graph', [])
                 if n.get('@type') not in ('BlogPosting', 'Article', 'NewsArticle')]
        graph.append({
          '@type': 'WebPage',
          '@id': url,
          'url': url,
          'name': p['title'],
          'description': p['description'],
          'isPartOf': {'@id': f'{BASE}/#website'},
          'about': {'@id': f'{BASE}/#business'},
          'mainEntity': {
            '@type': 'FAQPage',
            'mainEntity': [
              {'@type': 'Question', 'name': q,
               'acceptedAnswer': {'@type': 'Answer',
                                  'text': re.sub(r'<[^>]+>', '', a)}}
              for q, a in p['faq']
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

    problems = screen(f'/{p["path"]}/', doc)
    if problems:
        raise ValueError('house style or disclosure problem:\n  ' + '\n  '.join(problems))

    target = SITE / p['path'] / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    before = io.open(target, encoding='utf-8').read() if target.exists() else None
    io.open(target, 'w', encoding='utf-8').write(doc)
    changed = doc != before

    words = len(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', main_html)).split())
    print(f'  /{p["path"]}/  {words} words{"" if changed else "  (unchanged)"}')
    return target, changed


def update_sitemap(changed: dict) -> None:
    sm = SITE / 'sitemap.xml'
    s = io.open(sm, encoding='utf-8').read()
    today = date.today().isoformat()
    added = restamped = 0
    for path, did in changed.items():
        loc = f'{BASE}/{path}/'
        if loc not in s:
            s = s.replace('</urlset>',
                          f'<url><loc>{loc}</loc><lastmod>{today}</lastmod></url>\n</urlset>')
            added += 1
            continue
        if not did:
            continue
        pat = re.compile(r'(<url><loc>' + re.escape(loc) + r'</loc><lastmod>)[^<]*(</lastmod>)')
        s, n = pat.subn(lambda m: m.group(1) + today + m.group(2), s, count=1)
        if n != 1:
            raise ValueError(f'could not restamp lastmod for {loc}')
        restamped += 1
    io.open(sm, 'w', encoding='utf-8').write(s)
    print(f'  sitemap: +{added}, {restamped} restamped')


def main() -> int:
    from program_content import PROGRAMS
    template = io.open(TEMPLATE, encoding='utf-8').read()
    print('Program pages:')
    changed = {}
    for p in PROGRAMS:
        _, did = build(p, template)
        changed[p['path']] = did
    update_sitemap(changed)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
