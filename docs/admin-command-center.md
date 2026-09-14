# YTR Admin Command Center

A branded, interactive operational dashboard for Admins at `/dashboard/admin/`
— separate from, and not a replacement for, Django Admin at `/admin/`. Django
Admin stays the technical/fallback interface for anything the Command Center
doesn't (yet) have a bespoke screen for; the Command Center is where an Admin
should be able to answer "what's happening, what needs me, what's next"
without leaving it for routine work.

## Architecture

No new framework, no rewrite. Same Django + server-rendered templates +
Tailwind CSS this project already uses everywhere else. Two small additions,
vendored as static files (no npm runtime dependency, matching this project's
no-bundler convention — same reasoning as the self-hosted fonts in
`static/fonts/`):

- `static/js/vendor/htmx-2.0.10.min.js`
- `static/js/vendor/alpinejs-3.17.2.min.js`

**Where each is actually used, and why** — neither is sprinkled in for its
own sake:

- **HTMX**: the Content workspace's live filter bar (type/status/language/
  search — a real server round-trip per filter change, with `hx-push-url`
  keeping the URL bookmarkable) and the command palette's live search-as-you-
  type. Both are genuine "refresh part of the page from the server"
  interactions HTMX is built for.
- **Alpine.js**: sidebar collapse/expand (persisted to `localStorage`), the
  Create/notifications dropdown menus, and the command palette's open/close
  + keyboard handling. All pure client-side UI state — no server round trip
  needed, so this is exactly Alpine's job, not HTMX's.
- Everything else (KPI cards, the Morning Devotion card, Needs Attention,
  the publishing pipeline, recent content, community summary, bilingual
  health, activity) is a plain server-rendered page — "use HTMX/standard
  links rather than unnecessary JS navigation" wherever a plain `<a href>`
  already does the job.

### A note on script load order (a real bug hit while building this)

`Alpine.data('commandPalette', …)` must be registered **before** Alpine's own
script runs, via the `alpine:init` event. Because these scripts are `defer`
(parsing is done by the time they execute, so Alpine doesn't wait for
`DOMContentLoaded` — it starts immediately), script tag order matters:
`admin-command-center.js` (registers the component) loads *before*
`alpinejs-*.min.js` in `templates/dashboard/admin/_base.html`. Swapping that
order silently breaks every `x-data="commandPalette()"` reference with a
"commandPalette is not defined" runtime error.

### Query/composition layer

`apps/dashboard/services.py` holds every query behind the Overview and the
Content workspace (`overview_kpis`, `admin_morning_devotion_focus`,
`needs_attention`, `publishing_pipeline`, `recent_content`,
`bilingual_health`, `community_summary`, `recent_activity`,
`command_search`, `quick_create_actions`) so `views.py` stays a set of thin
view functions. Every number renders from a real query — nothing here is a
placeholder metric.

`apps/dashboard/context_processors.py: admin_notifications` computes the
notification-bell data (and the quick-create action list) once per request,
scoped to admin dashboard pages only, so the top bar — present on every
admin page via the shared `_base.html` — always has fresh data without an
HTMX round trip just to show a badge count. It's cheap (`.count()` queries),
so this is simpler and faster than fetching it separately.

## Navigation and roles

The sidebar is grouped (Main / Content / Community / Manage / System) and
lives in `templates/dashboard/admin/_base.html`, extending the shared
`templates/dashboard/_shell.html`. Author and Member dashboards are
untouched — the shell gained a handful of **optional, empty-by-default
blocks** (`shell_attrs`, `sidebar_attrs`, `topbar`, `mobile_bar_actions`,
`content_class`, `extra_scripts`) so the Command Center's sidebar
groups/collapse, top bar, and vendored scripts are additive and don't change
anything for `dashboard/author/_base.html` or `dashboard/member/_base.html`,
which simply don't populate those blocks.

Real permission model, not link-hiding:

- Every new view (`admin_dashboard`, `content_workspace`, `command_search`)
  uses the existing `@role_required(Profile.ROLE_ADMIN)` decorator —
  anonymous → login redirect, wrong role → 403, same as the rest of the
  dashboard.
