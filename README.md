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
- **Gear** — equipment used for capture and processing
- **Articles** — long-form write-ups on capture, processing and meteor showers, as a tiled index linking to one real page per article
- **Quiz** — interactive space knowledge quiz
- **Puzzle** — astrophoto jigsaw puzzle
- **Supernova Sweeper** — supernova sweeping clearing game
- **Star Word** — astro-related word guessing game

Per-object write-ups (the "Field Notes" content — how each image was captured, the equipment and conditions, and the story behind it) are surfaced inside the Gallery image viewer via **Detailed info**, rather than as a standalone page. The `field_notes.html` file still exists (and receives structured data) but is not currently linked in site navigation, gated behind a `HIDE_FIELD_NOTES` feature flag in `partials.js`.

---

## Content model

All gallery, gear, article, and write-up content is driven by a single source-of-truth file, `site-data.json`. Each entry carries its title, description, type, slug, capture specs, and detailed write-up. Pages that consume gallery data filter on the `section` field (`gallery`, `gear` or `article`) so entries never leak across contexts.

Long-form prose lives outside the JSON, as plain HTML fragments:

- `gear-reviews/<slug>.html` — the review body for a gear item
- `article-content/<slug>.html` — the body of an article

Fragments are ordinary HTML (`<h2>`, `<p>`, `<ul>`, `<table>`). Diagrams are hand-drawn inline `<svg>` inside a `<figure class="article-fig">` (or `.passband-fig` on gear reviews) rather than binary assets, so they scale, follow the light/dark theme through CSS variables, and cost nothing extra to load. An article may open with a `<div class="event-callout">` block for a dated, real-world event.

An entry flagged `"hidden": true` is staged but unpublished — usually waiting on photographs. It gets no tile, no generated page and no sitemap entry. Removing the flag publishes it on the next build.

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

A single GitHub Actions workflow, `.github/workflows/site-postprocess.yml`, builds and deploys the site to Pages on every push to `main`. It was consolidated from multiple workflows into one (with a `pages` concurrency group) to stop near-simultaneous runs from colliding on the same Pages environment. On each run it:

- **Regenerates the sitemap** — `generate-sitemap.py`
- **Regenerates structured data** — `generate-schema.py` injects JSON-LD (`ImageObject` per photo, `BlogPosting` per write-up) into the page `<head>` blocks from `site-data.json`
- **Regenerates per-image share pages** — `generate-share-pages.py` writes one small page per gallery image under `/share/<slug>.html`
- **Regenerates per-gear pages** — `generate-gear-pages.py` writes one page per gear item under `/gear/<slug>.html`, pulling its prose from `gear-reviews/`
- **Regenerates per-article pages** — `generate-article-pages.py` writes one page per article under `/articles/<slug>.html`, pulling its prose from `article-content/`. Both generators are idempotent and delete stale pages whose slug has left `site-data.json`
- **Bumps the service-worker cache version** — rewrites the `CACHE_VERSION` constant in `sw.js` with the latest commit hash
- **Deploys to Pages** and commits the regenerated files back to the repo

---

## Social sharing previews

Every page carries Open Graph and Twitter Card meta tags. Because link crawlers don't run JavaScript and ignore the `#slug` fragment, a shared gallery deep link would otherwise always preview the one site-wide image. To fix this, `generate-share-pages.py` emits a lightweight page per image at `/share/<slug>.html`, each carrying that image's own `og:image` (its thumbnail), title, and description. Human visitors are redirected straight to the image in the gallery; crawlers read the correct per-image tags. The Gallery share buttons point at these pages.

---

## Tech

- Vanilla HTML, CSS, and JavaScript — no framework, no build tooling
- Static hosting via GitHub Pages with a custom domain
- Progressive Web App (PWA) support via `manifest.json` and `sw.js`
- Service-worker caching (`sw.js`): the shell — HTML, CSS, JS, and partials — is **network-first** (bypassing the HTTP cache with `no-store`, falling back to cache only when offline); `*-data.json` feeds are **stale-while-revalidate**; images are **cache-first** (long-lived); external requests (analytics, fonts, Formspree, Vimeo, likes API) are **network-only**. The SW is disabled on `localhost`/`127.0.0.1` so Live Server hot-reload works, and activating a new version reloads open tabs
- Cloudflare Analytics; a Cloudflare Worker backs the image "likes" system
- Canonical tags on all pages
- Open Graph / Twitter Card previews, with per-image share pages (see above)

---

## Equipment

| Role | Gear |
|---|---|
| Telescopes | Askar V (60mm / 80mm objectives) |
| Mount | Juwei 14 |
| Camera | ZWO ASI585MC Air |
| Filters | Optolong L-Extreme (dual narrowband) / Optolong L-Quad EnHance |
| Smart scope | ZWO Seestar S30 |
| Camera (wide-field) | Sony A7 III |
| Lenses | Samyang 135mm f/2 · Rokinon 18mm f/2.8 · Samyang 14mm f/2.8 |
| Capture | ASIAir |
| Processing | Siril |

---

*All images © Bhapstar. All rights reserved.*
