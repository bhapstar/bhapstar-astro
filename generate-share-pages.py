#!/usr/bin/env python3
"""
generate-share-pages.py — bhapstar
-------------------------------------------------------------
Generates one REAL, indexable page per gallery item, under share/<slug>.html.

History / why this exists:
    v1: tiny noindex redirect stubs, purely so social crawlers (which don't
        run JS and ignore #fragments) could read per-image Open Graph tags.
    v2 (this version): full standalone pages. Same URLs, same og tags, but
        each page now shows the photo(s), the Field Notes write-up (intro +
        body from site-data.json), capture specs, and links into the gallery
        viewer and prints page. Pages are INDEXABLE (no robots meta,
        canonical points at themselves) and carry their own JSON-LD
        (ImageObject / VideoObject + WebPage), so each image gets a real
        landing page in Google Search and Google Images.

    Social sharing still works exactly as before — the gallery's share
    buttons point at these URLs and crawlers read the same og tags. The only
    behaviour change: humans who open a shared link now land on the image's
    page (with a one-tap "Open in the gallery viewer" button) instead of
    being JS-redirected into the gallery.

Pages use the site's shared chrome: /styles.css, header/footer injected by
/partials/partials.js (root-absolute, so it works from /share/), and
/protect-images.js for the usual right-click/drag speed bumps.

Idempotent: rewrites every page each run, and deletes any stale share/*.html
whose slug is no longer in site-data.json.

    python generate-share-pages.py
"""

import html
import json
import os
import sys
from datetime import datetime

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT_DIR = "share"
SITE_NAME = "Bhapstar Astrophotography"
PERSON_ID = f"{DOMAIN}/#person"
WEBSITE_ID = f"{DOMAIN}/#website"
PRINTS_PAGE = f"{DOMAIN}/prints.html"

