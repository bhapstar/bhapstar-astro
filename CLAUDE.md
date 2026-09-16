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
| `styles.css`, `partials/*` | `field_notes.html`, `start-here.html`, `field-cards.html` |
| | `tonight.html`, `glossary.html` |

Everything in the right column is overwritten on every build. A change made
there survives until the next `python build.py` and then vanishes, which is a
confusing failure because the site looks correct locally first.

`articles.html` is the one partial exception. The generator only rewrites the
blocks between its `ARTICLE-TILES` and `ARTICLE-JSONLD` marker comments.
Everything outside them (the controls, the runtime script, the order buttons)
is hand-written and safe to edit. Never touch anything between the markers.

**Do not touch `sw.js` or `scripts/generate-sitemap.py` without being asked.**
CI rewrites the service worker cache version on every deploy, so never change
`CACHE_VERSION` by hand.

A new top-level page needs a line in both, once asked: `PAGES` in
`scripts/generate-sitemap.py` (the list is static, not read from disk) and
`SHELL_ASSETS` in `sw.js` if it should work offline.

---

## Build

```bash
python build.py          # runs all ten generators in order
python build.py tonight  # just one stage
python build.py --list   # show the stages
```

Order is fixed and matters: gear, article, share, schema, sitemap, starthere,
tonight, feed, downloads, glossary. The article step must run before sitemap,
because sitemap only lists article, share and gear files that already exist on
disk.

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
- **`body_figures`** on a gallery entry puts extra pictures inside the share
  page write-up, each after a numbered body paragraph (`"after": 1` follows
  the first, `0` follows the intro). Fields: `file`, `alt`, `caption`,
  `credit`, `credit_url`. A missing file prints a `!` warning in the share
  stage rather than failing silently. Third-party reference images live in
  `images/reference/` and need no thumb.
- Never guess equipment attribution. Check the `specs` field on the gallery
  entry rather than inferring from the image.

---

## Start Here

`scripts/generate-start-here.py` holds its content as Python constants, not in
JSON. The page answers one question, what do I do next, in three parts:

1. **Try this tonight, with nothing.** Four steps in `TONIGHT_STEPS`. Step one
   is Stellarium Web, because that is how every session starts. The intro and
   `TONIGHT_LEDE` both say "four", so keep them in step with the list.
2. **Where are you right now?** Six hard-coded routes in `ROUTES`, three or
   four cards each. The same article can carry a different blurb on each
   route. A route lede that says "these three" or "all three" must match its
   card count.
3. **A link to `tonight.html`.** Nothing else from the planner lives here.

Copy tokens: `{route:key}`, `{article:slug|label}`, `{url:path|label}` and
`{ext:https://...|label}`. An unknown slug or route fails the build.

Opening a route card saves that route to sessionStorage
(`bhapstar:routeTrail`). The article page then shows a route bar above and
below the article, with where the reader is ("2 of 3"), a link back to the
route, and the next article, and hides the date-ordered previous/next bar. It
only appears when the reader came from Start Here or from another article on
the same route. The bar is built in the browser by `ROUTE_NAV_JS` in
`scripts/generate-article-pages.py`, so changing a route needs nothing there.

The script warns about any live article that is on no route card and linked
from no copy on the page. Seasonal articles such as the meteor shower piece
are linked from route endings rather than given a block of their own.

The full path that used to sit at the bottom is now the **Reading order**
button on `articles.html`, sorted by `stage` (plan, capture, process, gear),
then `stageOrder`, then newest. Articles with no `stage` come last.
`/articles.html?order=reading` opens it in that order. `stage` and
`stageOrder` in `site-data.json` therefore still matter.

---

## Tonight

`scripts/generate-tonight.py` writes `tonight.html`, the night planner. In the
nav it sits inside the Start Here dropdown, below Start Here itself.

- **Planner.** The shell comes from the generator and `/tonight-core.js` does
  all the astronomy. The CSS classes keep their `sh-sky-` prefix from when the
  panel lived on Start Here. Leaflet loads from unpkg with SRI hashes; if the
  map fails, the rest of the panel still works.
- **Target images are checked at build time.** Every target in
  `tonight-core.js` must have its image, its thumbnail and a gallery entry
  with the same slug, or the stage fails and lists every problem.
- **Meteor showers.** `SHOWERS` is a copy of the table in
  `content/articles/photograph-a-meteor-shower.html`. Change one, change the
  other. The page shows the next three peaks, with the moon for each peak
  night from `tonight-core.js`, and a button that moves the planner to that
  date through a `tonight:goto` event.
- Page CSS is in `styles.css` under "PAGE: Tonight", with the shared planner
  styles under "PAGE: Start Here — sky panel".

---

## Tap tracking

Two layers that must be updated together:

1. `TAP_SRCS` in `partials/partials.js`
2. `VALID_SRC` in the Cloudflare Worker. This one is **outside this repo**,
   edited in the Cloudflare dashboard

Update only one and taps are dropped with no error anywhere.

Current sources: `nfc`, `qr`, `card`, `x`, `pwa`, `pdf-phone`, `pdf-camera`,
`pdf-meteors`, `pdf-calibration`, `pdf-asiair`, `pdf-moon`.

`pwa` comes from `start_url` in `manifest.json` (`/?src=pwa`), so it counts
launches from an installed home-screen icon rather than a scan.

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
- Deliver complete files, not fragments. Individual files at their repo
  paths, never zips.
- Validate before handing anything over: JSON parses, CSS braces balance, HTML
  tags balance, `python build.py` runs clean.
- Commit order: CSS, then JS, then HTML. Generators before JSON before HTML.
- When copying folders in, use `unzip -o` in Terminal. Finder drag-and-drop
  replaces a folder rather than merging it, which deletes files.
