# Bhapstar — Astrophotography Portfolio

**Live site → [bhapstar.com](https://bhapstar.com)**

Personal deep-sky astrophotography portfolio.

---

## What this is

A static HTML/CSS/JS site hosted on GitHub Pages, showcasing deep-sky images including nebulae, galaxies, and star clusters.

**Pages:**

- **Home** — landing page
- **Gallery** — deep-sky image collection, with a full-screen image viewer (zoom, rotate, information, like, and share grouped under an Options menu), filtering, multiple view modes, and per-image deep links
- **Prints** — available prints for enquiry
- **Gear** — equipment used for capture and processing
- **Quiz** — interactive space knowledge quiz
- **Puzzle** — astrophoto jigsaw puzzle
- **Supernova Sweeper** — supernova sweeping clearing game

Per-object write-ups (the "Field Notes" content — how each image was captured, the equipment and conditions, and the story behind it) are surfaced inside the Gallery image viewer via **Detailed info**, rather than as a standalone page. The `field_notes.html` file still exists (and receives structured data) but is not currently linked in site navigation, gated behind a `HIDE_FIELD_NOTES` feature flag in `partials.js`.

---

## Content model

All gallery, gear, and write-up content is driven by a single source-of-truth file, `site-data.json`. Each entry carries its title, description, type, slug, capture specs, and detailed write-up. Pages that consume gallery data filter on the `section` field so gear entries never leak into gallery contexts.

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
| Capture | ASIAir |
| Processing | Siril |

---

*All images © Bhapstar. All rights reserved.*
