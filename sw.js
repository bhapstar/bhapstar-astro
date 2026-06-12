// ─────────────────────────────────────────────────────────────────────────────
// Bhapstar Service Worker
// Strategy:
//   - Shell (HTML, CSS, JS, partials)  → Network-first (fresh on every load, cache as offline fallback)
//   - site-data.json / gear-data.json → Stale-while-revalidate
//   - Images (.webp, .png, .jpg, .svg)  → Cache-first (long-lived assets)
//   - External (Cloudflare, Formspree, Vimeo, fonts) → Network-only
// ─────────────────────────────────────────────────────────────────────────────

// Disable SW entirely on local dev so Live Server hot-reload works normally
const IS_DEV = location.hostname === 'localhost' || location.hostname === '127.0.0.1';

if (!IS_DEV) {

const CACHE_VERSION = 'bhapstar-41622c9';

// Core shell — cached on install
const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/gallery.html',
  '/gear.html',
  '/prints.html',
  '/field_notes.html',
  '/quiz.html',
  '/jigsaw.html',
  '/supernova_sweeper.html',
  '/styles.css',
  '/protect-images.js',
  '/partials/partials.js',
  '/partials/header.html',
  '/partials/footer.html',
  '/site-data.json',
  '/gear-data.json',
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

// ── Activate: clean up old caches, then reload all open tabs ──────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key !== CACHE_VERSION)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
      .then(() => self.clients.matchAll({ type: 'window' }))
      .then(clients => {
        clients.forEach(client => client.navigate(client.url));
      })
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

  // site-data.json / gear-data.json → stale-while-revalidate
  if (url.pathname.endsWith('-data.json')) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Images → cache-first (they don't change often)
  if (/\.(webp|png|jpe?g|svg|gif)$/i.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // HTML pages, CSS, JS → network-first (always fresh, cache as offline fallback)
  event.respondWith(networkFirst(request));
});

// ── Strategies ────────────────────────────────────────────────────────────────

async function networkFirst(request) {
  const cache = await caches.open(CACHE_VERSION);
  // Bypass the browser HTTP cache entirely for HTML, CSS, JS
  const fetchRequest = request.mode === 'navigate' || /\.(html|css|js)$/i.test(new URL(request.url).pathname)
    ? new Request(request, { cache: 'no-store' })
    : request;
  try {
    const response = await fetch(fetchRequest);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    // Offline: serve from cache if available
    const cached = await cache.match(request);
    if (cached) return cached;
    // Last resort fallback for navigation
    if (request.mode === 'navigate') {
      const fallback = await cache.match('/index.html');
      if (fallback) return fallback;
    }
    return new Response('Offline — please check your connection.', {
      status: 503,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

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

} // end !IS_DEV
