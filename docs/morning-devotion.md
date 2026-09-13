# Morning Devotion

A Morning Devotion is a scheduled live session (Google Meet) that keeps
serving the ministry after it ends: an optional written summary, an optional
audio recording, and an optional video recording, all reachable from one
stable page — `/morning-devotions/<slug>/`.

This follows the model already sketched in
`docs/roadmaps/digital-discipleship-platform.md` (Phase C) rather than
inventing a new shape from scratch — that roadmap predates this feature
request and its guardrails (don't overload `Gathering`, compute session state
rather than persist a `live` flag, validate Meet URLs strictly) are exactly
what this implementation follows.

## Architecture: reusing Episode and Video, not a new media system

`MorningDevotionSession` has no audio/video fields of its own. It has
`recording_episode` (FK to `podcasts.Episode`) and `recording_video` (FK to
`videos.Video`) — the same models that already back the Podcasts and Videos
pages, with their own upload validation, publishing status, and (for
episodes) duration. A session is "listenable" when its `recording_episode` is
set **and** that episode's own `status` is `published` — never by copying an
audio file or URL onto the session itself.

This is why `has_audio`/`has_video` check the related object's status rather
than the session's own status:

```python
@property
def has_audio(self):
    return (
        self.recording_episode_id is not None
        and self.recording_episode.status == self.recording_episode.STATUS_PUBLISHED
    )
```

A Morning Devotion can therefore be published (schedulable, joinable) while
its recording is still a draft — the "Listen" button simply won't appear
until an editor publishes the episode, no separate workflow needed.

## Why not `ReviewableContent`

Article/Devotion/Episode/Video all extend `ReviewableContent` — a
draft → pending → published/rejected flow where an Author submits and an
Admin reviews. A Morning Devotion doesn't fit that: it's admin-scheduled
ministry logistics (a time, a Meet link, later a recording), not
Author-submitted editorial writing. It gets its own simple
`draft` / `published` / `cancelled` status instead, managed directly through
Django admin — there's no `morning_devotion` entry in
`apps/dashboard/forms.py: CONTENT_REGISTRY` (that registry is specifically
for the Author-submit/Admin-review pipeline).

## Session state is computed, never stored

`session_state` is a property, not a database column:

- `upcoming` — more than 15 minutes before `start_datetime`
- `starting_soon` — within 15 minutes of `start_datetime`
- `live` — between `start_datetime` and `end_datetime`
- `finished` — after `end_datetime`

A persisted "is_live" boolean would drift the moment nobody updates it after
the session actually ends. Computing it from the clock means it's always
correct, at the cost of nothing more expensive than a `timezone.now()`
comparison.

**Media availability is a separate axis from session state** — a `finished`
session might have audio, video, both, or neither, independent of whatever
state it's in. The detail page and cards render Read/Listen/Watch/Join Live
purely from `has_summary`/`has_audio`/`has_video`/`can_join_live`, never by
inferring them from `session_state`.

## Google Meet URL validation

`apps/morning_devotions/validators.py: validate_meet_url` requires `https://`
and a `meet.google.com` host with a real path (rejects the bare domain and
look-alike hosts like `meet.google.com.evil.com`, since `urlparse().hostname`
only matches an exact host). The Meet link is only ever rendered as a plain
outbound `<a href target="_blank">` — there is no server-side redirect
endpoint that takes a URL and forwards to it, so there's nothing to validate
at request time beyond the model field itself.

## Sharing

Same pattern as the devotion share sheet (`docs/devotional-sharing.md`):
WhatsApp/Facebook/X/Telegram/Email/Copy Link, built client-side
(`static/js/morning-devotion.js`) from a `json_script` payload so the links
follow whichever language the visitor currently has toggled. The shared link
is always the Morning Devotion page (`/morning-devotions/<slug>/`), never a
raw audio/video storage URL. Native Web Share (`navigator.share`) is wired as
"More…", hidden via progressive enhancement where unsupported.

Unlike the devotion share sheet, there's no "repost image" flow here — this
spec only asked for cover art (below) and link sharing, not a
generate-and-share branded card.

## Cover art

`apps/morning_devotions/cover.py` renders a branded PNG (title, scripture,
date, YTR footer) reusing the same Pillow foundation as the devotion share
cards. The generic parts (fonts, gradient, word-wrap, contact-footer lines)
were extracted from `apps/devotions/share_cards.py` into
`apps/core/card_rendering.py` specifically so this didn't need a second copy
of that plumbing — `apps/devotions/share_cards.py` now imports from there too
and re-exports the same names, so nothing else needed to change. Only
`square` (1080×1080) ships, same scope decision as the devotion cards.
Editors never design this image; it's generated from the session's own
fields and cached (see below).

