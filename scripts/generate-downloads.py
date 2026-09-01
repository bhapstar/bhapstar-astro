#!/usr/bin/env python3
"""
generate-downloads.py — bhapstar
-------------------------------------------------------------
Writes field-cards.html: every printable field card on the site, in one
place, with a direct download for each.

    python generate-downloads.py

Why this page exists:

  Each card already sits at the bottom of the article it belongs to, which
  is the right place for a first-time reader. It is the wrong place for
  everybody else. Somebody who read the Moon article three months ago and
  wants the card again has to remember which article carried it, and a
  group standing in a car park has no chance of being given six article
  URLs. This page is the one address that holds all of them.

  The per-article blocks stay exactly as they are. This page is an extra
  door, not a replacement.

Where the content comes from:

  site-data.json, and nothing else. Any article entry carrying a
  "download" object appears here automatically:

      "download": {
        "file":  "downloads/moon-field-card.pdf",
        "label": "Moon field card",
        "note":  "One side of A4: ..."
      }

  That is the same object generate-article-pages.py reads for the block at
  the foot of the article, so the two can never disagree about what a card
  is called or what it holds. Adding a seventh card means adding a
  "download" object to its article and nothing else here.

  Nothing else is read. The cards carry no route tags: with six of them on
  one screen the tags were noise, and the note under each title already
  says who the card is for in plain words.

Why the headings live here and not in site-data.json:

  The "label" on a download is the text inside the button at the foot of
  the article, where the reader already knows what the article is about
  and a short name is the right one. "Moon field card" reads well there.

  On this page nobody has that context. Six cards sit side by side with no
  article around them, so each heading has to say what the download is on
  its own. HEADINGS below carries that longer wording, keyed by slug.

  This is the same split generate-start-here.py makes with its route
  blurbs: one field in site-data.json cannot phrase the same thing
  correctly for two audiences, so the page-specific wording lives with the
  page. A slug with no entry in HEADINGS falls back to its "label", so
  nothing breaks if one is forgotten.

Order:

  ORDER below, by slug. Broadly lightest kit first, so somebody arriving
  with a phone meets the phone card before the one that assumes a mount,
  but subject grouping wins where the two disagree: the phone and camera
  Milky Way cards sit together because a reader comparing them wants them
  side by side more than they want a strict kit ladder. A card whose slug
  is not in ORDER still appears, at the end, and the build prints a note
  so it does not stay unordered by accident.

Missing PDFs:

  A card is skipped with a warning rather than failing the build. The PDFs
  are built by a separate manual workflow (build-field-cards.yml), so
  there is a real window where site-data.json names a card that has not
  been generated yet. Halting the whole site build for that would be worse
  than quietly leaving one card off a page until the next push.

Page CSS lives in /styles.css under "PAGE: Field cards".
The page is fully generated, so editing field-cards.html by hand will be
overwritten on the next build. Change the copy below instead.
"""

import json
import os
import sys
from html import escape as esc

DOMAIN = "https://bhapstar.com"
DATA = "site-data.json"
OUT = "field-cards.html"
ARTICLE_DIR = "articles"
SHARE_IMAGE = "images/icons/og-preview.jpg"

PAGE_TITLE = "Field Cards"
PAGE_DESC = ("Every printable field card on the site in one place. One side "
             "of A4 each, free, no sign-up: the settings from the articles in "
             "a form you can read in the dark with no signal.")

SUBTITLE = "The settings from the articles, on paper, for the dark."

INTRO = ("Each card is one side of A4. Print it, fold it, put it in a "
         "pocket. It carries the settings from one article so you have them "
         "with you in the field without needing a phone, and it links back "
         "to that article if you want the reasoning behind the numbers.")

# Slug -> where the card sits in the reading order. Lightest kit first.
ORDER = [
    "photograph-milky-way-phone",
    "photograph-milky-way-camera",
    "photograph-a-meteor-shower",
    "photograph-the-moon",
    "asiair-astrophotography-control",
    "calibration-frames-darks-flats-biases",
]

# Slug -> the heading on this page. Longer and more literal than the button
# label on the article, because here it is doing all the explaining. Any slug
# left out falls back to the "label" in site-data.json.
HEADINGS = {
    "photograph-milky-way-phone":
        "Phone settings for imaging the Milky Way",
    "photograph-the-moon":
        "Camera and phone settings for imaging the Moon",
    "photograph-a-meteor-shower":
        "Meteor shower dates, rates and settings",
    "photograph-milky-way-camera":
        "Camera settings for imaging the Milky Way",
    "asiair-astrophotography-control":
        "Running a whole rig from the ASIAir",
    "calibration-frames-darks-flats-biases":
        "Which calibration frames to shoot, and when",
}