# Capture-detail tiles, in display order. The SVGs are copied verbatim from
# gallery.html's SPEC_ICONS so the share pages' specs panel looks identical
# to the viewer's info popup (icon above value, violet tint).
SPEC_ICONS = [
    ("telescope",   "Telescope",   '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M2.4 9.3 8.9 5.6 10 7.5 3.5 11.2Z"/><path d="M8.9 5.6 11 4.4 12.1 6.3 10 7.5"/><path d="M3 10.4 1.8 11.1"/><path d="M4.3 11 3.2 13.9"/><path d="M5.1 10.5 6.4 13.4"/></svg>'),
    ("camera",      "Camera",      '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4.6" width="12" height="8.4" rx="1.5"/><path d="M5.6 4.6l1-1.6h2.8l1 1.6"/><circle cx="8" cy="8.8" r="2.2"/></svg>'),
    ("filter",      "Filter",      '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M2.6 3.4h10.8l-4.1 5v4.2l-2.6 1.3V8.4z"/></svg>'),
    ("integration", "Integration", '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="9.2" r="4.9"/><path d="M8 9.2V6.6"/><path d="M6.5 1.9h3"/><path d="M8 1.9v2.4"/></svg>'),
    ("location",    "Location",    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M8 14s4.1-3.9 4.1-7A4.1 4.1 0 0 0 8 2.9 4.1 4.1 0 0 0 3.9 7C3.9 10.1 8 14 8 14z"/><circle cx="8" cy="6.9" r="1.5"/></svg>'),
    ("date",        "Date",        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.4" width="11" height="10.1" rx="1.4"/><path d="M2.5 6.4h11"/><path d="M5.4 2.1v2.4"/><path d="M10.6 2.1v2.4"/></svg>'),
]

# Page-specific styles. Everything else comes from /styles.css so these pages
# always match the site theme. Kept as a plain constant (not an f-string) so
# the CSS braces don't need escaping.
PAGE_STYLE = """\
  <style>
    .share-wrap{ max-width: 900px; margin: 0 auto; }
    .share-date{ margin: 6px 0 26px; color: var(--muted); font-size: 14px; }
    .share-figure{ margin: 0 0 22px; }
    /* The image box. Both arrow sets are absolutely positioned against
       this, so they track the picture and not the caption below it. */
    .share-slides{ position: relative; }
    .share-slide{ display: none; }
    .share-slide.is-active{ display: block; }
    .share-figure img{
      display: block; width: 100%; height: auto; border-radius: 14px;
      border: 1px solid var(--line);
      /* Dark theme: a black shadow is invisible on #050414, so lift the
         image off the page with a soft violet bloom instead, plus a faint
         accent rim to define the edge. */
      box-shadow: 0 0 0 1px rgba(167,139,250,0.14),
                  0 12px 48px rgba(167,139,250,0.22),
                  0 4px 18px rgba(96,165,250,0.14);
    }
    /* Light theme: keep the original soft drop shadow, which reads well
       against the pale background. */
    html[data-theme="light"] .share-figure img{
      box-shadow: 0 10px 40px rgba(0,0,0,0.45);
    }
    .share-figure figcaption{
      margin-top: 8px; color: var(--muted); font-size: 13px;
    }
    .share-slide-cap:empty{ display: none; }
    /* Prev / next arrows overlaid on the image. The image itself links to the
       full-screen viewer, so the arrows sit above it on their own layer. */
    .share-arrow{
      position: absolute; top: 50%; transform: translateY(-50%); z-index: 3;
      width: 44px; height: 44px; border-radius: 50%;
      display: grid; place-items: center;
      font-size: 26px; line-height: 1; text-decoration: none;
      color: rgba(232,230,247,0.92);
      background: rgba(5,4,20,0.52);
      border: 1px solid rgba(167,139,250,0.28);
      backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
      opacity: 0.75;
      transition: background .18s ease, border-color .18s ease, opacity .18s ease;
    }
    .share-arrow:hover, .share-arrow:focus-visible{
      opacity: 1; background: rgba(5,4,20,0.78);
      border-color: rgba(167,139,250,0.6);
    }
    .share-arrow.prev{ left: 12px; }
    .share-arrow.next{ right: 12px; }
    html[data-theme="light"] .share-arrow{
      color: #0b0a1c; background: rgba(255,255,255,0.72);
      border-color: rgba(120,90,220,0.32);
    }
    html[data-theme="light"] .share-arrow:hover,
    html[data-theme="light"] .share-arrow:focus-visible{
      background: rgba(255,255,255,0.92);
    }
    @media (max-width: 620px){
      .share-arrow{ width: 38px; height: 38px; font-size: 22px; }
      .share-arrow.prev{ left: 8px; }
      .share-arrow.next{ right: 8px; }
    }
    /* Second control: cycles this entry's own pictures. Sat at the bottom
       centre of the image so it never collides with the page-to-page arrows
       on the left and right edges. Only rendered when there's more than one
       picture, and only usable with JS — hence the button elements. */
    .share-pager{
      position: absolute; left: 50%; transform: translateX(-50%);
      bottom: 14px; z-index: 3;
      display: flex; align-items: center; gap: 2px;
      padding: 4px 6px; border-radius: 999px;
      background: rgba(5,4,20,0.58);
      border: 1px solid rgba(167,139,250,0.28);
      backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
    }
    .share-pager-btn{
      appearance: none; background: none; border: 0; cursor: pointer;
      width: 30px; height: 30px; border-radius: 50%;
      display: grid; place-items: center;
      font: inherit; font-size: 20px; line-height: 1;
      color: rgba(232,230,247,0.92);
      transition: background .18s ease, color .18s ease;
    }
    .share-pager-btn:hover, .share-pager-btn:focus-visible{
      background: rgba(167,139,250,0.22);
    }
    .share-pager-count{
      min-width: 42px; text-align: center;
      font-size: 12px; font-weight: 600; letter-spacing: 0.06em;
      color: rgba(232,230,247,0.8);
      font-variant-numeric: tabular-nums;
    }
    html[data-theme="light"] .share-pager{
      background: rgba(255,255,255,0.78);
      border-color: rgba(120,90,220,0.32);
    }
    html[data-theme="light"] .share-pager-btn{ color: #0b0a1c; }
    html[data-theme="light"] .share-pager-count{ color: rgba(20,18,44,0.75); }
    @media (max-width: 620px){
      .share-pager{ bottom: 10px; }
      .share-pager-btn{ width: 26px; height: 26px; font-size: 18px; }
      .share-pager-count{ min-width: 38px; font-size: 11px; }
    }
    .share-body p{ color: var(--text); line-height: 1.7; margin: 0 0 16px; }
    .share-body .lead{ font-size: 17px; color: rgba(200,195,235,0.85); margin: 0 0 20px; max-width: none; }
    /* Capture-specs panel — mirrors the viewer's info popup tiles */
    .share-specs{
      margin: 28px 0; padding: 16px 14px;
      border: 1px solid rgba(167,139,250,0.14); border-radius: 12px;
      background: rgba(167,139,250,0.06);
    }
    .share-specs h2{
      margin: 0 0 14px; font-size: 13px; font-weight: 700;
      letter-spacing: 0.24em; text-transform: uppercase; color: var(--accent);
      text-align: center;
    }
    .share-specs-grid{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
      gap: 12px 10px;
    }
    .share-spec{
      display: flex; flex-direction: column;
      align-items: center; text-align: center; gap: 7px;
    }
    .share-spec-ico{
      width: 22px; height: 22px;
      display: grid; place-items: center; color: var(--accent);
    }
    .share-spec-ico svg{ width: 20px; height: 20px; }
    .sr-only{
      position: absolute; width: 1px; height: 1px;
      padding: 0; margin: -1px; overflow: hidden;
      clip: rect(0,0,0,0); white-space: nowrap; border: 0;
    }
    .share-spec-val{
      font-size: 12.5px; line-height: 1.3; font-weight: 500;
      color: rgba(232,230,247,0.9);
    }
    .share-nav{
      display: flex; justify-content: space-between; gap: 16px;
      margin-top: 34px; padding-top: 18px; border-top: 1px solid var(--line);
      font-size: 14px;
    }
    .share-nav a{ color: var(--accent); text-decoration: none; max-width: 46%; }
    .share-nav a:hover{ text-decoration: underline; }
    .share-nav .nav-next{ margin-left: auto; text-align: right; }
  </style>
"""


# ── helpers ──────────────────────────────────────────────────────────────────

def to_iso(date_str):
    """Convert 'DD-MM-YYYY' to ISO 8601 'YYYY-MM-DD'. Falls back to None."""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def display_date(date_str):
    """Convert 'DD-MM-YYYY' to 'December 2025' — the same month-year format
    the viewer's date tile uses. Falls back to None."""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%B %Y")
    except (TypeError, ValueError):
        return None


def cover_file(entry):
    """The image used as the item's preview — mirrors the gallery grid's cover:
    first image in images[], else the single file, else a video poster."""
    imgs = entry.get("images")
    if imgs and imgs[0].get("file"):
        return imgs[0]["file"]
    if entry.get("file"):
        return entry["file"]
    vids = entry.get("videos")
    if vids and vids[0].get("poster"):
        return vids[0]["poster"]
    return None


def thumb_for(file):
    """images/foo.webp -> images/thumbs/foo.webp  (same rule the grid uses)."""
    prefix = "images/"
    if file.startswith(prefix) and not file.startswith(prefix + "thumbs/"):
        return prefix + "thumbs/" + file[len(prefix):]
    return file


def url_for(path):
    return path if path.startswith("http") else f"{DOMAIN}/{path}"


def a(value):
    """Escape a string for use inside an HTML attribute."""
    return html.escape(str(value or ""), quote=True)


def t(value):
    """Escape a string for use as HTML text content."""
    return html.escape(str(value or ""), quote=False)


def meta_description(entry, limit=160):
    """Meta description from desc/intro, truncated cleanly at a word break."""
    text = " ".join((entry.get("desc") or entry.get("intro") or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


def entry_media(entry):
    """List of (full_file, alt) image pairs shown on the page.
    For video entries these are the poster stills."""
    imgs = entry.get("images")
    if imgs:
        return [(i["file"], i.get("alt") or entry.get("alt") or entry.get("title"))
                for i in imgs if i.get("file")]
    if entry.get("file"):
        return [(entry["file"], entry.get("alt") or entry.get("title"))]
    vids = entry.get("videos") or []
    return [(v["poster"], v.get("alt") or entry.get("title"))
            for v in vids if v.get("poster")]


# ── JSON-LD ──────────────────────────────────────────────────────────────────

def build_json_ld(entry, share_url, iso_date, media, meta_desc):
    """Person + WebPage + ImageObject per photo (or VideoObject per video).
    Field names mirror generate-schema.py so the same @ids are used
    consistently across the site."""
    graph = [{
        "@type": "Person",
        "@id": PERSON_ID,
        "name": "Bhapinder Singh",
        "alternateName": "Bobby Singh",
        "url": DOMAIN,
    }]

    is_video_entry = bool(entry.get("videos"))

    page = {
        "@type": "WebPage",
        "@id": share_url,
        "url": share_url,
        "name": f"{entry.get('title')} — {SITE_NAME}",
        "description": meta_desc or None,
        "author": {"@id": PERSON_ID},
        "isPartOf": {"@id": WEBSITE_ID},
    }
    if iso_date:
        page["datePublished"] = iso_date
    if media and not is_video_entry:
        page["primaryImageOfPage"] = {"@id": f"{url_for(media[0][0])}#image"}
    graph.append({k: v for k, v in page.items() if v is not None})

    if is_video_entry:
        # VideoObject per Vimeo clip — name/thumbnailUrl/uploadDate are the
        # fields Google requires for video results.
        for i, v in enumerate(entry.get("videos") or [], start=1):
            if not v.get("vimeoId"):
                continue
            node = {
                "@type": "VideoObject",
                "name": f"{entry.get('title')} — {i}",
                "description": entry.get("desc") or entry.get("intro"),
                "thumbnailUrl": url_for(v["poster"]) if v.get("poster") else None,
                "embedUrl": f"https://player.vimeo.com/video/{v['vimeoId']}",
                "uploadDate": iso_date,
                "author": {"@id": PERSON_ID},
            }
            graph.append({k: val for k, val in node.items() if val is not None})
    else:
        for i, (file, alt) in enumerate(media):
            img_url = url_for(file)
            node = {
                "@type": "ImageObject",
                "@id": f"{img_url}#image",
                "contentUrl": img_url,
                "url": img_url,
                "name": entry.get("title") if i == 0 else (alt or entry.get("title")),
                "description": entry.get("desc"),
                "creator": {"@id": PERSON_ID},
                "creditText": "Bhapinder Singh",
                "copyrightNotice": "© Bhapinder Singh",
                "license": PRINTS_PAGE,
                "acquireLicensePage": PRINTS_PAGE,
            }
            if alt:
                node["caption"] = alt
            if iso_date:
                node["datePublished"] = iso_date
            graph.append({k: v for k, v in node.items() if v is not None})

    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      indent=2, ensure_ascii=False)


# ── page template ────────────────────────────────────────────────────────────

def build_page(entry, prev_link, next_link):
    slug = entry["slug"]
    title = entry.get("title") or SITE_NAME
    cover = cover_file(entry)
    if not cover:
        return None

    is_video_entry = bool(entry.get("videos"))
    media = entry_media(entry)
    alt = entry.get("alt") or title
    meta_desc = meta_description(entry)
    thumb_url = url_for(thumb_for(cover))
    share_url = f"{DOMAIN}/{OUT_DIR}/{slug}.html"
    viewer_url = f"/gallery.html#{slug}"
    iso_date = to_iso(entry.get("date"))
    nice_date = display_date(entry.get("date"))

    specs = entry.get("specs") or {}

    # ── figures ──
    # Prev / next arrows, overlaid on the cover image (first figure only).
    arrows = ""
    if prev_link:
        arrows += (f'\n        <a class="share-arrow prev" href="{a(prev_link[0])}"'
                   f' rel="prev" aria-label="Previous image: {a(prev_link[1])}"'
                   f' title="{a(prev_link[1])}">‹</a>')
    if next_link:
        arrows += (f'\n        <a class="share-arrow next" href="{a(next_link[0])}"'
                   f' rel="next" aria-label="Next image: {a(next_link[1])}"'
                   f' title="{a(next_link[1])}">›</a>')

    # All of an entry's pictures live in one figure as slides. With a single
    # picture that's just the picture; with several, the pager below cycles
    # them in place instead of stacking them down the page.
    multi = len(media) > 1
    slides = []
    for i, (file, img_alt) in enumerate(media):
        eager = 'loading="eager" fetchpriority="high"' if i == 0 else 'loading="lazy"'
        cap = t(img_alt) if (multi and img_alt) else ""
        slides.append(
            f'          <div class="share-slide{" is-active" if i == 0 else ""}"'
            f' data-cap="{a(cap)}">'
            f'<a href="{a(viewer_url)}" aria-label="Open {a(title)} full screen">'
            f'<img src="/{a(file)}" alt="{a(img_alt or title)}" {eager} '
            f'decoding="async" draggable="false"></a></div>'
        )

    pager = ""
    if multi:
        pager = (
            '\n          <div class="share-pager">'
            '<button class="share-pager-btn prev" type="button"'
            ' aria-label="Previous picture">‹</button>'
            f'<span class="share-pager-count" aria-live="polite">1 / {len(media)}</span>'
            '<button class="share-pager-btn next" type="button"'
            ' aria-label="Next picture">›</button>'
            '</div>'
        )

    first_cap = t(media[0][1]) if (multi and media[0][1]) else ""
    figures_html = (
        '      <figure class="share-figure">\n'
        '        <div class="share-slides">\n'
        + "\n".join(slides)
        + arrows.replace("\n        ", "\n          ")
        + pager
        + '\n        </div>\n'
        f'        <figcaption class="share-slide-cap">{first_cap}</figcaption>\n'
        '      </figure>'
    )
    if is_video_entry:
        figures_html += (
            '\n      <p class="share-date">Stills from the time-lapse videos — '
            'watch them in the gallery viewer below.</p>'
        )

    # ── write-up ──
    body_parts = []
    if entry.get("intro"):
        body_parts.append(f'        <p class="lead">{t(entry["intro"])}</p>')
    body_text = entry.get("body") or ""
    for para in [p.strip() for p in body_text.split("\n\n") if p.strip()]:
        body_parts.append(f"        <p>{t(para)}</p>")
    if not body_parts and entry.get("desc"):
        body_parts.append(f"        <p>{t(entry['desc'])}</p>")
    body_html = "\n".join(body_parts)

    # ── capture specs: icon tiles, identical to the viewer's info popup ──
    specs_html = ""
    rows = [(label, specs.get(key) if key != "date" else nice_date, icon)
            for key, label, icon in SPEC_ICONS]
    rows = [(label, val, icon) for label, val, icon in rows
            if val and str(val).strip()]
    if rows:
        tiles = "\n".join(
            f'          <div class="share-spec" title="{a(lbl)}">'
            f'<span class="share-spec-ico" aria-hidden="true">{icon}</span>'
            f'<span class="share-spec-val">{t(val)}</span>'
            f'<span class="sr-only">{t(lbl)}</span></div>'
            for lbl, val, icon in rows)
        specs_html = (
            '      <div class="share-specs">\n'
            "        <h2>Capture details</h2>\n"
            '        <div class="share-specs-grid">\n' + tiles + "\n        </div>\n"
            "      </div>\n"
        )

    # ── prev / next ──
    slides_script = ""
    if multi:
        slides_script = (
            "      <script>\n"
            "        (function(){\n"
            "          var box = document.querySelector('.share-slides');\n"
            "          if (!box) return;\n"
            "          var slides = box.querySelectorAll('.share-slide');\n"
            "          var count  = box.querySelector('.share-pager-count');\n"
            "          var cap    = document.querySelector('.share-slide-cap');\n"
            "          var i = 0;\n"
            "          function show(n){\n"
            "            i = (n + slides.length) % slides.length;\n"
            "            for (var k = 0; k < slides.length; k++){\n"
            "              slides[k].classList.toggle('is-active', k === i);\n"
            "            }\n"
            "            if (count) count.textContent = (i + 1) + ' / ' + slides.length;\n"
            "            if (cap) cap.textContent = slides[i].getAttribute('data-cap') || '';\n"
            "          }\n"
            "          box.querySelector('.share-pager-btn.prev')\n"
            "             .addEventListener('click', function(){ show(i - 1); });\n"
            "          box.querySelector('.share-pager-btn.next')\n"
            "             .addEventListener('click', function(){ show(i + 1); });\n"
            "        })();\n"
            "      </script>\n"
        )

    # Keyboard support for the overlaid arrows: left / right move between images.
    nav_html = ""
    if prev_link or next_link:
        prev_js = f'"{a(prev_link[0])}"' if prev_link else "null"
        next_js = f'"{a(next_link[0])}"' if next_link else "null"
        nav_html = (
            "      <script>\n"
            "        (function(){\n"
            f"          var prev = {prev_js}, next = {next_js};\n"
            "          document.addEventListener('keydown', function(e){\n"
            "            if (e.metaKey || e.ctrlKey || e.altKey) return;\n"
            "            var tag = (e.target.tagName || '').toLowerCase();\n"
            "            if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;\n"
            "            if (e.key === 'ArrowLeft'  && prev) location.href = prev;\n"
            "            if (e.key === 'ArrowRight' && next) location.href = next;\n"
            "          });\n"
            "        })();\n"
            "      </script>\n"
        )

    published = (f'  <meta property="article:published_time" content="{a(iso_date)}" />\n'
                 if iso_date else "")
    json_ld = build_json_ld(entry, share_url, iso_date, media, meta_desc)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{t(title)} — {t(SITE_NAME)}</title>

  <link rel="icon" href="/images/icons/favicon-32.png" sizes="32x32" type="image/png" />
  <link rel="apple-touch-icon" href="/images/icons/apple-touch-icon.png" />
  <meta name="theme-color" content="#050414" />

  <link rel="canonical" href="{a(share_url)}" />
  <meta name="description" content="{a(meta_desc)}" />
  <meta name="author" content="Bhapinder Singh" />

  <!-- Open Graph (Facebook, WhatsApp, LinkedIn, Slack, Discord, …) -->
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="{a(SITE_NAME)}" />
  <meta property="og:title" content="{a(title)}" />
  <meta property="og:description" content="{a(meta_desc)}" />
  <meta property="og:image" content="{a(thumb_url)}" />
  <meta property="og:image:alt" content="{a(alt)}" />
  <meta property="og:url" content="{a(share_url)}" />
{published}
  <!-- Twitter / X -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{a(title)}" />
  <meta name="twitter:description" content="{a(meta_desc)}" />
  <meta name="twitter:image" content="{a(thumb_url)}" />
  <meta name="twitter:image:alt" content="{a(alt)}" />

  <!-- Cloudflare Web Analytics -->
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js"
    data-cf-beacon='{{"token":"b3353c7dd8764a64baee57fd09c3dbb9"}}'></script>

  <link rel="stylesheet" href="/styles.css" />
{PAGE_STYLE}
  <script type="application/ld+json">
{json_ld}
  </script>
</head>
<body>

<!-- ── Header (injected by partials.js) ── -->
<div id="siteHeader"></div>

<main>
  <section class="section">
    <div class="wrap share-wrap">
      <h1>{t(title)}</h1>

{figures_html}

      <div class="share-body">
{body_html}
      </div>

{specs_html}
      <div class="actions">
        <a class="btn primary" href="/gallery.html">Back to gallery</a>
        <a class="btn" href="/prints.html">Order a print</a>
      </div>

{slides_script}{nav_html}
    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

<script src="/partials/partials.js"></script>
<script src="/protect-images.js"></script>
</body>
</html>
"""


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        with open(DATA, "r", encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        print(f"Could not find {DATA}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)

    # First pass: which entries get a page (needed for prev/next links).
    pageable = [e for e in items
                if e.get("section", "gallery") == "gallery"
                and e.get("slug") and cover_file(e)]

    written = set()
    skipped = sum(1 for e in items
                  if e.get("section", "gallery") == "gallery"
                  and e.get("slug") and not cover_file(e))

    for i, entry in enumerate(pageable):
        prev_link = next_link = None
        if i > 0:
            p = pageable[i - 1]
            prev_link = (f"/{OUT_DIR}/{p['slug']}.html", p.get("title") or p["slug"])
        if i < len(pageable) - 1:
            n = pageable[i + 1]
            next_link = (f"/{OUT_DIR}/{n['slug']}.html", n.get("title") or n["slug"])

        page = build_page(entry, prev_link, next_link)
        if page is None:
            continue
        fname = f"{entry['slug']}.html"
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
            f.write(page)
        written.add(fname)

    # Remove stale pages for slugs that no longer exist.
    removed = 0
    for existing in os.listdir(OUT_DIR):
        if existing.endswith(".html") and existing not in written:
            os.remove(os.path.join(OUT_DIR, existing))
            removed += 1

    print(f"  Wrote {len(written)} share pages to {OUT_DIR}/"
          + (f", removed {removed} stale" if removed else "")
          + (f", skipped {skipped} (no cover image)" if skipped else ""))


if __name__ == "__main__":
    main()