## Caching

Identical approach to the devotion share cards: `cover.cache_key()` hashes
`(session.pk, format, session.updated_at, site_settings.updated_at)` and the
view stores the rendered bytes in Django's cache indefinitely — editing the
session or the contact details changes the key, so it re-renders
automatically next request.

## Audio player

The audio player is the same native `<audio controls>` element the Podcasts
page already uses (play/pause/seek/volume/duration all come for free from
the browser) plus a small speed-selector enhancement
(`static/js/morning-devotion.js`) that sets `audio.playbackRate` — Chrome's
native controls don't expose a speed menu the way Safari's do, so 1x/1.25x/
1.5x/2x buttons sit next to the player.

## Video

The public Videos app doesn't have detail/embed pages yet (that's Phase D in
the roadmap) — it currently just links out to YouTube. Since this session
needed a real embedded player, `apps/morning_devotions/youtube.py` extracts a
video ID from `recording_video.youtube_url` and the detail page embeds it via
`youtube-nocookie.com` (the privacy-conscious embed domain, per the
roadmap's own guidance), falling back to a native `<video>` tag if the video
was uploaded as a file instead of a YouTube link. This embedding logic is
scoped to this app only, not added to the Videos app itself.

## Homepage and My YTR integration, and `Gathering` vs `MorningDevotionSession`

**These are two different concepts and must stay that way:**

```text
MorningDevotionSession = the daily/recurring live-then-recorded YTR Morning
                          Devotion — Google Meet + read/listen/watch archive.

Gathering              = fellowship/community events: conferences, prayer
                          nights, special programs. Its own RSVP flow.
```

The homepage used to have a card labeled "Morning Devotion" that actually
rendered a `Gathering` plus a raw `SiteSettings.morning_devotion_url` field —
a naming collision from before `MorningDevotionSession` existed. That's fixed:
the homepage's "Morning Devotion" card (`templates/home/home.html`) and My
YTR's "Morning Devotion" card (`templates/dashboard/member/home.html`) are
both now powered by `MorningDevotionSession.current_or_next()`. `Gathering`
still has its own separate "Upcoming Gathering" section/card on both pages —
it was never removed, just no longer mislabeled.

`SiteSettings.morning_devotion_url` is now unused by any template. It's left
in place rather than migrated away (deleting a model field is a schema
change with its own risk, out of scope for this cleanup) but nothing reads it
anymore — a future pass could remove it.

### Selection priority: `MorningDevotionSession.current_or_next()`

Both the homepage and My YTR call the same classmethod, so they can never
disagree about which session is "the" current one:

```text
live > starting soon > next upcoming > latest finished session with content > None
```

A finished session with no summary/audio/video yet is skipped in favor of an
earlier finished one that does have content — surfacing a dead-end card
(nothing to read/listen/watch, live call long over) is worse than showing an
older but actually useful session. If nothing qualifies at all, the method
returns `None` and both templates render a plain empty state rather than a
broken or misleading card.

### Homepage card states

| `session_state` | Card shows | Primary action |
| --- | --- | --- |
| `live` | "LIVE NOW" badge | Join Morning Devotion (+ Read·Listen·Watch link if content already attached) |
| `starting_soon` | "Starting soon" badge | Join Morning Devotion (join opens early, same as live) |
| `upcoming` | "Next session" badge, date/time/title/scripture/speaker | View details (no join link yet — nothing to join) |
| `finished` (with content) | "Latest devotion" badge | ▶ Listen (prominent) if audio exists, plus Read/Watch as secondary links |
| `None` | — | Empty-state copy, no card content |

## Fixes made during Phase C closure (not new functionality, restoring the
intended behavior)

- **PWA bottom app-nav was showing to anonymous visitors.**
  `templates/partials/pwa_mobile_nav.html` rendered the `.pwa-bottom-nav` and
  its "More" sheet unconditionally; per the roadmap's own Phase A spec
  ("Add an **authenticated** mobile bottom navigation..."), it's meant to be
  authenticated-only. Anonymous visitors lose nothing — the same links
  (About/Videos/Library/FAQ/Contact/Login/Register) are already in the
  regular hamburger menu (`partials/nav.html`) available to everyone. The
  authenticated "More" sheet was also missing direct Videos/Library/FAQ/
  Contact links (it only had "Dashboard"), and its Dashboard link now
  resolves to the correct role-specific home (`dashboard:member_home` for a
  member) instead of the generic `dashboard:home` redirect stub.
