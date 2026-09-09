#!/usr/bin/env python3
"""
Generates one REAL, indexable page per gear item in site-data.json, under
gear/<slug>.html. Mirrors the logic of generate-share-pages.py but for gear.

Each page includes:
  - Hero image (first image from entry.images)
  - Fixed-height carousel: arrows, in-stage thumbnails, keyboard, swipe
  - Review prose (read from content/gear/<slug>.html if it exists, else placeholder)
  - Buy links from the entry's buy array
  - JSON-LD Article schema
  - Canonical URL pointing at itself
  - OG tags for social sharing

Pages use the site's shared chrome: /styles.css, header/footer injected by
/partials/partials.js (root-absolute, so it works from /gear/), and
/protect-images.js for the usual right-click/drag speed bumps.

Idempotent: rewrites every page each run, and deletes any stale gear/*.html
whose slug is no longer in site-data.json.

    python generate-gear-pages.py
"""

import html
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import quote

# Shared with generate-article-pages.py. sys.path[0] is this script's own
# folder, so scripts/glossary.py is importable without any path juggling.
from glossary import (GLOSSARY_CSS, GLOSSARY_JS, annotate_glossary,
                      load_glossary)

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT_DIR = "gear"
REVIEWS_DIR = "content/gear"

# Retailer links are suppressed until there is an actual arrangement with
# each shop. The URLs stay in site-data.json, so flipping this back to True
# restores every link at once. No data is thrown away.
SHOW_BUY_LINKS = True
SITE_NAME = "Bhapstar Astrophotography"
# Stable date. Bump by hand when a review has a real content change; do NOT
# derive from "now", or every workflow run restamps all 12 pages.
PUBLISHED_DATE = "2026-07-30"

def esc(s):
    """Escape for HTML attribute/text context."""
    return html.escape(str(s or ''), quote=True)

def thumb_for(file):
    """Convert images/gear/X.webp -> images/gear/thumbs/X.webp."""
    if not file:
        return None
    return file.replace('/gear/', '/gear/thumbs/')

def url_for(path):
    """Full URL for a file path."""
    return DOMAIN + '/' + path.lstrip('/')

def read_review(slug):
    """Read review fragment from content/gear/<slug>.html, or return placeholder."""
    path = os.path.join(REVIEWS_DIR, f"{slug}.html")
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<p><em>Review coming soon.</em></p>"

def build_json_ld(entry, page_url, cover_src):
    """Build Article + Product schema."""
    iso_date = PUBLISHED_DATE
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": entry.get('title', ''),
        "description": entry.get('desc', ''),
        "author": {
            "@type": "Person",
            "name": "Bhapinder Singh",
            "url": DOMAIN
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": DOMAIN
        },
        "datePublished": iso_date,
        "dateModified": iso_date,
        "mainEntity": {
            "@type": "Product",
            "name": entry.get('title', ''),
            "image": url_for(cover_src) if cover_src else None,
            "description": entry.get('desc', '')
        },
        "image": url_for(cover_src) if cover_src else None
    }
    def prune(o):
        if isinstance(o, dict):
            return {k: prune(v) for k, v in o.items() if v is not None}
        return o

    return json.dumps(prune(schema), ensure_ascii=False)

