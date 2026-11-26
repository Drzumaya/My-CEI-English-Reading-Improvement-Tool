const CACHE_NAME = "cei-pwa-cache-v2";
const ASSETS_TO_CACHE = [
  "./",
  "./index.html",
  "./static/manifest.json",
  "./static/android-launchericon-192-192.png",
  "./static/android-launchericon-512-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});

self.addEventListener("sync", (event) => {
  if (event.tag === "cei-sync-progress") {
    event.waitUntil(Promise.resolve());
  }
});

self.addEventListener("periodicsync", (event) => {
  if (event.tag === "cei-daily-update") {
    event.waitUntil(Promise.resolve());
  }
});

self.addEventListener("push", (event) => {
  const data = event.data ? event.data.text() : "Nueva actividad disponible en Career English Institute (CEI).";
  event.waitUntil(
    self.registration.showNotification("Career English Institute — CEI", {
      body: data,
      icon: "./static/android-launchericon-192-192.png",
      badge: "./static/android-launchericon-192-192.png"
    })
  );
});
