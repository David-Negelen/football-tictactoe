// Service worker for the Tiki-Taka-Toe game page only (registered with scope
// "/game" — see static/js/pwa.js). Never touches "/", "/combos" or
// "/squad-guesser", which stay outside this service worker's scope.

const CACHE_NAME = 'ttt-shell-v18';
const SHELL_URLS = [
  '/game',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/js/game.js',
  '/static/js/pwa.js',
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
  // Live game data (puzzles, search, validation, solutions) must never be
  // served from cache — a stale puzzle or stale validation would be a
  // correctness bug, not just a staleness annoyance.
  if (url.origin === self.location.origin && url.pathname.startsWith('/api/')) return;

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