def build_page(entry, slug, prev_entry=None, next_entry=None, glossary=None):
    """Build the full HTML page for one gear item."""
    title = entry.get('title', 'Gear')
    desc = entry.get('desc', '')
    images = [im for im in (entry.get('images') or [])
              if im.get('file') and os.path.isfile(im['file'])]
    cover = images[0] if images else {}
    cover_src = cover.get('file', '')
    cover_alt = cover.get('alt', title)
    buy_links = entry.get('buy', []) if SHOW_BUY_LINKS else []
    
    page_url = f"{DOMAIN}/{OUT_DIR}/{slug}.html"
    review_html = read_review(slug)

    # Glossary explainers on the first mention of each technical word. The
    # description is passed in alongside the review, in reading order, so a
    # word used in both is marked once rather than twice. It is escaped first
    # and inserted raw below, because the marks are HTML. site-data.json is
    # never touched: the same desc string also feeds the meta description,
    # og:description, the JSON-LD and the index tiles, which must stay plain.
    (desc_html, review_html), gloss_count = annotate_glossary(
        [esc(desc), review_html], slug, glossary or [])

    # A page with none carries neither the styles nor the script.
    gloss_css = GLOSSARY_CSS if gloss_count else ''
    gloss_js = GLOSSARY_JS if gloss_count else ''
    build_page.last_gloss_count = gloss_count
    json_ld = build_json_ld(entry, page_url, cover_src)
    
    if cover_src:
        og_image = (
            f'  <meta property="og:image" content="{esc(url_for(cover_src))}" />\n'
            f'  <meta name="twitter:image" content="{esc(url_for(cover_src))}" />\n'
        )
        twitter_card = 'summary_large_image'
    else:
        og_image = ''
        twitter_card = 'summary'

    # ── Carousel ──
    # Every slide is absolutely positioned inside a stage with a fixed
    # aspect-ratio, and images use object-fit: contain. That means the stage
    # never changes height, so portrait and landscape shots can sit in the
    # same carousel without the page jumping when you change slide.
    carousel_html = ''
    if images:
        slides = ''
        for i, img in enumerate(images):
            slides += (
                f'            <img class="gc-slide{" is-active" if i == 0 else ""}" '
                f'data-idx="{i}" src="/{esc(img["file"])}" '
                f'alt="{esc(img.get("alt") or title)}" '
                f'{"" if i == 0 else "loading=\"lazy\" "}decoding="async" '
                f'draggable="false" />\n'
            )

        # Arrows and thumbnails are only worth rendering for multi-image items.
        arrows = ''
        thumbs = ''
        counter = ''
        if len(images) > 1:
            arrows = (
                '            <button class="gc-arrow gc-prev" type="button" '
                'aria-label="Previous image">\n'
                '              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
                'aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>\n'
                '            </button>\n'
                '            <button class="gc-arrow gc-next" type="button" '
                'aria-label="Next image">\n'
                '              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
                'aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>\n'
                '            </button>\n'
            )
            counter = (
                f'            <div class="gc-counter" aria-hidden="true">'
                f'<span class="gc-current">1</span> / {len(images)}</div>\n'
            )
            tlist = ''
            for i, img in enumerate(images):
                t = thumb_for(img['file'])
                if not os.path.isfile(t):
                    t = img['file']
                tlist += (
                    f'                <button class="gc-thumb'
                    f'{" is-active" if i == 0 else ""}" type="button" data-idx="{i}" '
                    f'aria-label="Go to image {i + 1}">'
                    f'<img src="/{esc(t)}" alt="" loading="lazy" decoding="async" />'
                    f'</button>\n'
                )
            thumbs = (
                '            <div class="gc-thumbs" role="tablist" '
                'aria-label="Choose image">\n'
                f'{tlist}'
                '            </div>\n'
            )

        carousel_html = (
            '        <div class="gear-carousel" id="gearCarousel" '
            f'data-count="{len(images)}" tabindex="0" role="group" '
            'aria-label="Product images">\n'
            '          <div class="gc-stage">\n'
            f'{slides}'
            f'{arrows}'
            f'{counter}'
            f'{thumbs}'
            '          </div>\n'
            '        </div>\n'
        )

    # Previous / next item. Labelled with the item names so they cannot be
    # confused with the carousel's image arrows just below. The chain wraps, so
    # there is never a dead end, and hidden items are already excluded.
    def nav_link(target, direction):
        if not target:
            return ''
        arrow = '&#8592;' if direction == 'prev' else '&#8594;'
        label = 'Previous' if direction == 'prev' else 'Next'
        inner = (f'<span class="gn-arrow" aria-hidden="true">{arrow}</span>'
                 f'<span class="gn-text"><span class="gn-label">{label}</span>'
                 f'<span class="gn-title">{esc(target.get("title", ""))}</span></span>')
        if direction == 'next':
            inner = (f'<span class="gn-text"><span class="gn-label">{label}</span>'
                     f'<span class="gn-title">{esc(target.get("title", ""))}</span></span>'
                     f'<span class="gn-arrow" aria-hidden="true">{arrow}</span>')
        return (f'        <a class="gear-nav-link gn-{direction}" '
                f'href="/{OUT_DIR}/{esc(target.get("slug", ""))}.html" '
                f'aria-label="{label} item: {esc(target.get("title", ""))}">'
                f'{inner}</a>\n')

    nav_html = ''
    if prev_entry or next_entry:
        nav_html = (
            '      <nav class="gear-nav" aria-label="Gear navigation">\n'
            f'{nav_link(prev_entry, "prev")}'
            f'{nav_link(next_entry, "next")}'
            '      </nav>\n'
        )

    # Render buy buttons
    buy_html = ''
    has_affiliate = any(b.get('affiliate') for b in buy_links)
    if buy_links:
        buy_html = '      <div class="gear-buy">\n'
        buy_html += '        <p class="gear-buy-label">Where to buy</p>\n'
        buy_html += '        <div class="gear-buy-list">\n'
        for b in buy_links:
            retailer = esc(b.get('retailer', ''))
            url = esc(b.get('url', '#'))
            is_aff = b.get('affiliate')
            rel = 'sponsored noopener noreferrer' if is_aff else 'noopener noreferrer'
            buy_html += (
                f'          <a class="gear-buy-link" href="{url}" target="_blank" '
                f'rel="{rel}">{retailer} <svg viewBox="0 0 12 12" fill="none" '
                f'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
                f'stroke-linejoin="round" aria-hidden="true">'
                f'<path d="M3.5 8.5L8.5 3.5"/><path d="M4.5 3.5h4v4"/></svg></a>\n'
            )
        buy_html += '        </div>\n'
        if has_affiliate:
            # Amazon's Operating Agreement requires this exact sentence on any
            # page carrying their links. Only added when one is present.
            has_amazon = any(
                b.get('affiliate') and re.match(
                    r'^https?://([^/]*\.)?(amazon|amzn)(\.|/|$)',
                    (b.get('url') or '').strip(), re.I)
                for b in buy_links
            )
            note = ('Some links above are affiliate links. '
                    'If you buy through them I may earn a small commission, at no extra cost '
                    'to you. It does not affect which gear I use or recommend.')
            if has_amazon:
                note += ' As an Amazon Associate I earn from qualifying purchases.'
            buy_html += f'        <p class="gear-buy-note">{note}</p>\n'
        buy_html += '      </div>\n'
    
    html_content = f'''<!doctype html>
<!-- Generated by scripts/generate-gear-pages.py. Do not edit this file by
     hand. Every build overwrites it. Edit content/gear/[slug].html instead. -->
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{esc(title)} | Bhapstar</title>
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
  
  <!-- Page CSS lives in /styles.css under "PAGE: Gear detail pages". -->

  <script type="application/ld+json">
{json_ld}
  </script>
</head>
<body class="page-gear-detail">

<!-- ── Header (injected by partials.js) ── -->
<div id="siteHeader"></div>

<main>
  <section class="section">
    <div class="wrap gear-page">
{nav_html}

      <div class="gear-header">
{carousel_html}        <h1 class="gear-title">{esc(title)}</h1>
        <p class="gear-desc">{desc_html}</p>
      </div>


      <div class="gear-review">
{review_html}      </div>

{buy_html}    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

  <script src="/partials/partials.js"></script>
  <script src="/protect-images.js"></script>
  <script>
    /* Carousel: arrows, thumbnails, keyboard and touch swipe.
       All slides are already in the DOM, so changing image is only a class
       swap. Nothing is resized or reloaded, so the page cannot shift. */
    (function () {{
      var root = document.getElementById('gearCarousel');
      if (!root) return;

      var slides = Array.prototype.slice.call(root.querySelectorAll('.gc-slide'));
      var thumbs = Array.prototype.slice.call(root.querySelectorAll('.gc-thumb'));
      var counter = root.querySelector('.gc-current');
      var stage = root.querySelector('.gc-stage');
      if (slides.length < 2) return;

      var index = 0;

      function show(next) {{
        var n = (next + slides.length) % slides.length;
        if (n === index) return;
        slides[index].classList.remove('is-active');
        slides[n].classList.add('is-active');
        if (thumbs[index]) thumbs[index].classList.remove('is-active');
        if (thumbs[n]) thumbs[n].classList.add('is-active');
        index = n;
        if (counter) counter.textContent = String(n + 1);
        if (thumbs[n] && thumbs[n].scrollIntoView) {{
          thumbs[n].scrollIntoView({{ block: 'nearest', inline: 'nearest' }});
        }}
      }}

      var prev = root.querySelector('.gc-prev');
      var next = root.querySelector('.gc-next');
      if (prev) prev.addEventListener('click', function () {{ show(index - 1); }});
      if (next) next.addEventListener('click', function () {{ show(index + 1); }});

      thumbs.forEach(function (t) {{
        t.addEventListener('click', function () {{
          show(Number(t.getAttribute('data-idx')));
        }});
      }});

      root.addEventListener('keydown', function (e) {{
        if (e.key === 'ArrowLeft') {{ e.preventDefault(); show(index - 1); }}
        else if (e.key === 'ArrowRight') {{ e.preventDefault(); show(index + 1); }}
      }});

      /* Touch swipe. Only treat it as a swipe if the gesture is clearly
         horizontal, so vertical page scrolling still works normally. */
      var x0 = null, y0 = null;
      stage.addEventListener('touchstart', function (e) {{
        var t = e.changedTouches[0];
        x0 = t.clientX; y0 = t.clientY;
      }}, {{ passive: true }});
      stage.addEventListener('touchend', function (e) {{
        if (x0 === null) return;
        var t = e.changedTouches[0];
        var dx = t.clientX - x0, dy = t.clientY - y0;
        if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {{
          show(dx < 0 ? index + 1 : index - 1);
        }}
        x0 = null; y0 = null;
      }}, {{ passive: true }});
    }})();
  </script>
{gloss_js}
</body>
</html>'''
    
    return html_content


