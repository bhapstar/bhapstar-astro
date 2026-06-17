#!/usr/bin/env python3
"""
generate-sitemap.py — bhapstar
-------------------------------------------------------------
Rebuilds sitemap.xml from site-data.json so the image list never
goes stale. Run by the GitHub Action on every push, or by hand:

    python generate-sitemap.py

- Collects every full-size image + video poster from site-data.json
  and lists them as <image:image> entries under the gallery URL.
- De-duplicates shared images (e.g. star-trails files used by two posts).
- Sets <lastmod> on the content pages to today's date.
- Page list / priorities / changefreq are fixed below — edit here if
  you add or remove top-level pages.
"""

import json, sys, datetime
from urllib.parse import quote

DOMAIN   = "https://bhapstar.com/"
DATA     = "site-data.json"
OUT      = "sitemap.xml"
TODAY    = datetime.date.today().isoformat()

# Pages that change when content is added (get today's lastmod).
# Static pages keep a fixed lastmod so they don't churn needlessly.
PAGES = [
    # (path,                    changefreq, priority, dynamic_lastmod, carries_images)
    ("",                        "monthly",  "1.0",  True,  False),
    ("gallery.html",            "monthly",  "0.9",  True,  True),
    ("gear.html",               "yearly",   "0.8",  False, False),
    ("prints.html",             "monthly",  "0.7",  False, False),
    ("jigsaw.html",             "yearly",   "0.6",  False, False),
    ("quiz.html",               "yearly",   "0.6",  False, False),
    ("supernova_sweeper.html",  "monthly",  "0.6",  True,  False),
    ("field_notes.html",        "monthly",  "0.8",  True,  False),
]
STATIC_LASTMOD = "2025-04-20"   # used for the non-dynamic pages


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
            if u not in urls:          # de-dupe, preserve order
                urls.append(u)
    return urls


def main():
    with open(DATA, encoding="utf-8") as fh:
        items = json.load(fh)

    images = collect_images(items)
    image_block = "\n".join(
        f"    <image:image>\n      <image:loc>{u}</image:loc>\n    </image:image>"
        for u in images
    )

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for path, freq, prio, dynamic, carries in PAGES:
        lastmod = TODAY if dynamic else STATIC_LASTMOD
        out.append("  <url>")
        out.append(f"    <loc>{DOMAIN}{path}</loc>")
        out.append(f"    <lastmod>{lastmod}</lastmod>")
        out.append(f"    <changefreq>{freq}</changefreq>")
        out.append(f"    <priority>{prio}</priority>")
        if carries and image_block:
            out.append(image_block)
        out.append("  </url>")
    out.append("</urlset>")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")

    print(f"Wrote {OUT}: {len(PAGES)} pages, {len(images)} images.")


if __name__ == "__main__":
    sys.exit(main())
