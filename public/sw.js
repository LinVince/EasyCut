const CACHE = 'twstocks-v17';
const SHELL = [
  './',
  'index.html',
  'styles.css',
  'script.js',
  'manifest.json',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/apple-touch-icon.png',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const { request } = e;
  const url = new URL(request.url);

  // Yahoo Finance: network-only (never cache live prices)
  if (url.hostname.includes('finance.yahoo.com')) return;

  // Network-first with cache fallback: always get fresh app + data online,
  // still works offline. Old cached copies get replaced in the background.
  e.respondWith(
    caches.open(CACHE).then(cache =>
      fetch(request)
        .then(resp => {
          if (resp.ok && request.method === 'GET' && !request.url.includes('/api/chart?')) {
            cache.put(request, resp.clone());
          }
          return resp;
        })
        .catch(() => cache.match(request, { ignoreVary: true }))
    )
  );
});
