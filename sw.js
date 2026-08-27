// Bump CACHE on every release or installed copies keep serving the old build.
const CACHE = 'doveclem-v5';

// Shell only. Audio is cached the first time it is fetched, so adding a voice
// pack needs no change here.
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
  './icons/apple-touch-icon.png',
  './audio/clem/01-mi-chiamo-clementina.m4a',
  './audio/clem/02-marco-1.m4a',
  './audio/clem/03-marco-2.m4a',
  './audio/clem/04-suona-un-po-sbagliato.m4a',
  './audio/clem/05-theory.m4a'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.all(ASSETS.map(u => c.add(u).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const isDoc = req =>
  req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html');

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  // Network-first for the app shell, so a fix always reaches an installed copy
  // instead of being masked by a stale cache entry.
  if (isDoc(req)) {
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req).then(hit => hit || caches.match('./index.html')))
    );
    return;
  }

  // Audio, icons and fonts are immutable per release: cache-first, and any new
  // pack lands in the cache on first play.
  e.respondWith(
    caches.match(req).then(hit =>
      hit || fetch(req).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        return res;
      })
    )
  );
});
