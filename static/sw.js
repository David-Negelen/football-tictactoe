// Service worker for the Tiki-Taka-Toe game, which now lives at the site
// root (registered with scope "/" — see static/js/pwa.js, and the game()
// route in app.py). That scope technically also covers the sibling
// "/combos" and "/squad-guesser" pages — see the fetch handler below, which
// explicitly bypasses both so this cache never touches them.

const CACHE_NAME = 'ttt-shell-v65';
const SHELL_URLS = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/js/game.js',
  '/static/js/pwa.js',
  '/static/fonts/fonts.css',
  '/static/fonts/inter-var-latin.woff2',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(SHELL_URLS))
      .catch(() => {}) // offline-first install shouldn't hard-fail on a flaky network
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin === self.location.origin) {
    // Live game data (puzzles, search, validation, solutions) must never be
    // served from cache — a stale puzzle or stale validation would be a
    // correctness bug, not just a staleness annoyance.
    if (url.pathname.startsWith('/api/')) return;
    // Siblings of the game at this scope, but not part of its shell — see
    // the file header. Their own page loads always go straight to network;
    // this only covers their own document request, not third-party assets
    // (e.g. the Tailwind CDN script) they load themselves, which is fine —
    // those were never part of the "no stale content" guarantee this cache
    // exists for.
    if (url.pathname.startsWith('/combos') || url.pathname.startsWith('/squad-guesser')) return;
  }

  // App shell + fonts/CDN assets: stale-while-revalidate.
  event.respondWith(
    caches.open(CACHE_NAME).then(async cache => {
      const cached = await cache.match(request);
      const network = fetch(request)
        .then(resp => {
          if (resp && (resp.ok || resp.type === 'opaque')) cache.put(request, resp.clone());
          return resp;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
