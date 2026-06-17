#!/usr/bin/env python3
"""
generate-sitemap.py — bhapstar
-------------------------------------------------------------
Rebuilds sitemap.xml from site-data.json so the image list never
goes stale. Run by the GitHub Action on every push, or by hand:

    python generate-sitemap.py

- site-data.json holds both gallery and gear entries, tagged with a
  "section" field ("gallery" or "gear").
- Gallery images are listed under gallery.html; gear images under
  gear.html. Each set is de-duplicated (shared files counted once).
- <lastmod> on content pages is set to today's date.
- Page list / priorities / changefreq are fixed below — edit here if
  you add or remove top-level pages.
"""

import json, sys, datetime
from urllib.parse import quote

DOMAIN   = "https://bhapstar.com/"
DATA     = "site-data.json"
OUT      = "sitemap.xml"
TODAY    = datetime.date.today().isoformat()

# (path, changefreq, priority, dynamic_lastmod, image_section)
# image_section: None = no images, else the "section" whose images go here.
PAGES = [
    ("",                        "monthly",  "1.0",  True,  None),
    ("gallery.html",            "monthly",  "0.9",  True,  "gallery"),
    ("gear.html",               "monthly",  "0.8",  True,  "gear"),
    ("prints.html",             "monthly",  "0.7",  False, None),
    ("jigsaw.html",             "yearly",   "0.6",  False, None),
    ("quiz.html",               "yearly",   "0.6",  False, None),
    ("supernova_sweeper.html",  "monthly",  "0.6",  True,  None),
    ("field_notes.html",        "monthly",  "0.8",  True,  None),
]
STATIC_LASTMOD = "2025-04-20"


def collect_images(items):
    urls = []
    for it in items:
        files = []
        if it.get("file"):
            files.append(it["file"])
        for im in it.get("images", []) or []:
            if im.get("file"):
                files.append(im["file"])
        for v in it.get("videos", []) or []:
            if v.get("poster"):
                files.append(v["poster"])
        for f in files:
            u = DOMAIN + quote(f)
            if u not in urls:
                urls.append(u)
    return urls


def image_block_for(items, section):
    sect_items = [it for it in items if (it.get("section") or "gallery") == section]
    urls = collect_images(sect_items)
    block = "\n".join(
        f"    <image:image>\n      <image:loc>{u}</image:loc>\n    </image:image>"
        for u in urls
    )
    return block, len(urls)


def main():
    with open(DATA, encoding="utf-8") as fh:
        items = json.load(fh)

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    counts = {}
    for path, freq, prio, dynamic, section in PAGES:
        lastmod = TODAY if dynamic else STATIC_LASTMOD
        out.append("  <url>")
        out.append(f"    <loc>{DOMAIN}{path}</loc>")
        out.append(f"    <lastmod>{lastmod}</lastmod>")
        out.append(f"    <changefreq>{freq}</changefreq>")
        out.append(f"    <priority>{prio}</priority>")
        if section:
            block, n = image_block_for(items, section)
            if block:
                out.append(block)
            counts[section] = n
        out.append("  </url>")
    out.append("</urlset>")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")

    print(f"Wrote {OUT}: {len(PAGES)} pages; images by section: {counts}")


if __name__ == "__main__":
    sys.exit(main())
