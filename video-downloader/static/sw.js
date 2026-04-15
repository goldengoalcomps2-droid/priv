// SnapVid Service Worker
const CACHE_NAME = 'snapvid-v1';
const STATIC_ASSETS = [
    '/',
    '/static/manifest.json',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png'
];

// Install: cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS).catch(() => {});
        })
    );
    self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            );
        })
    );
    self.clients.claim();
});

// Fetch: network first for API calls, cache first for static assets
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Never cache API endpoints
    if (url.pathname.startsWith('/download') ||
        url.pathname.startsWith('/status') ||
        url.pathname.startsWith('/file')) {
        return;
    }

    // For HTML: try network first, fallback to cache
    if (event.request.mode === 'navigate' || event.request.destination === 'document') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request).then(r => r || caches.match('/')))
        );
        return;
    }

    // For static assets: cache first, fallback to network
    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request).then(response => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            }).catch(() => cached);
        })
    );
});

// Handle share target (when user shares a URL to SnapVid from another app)
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    if (url.pathname === '/' && (url.searchParams.has('url') || url.searchParams.has('text'))) {
        // Pass through - the front-end will read the URL param
    }
});
