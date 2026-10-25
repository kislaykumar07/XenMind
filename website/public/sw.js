// XenMind service worker: cache the app shell, never cache API responses.
// NOTE: bump CACHE on every frontend release, and app.js itself is
// network-first — otherwise returning visitors stay stuck on stale JS
// (which is how a pre-auth frontend survived after server auth shipped).
const CACHE = "xenmind-v4";
const SHELL = ["/", "/index.html", "/styles.css", "/app.js", "/manifest.json", "/icon.svg"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith("/api")) return; // always live
  if (url.pathname === "/app.js") {
    // The app bundle must never go stale: network first, cache as fallback.
    e.respondWith(fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match(e.request)));
    return;
  }
  if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request).catch(() => caches.match("/index.html")));
    return;
  }
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
    const copy = res.clone();
    caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
    return res;
  })));
});