# ---------------------------------------------------------------------------
# Tile grid inside gear.html.
#
# gear.html builds its grid client-side from site-data.json, which means the
# HTML that ships contains no link to any gear page at all. A crawler that
# does not run JavaScript sees an index that links nowhere, and a reader on a
# slow connection sees skeletons. articles.html solved this by writing real
# tiles at build time and letting the script re-render identical markup once
# the JSON lands; this does the same for gear.
#
# The markup below must stay in step with the template in gear.html's own
# render(). If the card structure changes there, change it here too, or the
# tiles will visibly reflow the moment the JSON arrives.
# ---------------------------------------------------------------------------
INDEX_PAGE = "gear.html"
TILES_START = "<!-- GEAR-TILES:START -->"
TILES_END = "<!-- GEAR-TILES:END -->"

ON_ARROW = ('<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true"><path d="M2.5 6h7"/><path d="M6.5 3l3 3-3 3"/></svg>')

OUT_ARROW = ('<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" '
             'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
             'aria-hidden="true"><path d="M4 2.5h5.5V8"/><path d="M9.5 2.5 2.5 9.5"/></svg>')


def cover_for(entry):
    """First image on the entry, matching getList()/getCover() in gear.html."""
    alt_fallback = entry.get('alt') or entry.get('title') or ''
    images = entry.get('images') or []
    if images:
        first = images[0]
        return first.get('file', ''), (first.get('alt') or alt_fallback)
    files = entry.get('files') or []
    if files:
        return files[0], alt_fallback
    return entry.get('file', ''), alt_fallback


