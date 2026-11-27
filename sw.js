const CACHE_NAME = "cei-suite-v3";
const OFFLINE_ASSETS = [
  "./",
  "./index.html",
  "./docente_app.html",
  "./socio_app.html",
  "./manifest.json",
  "./manifest_docente.json",
  "./manifest_socio.json",
  "./static/android-launchericon-192-192.png",
  "./static/android-launchericon-512-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_ASSETS).catch(() => {}))
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
    fetch(event.request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy)).catch(() => {});
        return response;
      })
      .catch(() => caches.match(event.request).then((cached) => cached || caches.match("./index.html")))
  );
});

self.addEventListener("push", (event) => {
  const data = event.data ? event.data.text() : "Notificación Académica CEI";
  event.waitUntil(
    self.registration.showNotification("Career English Institute (CEI)", {
      body: data,
      icon: "./static/android-launchericon-192-192.png",
      badge: "./static/android-launchericon-192-192.png"
    })
  );
});

self.addEventListener("sync", (event) => {
  if (event.tag === "cei-sync") {
    event.waitUntil(Promise.resolve());
  }
});
