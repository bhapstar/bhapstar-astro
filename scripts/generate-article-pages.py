#!/usr/bin/env python3
"""
Generates one REAL, indexable page per article in site-data.json, under
articles/<slug>.html. Mirrors generate-gear-pages.py, but for long-form
write-ups rather than equipment.

Each page includes:
  - Hero image (the entry's cover), with the standfirst beneath it
  - A meta line: category, date, read time
  - Article prose, read from content/articles/<slug>.html
  - Previous / next article navigation (wraps, so no dead ends)
  - JSON-LD Article schema
  - Canonical URL pointing at itself
  - OG tags for social sharing

Pages use the site's shared chrome: /styles.css, header/footer injected by
/partials/partials.js (root-absolute, so it works from /articles/), and
/protect-images.js for the usual right-click/drag speed bumps.

Prose fragments are plain HTML: <h2>, <p>, <ul>, <table>, and figures using
<figure class="article-fig"> with an inline <svg> and a <figcaption>. Diagrams
are drawn by hand in the fragment rather than shipped as binary assets, so they
scale, theme with the site and cost nothing to load. An article can also open
with a <div class="event-callout"> block for a dated, real-world event.

Idempotent: rewrites every page each run, and deletes any stale
articles/*.html whose slug is no longer in site-data.json.

    python generate-article-pages.py
"""

import html
import json
import os
from datetime import datetime

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT_DIR = "articles"
CONTENT_DIR = "content/articles"
SITE_NAME = "Bhapstar Astrophotography"


def esc(s):
    """Escape for HTML attribute/text context."""
    return html.escape(str(s or ''), quote=True)


def url_for(path):
    """Full URL for a file path."""
    return DOMAIN + '/' + path.lstrip('/')


def thumb_for(file):
    """Gallery images thumb to images/thumbs/, gear images to images/gear/thumbs/."""
    if not file:
        return None
    if file.startswith('images/gear/'):
        return file.replace('images/gear/', 'images/gear/thumbs/', 1)
    if file.startswith('images/'):
        return file.replace('images/', 'images/thumbs/', 1)
    return file


def iso_date(entry):
    """'DD-MM-YYYY' -> ISO 'YYYY-MM-DD'. Falls back to a fixed date rather than
    'now', so a rebuild never restamps every article."""
    try:
        return datetime.strptime(entry.get('date', ''), "%d-%m-%Y").strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return "2026-07-30"


def pretty_date(entry):
    """'DD-MM-YYYY' -> '30 July 2026'. Empty string if unparseable."""
    try:
        d = datetime.strptime(entry.get('date', ''), "%d-%m-%Y")
    except (TypeError, ValueError):
        return ''
    return f"{d.day} {d.strftime('%B %Y')}"


def read_body(slug):
    """Read the prose fragment from content/articles/<slug>.html."""
    path = os.path.join(CONTENT_DIR, f"{slug}.html")
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<p><em>Article coming soon.</em></p>"


def build_json_ld(entry, page_url, cover_src):
    """Article schema. Deliberately plain: headline, dates, author, publisher."""
    d = iso_date(entry)
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": entry.get('title', ''),
        "description": entry.get('desc', ''),
        "articleSection": entry.get('category', ''),
        "author": {"@type": "Person", "name": "Bhapinder Singh", "url": DOMAIN},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": DOMAIN},
        "datePublished": d,
        "dateModified": d,
        "mainEntityOfPage": {"@type": "WebPage", "@id": page_url},
        "image": url_for(cover_src) if cover_src else None,
    }

    def prune(o):
        if isinstance(o, dict):
            return {k: prune(v) for k, v in o.items() if v not in (None, '')}
        return o

    return json.dumps(prune(schema), ensure_ascii=False)