def buy_links_for(entry):
    """Same filter gear.html applies: a retailer name and a real http(s) URL."""
    if not SHOW_BUY_LINKS:
        return []
    out = []
    for b in entry.get('buy') or []:
        url = (b.get('url') or '').strip() if isinstance(b, dict) else ''
        if not b or not isinstance(b, dict) or not b.get('retailer'):
            continue
        if not re.match(r'^https?://', url, re.I):
            continue
        out.append(b)
    return out


def build_tile(entry, eager=False):
    slug = entry['slug']
    page_url = f"/{OUT_DIR}/{quote(slug)}.html"
    cover, alt = cover_for(entry)
    thumb = thumb_for(cover) or ''

    # The first tile is above the fold on every screen, so it loads eagerly.
    # Everything below it waits, exactly as the article grid does.
    loading = 'eager' if eager else 'lazy'

    buys = ''.join(
        f'<a class="card-buy" href="{esc((b.get("url") or "").strip())}" '
        f'target="_blank" rel="'
        + ('sponsored noopener noreferrer' if b.get('affiliate') is True
           else 'noopener noreferrer')
        + f'">{esc(b.get("retailer"))}{OUT_ARROW}</a>'
        for b in buy_links_for(entry)
    )
    buy_block = f'<div class="card-buys">{buys}</div>' if buys else ''

    return (
        f'        <article class="card">\n'
        f'          <a class="card-hit" href="{esc(page_url)}" tabindex="-1" '
        f'aria-hidden="true"></a>\n'
        f'          <img src="{esc(thumb)}" alt="{esc(alt)}" '
        f'loading="{loading}" decoding="async">\n'
        f'          <div class="cap">\n'
        f'            <div class="t">{esc(entry.get("title", ""))}</div>\n'
        f'            <div class="d">{esc(entry.get("desc", ""))}</div>\n'
        f'            <div class="card-acts">\n'
        f'              <a class="card-writeup" href="{esc(page_url)}">'
        f'Read the full write-up{ON_ARROW}</a>\n'
        f'              {buy_block}\n'
        f'            </div>\n'
        f'          </div>\n'
        f'        </article>\n'
    )


