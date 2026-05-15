const CACHE_NAME = 'market-pulse-v6';
const ASSET_VERSION = '20260326r4';
const urlsToCache = [
    '/',
    '/predict-form',
    '/history',
    '/help',
    '/ussd',
    '/offline',
    `/static/css/style.css?v=${ASSET_VERSION}`,
    `/static/js/app.js?v=${ASSET_VERSION}`,
    `/static/js/charts.js?v=${ASSET_VERSION}`,
    `/static/js/i18n-overrides.js?v=${ASSET_VERSION}`,
    `/static/js/offline-cache.js?v=${ASSET_VERSION}`,
    '/static/data/offline_model.json',
    '/static/data/offline_seed.json',
    `/static/manifest.json?v=${ASSET_VERSION}`
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return cache.addAll(urlsToCache);
            })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
        ))
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') {
        return;
    }

    const requestUrl = new URL(event.request.url);
    const sameOrigin = requestUrl.origin === self.location.origin;

    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    if (response && response.ok) {
                        const copy = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
                    }
                    return response;
                })
                .catch(async () => {
                    const cached = await caches.match(event.request);
                    return cached || caches.match('/offline');
                })
        );
        return;
    }

    if (sameOrigin) {
        event.respondWith(
            caches.match(event.request).then(async cached => {
                if (cached) {
                    return cached;
                }
                try {
                    const response = await fetch(event.request);
                    if (response && response.ok) {
                        const copy = response.clone();
                        const cache = await caches.open(CACHE_NAME);
                        cache.put(event.request, copy);
                    }
                    return response;
                } catch (error) {
                    return caches.match(event.request);
                }
            })
        );
    }
});
