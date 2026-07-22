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
      /* Dark theme: a plain black shadow is invisible on #050414, so lift the
         image with a deep shadow plus a violet bloom and a faint accent rim. */
      box-shadow: 0 24px 70px rgba(0,0,0,0.55),
                  0 0 0 1px rgba(167,139,250,0.18),
                  0 10px 44px rgba(167,139,250,0.28),
                  0 4px 18px rgba(96,165,250,0.16);
    }
    /* Light theme: a soft, clearly visible drop shadow. */
    html[data-theme="light"] .share-figure img{
      box-shadow: 0 20px 50px rgba(0,0,0,0.35),
                  0 6px 18px rgba(0,0,0,0.18);
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
    .share-open{ cursor: pointer; }

    /* ── Full-screen lightbox ──────────────────────────────────────────────
       Opens in place when a photo is clicked; the page URL never changes.
       Pinch (or trackpad / browser zoom) to zoom — there is no click-to-zoom.
       The arrows cycle through every photo in the gallery. */
    .share-lightbox{
      position: fixed; inset: 0; z-index: 1000;
      display: none; align-items: center; justify-content: center;
      background: rgba(3,2,12,0.94);
      backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
    }
    .share-lightbox.is-open{ display: flex; }
    body.slb-lock{ overflow: hidden; }
    .slb-stage{
      position: relative; display: grid; place-items: center;
      max-width: 100vw; max-height: 100vh;
      touch-action: pinch-zoom;   /* two-finger pinch zooms; one-finger swipe navigates */
    }
    .slb-img{
      max-width: 96vw; max-height: 92vh; width: auto; height: auto;
      display: block; border-radius: 8px;
      user-select: none; -webkit-user-select: none;
      box-shadow: 0 24px 70px rgba(0,0,0,0.55),
                  0 0 0 1px rgba(167,139,250,0.18),
                  0 10px 44px rgba(167,139,250,0.28);
    }
    html[data-theme="light"] .slb-img{
      box-shadow: 0 22px 55px rgba(0,0,0,0.45);
    }
    .slb-close, .slb-arrow, .slb-share{
      position: fixed; z-index: 2; appearance: none; cursor: pointer;
      display: grid; place-items: center; line-height: 1;
      color: rgba(232,230,247,0.92);
      background: rgba(5,4,20,0.55);
      border: 1px solid rgba(167,139,250,0.30);
      backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
      transition: background .18s ease, border-color .18s ease;
    }
    .slb-close{ top: 16px; right: 16px; width: 44px; height: 44px;
      border-radius: 50%; font-size: 20px; }
    .slb-share{ top: 16px; left: 16px; width: 44px; height: 44px; border-radius: 50%; }
    .slb-share svg{ width: 20px; height: 20px; }
    .slb-share.copied{ color: #34d399; border-color: rgba(52,211,153,0.6); }
    .slb-arrow{ top: 50%; transform: translateY(-50%);
      width: 52px; height: 52px; border-radius: 50%; font-size: 30px; }
    .slb-arrow.prev{ left: 16px; }
    .slb-arrow.next{ right: 16px; }
    .slb-close:hover, .slb-arrow:hover, .slb-share:hover,
    .slb-close:focus-visible, .slb-arrow:focus-visible, .slb-share:focus-visible{
      background: rgba(5,4,20,0.82); border-color: rgba(167,139,250,0.6);
    }
    .slb-count{
      position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
      z-index: 2; font-size: 13px; font-weight: 600; letter-spacing: 0.06em;
      color: rgba(232,230,247,0.82); font-variant-numeric: tabular-nums;
      padding: 5px 12px; border-radius: 999px;
      background: rgba(5,4,20,0.55); border: 1px solid rgba(167,139,250,0.24);
    }
    html[data-theme="light"] .share-lightbox{ background: rgba(245,244,255,0.96); }
    html[data-theme="light"] .slb-close,
    html[data-theme="light"] .slb-arrow,
    html[data-theme="light"] .slb-share,
    html[data-theme="light"] .slb-count{
      color: #0b0a1c; background: rgba(255,255,255,0.80);
      border-color: rgba(120,90,220,0.32);
    }
    @media (max-width: 620px){
      .slb-arrow{ width: 42px; height: 42px; font-size: 26px; }
      .slb-arrow.prev{ left: 8px; } .slb-arrow.next{ right: 8px; }
      .slb-close{ top: 10px; right: 10px; width: 40px; height: 40px; }
      .slb-share{ top: 10px; left: 10px; width: 40px; height: 40px; }
      .slb-img{ max-width: 100vw; max-height: 88vh; border-radius: 0; }
    }
    .sm-backdrop{ position: fixed; inset: 0; z-index: 1100; display: none;
      background: rgba(3,2,12,0.55); backdrop-filter: blur(2px); -webkit-backdrop-filter: blur(2px); }
    .sm-backdrop.open{ display: block; }
    .share-menu{ position: fixed; z-index: 1101; left: 50%; top: 50%;
      transform: translate(-50%,-50%); display: none; width: min(300px, 88vw);
      background: #0b0a1c; border: 1px solid rgba(167,139,250,0.28);
      border-radius: 16px; box-shadow: 0 30px 80px rgba(0,0,0,0.6); padding: 8px; }
    .share-menu.open{ display: block; }
    .sm-title{ font-size: 12px; letter-spacing: .04em; text-transform: uppercase;
      color: var(--muted); padding: 8px 12px 6px; }
    .sm-item{ display: flex; align-items: center; gap: 13px; width: 100%;
      padding: 11px 12px; border: 0; border-radius: 10px; cursor: pointer;
      background: transparent; color: rgba(232,230,247,0.92); font-size: 15px;
      text-align: left; font-family: inherit; transition: background .15s ease, color .15s ease; }
    .sm-item:hover, .sm-item:focus-visible{ background: rgba(167,139,250,0.14); outline: none; }
    .sm-item svg{ width: 19px; height: 19px; flex: 0 0 auto; }
    .sm-item.copied{ color: #34d399; }
    .sm-item[data-share="whatsapp"]:hover{ color: #25d366; }
    .sm-item[data-share="facebook"]:hover{ color: #1877f2; }
    html[data-theme="light"] .share-menu{ background: #fff; border-color: rgba(120,90,220,0.28);
      box-shadow: 0 30px 80px rgba(0,0,0,0.25); }
    html[data-theme="light"] .sm-item{ color: #14122c; }
    html[data-theme="light"] .sm-item:hover, html[data-theme="light"] .sm-item:focus-visible{ background: rgba(120,90,220,0.12); }
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

def build_page(entry, prev_link, next_link, all_photos=None, global_start=None):
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
        # Non-video photos open the in-page lightbox (JS intercepts the click
        # via .share-open + data-idx). The href stays pointed at the gallery
        # viewer as a no-JS / new-tab / crawler fallback. Video entries keep
        # the plain link so they open in the gallery viewer and actually play.
        if is_video_entry:
            # Video stills link to the gallery viewer so the clip can play.
            slides.append(
                f'          <div class="share-slide{" is-active" if i == 0 else ""}"'
                f' data-cap="{a(cap)}">'
                f'<a href="{a(viewer_url)}" aria-label="Play {a(title)} in the viewer">'
                f'<img src="/{a(file)}" alt="{a(img_alt or title)}" {eager} '
                f'decoding="async" draggable="false"></a></div>'
            )
        else:
            # Photo opens the in-page lightbox (JS intercepts via .share-open +
            # data-idx). Fallback href -> gallery viewer for no-JS / crawlers.
            gidx = (global_start + i) if (global_start is not None) else i
            slides.append(
                f'          <div class="share-slide{" is-active" if i == 0 else ""}"'
                f' data-cap="{a(cap)}">'
                f'<a class="share-open" data-idx="{gidx}" href="{a(viewer_url)}"'
                f' aria-label="Open {a(title)} full screen">'
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

    # ── full-screen lightbox (photo entries only) ──
    # Opens in place on click; URL stays put. Pinch to zoom (no click-to-zoom);
    # arrows cycle the whole gallery. Video entries are skipped.
    lightbox_html = ""
    lightbox_script = ""
    lb_all = all_photos if all_photos else []
    if not is_video_entry and lb_all:
        lb_json = json.dumps(lb_all, ensure_ascii=False).replace("<", "\\u003c")
        lb_arrows = lb_count = ""
        if len(lb_all) > 1:
            lb_arrows = (
                '\n    <button class="slb-arrow prev" type="button" aria-label="Previous photo">‹</button>'
                '\n    <button class="slb-arrow next" type="button" aria-label="Next photo">›</button>'
            )
            lb_count = '\n    <div class="slb-count" aria-live="polite"></div>'
        lightbox_html = (
            '\n  <div class="share-lightbox" id="shareLightbox" aria-hidden="true"'
            ' role="dialog" aria-modal="true" aria-label="' + a(title) + ' — full screen">'
            '\n    <button class="slb-close" type="button" aria-label="Close full screen">✕</button>'
            '\n    <button class="slb-share" type="button" aria-label="Share this photo">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
            ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle>'
            '<circle cx="18" cy="19" r="3"></circle>'
            '<line x1="8.6" y1="10.5" x2="15.4" y2="6.5"></line>'
            '<line x1="8.6" y1="13.5" x2="15.4" y2="17.5"></line></svg></button>'
            + lb_arrows
            + '\n    <div class="slb-stage"><img class="slb-img" src="" alt="" draggable="false"></div>'
            + lb_count
            + '\n  </div>'
        )
        lightbox_script = (
            "  <script>\n"
            "    (function(){\n"
            f"      var media = {lb_json};\n"
            "      var box = document.getElementById('shareLightbox');\n"
            "      if (!box || !media.length) return;\n"
            "      var img   = box.querySelector('.slb-img');\n"
            "      var stage = box.querySelector('.slb-stage');\n"
            "      var count = box.querySelector('.slb-count');\n"
            "      var multi = media.length > 1;\n"
            "      var i = 0, lastFocus = null;\n"
            "      function render(){\n"
            "        var m = media[i];\n"
            "        img.src = m.src; img.alt = m.alt || '';\n"
            "        if (count) count.textContent = (i + 1) + ' / ' + media.length;\n"
            "      }\n"
            "      function open(n){\n"
            "        i = ((n || 0) % media.length + media.length) % media.length;\n"
            "        lastFocus = document.activeElement;\n"
            "        render();\n"
            "        box.classList.add('is-open');\n"
            "        box.setAttribute('aria-hidden', 'false');\n"
            "        document.body.classList.add('slb-lock');\n"
            "        var c = box.querySelector('.slb-close'); if (c) c.focus();\n"
            "      }\n"
            "      function close(){\n"
            "        box.classList.remove('is-open');\n"
            "        box.setAttribute('aria-hidden', 'true');\n"
            "        document.body.classList.remove('slb-lock');\n"
            "        img.src = '';\n"
            "        if (lastFocus && lastFocus.focus) lastFocus.focus();\n"
            "      }\n"
            "      function step(d){ if (multi){ i = (i + d + media.length) % media.length; render(); } }\n"
            "      var opens = document.querySelectorAll('a.share-open');\n"
            "      for (var k = 0; k < opens.length; k++){\n"
            "        opens[k].addEventListener('click', function(e){\n"
            "          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;\n"
            "          e.preventDefault();\n"
            "          open(parseInt(this.getAttribute('data-idx'), 10) || 0);\n"
            "        });\n"
            "      }\n"
            "      var cb = box.querySelector('.slb-close'); if (cb) cb.addEventListener('click', close);\n"
            "      var pb = box.querySelector('.slb-arrow.prev'); if (pb) pb.addEventListener('click', function(){ step(-1); });\n"
            "      var nb = box.querySelector('.slb-arrow.next'); if (nb) nb.addEventListener('click', function(){ step(1); });\n"
            "      box.addEventListener('click', function(e){ if (e.target === box) close(); });\n"
            "      var moved = false;\n"
            "      img.addEventListener('click', function(){\n"
            "        if (moved) { moved = false; return; }  /* a swipe, not a tap */\n"
            "        var pg = media[i] && media[i].page;\n"
            "        if (pg) window.location.href = pg;      /* go to this photo's share page */\n"
            "      });\n"
            "      document.addEventListener('keydown', function(e){\n"
            "        if (!box.classList.contains('is-open')) return;\n"
            "        var _sm=document.getElementById('shareMenu'); if(_sm && _sm.classList.contains('open')) return;\n"
            "        if (e.key === 'Escape' || e.key === 'ArrowLeft' || e.key === 'ArrowRight'){\n"
            "          e.preventDefault(); e.stopPropagation();\n"
            "        }\n"
            "        if (e.key === 'Escape') close();\n"
            "        else if (e.key === 'ArrowLeft') step(-1);\n"
            "        else if (e.key === 'ArrowRight') step(1);\n"
            "      }, true);\n"
            "      var sx = 0, sy = 0, swiping = false;\n"
            "      stage.addEventListener('touchstart', function(e){\n"
            "        if (e.touches.length !== 1){ swiping = false; return; }\n"
            "        sx = e.touches[0].clientX; sy = e.touches[0].clientY; swiping = true;\n"
            "      }, { passive: true });\n"
            "      stage.addEventListener('touchend', function(e){\n"
            "        if (!swiping) return; swiping = false;\n"
            "        var tt = e.changedTouches[0];\n"
            "        var dx = tt.clientX - sx, dy = tt.clientY - sy;\n"
            "        if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) { moved = true; step(dx < 0 ? 1 : -1); }\n"
            "      }, { passive: true });\n"
            "      var shareBtn = box.querySelector('.slb-share');\n"
            "      if (shareBtn) shareBtn.addEventListener('click', function(e){ e.stopPropagation(); if(window.openShareMenu){ window.openShareMenu({url:(media[i].share||media[i].page||location.href), title:(media[i].alt||document.title), image:media[i].src}); } });\n"
            "    })();\n"
            "  </script>\n"
        )

    # ── share menu (Copy link / WhatsApp / X / Facebook / Email / Share…) ──
    # One menu opened by the page's Share button OR the lightbox share icon via
    # window.openShareMenu({url,title,image}). Per-network share links (X uses
    # the composer, which cards from og:image) — the way that shares reliably.
    def _j(v):
        return json.dumps(v, ensure_ascii=False).replace("<", "\\u003c")
    share_file = f"/{cover}"

    _IC = {
        "native": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 10V2"/><path d="M5 5l3-3 3 3"/><path d="M3.5 8v5.5h9V8"/></svg>',
        "copy": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6.4 9.6l3.2-3.2"/><path d="M7.2 5.2l1.1-1.1a2.6 2.6 0 0 1 3.6 3.6l-1.1 1.1"/><path d="M8.8 10.8l-1.1 1.1a2.6 2.6 0 0 1-3.6-3.6l1.1-1.1"/></svg>',
        "whatsapp": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 13.4l.85-2.9A5.6 5.6 0 1 1 8 13.6a5.6 5.6 0 0 1-2.55-.62z"/><path d="M6 6c.15-.4.3-.4.55-.4.2 0 .45.05.6.5.15.45.45 1 .5 1.1.05.1.05.25-.05.4-.25.35-.4.45-.2.7.35.5.85.85 1.35 1.05.2.08.35.05.5-.1.15-.2.45-.55.6-.75"/></svg>',
        "x": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><line x1="3.6" y1="3.6" x2="12.4" y2="12.4"/><line x1="12.4" y1="3.6" x2="3.6" y2="12.4"/></svg>',
        "facebook": '<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M9.6 14V8.4h1.9l.3-2.2H9.6V4.8c0-.64.18-1.07 1.1-1.07h1.17V1.76A15.6 15.6 0 0 0 10.16 1.6c-1.7 0-2.86 1.04-2.86 2.94v1.66H5.4v2.2h1.9V14z"/></svg>',
        "email": '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.2" y="3.6" width="11.6" height="8.8" rx="1.4"/><path d="M2.6 4.4L8 8.6l5.4-4.2"/></svg>',
    }
    def _item(net, label):
        return (f'\n    <button class="sm-item" data-share="{net}" role="menuitem" type="button">'
                f'{_IC[net]}<span class="sm-lbl">{label}</span></button>')

    sharemenu_html = (
        '\n  <div class="sm-backdrop" id="smBackdrop" aria-hidden="true"></div>'
        '\n  <div class="share-menu" id="shareMenu" role="menu" aria-label="Share options" aria-hidden="true">'
        '\n    <div class="sm-title">Share</div>'
        + _item("native", "Share\u2026")
        + _item("copy", "Copy link")
        + _item("whatsapp", "WhatsApp")
        + _item("x", "X")
        + _item("facebook", "Facebook")
        + _item("email", "Email")
        + '\n  </div>'
    )

    sharemenu_script = (
        "  <script>\n"
        "    (function(){\n"
        "      var menu = document.getElementById('shareMenu'), backdrop = document.getElementById('smBackdrop');\n"
        "      if (!menu) return;\n"
        "      var cur = null;\n"
        "      var nat = menu.querySelector('[data-share=\"native\"]'); if (nat && !navigator.share) nat.style.display = 'none';\n"
        "      function openM(t){ cur = t; menu.classList.add('open'); backdrop.classList.add('open'); menu.setAttribute('aria-hidden','false'); var f=menu.querySelector('.sm-item'); if(f) f.focus(); }\n"
        "      function closeM(){ menu.classList.remove('open'); backdrop.classList.remove('open'); menu.setAttribute('aria-hidden','true'); }\n"
        "      window.openShareMenu = openM;\n"
        "      function flashCopy(btn){ if(!btn) return; var l=btn.querySelector('.sm-lbl'); var o=l?l.textContent:''; if(l) l.textContent='Link copied!'; btn.classList.add('copied'); clearTimeout(flashCopy._t); flashCopy._t=setTimeout(function(){ if(l) l.textContent=o; btn.classList.remove('copied'); }, 1400); }\n"
        "      function doCopy(btn){ var url=cur.url; if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(url).then(function(){flashCopy(btn);}, function(){fbCopy(url,btn);}); } else fbCopy(url,btn); }\n"
        "      function fbCopy(url,btn){ try{ var ta=document.createElement('textarea'); ta.value=url; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); flashCopy(btn);}catch(_){} }\n"
        "      function jpeg(blob){ return new Promise(function(res){ var o=URL.createObjectURL(blob), im=new Image(); im.onload=function(){ try{ var c=document.createElement('canvas'); c.width=im.naturalWidth||1200; c.height=im.naturalHeight||800; var x=c.getContext('2d'); x.fillStyle='#050414'; x.fillRect(0,0,c.width,c.height); x.drawImage(im,0,0); c.toBlob(function(b){ URL.revokeObjectURL(o); res(b); },'image/jpeg',0.9);}catch(_){URL.revokeObjectURL(o);res(null);} }; im.onerror=function(){URL.revokeObjectURL(o);res(null);}; im.src=o; }); }\n"
        "      async function mkfile(src){ try{ var r=await fetch(src,{cache:'force-cache'}); if(!r.ok) return null; var b=await r.blob(); var base=(src.split('/').pop()||'image').replace(/\\.[^.]+$/,''); var j=await jpeg(b); if(j) return new File([j],base+'.jpg',{type:'image/jpeg'}); return new File([b],base+'.webp',{type:b.type||'image/webp'}); }catch(_){ return null; } }\n"
        "      async function nativeShare(){ var f=cur.image?await mkfile(cur.image):null; try{ if(f && navigator.canShare && navigator.canShare({files:[f]})){ await navigator.share({files:[f], title:cur.title, text:cur.title, url:cur.url}); return; } }catch(_){ return; } try{ await navigator.share({title:cur.title, text:cur.title, url:cur.url}); }catch(_){} }\n"
        "      function shareTo(net){ var url=cur.url, text=cur.title; var u=encodeURIComponent(url), t=encodeURIComponent(text), ti=encodeURIComponent(text); var tgt=''; if(net==='whatsapp') tgt='https://wa.me/?text='+encodeURIComponent(text+' '+url); else if(net==='x') tgt='https://twitter.com/intent/tweet?url='+u+'&text='+t; else if(net==='facebook') tgt='https://www.facebook.com/sharer/sharer.php?u='+u; else if(net==='email') tgt='mailto:?subject='+ti+'&body='+encodeURIComponent(text+'\\n\\n'+url); if(!tgt) return; if(net==='email') window.location.href=tgt; else window.open(tgt,'_blank','noopener,noreferrer'); }\n"
        "      menu.addEventListener('click', function(e){ var btn=e.target.closest('[data-share]'); if(!btn) return; var net=btn.dataset.share; if(net==='copy'){ doCopy(btn); return; } if(net==='native'){ closeM(); nativeShare(); return; } shareTo(net); closeM(); });\n"
        "      backdrop.addEventListener('click', closeM);\n"
        "      document.addEventListener('keydown', function(e){ if(e.key==='Escape' && menu.classList.contains('open')){ e.stopPropagation(); closeM(); } }, true);\n"
        f"      var PAGE = {_j(share_url)}, TITLE = {_j(title)}, IMG = {_j(share_file)};\n"
        "      var pb = document.getElementById('shareBtn'); if (pb) pb.addEventListener('click', function(){ openM({url:PAGE, title:TITLE, image:IMG}); });\n"
        "    })();\n"
        "  </script>\n"
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
        <button class="btn" id="shareBtn" type="button">Share</button>
      </div>

{slides_script}{nav_html}
    </div>
  </section>
</main>
{lightbox_html}
{lightbox_script}
{sharemenu_html}
{sharemenu_script}
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

    # Global, gallery-ordered list of every photo so the lightbox arrows cycle
    # the whole collection. Video entries excluded (they open in the gallery
    # viewer to play). entry_photo_start[slug] = global index of its 1st photo.
    all_photos = []
    entry_photo_start = {}
    for e in pageable:
        if e.get("videos"):
            continue
        entry_photo_start[e["slug"]] = len(all_photos)
        page = f"/{OUT_DIR}/{e['slug']}.html"
        share = f"{DOMAIN}/{OUT_DIR}/{e['slug']}.html"
        for file, alt in entry_media(e):
            all_photos.append({"src": f"/{file}",
                               "alt": alt or e.get("title") or "",
                               "page": page,
                               "share": share})

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

        page = build_page(entry, prev_link, next_link,
                          all_photos, entry_photo_start.get(entry["slug"]))
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