# Split so "Start Here" is a link on its first mention and plain text after.
# A second link to the same page in the same sentence adds nothing and makes
# the paragraph harder to scan.
CLOSING_BEFORE = ("New to all of this and not sure which card is the one to "
                  "take first, have a look at ")
CLOSING_LINK = ("start-here.html", "Start Here")
CLOSING_AFTER = (". It sorts the articles by what you already own rather "
                 "than by what you might buy.")


class BuildError(Exception):
    pass


# ---------------------------------------------------------------- data

def load_cards():
    """Every article entry carrying a download, in ORDER, then the rest."""
    with open(DATA, "r", encoding="utf-8") as f:
        items = json.load(f)

    found = {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        if entry.get("section") != "article" or entry.get("hidden"):
            continue
        slug = entry.get("slug")
        dl = entry.get("download") or {}
        if not slug or not dl.get("file"):
            continue
        found[slug] = entry

    if not found:
        raise BuildError("no article in site-data.json carries a "
                         "\"download\" object, so there is nothing to list")

    ordered = [found[s] for s in ORDER if s in found]
    extra = sorted(s for s in found if s not in ORDER)
    for slug in extra:
        print(f"  ! '{slug}' is not in ORDER, so it was placed last")
        ordered.append(found[slug])

    for slug in ORDER:
        if slug not in found:
            print(f"  ! ORDER lists '{slug}', which carries no download")

    return ordered


def file_size(path):
    """'26 KB', or None if the PDF is not on disk yet."""
    if not os.path.exists(path):
        return None
    kb = max(1, round(os.path.getsize(path) / 1024))
    return f"{kb} KB"


# ---------------------------------------------------------------- markup

DOWNLOAD_ICON = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" '
                 'stroke-width="1.7" stroke-linecap="round" '
                 'stroke-linejoin="round" aria-hidden="true">'
                 '<path d="M8 2v8"/><path d="M4.5 7L8 10.5 11.5 7"/>'
                 '<path d="M2.5 13h11"/></svg>')

READ_ICON = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" '
             'stroke-width="1.7" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true">'
             '<path d="M2.5 3.5h4a2 2 0 0 1 2 2v7a1.6 1.6 0 0 0-1.6-1.6H2.5z"/>'
             '<path d="M13.5 3.5h-4a2 2 0 0 0-2 2v7a1.6 1.6 0 0 1 1.6-1.6h4.4z"/>'
             '</svg>')


def build_card(entry, index):
    """One card.

    The title is a plain heading rather than a link. Two links to the same
    article inside one small card is a well-worn way to make a card feel
    fiddly, and the download is the reason somebody came to this page, so it
    keeps the only strong-looking control. "Read the article" is a proper
    outlined button beside it instead: clearly a second action, clearly not
    the main one.
    """
    dl = entry["download"]
    path = dl["file"].lstrip("/")
    slug = entry["slug"]
    label = (HEADINGS.get(slug)
             or dl.get("label")
             or entry.get("title")
             or "Field card")
    note = dl.get("note") or entry.get("desc") or ""
    heading_id = f"fcCard{index}"

    size = file_size(path)
    meta = f"PDF, one side of A4, {size}" if size else "PDF, one side of A4"

    return f'''        <li class="fc-card">
          <h2 class="fc-card-title" id="{heading_id}">{esc(label)}</h2>
          <p class="fc-note">{esc(note)}</p>
          <div class="fc-actions">
            <a class="fc-btn" href="/{esc(path)}" download
               aria-describedby="{heading_id}">{DOWNLOAD_ICON}<span>Download</span></a>
            <a class="fc-read" href="/{ARTICLE_DIR}/{esc(slug)}.html"
               aria-describedby="{heading_id}">{READ_ICON}<span>Read the article</span></a>
          </div>
          <p class="fc-meta">{esc(meta)}</p>
        </li>'''


def build_grid(cards):
    items = "\n".join(build_card(e, i) for i, e in enumerate(cards, 1))
    return f'''      <ul class="fc-grid" aria-label="Field cards">
{items}
      </ul>'''


def build_json_ld(cards):
    elements = []
    for i, entry in enumerate(cards, 1):
        dl = entry["download"]
        elements.append({
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "DigitalDocument",
                # Same wording as the visible heading, so what a search
                # result shows matches what the page shows.
                "name": (HEADINGS.get(entry["slug"])
                         or dl.get("label")
                         or entry.get("title")),
                "description": dl.get("note") or "",
                "encodingFormat": "application/pdf",
                "url": f"{DOMAIN}/{dl['file'].lstrip('/')}",
                "isAccessibleForFree": True,
            },
        })

    doc = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{PAGE_TITLE} — Bhapstar Astrophotography",
        "description": PAGE_DESC,
        "url": f"{DOMAIN}/{OUT}",
        "isPartOf": {"@type": "WebSite", "url": f"{DOMAIN}/"},
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(elements),
            "itemListElement": elements,
        },
    }
    return json.dumps(doc, indent=2, ensure_ascii=False)


