# Digital Discipleship Platform: architecture and phased roadmap

**Status:** pre-implementation design

**Decision:** Extend the existing Django application in small, reversible phases. Do
not replace the current content apps or introduce a new API/mobile stack for the
first release.

## Executive recommendation

YTR already has the right foundations for the product direction:

- Django session authentication, roles, and an approval workflow.
- A shared `ReviewableContent` lifecycle for Articles, Devotions, Episodes, and
  Videos.
- Separate content apps with bilingual English/Kinyarwanda fields.
- Podcast audio, YouTube-first video support, series models, bookmarks, RSVPs,
  a member dashboard, and responsive dashboard patterns.
- Production security hardening, upload validation, rate limiting, and safe
  redirect handling.

The platform should therefore evolve around those foundations. The first usable
release is an installable web application with a richer **My YTR** home, not a
premature attempt to merge every existing content model into one model.

## Current-state audit

| Capability | Existing reusable foundation | Gap / recommended extension |
| --- | --- | --- |
| Installable app | Responsive public and dashboard layouts; static assets served by WhiteNoise | No manifest, icons, service worker, install UI, or offline policy |
| Accounts | Django `User`, `Profile` roles, registration, login, pending-admin approval | Profile has no name, phone, language preference, or consent record; no password-reset flow |
| Public/member split | Published-content filtering and `member` dashboard | Member home is account activity, not a personalised discipleship home |
| Daily devotion | Dated, bilingual `Devotion`; featured/today selection; review workflow | No title, reading time, author, introduction, or optional audio/video relationship |
| Audio/video | `Episode` has local audio or URL; `Video` supports validated YouTube; both support series | No durable player state, embedded-video detail page, topics, speaker metadata, or cross-media relationship |
| Saved/library | Article `Bookmark`, gathering `RSVP` | Saved items are article-only; no unified library, history, completed status, or resume point |
| Fellowship/live devotion | `Gathering` models scheduled events and RSVPs | No morning-devotion model, trusted Meet URL, status logic, archive, reminders, or recordings |
| Search/discovery | Existing JSON search endpoint and public content sections | No media/topic/series filters and no archive search surface |
| Notifications/offline | None | Web Push, notification preferences, subscriptions, and cache policy are new capabilities |

## Guardrails

- Preserve the existing application boundaries (`articles`, `devotions`,
  `podcasts`, `videos`, `accounts`, and `core`) and their review workflow.
- Keep Articles, Devotions, Episodes, and Videos as source-of-truth models until
  real editorial use proves which shared fields and relationships are stable.
- Store only the minimum playback data needed to resume media. Do not create
  event-level behavioural analytics by default.
- Keep YouTube as the primary video host. Do not cache or download video files
  for offline use in the early releases.
- Maintain English and Kinyarwanda as editor-controlled content; a preference
  selects the initial presentation but never removes the manual language switch.
- Each schema phase gets a data migration only when existing rows need a value,
  plus model validation, admin/form coverage, and regression tests before the
  feature is enabled.

## PWA architecture (Phase A)

Use a conventional, framework-free PWA that fits this server-rendered Django
site. A service worker should be hand-written rather than adding a client build
system solely for PWA support.

### Deliverables

1. Add a versioned `static/manifest.webmanifest` and link it from `base.html`.
   Use `Youth Time Revival` / `YTR`, `display: standalone`, app start URL,
   `theme_color: #1a1230` (night), and `background_color: #1a1230`.
2. Add purpose-designed 192px and 512px PNG app icons, including maskable
   variants. Verify safe padding in Android adaptive icon masks.
3. Register `static/js/service-worker.js` only on supported secure origins
   (HTTPS, or localhost during development). Use cache versioning and a
   controlled `skipWaiting`/reload update flow.
4. Precache the public application shell and immutable static assets. Use a
   network-first strategy for HTML navigation with a small offline page fallback.
   Cache successful public articles/devotions on read with a bounded
   stale-while-revalidate policy.
5. Never cache authenticated dashboard HTML, POST requests, CSRF pages, private
   prayer/testimony content, or media files. Never cache Google Meet or YouTube.
6. Add a non-intrusive `Install YTR App` control. It appears only after the
   browser's `beforeinstallprompt` event and disappears after installation;
   include simple iOS install instructions where browser detection supports it.
7. Add an authenticated mobile bottom navigation only after the app shell is
   present, using Home, Word, Listen, Watch, and More. Public desktop navigation
   remains unchanged.

### PWA acceptance criteria

