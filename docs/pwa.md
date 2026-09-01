# YTR Progressive Web App (Phase A)

This document covers the installable-app layer added on top of the existing
server-rendered Django site: the manifest, service worker, install UI, and
offline fallback. It does not cover authentication, Morning Devotion, push
notifications, or playback progress — those are later roadmap phases and were
deliberately not touched here. See `docs/roadmaps/digital-discipleship-platform.md`
for the full phased plan.

## Architecture

YTR ships a hand-written, framework-free service worker — no Workbox, no build
step beyond the existing Tailwind pipeline. Three pieces make it work:

- `static/manifest.webmanifest` — a static JSON file served by WhiteNoise and
  linked from `templates/base.html`.
- `templates/service-worker.js` + `apps/core/views.service_worker` — the worker
  script is a Django template, not a plain static file. It is rendered at
  request time and served from `/service-worker.js` (via `apps/core/urls.py`),
  not from `/static/js/...`. Two things require this:
  1. **Scope.** A service worker's default scope is the directory it's served
     from. Serving it from the origin root gives it a `/` scope, so it can
     intercept navigation to any public page. Serving it from `/static/js/`
     would restrict it to that subtree, breaking the point of the whole
     exercise. The view also sends `Service-Worker-Allowed: /` as a
     belt-and-suspenders header.
  2. **Hashed static filenames.** Production static files are served through
     `whitenoise.storage.CompressedManifestStaticFilesStorage`, which renames
     assets to `name.<hash>.ext` on `collectstatic`. Rendering the worker as a
     template means its list of shell URLs is built with `{% static %}` and is
     always correct, instead of a hardcoded filename that silently goes stale
     after the next deploy.
- `static/js/pwa.js` — the browser-side script: registers the worker,
  drives the install prompt, the update banner, the iOS instructions, and the
  online/offline indicator. Kept separate from the existing `static/js/site.js`
  so the two concerns (general site behaviour vs. PWA plumbing) don't get
  tangled together.

## Cache policy

The worker keeps two caches, both versioned (`ytr-shell-v1`, `ytr-public-pages-v1`)
so a version bump in `templates/service-worker.js` cleanly evicts the old ones
on activation. Everything else is deliberately network-only.

### Cached

- **Application shell** (`SHELL_CACHE`): `dist.css`, `site.js`, `pwa.js`, the
  manifest, the two non-maskable icons, and the offline fallback page.
  Precached on install; served cache-first since these are immutable
  (content-hashed) assets in production.
- **Public articles and devotions** (`PAGE_CACHE`, bounded to the 24 most
  recently opened): only `/articles/<slug>/` and `/devotions/` — matched by
  the exact URL patterns those two apps use, checked in
  `templates/service-worker.js`. On a successful navigation to one of those
  paths, the response is cached; the oldest entries are evicted once the
  bound is exceeded.

### Never cached

- `/dashboard/`, `/accounts/`, `/admin/`, and anything else that isn't one of
  the two explicit public paths above.
- Any authenticated response, even under `/articles/` or `/devotions/`. The
  views (`apps/articles/views.article_detail`,
  `apps/devotions/views.devotion_list`) only set the `X-YTR-Public-Cache: 1`
  response header — the signal the worker checks before caching — via
  `apps.core.pwa.mark_public_cacheable`, and that helper is a no-op for a
  signed-in `request.user`. A logged-in visitor's bookmark state, RSVP state,
  or CSRF-bearing form markup is never written to the cache, and one user's
  cached page can't be served back to a different user of the same browser.
  This is why the approach is allowlist-based (cache only these two exact
  paths, only for anonymous GETs) rather than "cache everything except a
  denylist" — a missed entry in a denylist is a privacy bug; a missed entry in
  an allowlist is just a missed caching opportunity.
- Anything paginated (`/devotions/?page=2`, ...) — only the single "today" view
  is cached, keeping the bound meaningful instead of caching an unbounded
  archive.
- Non-GET requests are rejected at the top of the `fetch` handler.
- Google Meet and YouTube are never touched by this worker — YTR embeds/links
  to them, it doesn't proxy them, so there's nothing for the worker to see.
- Uploaded audio/video files: not matched by the shell list or the public-page
  allowlist, so they fall through to normal network requests.

### Navigation strategy

All same-origin page navigations are network-first: try the network, and only
on failure fall back to a cached copy of that exact page (if it was a public
page previously cached) or, failing that, `static/offline.html`. A logged-in
user's dashboard therefore never silently serves a stale cached page — it
either loads fresh or fails visibly offline, per `isPrivatePath` in the worker.

## Installation

- **Android / desktop Chrome, Edge:** the browser fires `beforeinstallprompt`
  once its own installability heuristics are satisfied. `static/js/pwa.js`
  captures that event, and only then reveals the "Install YTR App" card
  (`templates/partials/pwa_install.html`) — there's no unsolicited native
  prompt. Dismissing the card is remembered in `localStorage` for 14 days.
- **iOS Safari:** `beforeinstallprompt` doesn't exist on iOS. `pwa.js` detects
  iOS via user agent and, if not already running standalone and not recently
  dismissed, shows a small "Add to Home Screen" instruction card. Also
  dismissible, also remembered for 14 days.
- Once installed, `appinstalled` and `@media (display-mode: standalone)` both
  hide the install/iOS cards — there is no route to see an install prompt for
  an app you already installed.
- Installing is always optional. Every public page works the same, installed
  or not; nothing is gated behind installation.

## Updating

Each release that changes `templates/service-worker.js` should bump the
`SHELL_CACHE` / `PAGE_CACHE` version suffix (`-v1` → `-v2`). The `activate`
handler deletes any `ytr-*`-prefixed cache that isn't the current version, so
old shells don't linger.

At runtime: when a new worker finishes installing while an old one is still
controlling the page, `pwa.js` shows an "A new version of YTR is available"
banner (`#pwaUpdate`) instead of forcing a reload. Clicking **Update** posts
`{type: "SKIP_WAITING"}` to the waiting worker; it activates, `controllerchange`
fires once, and the page reloads exactly once. There is no scenario where old
HTML runs against new precached assets, because the reload only happens after
the new worker has taken control.

## Development

- `npm run watch:css` while working on styles; the PWA classes live at the
  bottom of `static/css/input.css` under `/* ============ PWA ============ */`.
- The worker only registers on `https:`, `localhost`, or `127.0.0.1`
  (`isSecureContext()` in `static/js/pwa.js`), matching the browser's own
  secure-context requirement for service workers — so plain-HTTP LAN testing
  won't register one, by design.
- `config.settings.dev` swaps WhiteNoise's manifest storage for plain
  `StaticFilesStorage` so `runserver`/`manage.py test` work without running
  `collectstatic` first. That means in dev, `{% static %}` URLs in
  `templates/service-worker.js` resolve to the unhashed filenames — the
  behaviour is equivalent, just without the hash.
- To see the worker without a full reinstall cycle during iteration, use
  DevTools → Application → Service Workers → **Update on reload**.

## Production

- Service workers require a secure context; deploy behind HTTPS (already
  required by `config.settings.prod`'s `SECURE_SSL_REDIRECT`).
- Run `collectstatic` as usual — the worker template resolves shell URLs
  through `{% static %}`, so hashed filenames are picked up automatically.
- No new environment variables, no CSP was in place to adjust, and no
  database migration is involved in any of this (see below).
