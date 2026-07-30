#!/usr/bin/env python3
"""
Generates one REAL, indexable page per gear item in site-data.json, under
gear/<slug>.html. Mirrors the logic of generate-share-pages.py but for gear.

Each page includes:
  - Hero image (first image from entry.images)
  - Swipeable image strip (all images, thumbnail carousel)
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
from datetime import datetime

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT_DIR = "gear"
REVIEWS_DIR = "gear-reviews"
SITE_NAME = "Bhapstar Astrophotography"

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
    iso_date = datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat() + 'Z'
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
    return json.dumps(schema, ensure_ascii=False)

def build_page(entry, slug):
    """Build the full HTML page for one gear item."""
    title = entry.get('title', 'Gear')
    desc = entry.get('desc', '')
    images = entry.get('images', [])
    cover = images[0] if images else {}
    cover_src = cover.get('file', '')
    cover_alt = cover.get('alt', title)
    buy_links = entry.get('buy', [])
    
    page_url = f"{DOMAIN}/{OUT_DIR}/{slug}.html"
    review_html = read_review(slug)
    json_ld = build_json_ld(entry, page_url, cover_src)
    
    # Render image strip (swipeable carousel)
    thumb_strip = ''
    for i, img in enumerate(images):
        thumb_src = thumb_for(img['file'])
        thumb_alt = esc(img.get('alt', title))
        active_cls = 'active' if i == 0 else ''
        thumb_strip += (
            f'        <img class="dv-thumb {active_cls}" data-idx="{i}" '
            f'src="{esc(thumb_src)}" alt="{thumb_alt}" />\n'
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
  <meta property="og:image" content="{esc(url_for(cover_src))}" />
  <meta property="og:url" content="{esc(page_url)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(desc[:160])}" />
  <meta name="twitter:image" content="{esc(url_for(cover_src))}" />
  <link rel="preconnect" href="https://static.cloudflareinsights.com" crossorigin />
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token":"b3353c7dd8764a64baee57fd09c3dbb9"}}'></script>
  <link rel="stylesheet" href="../styles.css" />
  
  <style>
    .gear-page {{ max-width: 900px; margin: 40px auto; padding: 0 16px; }}
    .gear-header {{ margin-bottom: 40px; }}
    .gear-hero {{ margin-bottom: 32px; border-radius: 16px; overflow: hidden; }}
    .gear-hero img {{ width: 100%; height: auto; display: block; }}
    .gear-title {{ font-size: 32px; font-weight: 600; margin: 0 0 16px; 
                    background: linear-gradient(90deg, #a78bfa, #60a5fa, #f472b6, #60a5fa, #a78bfa);
                    background-size: 300% 100%;
                    -webkit-background-clip: text;
                    background-clip: text;
                    -webkit-text-fill-color: transparent;
                    animation: gradientRoll 4s linear infinite reverse; }}
    .gear-desc {{ font-size: 16px; line-height: 1.6; color: rgba(232,230,247,0.84); margin: 0; }}
    .gear-thumbs {{ display: flex; gap: 8px; margin: 20px 0; overflow-x: auto; padding-bottom: 8px; }}
    .gear-thumb {{ width: 80px; height: 60px; border-radius: 8px; cursor: pointer;
                   border: 2px solid transparent; transition: all 200ms ease;
                   flex-shrink: 0; object-fit: cover; }}
    .gear-thumb.active {{ border-color: #a78bfa; }}
    .gear-thumb:hover {{ border-color: #60a5fa; }}
    .gear-review {{ margin: 40px 0; font-size: 15px; line-height: 1.7; 
                    color: rgba(232,230,247,0.88); }}
    .gear-review h2 {{ font-size: 20px; font-weight: 600; margin: 24px 0 12px; 
                       color: rgba(232,230,247,0.92); }}
    .gear-review h3 {{ font-size: 17px; font-weight: 600; margin: 18px 0 10px; 
                       color: rgba(232,230,247,0.88); }}
    .gear-review p {{ margin: 12px 0; }}
    .gear-review table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    .gear-review table td, .gear-review table th {{ padding: 10px; text-align: left; 
                                                     border-bottom: 1px solid rgba(167,139,250,0.16); }}
    .gear-review table th {{ background: rgba(167,139,250,0.08); font-weight: 600; }}
    .gear-buy {{ margin: 32px 0; padding-top: 24px; border-top: 1px solid rgba(167,139,250,0.16); }}
    .gear-buy-label {{ font-size: 10.5px; letter-spacing: 0.18em; text-transform: uppercase;
                       color: rgba(232,230,247,0.55); margin: 0 0 12px; }}
    .gear-buy-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .gear-buy-link {{ display: inline-flex; align-items: center; gap: 7px;
                      padding: 10px 14px; border-radius: 11px; font-size: 13px; font-weight: 500;
                      text-decoration: none; color: rgba(232,230,247,0.92);
                      border: 1px solid rgba(167,139,250,0.26);
                      background: rgba(167,139,250,0.07);
                      transition: all 200ms ease; }}
    .gear-buy-link:hover, .gear-buy-link:focus-visible {{ color: #fff;
                      border-color: rgba(96,165,250,0.55); background: rgba(96,165,250,0.14);
                      transform: translateY(-2px); }}
    .gear-buy-link svg {{ width: 11px; height: 11px; flex-shrink: 0; opacity: 0.6; }}
    .gear-buy-link:hover svg {{ opacity: 1; }}
    .gear-buy-note {{ margin: 12px 0 0; font-size: 11.5px; line-height: 1.5;
                      color: rgba(232,230,247,0.48); }}
    .gear-back {{ display: inline-block; margin-bottom: 20px; padding: 8px 14px;
                  font-size: 13px; color: #a78bfa; text-decoration: none;
                  border: 1px solid rgba(167,139,250,0.26); border-radius: 8px;
                  transition: all 200ms ease; }}
    .gear-back:hover {{ border-color: #a78bfa; background: rgba(167,139,250,0.08); }}
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
  <div id="app"></div>
  <script src="../partials/partials.js"></script>

  <main class="gear-page">
    <a href="/gear.html" class="gear-back">← Back to gear</a>
    
    <div class="gear-header">
      <div class="gear-hero">
        <img id="heroImg" src="{esc(cover_src)}" alt="{esc(cover_alt)}" />
      </div>
      <h1 class="gear-title">{esc(title)}</h1>
      <p class="gear-desc">{esc(desc)}</p>
    </div>

    <div class="gear-thumbs" id="thumbstrip">
{thumb_strip}    </div>

    <div class="gear-review">
{review_html}    </div>

{buy_html}  </main>

  <script src="../protect-images.js"></script>
  <script>
    // Swipeable image strip: click a thumbnail to swap the hero image.
    document.querySelectorAll('.gear-thumb').forEach(thumb => {{
      thumb.addEventListener('click', () => {{
        const idx = thumb.getAttribute('data-idx');
        const images = {json.dumps([img['file'] for img in images])};
        if (idx !== null && idx < images.length) {{
          document.getElementById('heroImg').src = images[idx];
          document.querySelectorAll('.gear-thumb').forEach(t => 
            t.classList.remove('active'));
          thumb.classList.add('active');
        }}
      }});
    }});
  </script>
</body>
</html>'''
    
    return html_content

def main():
    # Load data
    with open(DATA, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    # Filter: all gear items
    gear_items = [e for e in items if e.get('section') == 'gear' and e.get('slug')]
    
    # Create output dir
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Generate pages for every gear item
    generated_slugs = set()
    for entry in gear_items:
        slug = entry['slug']
        generated_slugs.add(slug)
        filename = os.path.join(OUT_DIR, f"{slug}.html")
        page_html = build_page(entry, slug)
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