def build_page(entry, slug, prev_entry=None, next_entry=None):
    """Build the full HTML page for one article."""
    title = entry.get('title', 'Article')
    desc = entry.get('desc', '')
    cover_src = entry.get('file', '')
    cover_alt = entry.get('alt', title)
    page_url = f"{DOMAIN}/{OUT_DIR}/{slug}.html"
    body_html = read_body(slug)
    json_ld = build_json_ld(entry, page_url, cover_src)

    if cover_src:
        og_image = (
            f'  <meta property="og:image" content="{esc(url_for(cover_src))}" />\n'
            f'  <meta name="twitter:image" content="{esc(url_for(cover_src))}" />\n'
        )
        twitter_card = 'summary_large_image'
        hero_html = (
            '        <figure class="article-hero">\n'
            f'          <img src="/{esc(cover_src)}" alt="{esc(cover_alt)}" '
            'decoding="async" draggable="false" />\n'
            '        </figure>\n'
        )
    else:
        og_image = ''
        twitter_card = 'summary'
        hero_html = ''

    # Meta line: category, date, read time. Any of them may be absent.
    meta_bits = [b for b in (entry.get('category'), pretty_date(entry),
                             entry.get('readTime')) if b]
    meta_html = ''
    if meta_bits:
        sep = ' <span aria-hidden="true">&middot;</span> '
        meta_html = ('        <p class="article-meta">'
                     + sep.join(esc(b) for b in meta_bits) + '</p>\n')

    # Previous / next article. The chain wraps, so there is never a dead end.
    def nav_link(target, direction):
        if not target:
            return ''
        arrow = '&#8592;' if direction == 'prev' else '&#8594;'
        label = 'Previous' if direction == 'prev' else 'Next'
        text = (f'<span class="gn-text"><span class="gn-label">{label}</span>'
                f'<span class="gn-title">{esc(target.get("title", ""))}</span></span>')
        arrow_span = f'<span class="gn-arrow" aria-hidden="true">{arrow}</span>'
        inner = (arrow_span + text) if direction == 'prev' else (text + arrow_span)
        return (f'        <a class="gear-nav-link gn-{direction}" '
                f'href="/{OUT_DIR}/{esc(target.get("slug", ""))}.html" '
                f'aria-label="{label} article: {esc(target.get("title", ""))}">'
                f'{inner}</a>\n')

    nav_html = ''
    if prev_entry or next_entry:
        nav_html = ('      <nav class="gear-nav" aria-label="Article navigation">\n'
                    f'{nav_link(prev_entry, "prev")}'
                    f'{nav_link(next_entry, "next")}'
                    '      </nav>\n')

    html_content = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{esc(title)} — Bhapstar Astrophotography</title>
  <link rel="icon" href="/images/icons/favicon-32.png" sizes="32x32" type="image/png" />
  <link rel="apple-touch-icon" href="/images/icons/apple-touch-icon.png" />
  <meta name="theme-color" content="#050414" />
  <link rel="canonical" href="{esc(page_url)}" />
  <meta name="description" content="{esc(desc[:160])}" />
  <meta name="author" content="Bhapinder Singh" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc[:160])}" />
  <meta property="og:url" content="{esc(page_url)}" />
{og_image}  <meta name="twitter:card" content="{twitter_card}" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(desc[:160])}" />
  <link rel="preconnect" href="https://static.cloudflareinsights.com" crossorigin />
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token":"b3353c7dd8764a64baee57fd09c3dbb9"}}'></script>
  <link rel="stylesheet" href="/styles.css" />

  <style>
    /* Narrower than the gear pages: this is a reading column, and a long
       measure is the quickest way to make a long article feel like work. */
    .article-page {{ max-width: 760px; margin: 40px auto; padding: 0 16px; }}
    .article-header {{ margin-bottom: 34px; }}
    .article-hero {{ margin: 0 0 26px; }}
    .article-hero img {{ width: 100%; height: auto; display: block;
                         border-radius: 16px;
                         border: 1px solid var(--line);
                         box-shadow: 0 24px 70px rgba(0,0,0,0.55),
                                     0 0 0 1px rgba(167,139,250,0.18),
                                     0 10px 44px rgba(167,139,250,0.28); }}
    html[data-theme="light"] .article-hero img {{
                         box-shadow: 0 20px 50px rgba(0,0,0,0.35),
                                     0 6px 18px rgba(0,0,0,0.18); }}
    .article-meta {{ font-size: 10.5px; letter-spacing: 0.16em;
                     text-transform: uppercase; color: var(--muted);
                     margin: 0 0 12px; }}
    .article-title {{ font-size: 30px; line-height: 1.2; margin: 0 0 12px; }}
    .article-standfirst {{ font-size: 16.5px; line-height: 1.6; color: var(--muted);
                           margin: 0; }}

    /* ── Body ── */
    .article-body {{ margin: 34px 0 10px; font-size: 15.5px; line-height: 1.75;
                     color: var(--text); }}
    .article-body h2 {{ font-size: 21px; font-weight: 600; margin: 34px 0 12px;
                        line-height: 1.3; }}
    .article-body h3 {{ font-size: 17px; font-weight: 600; margin: 24px 0 8px; }}
    .article-body p {{ margin: 13px 0; }}
    .article-body ul, .article-body ol {{ margin: 14px 0; padding-left: 22px; }}
    .article-body li {{ margin: 8px 0; }}
    .article-body code {{ font-size: 0.92em; padding: 2px 6px; border-radius: 5px;
                          background: var(--soft); border: 1px solid var(--line); }}
    .article-body a {{ color: var(--accent); text-decoration: none;
                       border-bottom: 1px solid rgba(167,139,250,0.35); }}
    .article-body a:hover, .article-body a:focus-visible {{
                       border-bottom-color: var(--accent); }}
    html[data-theme="light"] .article-body a {{ color: #6d4bd8; }}

    /* ── Tables ── */
    .article-body table {{ width: 100%; border-collapse: collapse; margin: 20px 0;
                           font-size: 14px; }}
    .article-body th, .article-body td {{ padding: 10px 12px; text-align: left;
                           border-bottom: 1px solid var(--line);
                           vertical-align: top; }}
    .article-body th {{ background: var(--soft); font-weight: 600;
                        font-size: 12px; letter-spacing: 0.06em;
                        text-transform: uppercase; color: var(--muted); }}
    @media (max-width: 560px) {{
      .article-body table {{ font-size: 13px; }}
      .article-body th, .article-body td {{ padding: 8px 8px; }}
    }}

    /* ── Hand-drawn figures ──
       The SVG is authored in the content fragment and inherits the site's
       theme variables, so it follows light/dark without a second asset. */
    .article-fig {{ margin: 26px 0; padding: 14px 14px 10px; border-radius: 12px;
                    background: var(--soft); border: 1px solid var(--line); }}
    .article-fig svg {{ width: 100%; height: auto; display: block; }}
    .article-fig figcaption {{ margin-top: 12px; font-size: 12.5px; line-height: 1.55;
                    color: var(--muted); }}
    .article-fig figcaption a {{ color: var(--accent); text-decoration: none; }}

    /* ── Photo and video figures ──
       Photos use the same frame as the hand-drawn figures. Videos are Vimeo
       embeds held in a 16:9 box so the page never reflows while the iframe
       loads. Use .article-figrow to sit two photos side by side, which
       collapses to a single column on narrow screens. */
    .article-fig img {{ width: 100%; height: auto; display: block;
                        border-radius: 9px; }}
    .article-figrow {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}

    /* ── Floated photo figures ──
       .fig-float sits a photo in the text column at a readable size and lets
       the prose wrap around it, instead of every photo running full width.
       Add .fig-left to flip the side. Collapses to full width on narrow
       screens, where wrapping around a 300px image would leave unreadable
       ribbons of text. */
    .article-fig.fig-float {{ float: right; width: 296px;
                              margin: 6px 0 18px 24px; }}
    .article-fig.fig-float.fig-left {{ float: left;
                                       margin: 6px 24px 18px 0; }}
    .article-body h2, .article-body h3 {{ clear: both; }}
    .article-video {{ position: relative; width: 100%; padding-top: 56.25%;
                      border-radius: 9px; overflow: hidden;
                      background: rgba(0,0,0,0.35); }}
    .article-video iframe {{ position: absolute; inset: 0; width: 100%;
                             height: 100%; border: 0; }}

    /* ── Click to enlarge ──
       Not the gallery lightbox: no chrome, no navigation, no like button.
       Just a larger copy of the same file, dismissed by clicking anywhere. */
    .article-fig img {{ cursor: zoom-in; }}
    .img-zoom {{ position: fixed; inset: 0; z-index: 9999; display: none;
                 align-items: center; justify-content: center; padding: 24px;
                 background: rgba(4,3,16,0.88); cursor: zoom-out; }}
    .img-zoom.open {{ display: flex; }}
    .img-zoom img {{ max-width: min(92vw, 900px); max-height: 92vh;
                     border-radius: 10px;
                     box-shadow: 0 20px 60px rgba(0,0,0,0.55); }}
    @media (max-width: 560px) {{
      .article-figrow {{ grid-template-columns: 1fr; }}
    }}

    /* ── Dated event callout ──
       Deliberately loud. It is the one part of the page with a deadline. */
    .event-callout {{ margin: 0 0 30px; padding: 18px 20px; border-radius: 14px;
                      border: 1px solid rgba(167,139,250,0.45);
                      background: linear-gradient(135deg,
                                  rgba(167,139,250,0.14),
                                  rgba(96,165,250,0.10));
                      box-shadow: 0 8px 30px rgba(167,139,250,0.14); }}
    .event-callout .ec-kicker {{ margin: 0 0 6px; font-size: 10px;
                      letter-spacing: 0.2em; text-transform: uppercase;
                      color: var(--accent); }}
    .event-callout .ec-title {{ margin: 0 0 10px; font-size: 17px; font-weight: 600;
                      line-height: 1.35; color: var(--text); }}
    .event-callout .ec-body {{ margin: 0; font-size: 14.5px; line-height: 1.65;
                      color: var(--text); opacity: 0.92; }}

    /* Previous / next reuses the gear page's chrome so the two section types
       feel like the same site. */
    .gear-nav {{ display: flex; gap: 10px; margin-bottom: 22px; align-items: stretch; }}
    .gear-nav-link {{ display: flex; align-items: center; gap: 10px;
                      flex: 1 1 0; min-width: 0; padding: 10px 14px;
                      border-radius: 11px; text-decoration: none;
                      color: var(--text); border: 1px solid var(--line);
                      background: var(--soft);
                      transition: border-color 200ms ease, background 200ms ease,
                                  transform 200ms ease; }}
    .gear-nav-link:hover, .gear-nav-link:focus-visible {{
                      border-color: var(--accent); background: var(--glow2);
                      transform: translateY(-1px); }}
    .gn-next {{ justify-content: flex-end; text-align: right; }}
    .gn-arrow {{ flex: 0 0 auto; font-size: 16px; line-height: 1; color: var(--accent); }}
    .gn-text {{ display: flex; flex-direction: column; gap: 2px; min-width: 0; }}
    .gn-label {{ font-size: 9.5px; letter-spacing: 0.16em; text-transform: uppercase;
                 color: var(--muted); }}
    .gn-title {{ font-size: 13px; font-weight: 500; line-height: 1.25;
                 overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}

    .article-back {{ display: inline-flex; align-items: center; gap: 7px;
                     margin-top: 36px; padding-top: 22px;
                     border-top: 1px solid var(--line);
                     font-size: 13px; color: var(--muted); text-decoration: none; }}
    .article-back:hover {{ color: var(--accent); }}

    @media (max-width: 768px) {{
      .article-page {{ margin: 24px auto; padding: 0 14px; }}
      .article-title {{ font-size: 24px; }}
      .article-standfirst {{ font-size: 15px; }}
      .gn-label {{ display: none; }}
    }}
  </style>

  <script type="application/ld+json">
{json_ld}
  </script>
</head>
<body>

<!-- ── Header (injected by partials.js) ── -->
<div id="siteHeader"></div>

<main>
  <section class="section">
    <div class="wrap article-page">
{nav_html}
      <div class="article-header">
{hero_html}{meta_html}        <h1 class="article-title">{esc(title)}</h1>
        <p class="article-standfirst">{esc(desc)}</p>
      </div>

      <div class="article-body">
{body_html}
      </div>

      <a class="article-back" href="/articles.html">&#8592; All articles</a>
    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

  <script src="/partials/partials.js"></script>
  <script src="/protect-images.js"></script>
  <script>
  /* Click any article photo to see it larger. protect-images.js does not
     intercept plain clicks, so this needs no cooperation from it. */
  (function () {{
    var ov = document.createElement('div');
    ov.className = 'img-zoom';
    ov.setAttribute('role', 'dialog');
    ov.setAttribute('aria-modal', 'true');
    var big = document.createElement('img');
    ov.appendChild(big);
    document.body.appendChild(ov);

    document.addEventListener('click', function (e) {{
      var img = e.target.closest && e.target.closest('.article-fig img');
      if (img) {{
        big.src = img.currentSrc || img.src;
        big.alt = img.alt || '';
        ov.classList.add('open');
        return;
      }}
      if (ov.classList.contains('open')) ov.classList.remove('open');
    }});

    document.addEventListener('keydown', function (e) {{
      if (e.key === 'Escape') ov.classList.remove('open');
    }});
  }})();
  </script>
</body>
</html>'''

    return html_content


def main():
    with open(DATA, 'r', encoding='utf-8') as f:
        items = json.load(f)

    # A hidden entry is staged in site-data.json but not ready to publish. It
    # gets no tile and no page.
    articles = [e for e in items
                if e.get('section') == 'article' and e.get('slug')
                and not e.get('hidden')]

    # Newest first, matching the order articles.html renders tiles in, so the
    # previous/next chain agrees with what the reader just clicked through.
    def sort_key(e):
        try:
            return datetime.strptime(e.get('date', ''), "%d-%m-%Y")
        except (TypeError, ValueError):
            return datetime.min
    articles.sort(key=sort_key, reverse=True)

    os.makedirs(OUT_DIR, exist_ok=True)

    n = len(articles)
    generated_slugs = set()
    for i, entry in enumerate(articles):
        slug = entry['slug']
        generated_slugs.add(slug)
        prev_entry = articles[(i - 1) % n] if n > 1 else None
        next_entry = articles[(i + 1) % n] if n > 1 else None
        filename = os.path.join(OUT_DIR, f"{slug}.html")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(build_page(entry, slug, prev_entry, next_entry))
        print(f"✓ {filename}")

    # Clean up stale files (whose slug is no longer in site-data.json)
    if os.path.isdir(OUT_DIR):
        for filename in os.listdir(OUT_DIR):
            if not filename.endswith('.html'):
                continue
            if filename[:-5] not in generated_slugs:
                os.remove(os.path.join(OUT_DIR, filename))
                print(f"✗ deleted stale {OUT_DIR}/{filename}")

    print(f"\nGenerated {len(generated_slugs)} article pages.")


if __name__ == '__main__':
    main()
