#!/usr/bin/env python3
"""
generate-glossary.py — bhapstar
-------------------------------------------------------------
Writes glossary.html: every term in content/glossary.json on one page.

    python generate-glossary.py

Why this page exists:

  The definitions already existed. glossary.py marks the first mention of
  each term inside the generated article and gear pages and attaches the
  explainer to it, which is the right behaviour mid-sentence: a reader who
  trips over "meridian flip" gets an answer without leaving the paragraph.

  What that cannot do is serve the reader who arrives already asking. A
  hover explainer is invisible to anyone searching for the word itself,
  invisible to a reader who met it three articles ago and wants it again,
  and invisible on a printed page. This is the one address that holds all
  of them, and it costs no new writing: the same JSON feeds both.

  Nothing about the inline explainers changes. This is an extra door.

Ordering and anchors:

  Terms are grouped by first letter and sorted case-insensitively, so
  "alt-az" and "APS-C" sit together rather than in ASCII order with every
  capital first. Each term carries a stable id derived from the term
  itself, so /glossary.html#meridian-flip can be linked to directly and
  will keep working as terms are added around it.

  Aliases are listed with their term rather than as separate rows. They
  exist so glossary.py can match "altazimuth" as well as "alt-az", and a
  reader searching for the alias should land on the same entry.
"""

import html
import json
import os
import re
import sys

DATA = "content/glossary.json"
OUT = "glossary.html"
DOMAIN = "https://bhapstar.com"

PAGE_TITLE = "Glossary"
SUBTITLE = "Every term used across the articles and gear write-ups, in plain English."
PAGE_DESC = ("Plain-English definitions of the astrophotography terms used "
             "across this site, from aperture and Bortle to meridian flip and "
             "quantum efficiency.")
INTRO = ("Astrophotography carries a lot of jargon and acronyms. Every term "
         "below is described in plain English and is used across the gallery, "
         "articles and gear write-ups, as an inline popup on the first "
         "mention of each word.")
SHARE_IMAGE = "images/andromeda-galaxy-m31.webp"


def esc(s):
    return html.escape(str(s or ''), quote=True)


def anchor_for(term):
    """Stable, readable id: 'Milky Way core' -> 'milky-way-core'."""
    slug = re.sub(r'[^a-z0-9]+', '-', str(term).lower()).strip('-')
    return slug or 'term'


def load_terms():
    if not os.path.exists(DATA):
        print(f"✗ {OUT}: {DATA} not found", file=sys.stderr)
        raise SystemExit(1)
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    terms = data.get('terms') if isinstance(data, dict) else data
    if not terms:
        print(f"✗ {OUT}: no terms in {DATA}", file=sys.stderr)
        raise SystemExit(1)

    # A duplicate id would make one of the two anchors unreachable, and the
    # only symptom would be a link that quietly scrolls to the wrong entry.
    seen = {}
    for entry in terms:
        a = anchor_for(entry.get('term'))
        if a in seen:
            print(f"  ! '{entry.get('term')}' and '{seen[a]}' both resolve to "
                  f"#{a}; the second is unreachable")
        seen[a] = entry.get('term')
    return terms


def group_terms(terms):
    """Group by first letter, sorted case-insensitively within each group."""
    groups = {}
    for entry in terms:
        term = str(entry.get('term') or '')
        if not term:
            continue
        first = term[0].upper()
        # Anything not A to Z (a term opening with a digit or a slash) goes
        # into one bucket at the front rather than inventing a letter for it.
        key = first if 'A' <= first <= 'Z' else '#'
        groups.setdefault(key, []).append(entry)
    for key in groups:
        groups[key].sort(key=lambda e: str(e.get('term')).lower())
    ordered = sorted(groups, key=lambda k: (k != '#', k))
    return [(k, groups[k]) for k in ordered]


def build_jump(groups):
    """A to Z rail. Letters with no terms are shown flat, not linked, so the
    rail keeps the same shape as terms are added rather than reflowing."""
    have = {k for k, _ in groups}
    out = []
    for letter in (['#'] if '#' in have else []) + [chr(c) for c in range(65, 91)]:
        if letter in have:
            out.append(f'<a class="gp-jump-on" href="#gp-{esc(letter.lower())}">'
                       f'{esc(letter)}</a>')
        else:
            out.append(f'<span class="gp-jump-off" aria-hidden="true">'
                       f'{esc(letter)}</span>')
    return ('      <nav class="gp-jump" aria-label="Jump to letter">\n'
            '        ' + ''.join(out) + '\n'
            '      </nav>\n')


