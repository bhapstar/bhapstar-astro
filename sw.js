// ─────────────────────────────────────────────────────────────────────────────
// Bhapstar Service Worker
// Strategy:
//   - Shell (HTML, CSS, JS, partials)  → Cache-first, update in background
//   - gallery-data.json / gear-data.json → Stale-while-revalidate
//   - Images (.webp, .png, .jpg, .svg)  → Cache-first (long-lived assets)
//   - External (Cloudflare, Formspree, Vimeo, fonts) → Network-only
// ─────────────────────────────────────────────────────────────────────────────

// Disable SW entirely on local dev so Live Server hot-reload works normally
if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') return;

const CACHE_VERSION = 'bhapstar-98ea867';

// Core shell — cached on install
const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/gallery.html',
  '/gear.html',
  '/prints.html',
  '/quiz.html',
  '/jigsaw.html',
  '/styles.css',
  '/protect-images.js',
  '/partials/partials.js',
  '/gallery-data.json',
  '/images/icons/favicon-32.png',
  '/images/icons/apple-touch-icon.png',
  '/images/icons/og-preview.jpg',
];

// ── Install: pre-cache the shell ──────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then(cache => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ── Activate: clean up old caches ─────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key !== CACHE_VERSION)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// ── Fetch: routing logic ───────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests
  if (request.method !== 'GET') return;

  // External requests → network only (analytics, fonts, Formspree, Vimeo, likes API)
  if (url.origin !== self.location.origin) {
    return; // fall through to browser default
  }

  // gallery-data.json / gear-data.json → stale-while-revalidate
  if (url.pathname.endsWith('-data.json')) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Images → cache-first (they don't change often)
  if (/\.(webp|png|jpe?g|svg|gif)$/i.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // HTML pages, CSS, JS → cache-first with network fallback
  event.respondWith(cacheFirst(request));
});

// ── Strategies ────────────────────────────────────────────────────────────────

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_VERSION);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    // Offline fallback for HTML navigation requests
    if (request.mode === 'navigate') {
      const fallback = await caches.match('/index.html');
      if (fallback) return fallback;
    }
    return new Response('Offline — please check your connection.', {
      status: 503,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_VERSION);
  const cached = await cache.match(request);

  const networkFetch = fetch(request)
    .then(response => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => null);

  return cached || await networkFetch;
}
