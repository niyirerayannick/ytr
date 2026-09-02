{% load static %}
/* Rendered by Django (apps.core.views.service_worker) so hashed static asset
   URLs stay correct after collectstatic, and so the file can be served from
   "/" with a scope covering the whole origin. Do not link to this file as a
   static asset — it is only reachable at /service-worker.js. */
const SHELL_CACHE = "ytr-shell-v1";
const PAGE_CACHE = "ytr-public-pages-v1";
const MAX_PUBLIC_PAGES = 24;
const SHELL_URLS = [
  "{% static 'css/dist.css' %}",
  "{% static 'js/site.js' %}",
  "{% static 'js/pwa.js' %}",
  "{% static 'manifest.webmanifest' %}",
  "{% static 'icons/ytr-192.png' %}",
  "{% static 'icons/ytr-512.png' %}"
];
const OFFLINE_URL = "{% static 'offline.html' %}";

function isPrivatePath(pathname) {
  return /^\/(?:dashboard|accounts|admin)(?:\/|$)/.test(pathname);
}

function isPublicTextPath(pathname) {
  return /^\/articles\/[^/]+\/$/.test(pathname) || pathname === "/devotions/";
}

function canCachePublicPage(request, response) {
  return request.method === "GET" && response && response.ok && response.headers.get("X-YTR-Public-Cache") === "1";
}

async function cachePublicPage(request, responseToCache) {
  const cache = await caches.open(PAGE_CACHE);
  await cache.delete(request);
  await cache.put(request, responseToCache);
  const keys = await cache.keys();
  await Promise.all(keys.slice(0, Math.max(0, keys.length - MAX_PUBLIC_PAGES)).map((key) => cache.delete(key)));
}

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((cache) => cache.addAll([...SHELL_URLS, OFFLINE_URL])));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys
    .filter((key) => key.startsWith("ytr-") && key !== SHELL_CACHE && key !== PAGE_CACHE)
    .map((key) => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (isPrivatePath(url.pathname)) {
    event.respondWith(fetch(request));
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith((async () => {
      try {
        const response = await fetch(request);
        const dbg = { pathname: url.pathname, isPublicTextPath: isPublicTextPath(url.pathname), header: response.headers.get("X-YTR-Public-Cache"), ok: response.ok, method: request.method };
        if (isPublicTextPath(url.pathname) && canCachePublicPage(request, response)) {
          event.waitUntil(cachePublicPage(request, response.clone()).then(() => {
            dbg.cached = true;
          }).catch((e) => {
            dbg.error = String(e);
          }).finally(() => {
            self.clients.matchAll().then((cs) => cs.forEach((c) => c.postMessage({ type: "DEBUG", dbg })));
          }));
        } else {
          self.clients.matchAll().then((cs) => cs.forEach((c) => c.postMessage({ type: "DEBUG", dbg })));
        }
        return response;
      } catch (error) {
        if (isPublicTextPath(url.pathname)) {
          const cached = await caches.open(PAGE_CACHE).then((cache) => cache.match(request));
          if (cached) return cached;
        }
        return caches.match(OFFLINE_URL);
      }
    })());
    return;
  }

  if (SHELL_URLS.includes(url.pathname)) {
    event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
  }
});