def build_groups(groups):
    out = []
    for letter, entries in groups:
        out.append(f'      <section class="gp-group" id="gp-{esc(letter.lower())}">\n')
        out.append(f'        <h2 class="gp-letter">{esc(letter)}</h2>\n')
        out.append('        <dl class="gp-list">\n')
        for entry in entries:
            term = entry.get('term')
            aliases = entry.get('aliases') or []
            alias_html = ''
            if aliases:
                joined = ', '.join(esc(a) for a in aliases)
                alias_html = f'<span class="gp-alias">also {joined}</span>'
            out.append(
                f'          <div class="gp-item" id="{esc(anchor_for(term))}">\n'
                f'            <dt class="gp-term">{esc(term)}{alias_html}</dt>\n'
                f'            <dd class="gp-def">{esc(entry.get("def"))}</dd>\n'
                f'          </div>\n')
        out.append('        </dl>\n')
        out.append('      </section>\n')
    return ''.join(out)


def build_json_ld(terms):
    """DefinedTermSet. Search engines understand this shape for glossaries,
    and it is the one piece of structured data this page can honestly claim."""
    graph = {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "@id": f"{DOMAIN}/{OUT}",
        "name": f"{PAGE_TITLE} — Bhapstar Astrophotography",
        "description": PAGE_DESC,
        "url": f"{DOMAIN}/{OUT}",
        "hasDefinedTerm": [
            {
                "@type": "DefinedTerm",
                "name": entry.get('term'),
                "description": entry.get('def'),
                "url": f"{DOMAIN}/{OUT}#{anchor_for(entry.get('term'))}",
            }
            for entry in sorted(terms, key=lambda e: str(e.get('term')).lower())
        ],
    }
    return json.dumps(graph, indent=2, ensure_ascii=False)


def build_page(terms):
    groups = group_terms(terms)
    page_url = f"{DOMAIN}/{OUT}"
    share_url = f"{DOMAIN}/{SHARE_IMAGE}"
    return f'''<!doctype html>
<!-- Generated by scripts/generate-glossary.py. Do not edit this file by
     hand. Every build overwrites it. Edit content/glossary.json instead. -->
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{esc(PAGE_TITLE)} — Bhapstar Astrophotography</title>
  <link rel="icon" href="/images/icons/favicon-32.png" sizes="32x32" type="image/png" />
  <link rel="apple-touch-icon" href="/images/icons/apple-touch-icon.png" />
  <meta name="theme-color" content="#050414" />
  <link rel="canonical" href="{esc(page_url)}" />
  <link rel="alternate" type="application/rss+xml" title="Fragments of the Universe" href="/feed.xml" />
  <meta name="description" content="{esc(PAGE_DESC)}" />
  <meta name="author" content="Bhapinder Singh" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(PAGE_TITLE)} — Bhapstar Astrophotography" />
  <meta property="og:description" content="{esc(PAGE_DESC)}" />
  <meta property="og:url" content="{esc(page_url)}" />
  <meta property="og:image" content="{esc(share_url)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(PAGE_TITLE)} — Bhapstar Astrophotography" />
  <meta name="twitter:description" content="{esc(PAGE_DESC)}" />
  <meta name="twitter:image" content="{esc(share_url)}" />
  <link rel="preconnect" href="https://static.cloudflareinsights.com" crossorigin />
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token":"b3353c7dd8764a64baee57fd09c3dbb9"}}'></script>
  <link rel="stylesheet" href="/styles.css" />

  <!-- Page CSS lives in /styles.css under "PAGE: Glossary". -->

  <script type="application/ld+json">
{build_json_ld(terms)}
  </script>
</head>
<body class="page-glossary">

<!-- ── Header (injected by partials.js) ── -->
<div id="siteHeader"></div>

<main>
  <section class="section">
    <div class="wrap">

      <div class="section-head gallery-head gp-header">
        <div class="gallery-topline">
          <h1>{esc(PAGE_TITLE)}</h1>
        </div>
        <p class="gp-subtitle">{esc(SUBTITLE)}</p>
        <p class="gp-intro">{esc(INTRO)}</p>
      </div>

{build_jump(groups)}
      <div class="gp-count">{len(terms)} terms</div>

{build_groups(groups)}
    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

  <script src="/partials/partials.js"></script>
  <script src="/protect-images.js"></script>
</body>
</html>
'''


def main():
    terms = load_terms()
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(build_page(terms))
    letters = len(group_terms(terms))
    print(f"✓ {OUT}  ({len(terms)} term(s) across {letters} letter(s))")


if __name__ == '__main__':
    main()
