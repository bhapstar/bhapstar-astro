# bhapstar.com

A static astrophotography site on GitHub Pages. Hand-written HTML, CSS and JS,
with Python generators that build most pages from one JSON file.

Bob (Bhapinder Singh) shoots from a Bortle 8 balcony in Dubai and from UAE
desert sites. He manages his own commits through GitHub Desktop.

---

## The one rule that matters most

**Edit generator inputs, never generated output.**

| Edit these | Never edit these |
| --- | --- |
| `content/articles/*.html` | `articles/*.html` |
| `content/gear/*.html` | `gear/*.html` |
| `site-data.json` | `articles.html`, `gallery.html` |
| `scripts/*.py` | `share/*`, `sitemap.xml`, `feed.xml` |
| `styles.css`, `partials/*` | `field_notes.html`, `start-here.html` |

Everything in the right column is overwritten on every build. A change made
there survives until the next `python build.py` and then vanishes, which is a
confusing failure because the site looks correct locally first.

**Do not touch `sw.js` or `scripts/generate-sitemap.py` without being asked.**
CI rewrites the service worker cache version on every deploy.

---

## Build

```bash
python build.py          # runs all seven generators in order
```

Order is fixed and matters: gear, article, share, schema, sitemap, starthere,
feed. The article step must run before sitemap, because sitemap only lists
files that already exist on disk.

CI (`.github/workflows/site-postprocess.yml`) runs `python build.py` on push,
bumps the SW cache version, deploys, then commits the regenerated files back.
**So only commit generator inputs.** Committing built output as well just
creates a conflict for the bot to resolve.

Test locally with Live Server in VS Code, in an incognito window, or the
service worker serves a stale cache.

---

## site-data.json

One flat list of entries, each with a `section`: `gallery`, `article`, `gear`,
or `_divider` (comment blocks, ignored by the generators).

Things that bite:

- **Missing images are dropped silently.** The generators use
  `os.path.isfile()`. If a `file` path does not exist the entry still builds,
  just with no picture and no warning. Add the image before the JSON entry.
- **Article covers need two copies.** `images/articles/x.webp` and a
  byte-identical `images/articles/thumbs/x.webp`. Gallery images use the
  separate `images/thumbs/` tree instead. Miss the thumb and the tile renders
  blank.
- **`category` does real work**; `type` currently does none for articles.
  `category` drives the meta line, schema `articleSection`, the RSS category
  and related-article scoring (same category +2, shared `tags` +3 each).
- **Order is `date` alone**, newest first, format `DD-MM-YYYY`. There is no
  manual ordering field. `date` also feeds the displayed date, schema
  `datePublished`, RSS `pubDate` and sitemap `lastmod`, so reordering by
  editing dates has visible side effects.
- **`hidden: true`** stages an entry without publishing it.
- Never guess equipment attribution. Check the `specs` field on the gallery
  entry rather than inferring from the image.

---

## Start Here

`scripts/generate-start-here.py` holds its content as Python constants, not in
JSON. Six hard-coded routes of three cards each, plus `EXTRAS` for articles
governed by the calendar rather than by skill level. An extras entry must have
no `stage` in `site-data.json` or it appears twice. The script warns about any
article that ends up on no route, no extra and no stage.

---

## Tap tracking

Two layers that must be updated together:

1. `TAP_SRCS` in `partials/partials.js`
2. `VALID_SRC` in the Cloudflare Worker. This one is **outside this repo**,
   edited in the Cloudflare dashboard

Update only one and taps are dropped with no error anywhere. Current sources
are `pdf-phone`, `pdf-camera`, `pdf-meteors`, `pdf-calibration`, `pdf-asiair`.

---

## Hosting, and why URLs need stubs

GitHub Pages, apex resolving to `185.199.108-111.153`, `www` a CNAME to
`bhapstar.github.io`, DNS at Namecheap. Cloudflare is used only for Workers
(likes, taps, newsletter) and Analytics; **it does not proxy the site**.

So there is no server in front to set headers or issue redirects. A 301 is not
available. When an article slug changes, the old URL must be kept alive by a
generated stub.

Add the old slug to a `redirects` array on the article entry:

```json
"slug": "photograph-milky-way-camera",
"redirects": ["photograph-meteor-shower-milky-way-camera"],
```

`generate-article-pages.py` then writes a stub at the old path and exempts it
from the stale-file cleanup. Renaming a slug also means renaming its body file
in `content/articles/`, which the generator looks up as
`content/articles/<slug>.html`.

Three things about the stub are load-bearing.

Its JavaScript hop carries `location.search` across, without which a scanned
field card arrives stripped of `?src=` and the tap goes uncounted.

**The script must come first in `<head>`, and the meta refresh must be wrapped
in `<noscript>`.** A meta refresh cannot carry a query string. At delay 0 in
`<head>` it navigates the moment it is parsed, so a script placed lower down
never runs. This failed in exactly that way once: the redirect worked and
looked correct, while `?src=` was dropped every time.

It carries a canonical but deliberately **no** `noindex`. The two contradict
each other, and on a URL with ranking history, having Google fold that history
into the new address beats having it drop the URL.

## Field cards

Printable A4 PDFs in `downloads/`, built by `scripts/make-*-card.py` on top of
the `scripts/fieldcard.py` drawing kit. Each carries a QR code to its article
with a `?src=pdf-*` parameter.

Printed cards are already in circulation, so **article slugs behind a QR code
must not change.** This is why the Milky Way articles still live at
`photograph-meteor-shower-milky-way-*.html` despite no longer covering
meteors.

Fonts: the kit instantiates static weights out of the variable Outfit into a
local `fonts/` directory on first run.

---

## Affiliate links

Amazon (`bhapstar-21` for .ae, `bhapstar-20` for .com), High Point Scientific
(Refersion), Svbony (`?ref=BHAPSTAR`), AliExpress, First Light Optics. The
Amazon disclosure sentence appears conditionally on pages carrying Amazon
links. New retailers need `SUPPORT_RETAILERS` in
`scripts/generate-article-pages.py` updating alongside `site-data.json`.

---

## Writing voice

Plain, direct, matter-of-fact. Written for general audiences including
children.

- **No em dashes.** They read as AI writing.
- No poetic or atmospheric phrasing.
- Positive framing. No negatively worded headings.
- Short sentences. Say the thing.
- Never invent equipment, measurements or workflow details. If a number is not
  verifiable from the repo, ask rather than estimate.

---

## Working style

- Minimal scope. Do what was asked; mention adjacent observations briefly
  rather than acting on them.
- Deliver complete files, not fragments.
- Validate before handing anything over: JSON parses, CSS braces balance, HTML
  tags balance, `python build.py` runs clean.
- Commit order: CSS, then JS, then HTML. Generators before JSON before HTML.
- When copying folders in, use `unzip -o` in Terminal. Finder drag-and-drop
  replaces a folder rather than merging it, which deletes files.
