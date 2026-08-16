const CACHE_NAME = 'ttt-shell-v67';
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
      .catch(() => {})
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

    if (url.pathname.startsWith('/api/')) return;

    if (url.pathname.startsWith('/combos') || url.pathname.startsWith('/squad-guesser')) return;
  }

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
