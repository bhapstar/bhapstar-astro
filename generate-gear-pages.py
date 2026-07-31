#!/usr/bin/env python3
"""
Generates one REAL, indexable page per gear item in site-data.json, under
gear/<slug>.html. Mirrors the logic of generate-share-pages.py but for gear.

Each page includes:
  - Hero image (first image from entry.images)
  - Fixed-height carousel: arrows, in-stage thumbnails, keyboard, swipe
  - Review prose (read from gear-reviews/<slug>.html if it exists, else placeholder)
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
from datetime import datetime, timezone

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT_DIR = "gear"
REVIEWS_DIR = "gear-reviews"

# Retailer links are suppressed until there is an actual arrangement with
# each shop. The URLs stay in site-data.json, so flipping this back to True
# restores every link at once. No data is thrown away.
SHOW_BUY_LINKS = False
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
    """Read review fragment from gear-reviews/<slug>.html, or return placeholder."""
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

def build_page(entry, slug, prev_entry=None, next_entry=None):
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
            buy_html += (
                '        <p class="gear-buy-note">Some links above are affiliate links. '
                'If you buy through them I may earn a small commission, at no extra cost '
                'to you. It does not affect which gear I use or recommend.</p>\n'
            )
        buy_html += '      </div>\n'
    
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
    .gear-page {{ max-width: 900px; margin: 40px auto; padding: 0 16px; }}
    .gear-header {{ margin-bottom: 40px; }}
    /* ── Carousel ──
       The stage has a fixed aspect-ratio and slides are absolutely
       positioned with object-fit: contain, so its height never changes.
       Mixing portrait and landscape shots cannot shift the page. */
    .gear-carousel {{ margin-bottom: 42px; outline: none; }}
    .gear-carousel:focus-visible .gc-stage {{ border-color: var(--accent); }}
    .gc-stage {{ position: relative; width: 100%; aspect-ratio: 3 / 2;
                 border-radius: 16px; overflow: hidden;
                 background: var(--bg2);
                 border: 1px solid var(--line);
                 /* Same lift as the gallery share pages. On #050414 a plain
                    black shadow is invisible, so the image is raised with a
                    deep shadow plus a violet bloom and a faint blue rim. */
                 box-shadow: 0 24px 70px rgba(0,0,0,0.55),
                             0 0 0 1px rgba(167,139,250,0.18),
                             0 10px 44px rgba(167,139,250,0.28),
                             0 4px 18px rgba(96,165,250,0.16); }}
    /* Light theme: a soft, clearly visible drop shadow instead of the bloom.
       Scoped to box-shadow only, so nothing else about the stage is touched. */
    html[data-theme="light"] .gc-stage {{
                 box-shadow: 0 20px 50px rgba(0,0,0,0.35),
                             0 6px 18px rgba(0,0,0,0.18); }}
    .gc-slide {{ position: absolute; inset: 0; width: 100%; height: 100%;
                 object-fit: contain; display: block;
                 opacity: 0; transition: opacity 280ms ease;
                 pointer-events: none; }}
    .gc-slide.is-active {{ opacity: 1; }}

    /* Overlay controls deliberately keep a dark scrim in both themes:
       they sit on top of photographs, not on the page background. */
    .gc-arrow {{ position: absolute; top: 50%; transform: translateY(-50%);
                 width: 40px; height: 40px; display: grid; place-items: center;
                 border-radius: 50%; cursor: pointer; z-index: 3;
                 color: rgba(255,255,255,0.94);
                 background: rgba(8,6,26,0.62);
                 border: 1px solid rgba(167,139,250,0.28);
                 backdrop-filter: blur(6px);
                 transition: background 200ms ease, border-color 200ms ease,
                             opacity 200ms ease; }}
    .gc-arrow:hover, .gc-arrow:focus-visible {{ background: rgba(96,165,250,0.24);
                 border-color: rgba(96,165,250,0.6); color: #fff; }}
    .gc-arrow svg {{ width: 20px; height: 20px; }}
    .gc-prev {{ left: 12px; }}
    .gc-next {{ right: 12px; }}

    .gc-counter {{ position: absolute; top: 12px; right: 12px; z-index: 3;
                   padding: 4px 10px; border-radius: 999px;
                   font-size: 11.5px; letter-spacing: 0.06em;
                   color: rgba(255,255,255,0.9);
                   background: rgba(8,6,26,0.62);
                   border: 1px solid rgba(167,139,250,0.22);
                   backdrop-filter: blur(6px); }}

    /* Thumbnails sit inside the stage, along the bottom. */
    .gc-thumbs {{ position: absolute; left: 0; right: 0; bottom: 0; z-index: 3;
                  display: flex; gap: 8px; justify-content: center;
                  padding: 10px 12px; overflow-x: auto;
                  scrollbar-width: none;
                  background: linear-gradient(to top,
                              rgba(5,4,20,0.82), rgba(5,4,20,0)); }}
    .gc-thumbs::-webkit-scrollbar {{ display: none; }}
    .gc-thumb {{ flex: 0 0 auto; width: 56px; height: 40px; padding: 0;
                 border-radius: 7px; overflow: hidden; cursor: pointer;
                 background: rgba(8,6,26,0.6);
                 border: 2px solid rgba(255,255,255,0.22);
                 opacity: 0.62;
                 transition: opacity 200ms ease, border-color 200ms ease,
                             transform 200ms ease; }}
    .gc-thumb img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .gc-thumb:hover, .gc-thumb:focus-visible {{ opacity: 1;
                 border-color: rgba(96,165,250,0.8); }}
    .gc-thumb.is-active {{ opacity: 1; border-color: #a78bfa;
                 transform: translateY(-2px); }}

    @media (prefers-reduced-motion: reduce) {{
      .gc-slide {{ transition: none; }}
    }}
    .gear-title {{ font-size: 32px; font-weight: 600; margin: 0 0 16px; 
                    background: linear-gradient(90deg, #a78bfa, #60a5fa, #f472b6, #60a5fa, #a78bfa);
                    background-size: 300% 100%;
                    -webkit-background-clip: text;
                    background-clip: text;
                    -webkit-text-fill-color: transparent;
                    animation: gradientRoll 4s linear infinite reverse; }}
    .gear-desc {{ font-size: 16px; line-height: 1.6; color: var(--muted); margin: 0; }}
    .gear-review {{ margin: 40px 0; font-size: 15px; line-height: 1.7;
                    color: var(--text); }}
    .gear-review h2 {{ font-size: 20px; font-weight: 600; margin: 24px 0 12px;
                       color: var(--text); }}
    .gear-review h3 {{ font-size: 17px; font-weight: 600; margin: 18px 0 10px;
                       color: var(--text); }}
    .gear-review p {{ margin: 12px 0; }}
    .gear-review ul, .gear-review ol {{ margin: 12px 0; padding-left: 22px; }}
    .gear-review li {{ margin: 6px 0; }}
    /* Links carry an underline as well as colour, so they stay identifiable
       without relying on hue alone. */
    .gear-review a {{ color: var(--accent); text-decoration: none;
                      border-bottom: 1px solid var(--line);
                      transition: border-color 180ms ease, color 180ms ease; }}
    .gear-review a:hover, .gear-review a:focus-visible {{
                      border-bottom-color: var(--accent); }}
    /* The dark-theme violet only reaches 2.3:1 on the light background, which
       is washed out at body-text size. A darker shade of the same hue clears
       4.5:1. Colour only, so nothing else about the link changes. */
    html[data-theme="light"] .gear-review a {{ color: #6d4bd8; }}
    html[data-theme="light"] .gear-review a:hover,
    html[data-theme="light"] .gear-review a:focus-visible {{
                      border-bottom-color: #6d4bd8; }}
    /* Passband diagrams: drawn in-page as SVG rather than lifted from a
       manufacturer's datasheet, so they follow the theme and can be corrected. */
    .passband-fig {{ margin: 22px 0; padding: 14px 14px 10px; border-radius: 12px;
                     background: var(--soft); border: 1px solid var(--line); }}
    .passband-fig svg {{ width: 100%; height: auto; display: block; }}
    .passband-fig figcaption {{ margin-top: 10px; font-size: 12px; line-height: 1.5;
                                color: var(--muted); }}
    .gear-review table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    .gear-review table td, .gear-review table th {{ padding: 10px; text-align: left;
                                                     border-bottom: 1px solid var(--line); }}
    .gear-review table th {{ background: var(--soft); font-weight: 600; }}
    .gear-buy {{ margin: 32px 0; padding-top: 24px; border-top: 1px solid var(--line); }}
    .gear-buy-label {{ font-size: 10.5px; letter-spacing: 0.18em; text-transform: uppercase;
                       color: var(--muted); margin: 0 0 12px; }}
    .gear-buy-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .gear-buy-link {{ display: inline-flex; align-items: center; gap: 7px;
                      padding: 10px 14px; border-radius: 11px; font-size: 13px; font-weight: 500;
                      text-decoration: none; color: var(--text);
                      border: 1px solid var(--line);
                      background: var(--soft);
                      transition: all 200ms ease; }}
    .gear-buy-link:hover, .gear-buy-link:focus-visible {{ color: #fff;
                      border-color: rgba(96,165,250,0.55); background: rgba(96,165,250,0.14);
                      transform: translateY(-2px); }}
    .gear-buy-link svg {{ width: 11px; height: 11px; flex-shrink: 0; opacity: 0.6; }}
    .gear-buy-link:hover svg {{ opacity: 1; }}
    /* Disclosure text: deliberately full contrast and not tiny. An
       affiliate disclosure that is hard to read does not count as one. */
    .gear-buy-note {{ margin: 12px 0 0; font-size: 12.5px; line-height: 1.55;
                      color: var(--text); opacity: 0.86; max-width: 60ch; }}
    /* Previous / next item. Sits above the carousel, and is labelled with
       item names so it reads as page navigation rather than image
       navigation, which the carousel arrows handle just below. */
    .gear-nav {{ display: flex; gap: 10px; margin-bottom: 20px;
                 align-items: stretch; }}
    .gear-nav-link {{ display: flex; align-items: center; gap: 10px;
                      flex: 1 1 0; min-width: 0; padding: 10px 14px;
                      border-radius: 11px; text-decoration: none;
                      color: var(--text);
                      border: 1px solid var(--line);
                      background: var(--soft);
                      transition: border-color 200ms ease, background 200ms ease,
                                  transform 200ms ease; }}
    .gear-nav-link:hover, .gear-nav-link:focus-visible {{
                      border-color: var(--accent);
                      background: var(--glow2);
                      transform: translateY(-1px); }}
    .gn-next {{ justify-content: flex-end; text-align: right; }}
    .gn-arrow {{ flex: 0 0 auto; font-size: 16px; line-height: 1;
                 color: var(--accent); }}
    .gn-text {{ display: flex; flex-direction: column; gap: 2px; min-width: 0; }}
    .gn-label {{ font-size: 9.5px; letter-spacing: 0.16em; text-transform: uppercase;
                 color: var(--muted); }}
    .gn-title {{ font-size: 13px; font-weight: 500; line-height: 1.25;
                 overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    @media (max-width: 560px) {{
      .gn-label {{ display: none; }}
      .gn-title {{ font-size: 12px; }}
      .gear-nav-link {{ padding: 9px 11px; }}
    }}
    @keyframes gradientRoll {{
      0% {{ background-position: 0% 50%; }}
      50% {{ background-position: 100% 50%; }}
      100% {{ background-position: 0% 50%; }}
    }}
    @media (max-width: 768px) {{
      .gear-page {{ margin: 24px auto; padding: 0 12px; }}
      .gear-title {{ font-size: 24px; }}
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
    <div class="wrap gear-page">
{nav_html}

      <div class="gear-header">
{carousel_html}        <h1 class="gear-title">{esc(title)}</h1>
        <p class="gear-desc">{esc(desc)}</p>
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
</body>
</html>'''
    
    return html_content

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
    
    # Generate pages for every gear item. Previous/next follow the order of
    # site-data.json and wrap around, so the chain has no dead ends. With a
    # single visible item there are no neighbours and the bar is omitted.
    n = len(gear_items)
    generated_slugs = set()
    for i, entry in enumerate(gear_items):
        slug = entry['slug']
        generated_slugs.add(slug)
        prev_entry = gear_items[(i - 1) % n] if n > 1 else None
        next_entry = gear_items[(i + 1) % n] if n > 1 else None
        filename = os.path.join(OUT_DIR, f"{slug}.html")
        page_html = build_page(entry, slug, prev_entry, next_entry)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_html)
        print(f"✓ {filename}")
    
    # Clean up stale files (whose slug is no longer in site-data.json)
    for filename in os.listdir(OUT_DIR):
        if not filename.endswith('.html'):
            continue
        filepath = os.path.join(OUT_DIR, filename)
        slug = filename[:-5]  # strip .html
        if slug not in generated_slugs:
            os.remove(filepath)
            print(f"✗ deleted stale {filepath}")
    
    print(f"\nGenerated {len(generated_slugs)} gear pages.")

if __name__ == '__main__':
    main()
