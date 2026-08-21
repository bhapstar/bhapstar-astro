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
import re
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

# ── Capture-detail gear linking ───────────────────────────────────────────────
# Where a capture spec names a piece of kit that has its own gear page, the
# value in the specs panel becomes a link to /gear/<slug>.html.
#
# Two sources feed the lookup:
#   1. Every gear entry in site-data.json contributes its own title and slug as
#      aliases automatically, so new gear links itself with no edits here.
#   2. GEAR_ALIASES below covers the shorthand actually used in the specs
#      fields, which rarely matches the full product title.
#
# Only telescope / camera / filter values are linked. Integration, location and
# date are never gear.
GEAR_DIR = "gear"
LINKABLE_SPEC_KEYS = {"telescope", "camera", "filter"}
SPEC_VALUE_SKIP = {"none", "various", "n a", "na", "tbc", "unknown"}

GEAR_ALIASES = {
    # telescopes
    "askar v":              "askar-v-modular-apo-refractor",
    "evostar 72ed":         "skywatcher-evostar-72ed-refractor",
    "seestar s30 pro":      "zwo-seestar-s30-pro",
    "seestar s30":          "zwo-seestar-s30-smart-telescope",
    "seestar":              "zwo-seestar-s30-smart-telescope",
    # lenses used as astrographs
    "samyang 135mm":        "samyang-135mm-widefield-astrograph",
    "samyang 135":          "samyang-135mm-widefield-astrograph",
    "rokinon 18mm":         "rokinon-18mm-samyang-14mm-ultrawides",
    "rokinon 18":           "rokinon-18mm-samyang-14mm-ultrawides",
    "samyang 14mm":         "rokinon-18mm-samyang-14mm-ultrawides",
    "samyang 14":           "rokinon-18mm-samyang-14mm-ultrawides",
    # cameras
    "sony a7 iii":          "sony-a7iii-full-frame-camera",
    "sony a7iii":           "sony-a7iii-full-frame-camera",
    "a7 iii":               "sony-a7iii-full-frame-camera",
    "a7iii":                "sony-a7iii-full-frame-camera",
    "zwo asi585mc air":     "zwo-asi585mc-air-camera",
    "asi585mc air":         "zwo-asi585mc-air-camera",
    "asi585mc":             "zwo-asi585mc-air-camera",
    "zwo asi585":           "zwo-asi585mc-air-camera",
    "asi585":               "zwo-asi585mc-air-camera",
    # filters — note the L-Quad entries in site-data.json spell it "Enance",
    # so both spellings are covered here rather than editing the data.
    "optolong l extreme":   "optolong-l-extreme-filter",
    "l extreme":            "optolong-l-extreme-filter",
    "optolong l quad enhance": "optolong-l-quad-enhance-filter",
    "optolong l quad enance":  "optolong-l-quad-enhance-filter",
    "l quad enhance":       "optolong-l-quad-enhance-filter",
    "l quad enance":        "optolong-l-quad-enhance-filter",
    "l quad":               "optolong-l-quad-enhance-filter",
    "svbony sv220":         "svbony-sv220-3nm-filter",
    "sv220":                "svbony-sv220-3nm-filter",
}

# Aliases shorter than this are only matched when the spec value is exactly
# that alias, never as a fragment of a longer value.
MIN_FRAGMENT_ALIAS = 6

_GEAR_LINKS = {}        # normalised alias -> slug
_GEAR_UNMATCHED = set()  # spec values with no gear page, for the run summary
_GEAR_NO_PAGE = set()    # matched slugs whose gear page file is missing


def norm_spec(value):
    """Lowercase, strip punctuation, collapse spaces — 'Optolong L-eXtreme'
    and 'optolong l extreme' both become 'optolong l extreme'."""
    s = html.unescape(str(value or "")).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def build_gear_index(items):
    """Build the alias -> slug lookup from site-data.json plus GEAR_ALIASES."""
    gear = [e for e in items
            if e.get("section") == "gear" and e.get("slug")]
    slugs = {e["slug"] for e in gear}

    idx = {}
    for e in gear:
        for cand in (e.get("title"), e["slug"].replace("-", " ")):
            key = norm_spec(cand)
            if key:
                idx.setdefault(key, e["slug"])
    for alias, slug in GEAR_ALIASES.items():
        if slug in slugs:
            idx[norm_spec(alias)] = slug
        else:
            print(f"  ! gear alias '{alias}' points at '{slug}', which is not "
                  f"in {DATA} — ignored", file=sys.stderr)

    _GEAR_LINKS.clear()
    _GEAR_LINKS.update(idx)


