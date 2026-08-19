#!/usr/bin/env python3
"""
generate-feed.py — bhapstar
-------------------------------------------------------------
Writes feed.xml at the repository root: an RSS 2.0 feed of the articles
in site-data.json, newest first.

    python generate-feed.py

Why this exists: feed readers, aggregators and a few community sites pick
up new posts automatically from a feed. Without one, every new article has
to be announced by hand. WordPress sites get this for free, which is part
of why they spread.

What goes in:
  - every entry with section "article", a slug, and no "hidden" flag
  - title, link, description (the desc field, as plain text), publication
    date, a stable guid, and the cover image as an <enclosure> so readers
    that show thumbnails have one

Gear pages are deliberately left out. To include them, add "gear" to
SECTIONS below; nothing else needs to change.

Dates in site-data.json are DD-MM-YYYY. RSS wants RFC 822, so they are
converted here. An entry with an unparseable date keeps its place in the
file order but is published as the epoch rather than crashing the build.
"""

import json
import os
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT = "feed.xml"

SITE_TITLE = "Fragments of the Universe — Bhapstar Astrophotography"
SITE_DESC = ("Astrophotography from a Dubai balcony and the dark skies of "
             "the UAE desert. Deep-sky images, gear notes and guides for "
             "anyone starting out under the stars.")
AUTHOR = "Bhapinder Singh"
LANGUAGE = "en-gb"

# Which site-data.json sections become feed items, and where their pages live.
SECTIONS = {
    "article": "articles",
    # "gear": "gear",
}

# Feed readers do not need the whole archive, and a shorter file is cheaper
# to fetch on every poll. Set to None for no limit.
MAX_ITEMS = 30


def parse_date(value):
    """DD-MM-YYYY -> aware datetime. Falls back to the epoch."""
    try:
        dt = datetime.strptime(value, "%d-%m-%Y")
        return dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.fromtimestamp(0, tz=timezone.utc)


def url_for(path):
    """Root-relative site path -> absolute URL, leaving absolute URLs alone."""
    if not path:
        return ""
    if path.startswith("http"):
        return path
    # Spaces are legal in the repo's image filenames but not in a URL.
    return f"{DOMAIN}/{path.lstrip('/')}".replace(" ", "%20")


def enclosure_for(entry):
    """<enclosure> for the cover image, if the file actually exists on disk.

    The path is checked rather than trusted, because a feed pointing at a
    missing image is worse than a feed with no image at all.
    """
    src = entry.get("file", "")
    if not src or src.startswith("http") or not os.path.isfile(src):
        return ""
    ext = os.path.splitext(src)[1].lower()
    mime = {".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".avif": "image/avif"}.get(ext)
    if not mime:
        return ""
    size = os.path.getsize(src)
    return (f'      <enclosure url="{escape(url_for(src))}" '
            f'length="{size}" type="{mime}" />\n')


def build_item(entry, out_dir):
    slug = entry.get("slug", "")
    link = f"{DOMAIN}/{out_dir}/{slug}.html"
    published = parse_date(entry.get("date"))
    category = entry.get("category", "")

    parts = [
        "    <item>\n",
        f"      <title>{escape(entry.get('title', ''))}</title>\n",
        f"      <link>{escape(link)}</link>\n",
        f'      <guid isPermaLink="true">{escape(link)}</guid>\n',
        f"      <pubDate>{format_datetime(published)}</pubDate>\n",
        f"      <description>{escape(entry.get('desc', ''))}</description>\n",
    ]
    if category:
        parts.append(f"      <category>{escape(category)}</category>\n")
    parts.append(enclosure_for(entry))
    parts.append("    </item>\n")
    return "".join(parts)


def main():
    with open(DATA, "r", encoding="utf-8") as f:
        items = json.load(f)

    entries = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        out_dir = SECTIONS.get(entry.get("section"))
        if not out_dir or not entry.get("slug") or entry.get("hidden"):
            continue
        entries.append((parse_date(entry.get("date")), entry, out_dir))

    entries.sort(key=lambda t: t[0], reverse=True)
    if MAX_ITEMS:
        entries = entries[:MAX_ITEMS]

    # lastBuildDate tracks the newest post, not the moment this ran, so a
    # rebuild that changed nothing does not produce a different file.
    latest = entries[0][0] if entries else datetime.now(timezone.utc)

    body = "".join(build_item(e, d) for _, e, d in entries)

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{escape(SITE_TITLE)}</title>\n"
        f"    <link>{DOMAIN}/</link>\n"
        f"    <description>{escape(SITE_DESC)}</description>\n"
        f"    <language>{LANGUAGE}</language>\n"
        f"    <copyright>{escape(AUTHOR)}</copyright>\n"
        f"    <managingEditor>{escape(AUTHOR)}</managingEditor>\n"
        f"    <lastBuildDate>{format_datetime(latest)}</lastBuildDate>\n"
        f'    <atom:link href="{DOMAIN}/{OUT}" rel="self" '
        'type="application/rss+xml" />\n'
        f"    <image>\n"
        f"      <url>{DOMAIN}/images/icons/apple-touch-icon.png</url>\n"
        f"      <title>{escape(SITE_TITLE)}</title>\n"
        f"      <link>{DOMAIN}/</link>\n"
        f"    </image>\n"
        + body +
        "  </channel>\n"
        "</rss>\n"
    )

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"✓ {OUT}  ({len(entries)} items)")


if __name__ == "__main__":
    main()
