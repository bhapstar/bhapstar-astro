#!/usr/bin/env python3
"""
generate-share-pages.py — bhapstar
-------------------------------------------------------------
Generates one tiny static share page per gallery photo, under share/<slug>.html.

Why this exists:
    When a gallery image is shared on X / Facebook / WhatsApp etc., those
    platforms' link crawlers fetch the URL, DO NOT run JavaScript, and
    IGNORE the "#slug" fragment. So a shared "gallery.html#some-slug" link
    is always scraped as plain "gallery.html", whose single static og:image
    is the site-wide preview (the Rosette). Every image ends up previewing
    as the Rosette.

    The fix: give each image its own real URL with its own Open Graph tags.
    Crawlers read the correct per-image title / description / image; humans
    are redirected (via JS, which crawlers don't run) straight to the image
    in the gallery.

    The share buttons in gallery.html point at share/<slug>.html instead of
    gallery.html#slug.

Idempotent: rewrites every page each run, and deletes any stale share/*.html
whose slug is no longer in site-data.json.

    python generate-share-pages.py
"""

import html
import json
import os
import sys

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT_DIR = "share"
SITE_NAME = "Bhapstar Astrophotography"


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


def build_page(entry):
    slug = entry["slug"]
    title = entry.get("title") or "Bhapstar Astrophotography"
    desc = entry.get("desc") or entry.get("intro") or ""
    cover = cover_file(entry)
    if not cover:
        return None

    alt = entry.get("alt") or title
    thumb_url = url_for(thumb_for(cover))
    share_url = f"{DOMAIN}/{OUT_DIR}/{slug}.html"
    gallery_url = f"{DOMAIN}/gallery.html#{slug}"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{a(title)} — {a(SITE_NAME)}</title>

  <!-- Thin redirect page: humans go to the gallery, crawlers read the tags below. -->
  <meta name="robots" content="noindex,follow" />
  <link rel="canonical" href="{a(gallery_url)}" />
  <meta name="description" content="{a(desc)}" />

  <!-- Open Graph (Facebook, WhatsApp, LinkedIn, Slack, Discord, …) -->
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{a(SITE_NAME)}" />
  <meta property="og:title" content="{a(title)}" />
  <meta property="og:description" content="{a(desc)}" />
  <meta property="og:image" content="{a(thumb_url)}" />
  <meta property="og:image:alt" content="{a(alt)}" />
  <meta property="og:url" content="{a(share_url)}" />

  <!-- Twitter / X -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{a(title)}" />
  <meta name="twitter:description" content="{a(desc)}" />
  <meta name="twitter:image" content="{a(thumb_url)}" />
  <meta name="twitter:image:alt" content="{a(alt)}" />

  <!-- JS redirect: crawlers don't run JS, so they stay and read the tags above.
       Humans are sent straight to the image in the gallery. -->
  <script>location.replace({{json_url}});</script>
  <style>
    body {{ margin:0; background:#050414; color:#c8c3eb;
           font-family:system-ui,sans-serif; display:grid; place-items:center;
           min-height:100vh; text-align:center; padding:24px; }}
    a {{ color:#a78bfa; }}
  </style>
</head>
<body>
  <p>Taking you to <a href="{a(gallery_url)}">{a(title)}</a>…</p>
</body>
</html>
""".replace("{json_url}", json.dumps(gallery_url))


def main():
    try:
        with open(DATA, "r", encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        print(f"Could not find {DATA}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)

    written = set()
    skipped = 0
    for entry in items:
        if entry.get("section", "gallery") != "gallery":
            continue
        slug = entry.get("slug")
        if not slug:
            continue
        page = build_page(entry)
        if page is None:
            skipped += 1
            continue
        fname = f"{slug}.html"
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