def gear_slug_for(key, value):
    """Slug of the gear page this spec value refers to, or None."""
    if key not in LINKABLE_SPEC_KEYS:
        return None
    n = norm_spec(value)
    if not n or n in SPEC_VALUE_SKIP:
        return None
    if n in _GEAR_LINKS:
        return _GEAR_LINKS[n]
    # Longest alias first, so 'zwo seestar s30 pro' never loses to 'seestar s30'.
    for alias in sorted(_GEAR_LINKS, key=len, reverse=True):
        if len(alias) < MIN_FRAGMENT_ALIAS:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", n):
            return _GEAR_LINKS[alias]
    _GEAR_UNMATCHED.add(f"{key}: {value}")
    return None


def gear_href(slug):
    """Root-absolute href for a gear page, or None if the page doesn't exist
    yet (run generate-gear-pages.py first and the link appears next time)."""
    if not slug:
        return None
    if not os.path.exists(os.path.join(GEAR_DIR, f"{slug}.html")):
        _GEAR_NO_PAGE.add(slug)
        return None
    return f"/{GEAR_DIR}/{slug}.html"


# Page-specific styles. Everything else comes from /styles.css so these pages
# always match the site theme. Kept as a plain constant (not an f-string) so
# the CSS braces don't need escaping.
PAGE_STYLE = ""   # moved to /styles.css (PAGE: Share pages)


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
    viewer_url_base = "/gallery.html"
    viewer_url = f"{viewer_url_base}#{slug}"
    iso_date = to_iso(entry.get("date"))
    nice_date = display_date(entry.get("date"))

    specs = entry.get("specs") or {}

    # ── figures ──
    # The corner pill telling people the picture opens. Six desert sessions
    # showed that without it nobody worked out the photo was tappable — a
    # picture that fills the screen reads as the page, not as a control.
    _EXPAND_SVG = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"'
                   ' stroke-width="1.5" stroke-linecap="round"'
                   ' stroke-linejoin="round" aria-hidden="true">'
                   '<path d="M6.2 2.4H2.4v3.8"/><path d="M9.8 2.4h3.8v3.8"/>'
                   '<path d="M13.6 9.8v3.8H9.8"/><path d="M2.4 9.8v3.8h3.8"/></svg>')
    _PLAY_SVG = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"'
                 ' stroke-width="1.5" stroke-linecap="round"'
                 ' stroke-linejoin="round" aria-hidden="true">'
                 '<circle cx="8" cy="8" r="6.1"/><path d="M6.6 5.5l4 2.5-4 2.5z"/></svg>')

    def hint(icon, tap, click):
        return (f'<span class="share-hint" aria-hidden="true">{icon}'
                f'<span class="sh-lbl" data-tap="{a(tap)}"'
                f' data-click="{a(click)}"></span></span>')

    photo_hint = hint(_EXPAND_SVG, "Tap to view full screen",
                      "Click to view full screen")
    video_hint = hint(_PLAY_SVG, "Tap to play", "Click to play")

    # ── figures ──
    # Page-to-page navigation lives in the bar above the title, not on the
    # image. The only controls over a picture are the pager for entries with
    # several pictures, and the lightbox arrows once one is opened.

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
            # ?v=N (1-based) tells the viewer which clip to open, otherwise
            # every poster on the page opens the first one. A viewer that does
            # not understand the parameter ignores it and opens at clip 1,
            # which is the old behaviour rather than a broken link.
            clip_href = f'{viewer_url_base}?v={i + 1}#{slug}'
            clip_label = (f'Play {title} video {i + 1} of {len(media)} in the viewer'
                          if multi else f'Play {title} in the viewer')
            slides.append(
                f'          <div class="share-slide{" is-active" if i == 0 else ""}"'
                f' data-cap="{a(cap)}">'
                f'<a href="{a(clip_href)}" aria-label="{a(clip_label)}">'
                f'<img src="/{a(file)}" alt="{a(img_alt or title)}" {eager} '
                f'decoding="async" draggable="false">{video_hint}</a></div>'
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
                f'decoding="async" draggable="false">{photo_hint}</a></div>'
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
    rows = [(key, label, specs.get(key) if key != "date" else nice_date, icon)
            for key, label, icon in SPEC_ICONS]
    rows = [(key, label, val, icon) for key, label, val, icon in rows
            if val and str(val).strip()]
    if rows:
        tile_list = []
        for key, lbl, val, icon in rows:
            val_html = t(val)
            href = gear_href(gear_slug_for(key, val))
            if href:
                val_html = f'<a href="{a(href)}">{val_html}</a>'
            tile_list.append(
                f'          <div class="share-spec" title="{a(lbl)}">'
                f'<span class="share-spec-ico" aria-hidden="true">{icon}</span>'
                f'<span class="share-spec-val">{val_html}</span>'
                f'<span class="sr-only">{t(lbl)}</span></div>')
        tiles = "\n".join(tile_list)
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

    # Previous / next item bar above the title, matching the gear and article
    # pages. Labelled with item titles so it reads as page navigation rather
    # than picture navigation, which the pager over the image handles.
    def top_nav_link(target, direction):
        if not target:
            return ""
        href, label_title = target
        arrow = "&#8592;" if direction == "prev" else "&#8594;"
        label = "Previous" if direction == "prev" else "Next"
        text = (f'<span class="gn-text"><span class="gn-label">{label}</span>'
                f'<span class="gn-title">{t(label_title)}</span></span>')
        mark = f'<span class="gn-arrow" aria-hidden="true">{arrow}</span>'
        inner = f"{mark}{text}" if direction == "prev" else f"{text}{mark}"
        return (f'        <a class="gear-nav-link gn-{direction}" href="{a(href)}" '
                f'rel="{direction}" aria-label="{label} item: {a(label_title)}">'
                f'{inner}</a>\n')

    topnav_html = ""
    if prev_link or next_link:
        topnav_html = ('      <nav class="gear-nav" aria-label="Gallery navigation">\n'
                       f'{top_nav_link(prev_link, "prev")}'
                       f'{top_nav_link(next_link, "next")}'
                       '      </nav>\n')

    # Keyboard shortcuts for the nav bar above: left / right move between items.
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
            "        resetZoom(); wake();\n"
            "      }\n"
            "      function close(){\n"
            "        box.classList.remove('is-open');\n"
            "        box.setAttribute('aria-hidden', 'true');\n"
            "        document.body.classList.remove('slb-lock');\n"
            "        if (dimT) { clearTimeout(dimT); dimT = null; }\n"
            "        box.classList.remove('slb-dim');\n"
            "        resetZoom();\n"
            "        img.src = '';\n"
            "        if (lastFocus && lastFocus.focus) lastFocus.focus();\n"
            "      }\n"
            "      function step(d){\n"
            "        if (!multi) return;\n"
            "        i = (i + d + media.length) % media.length;\n"
            "        render(); resetZoom(); wake();\n"
            "      }\n"
            "      /* Controls rest visible, then fade back so the picture is the\n"
            "         only thing on screen. Any touch, drag or key brings them back. */\n"
            "      var dimT = null;\n"
            "      function wake(){\n"
            "        box.classList.remove('slb-dim');\n"
            "        if (dimT) clearTimeout(dimT);\n"
            "        dimT = setTimeout(function(){\n"
            "          if (box.classList.contains('is-open')) box.classList.add('slb-dim');\n"
            "        }, 2600);\n"
            "      }\n"
            "      var opens = document.querySelectorAll('a.share-open');\n"
            "      for (var k = 0; k < opens.length; k++){\n"
            "        opens[k].addEventListener('click', function(e){\n"
            "          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;\n"
            "          e.preventDefault();\n"
            "          open(parseInt(this.getAttribute('data-idx'), 10) || 0);\n"
            "        });\n"
            "      }\n"
            "      function goToCurrent(){\n"
            "        var pg = media[i] && media[i].page;\n"
            "        /* Land on the photo currently shown. If that is the page we\n"
            "           are already on (or the item has no page), just close. */\n"
            "        if (pg && pg !== location.pathname) window.location.href = pg;\n"
            "        else close();\n"
            "      }\n"
            "      var cb = box.querySelector('.slb-close'); if (cb) cb.addEventListener('click', goToCurrent);\n"
            "      var pb = box.querySelector('.slb-arrow.prev'); if (pb) pb.addEventListener('click', function(){ step(-1); });\n"
            "      var nb = box.querySelector('.slb-arrow.next'); if (nb) nb.addEventListener('click', function(){ step(1); });\n"
            "      box.addEventListener('click', function(e){ if (e.target === box) close(); });\n"
            "      /* Tapping the picture opens the page for whatever is on screen.\n"
            "         Guarded twice: a tap that followed a drag is a pan finishing,\n"
            "         and a tap while zoomed in is someone inspecting detail. Only\n"
            "         a clean tap at fit-to-screen counts as 'take me to this one'. */\n"
            "      /* No waiting any more. Zoom moved to the wheel, so a click can\n"
            "         never be the first half of something else and fires at once. */\n"
            "      img.addEventListener('click', function(){\n"
            "        if (dragged) { dragged = false; return; }\n"
            "        if (scale > 1.02) return;   /* zoomed in: inspecting, not leaving */\n"
            "        goToCurrent();\n"
            "      });\n"
            "      document.addEventListener('keydown', function(e){\n"
            "        if (!box.classList.contains('is-open')) return;\n"
            "        var _sm=document.getElementById('shareMenu'); if(_sm && _sm.classList.contains('open')) return;\n"
            "        if (e.key === 'Escape' || e.key === 'ArrowLeft' || e.key === 'ArrowRight'){\n"
            "          e.preventDefault(); e.stopPropagation();\n"
            "        }\n"
            "        wake();\n"
            "        if (e.key === 'Escape') close();\n"
            "        else if (e.key === 'ArrowLeft') step(-1);\n"
            "        else if (e.key === 'ArrowRight') step(1);\n"
            "      }, true);\n"
            "      /* ── Zoom and pan ──\n"
            "         Swipe-to-navigate is gone on purpose. It claimed the same\n"
            "         one-finger drag that panning needs, and you cannot have both.\n"
            "         The arrows do the cycling and say so; panning gets the finger. */\n"
            "      var scale = 1, tx = 0, ty = 0, MAXS = 4;\n"
            "      var pts = {}, nPts = 0, startDist = 0, startScale = 1;\n"
            "      var panning = false, dragged = false;\n"
            "      var ox = 0, oy = 0, otx = 0, oty = 0;\n"
            "      function applyT(){\n"
            "        img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';\n"
            "        /* Cursors are three CSS rules; this only says which applies.\n"
            "           Zoomed in, the picture becomes something you take hold of and\n"
            "           move, so grab, then grabbing while you actually hold it. */\n"
            "        var zin = scale > 1.02;\n"
            "        img.classList.toggle('is-zoomed', zin);\n"
            "        img.classList.toggle('is-panning', zin && !!panning);\n"
            "      }\n"
            "      function resetZoom(){ scale = 1; tx = 0; ty = 0; applyT(); }\n"
            "      var fine = !!(window.matchMedia &&\n"
            "        window.matchMedia('(hover: hover) and (pointer: fine)').matches);\n"
            "      /* ── Wheel zoom ──\n"
            "         A mouse has one pointer and so can never pinch. Double-click was\n"
            "         the first attempt and it was a poor one: it fought the click that\n"
            "         opens the page, which forced a delay onto every click, and it only\n"
            "         offered one zoom step. The wheel is continuous, needs no timing,\n"
            "         and is what people already reach for. */\n"
            "      var wheelT = null;\n"
            "      stage.addEventListener('wheel', function(e){\n"
            "        e.preventDefault();\n"
            "        var d = e.deltaY;\n"
            "        /* deltaMode 1 is lines and 2 is pages; without this a mouse that\n"
            "           reports lines would zoom about sixteen times too slowly. */\n"
            "        if (e.deltaMode === 1) d *= 16;\n"
            "        else if (e.deltaMode === 2) d *= window.innerHeight;\n"
            "        var ns = Math.min(MAXS, Math.max(1, scale * Math.exp(-d * 0.0022)));\n"
            "        if (ns === scale) return;\n"
            "        /* Keep whatever is under the cursor under the cursor. The picture\n"
            "           is centred in the viewport, so its untransformed centre is just\n"
            "           the middle of the window, offset by the current pan. */\n"
            "        var midX = window.innerWidth / 2 + tx;\n"
            "        var midY = window.innerHeight / 2 + ty;\n"
            "        var r = ns / scale;\n"
            "        tx += (e.clientX - midX) - (e.clientX - midX) * r;\n"
            "        ty += (e.clientY - midY) - (e.clientY - midY) * r;\n"
            "        scale = ns;\n"
            "        if (scale <= 1.02){ scale = 1; tx = 0; ty = 0; }\n"
            "        clampT(); applyT(); wake();\n"
            "        /* Easing fights a wheel: each notch would lag behind the last.\n"
            "           Suspend it, and put it back once the wheel goes quiet. */\n"
            "        img.classList.add('is-gesturing');\n"
            "        if (wheelT) clearTimeout(wheelT);\n"
            "        wheelT = setTimeout(function(){ img.classList.remove('is-gesturing'); }, 160);\n"
            "      }, { passive: false });\n"
            "      /* Keep the picture covering the screen: you can never drag it\n"
            "         so far that empty space appears at an edge. */\n"
            "      function clampT(){\n"
            "        var w = img.clientWidth * scale, h = img.clientHeight * scale;\n"
            "        var mx = Math.max(0, (w - window.innerWidth) / 2);\n"
            "        var my = Math.max(0, (h - window.innerHeight) / 2);\n"
            "        tx = Math.min(mx, Math.max(-mx, tx));\n"
            "        ty = Math.min(my, Math.max(-my, ty));\n"
            "      }\n"
            "      function spread(){\n"
            "        var k = Object.keys(pts); if (k.length < 2) return 0;\n"
            "        var a = pts[k[0]], b = pts[k[1]];\n"
            "        return Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2));\n"
            "      }\n"
            "      function anchorOne(){\n"
            "        var k = Object.keys(pts); if (!k.length) return;\n"
            "        ox = pts[k[0]].x; oy = pts[k[0]].y; otx = tx; oty = ty;\n"
            "        panning = scale > 1.02;\n"
            "        applyT();   /* show 'grabbing' on press, not on first move */\n"
            "      }\n"
            "      stage.addEventListener('pointerdown', function(e){\n"
            "        if (e.pointerType === 'mouse' && e.button !== 0) return;\n"
            "        pts[e.pointerId] = { x: e.clientX, y: e.clientY }; nPts++;\n"
            "        img.classList.add('is-gesturing');\n"
            "        wake();\n"
            "        if (nPts === 1){ dragged = false; anchorOne(); }\n"
            "        else if (nPts === 2){ panning = false; startDist = spread(); startScale = scale; }\n"
            "      });\n"
            "      stage.addEventListener('pointermove', function(e){\n"
            "        if (!(e.pointerId in pts)) { wake(); return; }\n"
            "        pts[e.pointerId] = { x: e.clientX, y: e.clientY };\n"
            "        if (nPts >= 2){\n"
            "          if (startDist > 0){\n"
            "            scale = Math.min(MAXS, Math.max(1, startScale * (spread() / startDist)));\n"
            "            if (scale <= 1.02){ tx = 0; ty = 0; }\n"
            "            dragged = true; clampT(); applyT();\n"
            "          }\n"
            "        } else if (panning){\n"
            "          var dx = e.clientX - ox, dy = e.clientY - oy;\n"
            "          if (Math.abs(dx) > 6 || Math.abs(dy) > 6) dragged = true;\n"
            "          tx = otx + dx; ty = oty + dy; clampT(); applyT();\n"
            "        }\n"
            "      });\n"
            "      function endPt(e){\n"
            "        if (!(e.pointerId in pts)) return;\n"
            "        delete pts[e.pointerId]; nPts = Math.max(0, nPts - 1);\n"
            "        if (nPts < 2) startDist = 0;\n"
            "        if (nPts === 0){\n"
            "          panning = false; img.classList.remove('is-gesturing');\n"
            "          /* Let go just above fit and it settles back, so the picture\n"
            "             cannot be left a hair off centre. */\n"
            "          if (scale <= 1.02) resetZoom(); else { clampT(); applyT(); }\n"
            "          wake();\n"
            "        } else { anchorOne(); }   /* second finger lifted, carry on panning */\n"
            "      }\n"
            "      stage.addEventListener('pointerup', endPt);\n"
            "      stage.addEventListener('pointercancel', endPt);\n"
            "      stage.addEventListener('dragstart', function(e){ e.preventDefault(); });\n"
            "      box.addEventListener('pointermove', wake);\n"
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
        "      async function nativeShare(){ var f=cur.image?await mkfile(cur.image):null; try{ if(f && navigator.canShare && navigator.canShare({files:[f]})){ await navigator.share({files:[f]}); return; } }catch(_){ return; } try{ await navigator.share({title:cur.title, text:cur.title, url:cur.url}); }catch(_){} }\n"
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
<body class="page-share">

<!-- ── Header (injected by partials.js) ── -->
<div id="siteHeader"></div>

<main>
  <section class="section">
    <div class="wrap share-wrap">
{topnav_html}      <h1>{t(title)}</h1>

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
    build_gear_index(items)

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

    if _GEAR_NO_PAGE:
        print("  Gear matched but no page in "
              f"{GEAR_DIR}/ yet (run generate-gear-pages.py): "
              + ", ".join(sorted(_GEAR_NO_PAGE)))
    if _GEAR_UNMATCHED:
        print("  Capture values with no gear page (add to GEAR_ALIASES if "
              "they should link):")
        for miss in sorted(_GEAR_UNMATCHED):
            print(f"    - {miss}")


if __name__ == "__main__":
    main()
