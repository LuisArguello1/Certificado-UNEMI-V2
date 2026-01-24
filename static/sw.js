// Minimal Service Worker for PWA
const CACHE_NAME = 'unemi-certificate-v1';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

// Basic fetch handler that falls back to network
// This avoids the 'no-op' warning by having a minimal logic structure
self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request).catch(() => {
            // Optional: fallback logic for offline
            return new Response("Offline");
        })
    );
});