- **Deliberate widening**: `author_content_create` / `_edit` / `_submit` now
  accept `Profile.ROLE_ADMIN` as well as `Profile.ROLE_AUTHOR` (previously
  Author-only), so the "+ Create → New Article/Devotion/Episode/Video"
  quick actions actually work for Admins instead of hitting a 403 wall. This
  is a real, server-side authorization change — not a UI shortcut around
  the existing rule — and reuses the exact same views/forms Authors already
  use (no duplicate creation UI). Their internal redirects changed from a
  hardcoded `dashboard:author_home` to the role-aware `dashboard:home`
  router, since an Admin using these views shouldn't be bounced to a page
  gated to Authors only.
- Every sidebar link that doesn't yet have a bespoke Command Center screen
  points at a real, reachable destination — either the existing
  `content_queue`/`pending_testimonies`/`prayer_requests`/`messages`/
  `user_management` views, or (honestly, per "Django Admin remains
  available as fallback") a Django Admin changelist/add URL for content
  types this pass didn't build a workspace for (Morning Devotions, Library,
  Gatherings, Authors, Subscribers, Site settings). None of these are dead
  links.

## Dashboard sections (Overview)

- **KPI cards** (Members, Published resources, Pending review, Upcoming
  gatherings, Newsletter subscribers) — each a real count, each clickable to
  where that number is actionable.
- **Morning Devotion** — reuses `apps.morning_devotions.models.
  MorningDevotionSession`, but `services.admin_morning_devotion_focus()` is
  deliberately **not** the same as the member-facing
  `MorningDevotionSession.current_or_next()`: the member version skips a
  finished session with nothing attached yet (nothing useful to show a
  visitor); the admin version must surface exactly that session, because
  that's precisely when the **"Complete today's devotion"** checklist
  (summary/audio/video, one ✓/○ per item) needs to appear so the archive
  actually gets finished instead of silently staying incomplete.
- **Needs your attention** — pending content per type, sign-ups awaiting
  approval, unread contact messages, pending testimonies/prayer requests,
  and Morning Devotions finished without any content attached — every item
  links straight to the place that resolves it.
- **Publishing pipeline** — Draft → Pending review → Published → Rejected,
  aggregated across the four real `ReviewableContent` types. No invented
  "Scheduled" stage — this project has no scheduled-publish concept, and
  the spec was explicit: don't pretend a status exists that doesn't.
- **Recently published**, **Community** (counts only — see Privacy below),
  **Bilingual content health**, **Recent activity** — see the sections
  below for the two that need more explanation.

### Bilingual content health

For each of the 4 `ReviewableContent` types, `services._CONTENT_SHAPE` maps
that model's actual bilingual field names (Article: `title_en`/`body_en` +
`_rw`; Devotion: `verse_text_en`/`reflection_en` + `_rw`; Episode/Video:
`title_en`/`_rw`) to a uniform `has_en(obj)`/`has_rw(obj)` check, since the
field names genuinely differ per model — this is the one place that
difference is bridged, instead of repeated at every call site. Counts
**published** content only. No machine translation anywhere; this only
identifies which published items are missing a language, and links to the
Content workspace's `?language=missing` filter to review them.

### Recent activity — honestly derived, not fabricated

