# Bhapstar — Astrophotography Portfolio
**Live site → [bhapstar.com](https://bhapstar.com)**
Personal deep-sky astrophotography portfolio.
---
## What this is
A static HTML/CSS/JS site hosted on GitHub Pages, showcasing deep-sky images including nebulae, galaxies, and star clusters.

**Pages:**
- **Home** — landing page
- **Gallery** — deep-sky image collection
- **Prints** — available prints for enquiry
- **Gear** — equipment used for capture and processing
- **Field Notes** — write-ups on imaged objects and the story behind each capture
- **Quiz** — interactive space knowledge quiz
- **Puzzle** — astrophoto jigsaw puzzle
- **Supernova Sweeper** — supernova sweeping clearing game
---
## Image pipeline
Images are processed through a private-repo GitHub Actions workflow before any assets reach this public repo:
- **Watermarking** — watermark overlay applied to all full-size images
- **WebP thumbnail generation** — compressed thumbnails created for gallery performance
- **Compression** — file size optimisation for web delivery
- **Push to public repo** — processed assets are pushed here automatically on workflow completion
The pipeline is driven by `process-images.js` and triggered via `watermark.yml`.
---
## Tech
- Vanilla HTML, CSS, and JavaScript — no framework
- Static hosting via GitHub Pages
- Progressive Web App (PWA) support via `manifest.json` and `sw.js`
- Service worker caching strategy: cache-first for shell assets and images, stale-while-revalidate for JSON data feeds, network-only for external services
- Automatic SW cache busting on every push via `.github/workflows/bust-cache.yml` — rewrites the `CACHE_VERSION` constant in `sw.js` with the latest commit hash
- Cloudflare Analytics
- Open Graph and Twitter Card meta tags for social sharing previews
- Canonical tags on all pages
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