def write_tiles(gear_items):
    """Rewrite the marked tile block inside gear.html. Leaves the rest alone."""
    if not os.path.exists(INDEX_PAGE):
        print(f"  ! {INDEX_PAGE} not found, tile block skipped")
        return
    page = open(INDEX_PAGE, encoding='utf-8').read()
    if TILES_START not in page or TILES_END not in page:
        print(f"  ! markers missing in {INDEX_PAGE}, tile block skipped")
        return

    tiles = ''.join(build_tile(e, eager=(i == 0))
                    for i, e in enumerate(gear_items))
    new_block = f"{TILES_START}\n{tiles}        {TILES_END}"
    pattern = re.compile(re.escape(TILES_START) + r".*?" + re.escape(TILES_END),
                         re.DOTALL)
    updated = pattern.sub(lambda _: new_block, page, count=1)
    if updated != page:
        open(INDEX_PAGE, 'w', encoding='utf-8').write(updated)
    print(f"\u2713 {INDEX_PAGE}  ({len(gear_items)} tile(s) written)")


def main():
    # Load data
    with open(DATA, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    # Filter: all gear items
    # A hidden entry is one that is staged in site-data.json but not ready to
    # publish (usually waiting on photos). It gets no tile and no page.
    gear_items = [e for e in items
                  if e.get('section') == 'gear' and e.get('slug')
                  and not e.get('hidden')]
    
    # Create output dir
    os.makedirs(OUT_DIR, exist_ok=True)

    glossary = load_glossary()
    
    # Generate pages for every gear item. Previous/next follow the order of
    # site-data.json and wrap around, so the chain has no dead ends. With a
    # single visible item there are no neighbours and the bar is omitted.
    n = len(gear_items)
    generated_slugs = set()
    gloss_total = 0
    for i, entry in enumerate(gear_items):
        slug = entry['slug']
        generated_slugs.add(slug)
        prev_entry = gear_items[(i - 1) % n] if n > 1 else None
        next_entry = gear_items[(i + 1) % n] if n > 1 else None
        filename = os.path.join(OUT_DIR, f"{slug}.html")
        page_html = build_page(entry, slug, prev_entry, next_entry, glossary)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_html)
        marked = getattr(build_page, 'last_gloss_count', 0)
        gloss_total += marked
        print(f"✓ {filename}" + (f"  ({marked} explained)" if marked else ""))
    
    # Clean up stale files (whose slug is no longer in site-data.json)
    for filename in os.listdir(OUT_DIR):
        if not filename.endswith('.html'):
            continue
        filepath = os.path.join(OUT_DIR, filename)
        slug = filename[:-5]  # strip .html
        if slug not in generated_slugs:
            os.remove(filepath)
            print(f"✗ deleted stale {filepath}")
    
    write_tiles(gear_items)

    print(f"\nGenerated {len(generated_slugs)} gear pages, "
          f"{gloss_total} glossary explainers.")

if __name__ == '__main__':
    main()