- Lighthouse/installability and manual Chrome Android testing confirm the
  manifest, service worker, icons, standalone launch, and no forced prompt.
- A logged-out visitor can explore before installing.
- A recently read public text resource and the shell load offline; protected and
  stale pages do not reveal private data.
- Service-worker updates do not leave users on a mixed old/new asset set.

## Authentication and My YTR (Phase B)

Retain Django's built-in `User` and extend the existing one-to-one `Profile`.
This avoids a risky custom-user-model conversion after migrations already exist.

### Profile migration

Add nullable/blank-compatible fields first, then progressively require them for
new registrations:

```text
full_name              CharField(150, blank=True)
phone_number           CharField(40, blank=True)
preferred_language     CharField(2, choices=en/rw, default=en)
privacy_accepted_at    DateTimeField(null=True, blank=True)
privacy_policy_version CharField(40, blank=True)
```

Keep the user email authoritative for identity and keep `username` internally
until a deliberately planned migration replaces it. The registration form should
collect full name, email, optional phone, password, language, and explicit
privacy/terms agreement. Existing profiles must not be invalidated by the
migration.

### Account policy decision required

The current registration path creates inactive accounts awaiting admin approval.
That is compatible with a moderated community but creates friction for a daily
discipleship product. Before Phase B, choose one explicit policy:

- retain manual approval for all accounts; or
- activate members after verified email, retaining role changes and content
  authoring approval for administrators.

Implement password reset using Django's built-in token flow during this phase;
defer Google Sign-In and other external providers.

### My YTR composition

Build My YTR as a new member-home query layer, reusing existing published
content. It shows a greeting from `Profile.full_name`, today's devotion, live or
next morning devotion, resume cards when progress exists, saved resources,
latest teaching, and the next Gathering. Empty states should point to public
content, not leave blank cards.

## Morning Devotion and Google Meet (Phase C)

Create a dedicated model in a new `morning_devotions` app (or `core` only if the
team strongly prefers fewer apps). Do not overload `Gathering`: the live-state,
Meet link, archive, and recurring daily ministry workflow are distinct.

```text
MorningDevotionSession
  title, slug
  start_datetime, end_datetime
  topic, scripture_reference, description
  speaker_name (or optional Article.Author FK)
  meet_url
  publication_status: draft / published / cancelled
  related_devotion (optional FK to Devotion)
  summary_en, summary_rw (blank until archived)
  recording_episode (optional FK to Episode)
  recording_video (optional FK to Video)
  created_at, updated_at
```

Validation must require a timezone-aware end at or after start and accept only
HTTPS Google Meet URLs on an allowlist such as `meet.google.com`; restrict paths
to actual meeting patterns. Use the same safe external-link rule in the view:
never redirect to an arbitrary submitted URL.

Compute display state rather than persisting a fragile `live` flag:

- `upcoming` when start is in the future;
- `starting_soon` in a documented pre-start window (initially 15 minutes);
- `live` from start through end;
- `finished` after end, with archive links only when published assets exist.

Administrators need a focused management screen or Django admin configuration
to schedule, publish/cancel, and later attach summaries/recordings. The first
Join button opens the validated Meet URL in a new external context; YTR does not
embed or recreate video conferencing.

## Read / Listen / Watch architecture (Phase D)

Do **not** introduce a polymorphic `Resource` model yet. The current models are
well-suited to their editorial formats and have existing review flows.

Start with explicit optional links that meet concrete editorial needs:

- Add Devotion metadata: bilingual title, introduction, reading-time minutes,
  optional author, and optional related `Episode` / `Video`.
- Add optional article-to-episode/video relationships only when authors have
  paired material to publish.
- Add topic and series taxonomy through separate `Topic` and `TeachingSeries`
  models, with M2M relationships to the existing content types. Keep existing
  PodcastSeries and VideoSeries; map or cross-link them later instead of merging
  them pre-emptively.
- Add public detail pages for episode and video resources, using HTML5 audio for
  audio and a privacy-conscious YouTube embed/no-cookie domain where practical.

A shared display adapter can provide a consistent card shape (`kind`, title,
scripture, author/speaker, URL, image, duration) without changing persistence.
Once editors regularly create multi-format bundles, assess a small
`TeachingResource`/`ResourceBundle` linking model. It should reference existing
published objects, not duplicate their full content fields.

## Playback, history, and My Library (Phase E)

Begin with two explicit progress models, rather than a generic foreign key:

```text
EpisodeProgress(user, episode, position_seconds, duration_seconds,
                last_played_at, completed_at)
VideoProgress(user, video, position_seconds, duration_seconds,
              last_played_at, completed_at)
```

Use `UniqueConstraint(user, episode)` / `UniqueConstraint(user, video)`, non-
negative values, and an authenticated same-origin POST endpoint protected by
CSRF. Update at sensible intervals (for example every 15-30 seconds), on pause,
and on page exit; mark completed around 90-95%. The browser-only player should
be tolerant of failed updates and resume from server state on next load.

YouTube progress requires the IFrame Player API and explicit consent-aware embed
handling. Implement it only on the new detail page. Do not attempt background
audio in a first release beyond what browsers naturally permit; a persistent
mini-player can follow after the base player is reliable.

For a unified saved area, add a constrained `SavedResource` only in this phase.
If it uses Django content types, enforce an allowlist of public models in model
validation, views, and queries; include a unique user/content-type/object-ID
constraint. Migrate existing article bookmarks into it before switching reads.
This provides one library while preserving `Bookmark` during a safe transitional
release. Alternatively, keep `Bookmark` as an article compatibility facade until
all views are migrated.

“Recently viewed” is optional and must be limited to resource, timestamp, and
user; retain it for a short documented period. Do not collect scroll depth,
click-stream data, or detailed viewing analytics.

## Notifications (Phase F)

Web Push needs a server-side subscription model, per-user notification
preferences, VAPID keys in production environment variables, an unsubscribe
path, and a scheduled delivery mechanism. Build it only after Morning Devotion
has stable schedules. Permission is requested from a deliberate user action in
settings—not on page load—and a decline is respected. Start with a 15-minute
morning-devotion reminder and test expired subscriptions/removal rigorously.

## Offline and personalisation (Phase G)

Expand only from measured use:

- opt-in download management for selected audio, with quota/error UI;
- cache eviction controls and a “clear offline content” setting;
- continuation and suggested resources based on saved/progress data, not opaque
  profiling;
- optional series progress derived from completed resource progress;
- later notification inbox and richer search filters.

## Migration and rollout order

1. **No database migration:** PWA assets, service worker, install UI, public
   offline fallback, and mobile shell. Ship behind normal browser capability
   checks.
2. **Profile expansion:** nullable fields plus migration; backfill only safe
   values (e.g. `full_name` from existing user names where present). Release
   profile form and registration changes separately from any approval-policy
   change.
3. **Morning devotions:** new tables only; no modification to Gatherings or
   existing content. Seed/admin-test scheduling and Meet validation before
   rendering on My YTR.
4. **Content extensions:** add nullable devotion metadata and explicit optional
   relations. Backfill editorially, never infer a relation automatically.
5. **Progress/library:** new progress/saved tables, backfill article bookmarks,
   dual-read during transition, then remove obsolete code only in a later
   dedicated cleanup release.
6. **Push/offline media:** new subscription/download tables and background-job
   infrastructure only after operational ownership and privacy copy exist.

Every phase should run `makemigrations --check`, migration tests from a fresh
database and an existing-data fixture, permission tests, mobile browser checks,
and a production-settings deploy check.

## Phase exit criteria

| Phase | Done when |
| --- | --- |
| A | App is installable, responsive as an app shell, useful offline for public text, and never exposes private cache data |
| B | A member can create/manage an account, set language, reset password, and land on a meaningful My YTR dashboard |
| C | Admin can safely schedule and publish a devotion; members see correct time state and reach only validated Meet links |
| D | Editors can publish paired formats without duplicate content; readers can choose Read/Listen/Watch on supported resources |
| E | Resume and saved library work across supported media with minimal, secure progress data |
| F | Opted-in reminders deliver reliably and users can revoke permission/preferences |
| G | Offline downloads/personalisation are transparent, bounded, and operationally supported |

## Decisions to make before implementation begins

1. Account activation: manual approval versus email-verification activation.
2. Legal copy and current policy version for the registration consent checkbox.
3. Canonical Google Meet URL policy (usually `meet.google.com` only) and who is
   allowed to create/edit sessions.
4. Whether morning devotion links are public or require a signed-in member.
5. Source and licensing of the final YTR app icon, splash artwork, and any Bible
   translation text stored directly in the platform.
6. Initial notification sender/operations owner and production hosting capable
   of scheduled work and persistent shared cache/database.

The recommended next implementation is **Phase A only**, followed by a review
of install and offline behaviour on Android, iOS, desktop Chrome, and the
current responsive breakpoints before Phase B begins.