There is no generic audit log in this project (confirmed before writing any
of this — `ReviewableContent` only has single-slot `reviewed_by`/
`reviewed_at`, not a log; `django.contrib.admin.models.LogEntry` isn't used
anywhere). So "Recent activity" is built strictly from fields that already
carry real historical meaning: `published_at` + `reviewed_by` on
`ReviewableContent` ("X published Y"), and `date_joined` on `User` ("X
joined"). Nothing is invented, inferred, or backfilled — if a future
project phase adds a real audit trail, this is the function
(`services.recent_activity`) to extend, not replace.

## Content workspace

`/dashboard/admin/content-workspace/` — cross-type browsing/filtering over
Article/Devotion/Episode/Video by type, status, language, and search.
**Complements, not replaces** the existing pending-review action queue
(`content_queue` / `review_content`, unchanged): the workspace is for
*finding* content in any state; the queue is for *acting* on pending
submissions (approve/reject). Filter state lives in the query string
(`?type=&status=&language=&q=`) so a filtered view is bookmarkable/shareable
internally, and each filter field carries its own `hx-get`/`hx-target`/
`hx-push-url`/`hx-include="closest form"` rather than relying on attribute
inheritance from the `<form>` — more verbose, but avoids relying on HTMX's
ancestor-inheritance behavior for something this central to the page.
Progressively enhanced: the same `<form method="get" action=...>` works with
JavaScript disabled, just as a normal full-page GET.

Desktop renders a table; mobile renders the existing `.dash-mobile-list`/
`.dash-mobile-row` card pattern already used by every other dashboard list
in this project — reused, not reinvented.

## Command palette (Ctrl/Cmd+K)

`apps/dashboard/services.py: command_search()` is a **separate, admin-only**
search from the public `apps.core.views.search` endpoint — that one is
unauthenticated and only ever returns published content; this one is
role-gated and deliberately searches across every status (an Admin needs to
find a draft, not just what's already public) plus Members, Authors, and
Gatherings. The two must never be merged. Every result links to that
object's Django Admin change page — honest, since no bespoke per-type edit
UI exists yet for most of these (Morning Devotion, Gathering, Member,
Author).

## Privacy: what the Overview shows vs. what it never shows

Prayer requests and contact messages are private. The Overview and
Needs-Attention list only ever show **counts** ("6 prayer requests
unreviewed", "3 unread contact messages") with a link to the existing
secured queue view — never the message/prayer body text itself. Covered by
`SensitiveDataNotLeakedOnOverviewTests` in `apps/dashboard/tests.py`.

## Responsive rules

Tested at 320/390/768/1024/1440 with Playwright — zero horizontal overflow,
zero console errors, and every interactive surface (sidebar collapse or
mobile drawer, Create menu, notifications, command palette, workspace
filters) works at each width. Two real bugs surfaced and were fixed during
that pass, both are the classic CSS flex/grid "item won't shrink below its
content's intrinsic width" trap — worth knowing if you add more cards:

- `.kpi-card` (a grid item) needed an explicit `min-width: 0` — without it,
  a 2-column mobile KPI grid could push a card a few pixels past the
  viewport rather than let its text wrap.
- `.attention-label` (a flex child) needed the same treatment.

**Below 1024px there is no persistent top bar** (`.dash-topbar` is
desktop-only) — the mobile header only has room for the hamburger toggle,
title, and avatar. So Create/Search/Notifications get compact icon-only
equivalents in `{% block mobile_bar_actions %}` (populated only by
`admin/_base.html`), not the full desktop top bar squeezed into a phone
width.

## Reusable components

`kpi-card`, `attention-item`, `pipeline-stage`, `content-row`,
`activity-item`, `lang-health-row`, `dash-dropdown`/`dash-dropdown-panel`
(Create menu and notifications share this one pattern), `dash-palette*`
(command palette), `filter-bar` — all in `static/css/input.css` under
"ADMIN COMMAND CENTER", built on the pre-existing `dash-card`, `dash-table`,
`dash-mobile-list`, and `badge-*` primitives rather than duplicating them.

## What's deferred (Command Center Phases 3-5)

Per the rollout's own explicit phasing ("do NOT try to build every screen
simultaneously"), this pass delivered **Phase 1 (shell) + Phase 2
(overview)**, plus the Content workspace as the one flagship "Phase 3-style"
management screen (proving the filter/HTMX/responsive-table pattern other
content types can reuse later) and the Morning Devotion control card/
completion checklist. Deliberately **not** built in this pass:

- **Dedicated CRUD workspaces for Podcasts, Videos, Library, Gatherings,
  Morning Devotions.** Their sidebar links go to Django Admin today (honest,
  functional, just not bespoke-branded) — building each is real, repeatable
  work following the Content workspace's exact pattern.
- **Community workspaces** (Members table beyond the existing
  `user_management` screen, Authors, Subscribers) — same reasoning.
- **Website content editing** (Homepage/About/Mission/Vision/Call/Pillars/
  Site settings as branded forms) — links to Django Admin for now.
- **Charts.** Every number the spec asked for is already visible as a KPI/
  pipeline/health count; adding a charting dependency for 2-3 simple series
  didn't clear the "don't add a library merely for decoration" bar this
  pass. A lightweight option (e.g. a small vendored Chart.js build, same
  self-hosting pattern as HTMX/Alpine) is a reasonable follow-up once
  there's more than a few months of member/content-growth history to plot.
- **A general audit/activity log.** "Recent activity" is real but derived
  from existing fields only — a proper append-only audit trail (who
  cancelled a Morning Devotion, who changed a role, etc.) is new schema work
  or a later phase, not something to fake now.
