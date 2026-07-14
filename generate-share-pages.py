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

# Human-readable labels for the specs block, in display order.
SPEC_LABELS = [
    ("telescope",   "Telescope"),
    ("camera",      "Camera"),
    ("filter",      "Filter"),
    ("integration", "Integration"),
    ("location",    "Location"),
]

# Page-specific styles. Everything else comes from /styles.css so these pages
# always match the site theme. Kept as a plain constant (not an f-string) so
# the CSS braces don't need escaping.
PAGE_STYLE = """\
  <style>
    .share-wrap{ max-width: 900px; margin: 0 auto; }
    .share-date{ margin: 6px 0 26px; color: var(--muted); font-size: 14px; }
    .share-figure{ margin: 0 0 22px; }
    .share-figure img{
      display: block; width: 100%; height: auto; border-radius: 14px;
      border: 1px solid var(--line);
      box-shadow: 0 10px 40px rgba(0,0,0,0.45);
    }
    .share-figure figcaption{
      margin-top: 8px; color: var(--muted); font-size: 13px;
    }
    .share-body p{ color: var(--text); line-height: 1.7; margin: 0 0 16px; }
    .share-body .lead{ font-size: 17px; color: rgba(200,195,235,0.85); margin: 0 0 20px; }
    .share-specs{
      margin: 28px 0; padding: 18px 20px;
      border: 1px solid var(--line); border-radius: 14px;
      background: var(--soft);
    }
    .share-specs h2{
      margin: 0 0 12px; font-size: 13px; font-weight: 700;
      letter-spacing: 0.24em; text-transform: uppercase; color: var(--accent);
    }
    .share-specs dl{
      margin: 0; display: grid; grid-template-columns: auto 1fr;
      gap: 6px 18px; font-size: 14px;
    }
    .share-specs dt{ color: var(--muted); }
    .share-specs dd{ margin: 0; color: var(--text); }
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
    """Convert 'DD-MM-YYYY' to '27 December 2025'. Falls back to None."""
    try:
        d = datetime.strptime(date_str, "%d-%m-%Y")
        return f"{d.day} {d.strftime('%B %Y')}"
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

    # ── date / location line ──
    specs = entry.get("specs") or {}
    date_bits = [b for b in (nice_date, specs.get("location")) if b]
    date_line = (f'      <p class="share-date">{t(" · ".join(date_bits))}</p>\n'
                 if date_bits else "")

    # ── figures ──
    figures = []
    for i, (file, img_alt) in enumerate(media):
        eager = 'loading="eager" fetchpriority="high"' if i == 0 else 'loading="lazy"'
        caption = (f"\n        <figcaption>{t(img_alt)}</figcaption>"
                   if len(media) > 1 and img_alt else "")
        figures.append(
            f'      <figure class="share-figure">\n'
            f'        <a href="{a(viewer_url)}" aria-label="Open {a(title)} in the gallery viewer">'
            f'<img src="/{a(file)}" alt="{a(img_alt or title)}" {eager} '
            f'decoding="async" draggable="false"></a>{caption}\n'
            f'      </figure>'
        )
    figures_html = "\n".join(figures)
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

    # ── capture specs ──
    specs_html = ""
    rows = [(label, specs[key]) for key, label in SPEC_LABELS if specs.get(key)]
    if rows:
        dl = "\n".join(f"          <dt>{t(lbl)}</dt><dd>{t(val)}</dd>"
                       for lbl, val in rows)
        specs_html = (
            '      <div class="share-specs">\n'
            "        <h2>Capture details</h2>\n"
            "        <dl>\n" + dl + "\n        </dl>\n"
            "      </div>\n"
        )

    # ── prev / next ──
    nav_html = ""
    if prev_link or next_link:
        prev_a = (f'<a class="nav-prev" href="{a(prev_link[0])}">← {t(prev_link[1])}</a>'
                  if prev_link else "")
        next_a = (f'<a class="nav-next" href="{a(next_link[0])}">{t(next_link[1])} →</a>'
                  if next_link else "")
        nav_html = f'      <nav class="share-nav" aria-label="More images">{prev_a}{next_a}</nav>\n'

    viewer_label = "Watch in the gallery viewer" if is_video_entry else "Open in the gallery viewer"
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
{date_line}
{figures_html}

      <div class="share-body">
{body_html}
      </div>

{specs_html}
      <div class="actions">
        <a class="btn primary" href="{a(viewer_url)}">{t(viewer_label)}</a>
        <a class="btn" href="/prints.html">Order a print</a>
      </div>

{nav_html}
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