- **My YTR's Read/Listen/Watch tiles referenced a nonexistent `.title`
  attribute** on `Episode`/`Video` (only `title_en`/`title_rw` exist) and
  rendered blank. Fixed with a small reusable helper,
  `apps/core/i18n.py: bilingual_field(obj, field, lang)`, plus
  `viewer_language(user)` which reads the member's own
  `Profile.preferred_language` — a field that's been collected at
  registration since Phase B but was never actually used anywhere until now.
  This is deliberately a different mechanism from the public site's instant
  client-side `.i18n-en`/`.i18n-rw` toggle: My YTR is authenticated and
  server-rendered per request, so it can and does resolve the language
  server-side from the member's stored preference instead.
- **My YTR's same tiles also showed literal icon-name text** (`ARTICLE`,
  `HEADPHONES`, `PLAY_ARROW`) instead of icons — the Material Symbols font
  was only ever loaded on the public site's `base.html`, and its CSS rule was
  scoped inside a mobile-only media query for the bottom-nav's use of it. The
  dashboard shell (`templates/dashboard/_shell.html`) now loads that font
  too, and `.material-symbols-outlined` is defined unconditionally so it
  works in the dashboard at any width.
- **A podcast test was flaky depending on what a previous `manage.py test`
  run had left behind.** Django doesn't isolate uploaded test files into a
  temp `MEDIA_ROOT` by default, so a stray `media/episodes/episode.mp3` from
  an old run made every subsequent same-named upload get a collision-avoiding
  suffix, breaking an assertion on the exact upload URL. `config/settings/dev.py`
  now points `MEDIA_ROOT` at a fresh temp directory whenever `manage.py test`
  runs (mirroring the existing fast-password-hasher-under-test pattern in the
  same file), so test uploads can never collide with real local media or
  leftovers from a previous run.

## Security

- Only `status=published` sessions are reachable via the detail page, the
  cover-image endpoint, or the public list — draft/cancelled 404, same rule
  the rest of the public site enforces.
- `format` on the cover endpoint is a strict allow-list (currently just
  `square`) — anything else is a 400.
- The Meet link is never proxied or redirected through YTR's own server; it's
  a direct outbound anchor to a URL that was already validated at save time.

## Decisions made building this (documented per the roadmap's own "decisions
to make before implementation" list)

- **Public, not member-only.** The roadmap flagged this as an open decision.
  Given every other content type on the site (articles, devotions, podcasts,
  videos) is public, Morning Devotion sessions are public too, for
  consistency. This is easy to change later — wrap the detail/list views
  with `@login_required` if the ministry decides otherwise.
- **Speaker reuses `articles.Author`** rather than a plain text field, per
  the roadmap's own suggestion — avoids a duplicate "who's speaking" concept
  next to the one Articles already has.
- **`language` lives on the session, not on `Episode`.** It identifies which
  language the *attached recording* is in, not a translation of the
  session's own text (which doesn't have parallel `_en`/`_rw` fields the way
  Devotion/Article do — see below). Scoped to this model instead of adding a
  new field to the shared `Episode` model for a concern that's specific to
  Morning Devotion.
- **The "Latest" filter tab from the spec was folded into "All."** In a
  single flat list already sorted newest-first, "Latest" and "All" would
  render identically — there was nothing to give it distinct behavior
  without inventing product meaning that wasn't specified. The archive ships
  with **All / English / Kinyarwanda** instead of four tabs, one of which
  would have been a dead duplicate.
- **`title`/`scripture_reference`/`description`/`summary` are the fields
  that exist** (matching the roadmap sketch), not a `topic` field — the
  roadmap listed both `title` and `topic` but every example in the actual
  feature request (e.g. "Walking by Faith") uses the title itself as the
  theme, so a separate `topic` field would have duplicated it.

## What's deferred

- **Playback progress / "Continue Listening."** The roadmap's Phase E
  (`EpisodeProgress`/`VideoProgress`) is explicitly a later phase, and the
  spec for this feature explicitly said not to build it here. Nothing in
  this implementation blocks adding it later — the player is a plain
  `<audio>` element a future progress script can attach to.
- **Downloading / offline audio.** Streaming only, as specified. No object
  storage URLs are exposed for direct download.
- **Push notifications / reminders.** Roadmap Phase F, not part of this pass.
- **Removing the now-unused `SiteSettings.morning_devotion_url` field.**
  Nothing reads it anymore (see the closure fixes above), but deleting a
  model field is its own schema change/migration and wasn't asked for —
  left in place, flagged as safe to remove later.
- **Per-language recordings on one session.** For now, one session points to
  one `recording_episode`. If YTR later records separate English and
  Kinyarwanda sessions, the documented extension path is a second nullable
  `recording_episode_rw` FK (or a small through-model if more than two
  languages are ever needed) — no schema rewrite required.