def build_page(cards):
    page_url = f"{DOMAIN}/{OUT}"
    share_url = f"{DOMAIN}/{SHARE_IMAGE}"
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{esc(PAGE_TITLE)} — Bhapstar Astrophotography</title>
  <link rel="icon" href="/images/icons/favicon-32.png" sizes="32x32" type="image/png" />
  <link rel="apple-touch-icon" href="/images/icons/apple-touch-icon.png" />
  <meta name="theme-color" content="#050414" />
  <link rel="canonical" href="{esc(page_url)}" />
  <link rel="alternate" type="application/rss+xml" title="Fragments of the Universe" href="/feed.xml" />
  <meta name="description" content="{esc(PAGE_DESC)}" />
  <meta name="author" content="Bhapinder Singh" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(PAGE_TITLE)} — Bhapstar Astrophotography" />
  <meta property="og:description" content="{esc(PAGE_DESC)}" />
  <meta property="og:url" content="{esc(page_url)}" />
  <meta property="og:image" content="{esc(share_url)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(PAGE_TITLE)} — Bhapstar Astrophotography" />
  <meta name="twitter:description" content="{esc(PAGE_DESC)}" />
  <meta name="twitter:image" content="{esc(share_url)}" />
  <link rel="preconnect" href="https://static.cloudflareinsights.com" crossorigin />
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token":"b3353c7dd8764a64baee57fd09c3dbb9"}}'></script>
  <link rel="stylesheet" href="/styles.css" />

  <!-- Page CSS lives in /styles.css under "PAGE: Field cards". -->

  <script type="application/ld+json">
{build_json_ld(cards)}
  </script>
</head>
<body class="page-field-cards">

<!-- ── Header (injected by partials.js) ── -->
<div id="siteHeader"></div>

<main>
  <section class="section">
    <div class="wrap">

      <div class="section-head gallery-head fc-header">
        <div class="gallery-topline">
          <h1>{esc(PAGE_TITLE)}</h1>
        </div>
        <p class="fc-subtitle">{esc(SUBTITLE)}</p>
        <p class="fc-intro">{esc(INTRO)}</p>
        <p class="fc-free">Free, no sign-up needed. Every card opens or saves straight away.</p>
      </div>

{build_grid(cards)}

      <p class="fc-closing">{esc(CLOSING_BEFORE)}<a href="/{esc(CLOSING_LINK[0])}">{esc(CLOSING_LINK[1])}</a>{esc(CLOSING_AFTER)}</p>

    </div>
  </section>
</main>

<!-- ── Footer (injected by partials.js) ── -->
<div id="siteFooter"></div>

  <script src="/partials/partials.js"></script>
  <script src="/protect-images.js"></script>
</body>
</html>
'''


def main():
    try:
        cards = load_cards()
    except (OSError, ValueError, BuildError) as exc:
        print(f"✗ {OUT}: {exc}", file=sys.stderr)
        raise SystemExit(1)

    # A card whose PDF has not been built yet is left off rather than
    # published as a broken link. See the note at the top of this file.
    live, missing = [], []
    for entry in cards:
        path = entry["download"]["file"].lstrip("/")
        (live if os.path.exists(path) else missing).append(entry)

    for entry in missing:
        path = entry["download"]["file"]
        print(f"  ! {path} is not on disk, so '{entry['slug']}' was left off "
              f"(run the Rebuild field cards workflow)")

    if not live:
        print(f"✗ {OUT}: none of the listed PDFs exist on disk", file=sys.stderr)
        raise SystemExit(1)

    # A heading keyed to a slug that no longer carries a card is dead copy,
    # and a card with no heading silently falls back to its button label,
    # which is the short wording this page exists to avoid.
    slugs = {e["slug"] for e in cards}
    for slug in sorted(set(HEADINGS) - slugs):
        print(f"  ! HEADINGS has '{slug}', which carries no card")
    for entry in live:
        if entry["slug"] not in HEADINGS:
            print(f"  ! '{entry['slug']}' has no HEADINGS entry, so it fell "
                  f"back to its button label")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build_page(live))

    print(f"✓ {OUT}  ({len(live)} card(s) listed"
          + (f", {len(missing)} skipped" if missing else "") + ")")


if __name__ == "__main__":
    main()
