# Bhapstar — Astrophotography Portfolio

**Live site → [bhapstar.com](https://bhapstar.com)**

Personal deep-sky astrophotography portfolio.

---

## What this is

A static HTML/CSS/JS site hosted on GitHub Pages, showcasing deep-sky images including nebulae, galaxies, and star clusters, alongside equipment write-ups and practical astrophotography articles.

**Pages:**

- **Home** — landing page
- **Gallery** — deep-sky image collection, with a full-screen image viewer (zoom, rotate, information, like, and share grouped under an Options menu), filtering, multiple view modes, and per-image deep links
- **Prints** — available prints for enquiry
- **Gear** — equipment used for capture and processing, as a tiled index linking to one real page per item
- **Articles** — long-form write-ups on gear, capture, processing, light pollution and meteor showers, as a tiled index linking to one real page per article
- **Quiz** — interactive space knowledge quiz
- **Puzzle** — astrophoto jigsaw puzzle
- **Supernova Sweeper** — supernova sweeping clearing game
- **Star Word** — astro-related word guessing game

Per-object write-ups (the "Field Notes" content — how each image was captured, the equipment and conditions, and the story behind it) are surfaced inside the Gallery image viewer via **Detailed info**, rather than as a standalone page. The `field_notes.html` file still exists (and receives structured data) but is not currently linked in site navigation, gated behind a `HIDE_FIELD_NOTES` feature flag in `partials.js`.

---

## Repository layout

```
bhapstar-astro/                  ← this repo (PUBLIC)
├── .github/workflows/
│   └── site-postprocess.yml     ← the one build + deploy workflow
├── build.py                     ← runs every generator in the right order
├── scripts/
│   ├── generate-gear-pages.py
│   ├── generate-article-pages.py
│   ├── generate-share-pages.py
│   ├── generate-schema.py
│   └── generate-sitemap.py
├── content/                     ← hand-written prose, one file per slug
│   ├── articles/<slug>.html
│   └── gear/<slug>.html
├── articles/  gear/  share/     ← generated output, never edited by hand
├── partials/partials.js         ← header/footer injection + feature flags
├── site-data.json               ← the single source of data for all of it
├── images/                      ← full-size WebP, plus thumbs/, gear/, articles/, icons/
├── sounds/                      ← audio cues for the game pages
├── styles.css  sw.js  manifest.json  protect-images.js
└── *.html                       ← the hand-maintained pages listed above
```

---

## Content model

All gallery, gear, article, and write-up content is driven by a single source-of-truth file, `site-data.json`. Each entry carries its title, description, type, slug, capture specs, and detailed write-up. Article entries also carry a `category` and a `readTime`, which appear on the tile and in the page meta line. Pages that consume gallery data filter on the `section` field (`gallery`, `gear` or `article`) so entries never leak across contexts.

Long-form prose lives outside the JSON, as plain HTML fragments:

- `content/gear/<slug>.html` — the review body for a gear item
- `content/articles/<slug>.html` — the body of an article

Fragments are ordinary HTML (`<h2>`, `<p>`, `<ul>`, `<table>`). Diagrams are hand-drawn inline `<svg>` inside a `<figure class="article-fig">` (or `.passband-fig` on gear reviews) rather than binary assets, so they scale, follow the light/dark theme through CSS variables, and cost nothing extra to load. Photographs use the same `.article-fig` frame and can be floated beside the text with `.fig-float` (add `.fig-left` to flip the side), or paired two-up with `.article-figrow`, which collapses to a single column on narrow screens. Every image inside an `.article-fig` opens larger on click. Vimeo clips sit in a `.article-video` box, with a fixed-width wrapper and `padding-top: 177.78%` for portrait footage. An article may open with a `<div class="event-callout">` block for a dated, real-world event, or for a short summary above the body.

An entry flagged `"hidden": true` is staged but unpublished — usually waiting on photographs. It gets no tile, no generated page and no sitemap entry, and both the gear and article generators delete any page whose slug has since been hidden or removed. Setting the flag back to `false` publishes it on the next build.

---

## Image pipeline

Images are processed through a private-repo GitHub Actions workflow before any assets reach this public repo:

- **Watermarking** — watermark overlay applied to all full-size images
- **WebP conversion + thumbnail generation** — compressed full images and thumbnails created for gallery performance
- **Compression** — file size optimisation for web delivery
- **Push to public repo** — processed assets are pushed here automatically on workflow completion

The standard authoring flow for a new image: name the original → the pipeline generates the WebP + thumbnail in this repo → add the entry (with its `slug`) to `site-data.json` → commit. Everything downstream (sitemap, structured data, and per-image share pages) regenerates automatically on deploy.

---

## Build & deploy

A single GitHub Actions workflow, `.github/workflows/site-postprocess.yml`, builds and deploys the site to Pages on every push to `main`. It was consolidated from multiple workflows into one (with a `pages` concurrency group) to stop near-simultaneous runs from colliding on the same Pages environment.

The build itself is one command, `python build.py`, which runs the five generators in `scripts/` in a fixed order so the sequence never has to be repeated in the workflow file:

1. **gear** — `generate-gear-pages.py` writes one page per gear item under `/gear/<slug>.html`, pulling its prose from `content/gear/`. First, because share pages only turn a capture spec into a link if the gear page already exists on disk
2. **article** — `generate-article-pages.py` writes one page per article under `/articles/<slug>.html`, pulling its prose from `content/articles/`, and rewrites the tile grid and JSON-LD blocks inside `articles.html` between their marker comments
3. **share** — `generate-share-pages.py` writes one small page per gallery image under `/share/<slug>.html`
4. **schema** — `generate-schema.py` injects JSON-LD (`ImageObject` per photo, `BlogPosting` per write-up) into the `<head>` blocks of `gallery.html` and `field_notes.html`
5. **sitemap** — `generate-sitemap.py` rebuilds `sitemap.xml` from `site-data.json`

All the generators are idempotent, rewrite every page on each run, and delete stale pages whose slug has left `site-data.json`. `build.py --list` prints the stages, and naming stages (`python build.py gear share`) runs a subset, still in the correct order.

The workflow then **bumps the service-worker cache version** (rewriting the `CACHE_VERSION` constant in `sw.js` with the latest commit hash), **deploys to Pages**, and **commits the regenerated files back** to the repo.

Because everything under `articles/`, `gear/` and `share/` is regenerated on every push, a content change usually means committing only the fragment in `content/` and, where the tile or metadata changes, `site-data.json`.

---

## Social sharing previews

Every page carries Open Graph and Twitter Card meta tags. Because link crawlers don't run JavaScript and ignore the `#slug` fragment, a shared gallery deep link would otherwise always preview the one site-wide image. To fix this, `generate-share-pages.py` emits a lightweight page per image at `/share/<slug>.html`, each carrying that image's own `og:image` (its thumbnail), title, and description. Human visitors are redirected straight to the image in the gallery; crawlers read the correct per-image tags. The Gallery share buttons point at these pages.

---

## Tech

- Vanilla HTML, CSS, and JavaScript — no framework, no build tooling
- Static hosting via GitHub Pages with a custom domain
- Progressive Web App (PWA) support via `manifest.json` and `sw.js`
- Service-worker caching (`sw.js`): the shell — HTML, CSS, JS, and partials — is **network-first** (bypassing the HTTP cache with `no-store`, falling back to cache only when offline); `*-data.json` feeds are **stale-while-revalidate**; images are **cache-first** (long-lived); external requests (analytics, fonts, Formspree, Vimeo, likes API) are **network-only**. The SW is disabled on `localhost`/`127.0.0.1` so Live Server hot-reload works, and activating a new version reloads open tabs
- Light and dark themes throughout, driven by CSS custom properties on `html[data-theme]`
- Cloudflare Analytics; a Cloudflare Worker backs the image "likes" system
- Canonical tags on all pages
- Open Graph / Twitter Card previews, with per-image share pages (see above)

---

## Equipment

| Role | Gear |
|---|---|
| Telescopes | Askar V (interchangeable 60mm / 80mm ED objectives, 270–600mm) |
| Mount | Juwei 14 harmonic |
| Camera | ZWO ASI585MC Air (camera, guider and ASIAir controller in one body) |
| Focuser | ZWO EAF |
| Filters | Optolong L-eXtreme (7nm dual narrowband) · Svbony SV220 (3nm dual narrowband) · Optolong L-Quad Enhance (broadband) |
| Filter holder | Svbony filter drawer |
| Power | EcoFlow River 2 |
| Smart scopes | ZWO Seestar S30 · ZWO Seestar S30 Pro |
| Tripod | ZWO TC20 + TH10 fluid head |
| Camera (wide-field) | Sony A7 III |
| Lenses | Samyang 135mm f/2 · Rokinon 18mm f/2.8 · Samyang 14mm f/2.8 |
| Also owned | Skywatcher Evostar 72ED · Celestron 2in eyepiece kit |
| Capture | ASIAir |
| Processing | Siril · GraXpert · GIMP |

---

*All images © Bhapstar. All rights reserved.*
