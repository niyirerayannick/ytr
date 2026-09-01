# Youth Time Revival Codebase Audit

**Audit date:** 2026-09-01  
**Scope:** Repository source, Django configuration and migrations, models, routes, forms, templates, static assets, automated tests, dependency checks, and local browser checks.  
**Changes made during audit:** None. This report is observational only.

## 1. Executive Summary

YTR is a well-started, server-rendered Django ministry site. Its strongest foundations are the clear domain app split, a reusable draft/review/publish workflow for four media types, bilingual authoring fields, practical Django-admin coverage, and tested role-based dashboard access. The current implementation is a credible early content MVP, not yet a safe production deployment.

The main risks are operational and product-completeness risks rather than a broken core: production can start with a known fallback secret; public forms have no abuse protection; arbitrary uploaded audio/video files have no explicit type or size policy; user-controlled `next` values enable open redirects; and the source tree is effectively not version-controlled (`git ls-files` returned only `ytr.html`, while the Django project is untracked). SEO, error pages, logging, consent/privacy workflow, search depth, scheduling, and CMS coverage remain early-stage.

The existing visual direction is original and coherent: the `night` / `ember` / `dawn` / `paper` tokens and Fraunces/Work Sans pairing give the site a distinctive ministry character. It needs responsive polish: local browser checks found a repeatable 26px horizontal overflow at 320px on all public pages, caused by the shared navigation tools.

**Overall readiness score: 48 / 100**

| Area | Score | Reasoning |
| --- | ---: | --- |
| Architecture | 7/10 | Clear Django apps and an effective shared workflow base; dashboard views are beginning to centralize too many concerns. |
| Backend | 6/10 | Core public content, accounts, and workflows work; validation, scheduling, and several required domains are incomplete. |
| Frontend/UI | 6/10 | Cohesive, original visual system and useful shared partials; public navigation and several pages are still prototype-like. |
| Content Management | 5/10 | Django admin manages current models, but homepage, media, taxonomy, structured About content, and editorial roles are incomplete. |
| Security | 4/10 | CSRF, auth validators, role checks, and production HTTPS basics exist; secret fallback, redirects, upload controls, and abuse prevention require attention. |
| Performance | 6/10 | Good use of `select_related`, `prefetch_related`, and devotion pagination; no cache strategy, image pipeline, or query/performance regression tests. |
| SEO | 2/10 | Human-readable article slugs/titles exist; metadata, canonical URLs, sitemap, robots, structured data, and social cards are absent. |
| Accessibility | 5/10 | Semantic landmarks, visible focus styling, labels, skip link, and several ARIA labels exist; dialogs/menu behavior, alt text, and keyboard interaction need work. |
| Testing | 5/10 | 49 focused Django tests pass; major public and workflow paths lack coverage. |
| Deployment Readiness | 3/10 | Settings split and WhiteNoise are good starts; no tracked deployment manifests, error handlers, logging, backups, or source-control baseline. |

## 2. Existing Architecture

This is a Django 5.2 monolith using Django templates, plain JavaScript, Tailwind CSS, SQLite locally, and optional PostgreSQL through `DATABASE_URL`.

| Layer | Actual implementation |
| --- | --- |
| Apps | `core`, `accounts`, `dashboard`, `devotions`, `articles`, `podcasts`, `videos`, `library`, `about`, `faq`, `engagement`. |
| Content | `ReviewableContent` abstract model supplies draft/pending/published/rejected lifecycle to Article, Devotion, Episode, and Video. |
| Auth | Django built-in `User` plus one-to-one `Profile` role: admin, author, member. Registration creates inactive members; a signal creates profiles. |
| CMS | Django admin registers all current content models. Author dashboard permits author creation/editing of the four reviewable types; admins review them. |
| Bilingual copy | English/Kinyarwanda fields live on the same record. Both variants are rendered and client JS toggles visibility, persisting local choice in `localStorage`. |
| Frontend | `templates/base.html`, partial nav/footer/search overlay, conventional page templates, one Tailwind source file and one plain JS bundle. |
| Database | SQLite by default; `dj-database-url` enables PostgreSQL configuration. |
| Deployment | `base`, `dev`, and `prod` settings; WhiteNoise static storage; WSGI/ASGI modules. No Docker, compose, Gunicorn command, or deployment manifest is present. |

Important routes include public content lists (`/articles/`, `/devotions/`, `/podcasts/`, `/videos/`, `/library/`, `/about/`, `/faq/`, `/contact/`), `/search/`, account login/registration, and role-specific `/dashboard/admin/`, `/dashboard/author/`, and `/dashboard/member/` screens.

## 3. Features Already Implemented

| Feature | Status | Quality | Notes |
| ------- | ------ | ------- | ----- |
| Public homepage | Partial | Good start | Devotion, next gathering, articles and newsletter CTA; no admin-managed hero media, teaching, podcasts, testimonies, community blocks, or complete event presentation. |
| Articles | Partial | Good | Public list/detail, byline, cover, bilingual fields, review workflow, bookmarks. No taxonomy, rich blocks, SEO fields, reading time, related-by-topic logic, or author detail pages. |
| Devotions | Partial | Moderate | Date, verse/reflection/prayer, workflow and paginated archive. Missing title, detail route, author, introduction, topic/language filters, scheduled/archive statuses, SEO. |
| Podcasts | Partial | Moderate | Series and published episodes with efficient prefetch. Page does not render audio controls or episode detail pages. |
| Videos | Partial | Moderate | Series/feature and YouTube links exist. Interaction opens an external link; no validated embed model, thumbnail metadata, speaker/topic fields, or detail pages. |
| Library | Partial | Moderate | Curated bilingual book cards and optional external link. No resource type, file/download policy, category, status, or permission control. |
| Gatherings | Partial | Moderate | Basic model, next-gathering query, RSVP and calendar link. No public list/detail, flyer/media, status, registration URL, past-activity/recap model, or date validation. |
| About content | Partial | Moderate | Admin-managed seven mountains, beliefs, and call timeline. Mission/vision sit in singleton settings; no managed pillars/founder/story sections. |
| FAQ/Q&A | Partial | Moderate | Curated bilingual FAQ with highlight. No public submissions, categories, detail pages, related content, moderation workflow, or answer lifecycle. |
| Newsletter/contact | Partial | Moderate | Database persistence and email attempt; no double opt-in, unsubscribe, preferences, consent/audit trail, spam control, or reliable send-failure handling. |
| Accounts/dashboard | Partial | Good | Registration approval, roles, author review flow, member submissions/bookmarks/RSVPs. Roles are too coarse for a complete editorial organization. |
| Responsive dashboards | Complete | Good | Mobile drawer and card views are implemented below `lg`; prior local checks found no dashboard overflow at 375/768/1440. |
| Search | Partial | Moderate | JSON title/question search across articles, devotions and FAQs. No full-text ranking, filters, pagination, media/authors/events/library support, or accessible results/dialog semantics. |
| SEO | Missing | Low | No explicit SEO framework or assets. |
| Production operations | Missing | Low | No container/deploy definition, structured logging, backup/runbook, error templates, or health check. |

## 4. YTR Requirements Gap Analysis

| Requirement | Current State | Gap | Priority |
| ----------- | ------------- | --- | -------- |
| Secure production baseline | Partial | Require external secret, validated settings, upload policy, redirect protection, form throttling, logging and error pages. | P0 Critical |
| Source-control baseline | Needs Improvement | All Django source is untracked in the current Git repository. | P0 Critical |
| Mobile public navigation | Partial | Shared public nav overflows at 320px. | P0 Critical |
| Homepage as CMS composition | Partial | Hero is hardcoded SVG; no hero media/content block management and many planned modules absent. | P1 High |
| Editorial content workflow | Partial | Works for four models; lacks scheduling and archiving, editorial audit trail and moderation for other public content. | P1 High |
| Devotional platform | Partial | No title/detail/author/topics/SEO/filtering/scheduled states. | P1 High |
| Articles as resource platform | Partial | Missing taxonomy, rich content blocks, embeds, metadata, reading time and related logic. | P1 High |
| English/Kinyarwanda | Partial | Manually authored fields are appropriate, but no completeness policy, language URLs, metadata, language-aware search or API/query support. | P1 High |
| Events/gatherings | Partial | No public archive, status, flyer, details, registration, recaps or media. | P1 High |
| Q&A submissions/moderation | Missing | Existing FAQ is only curated static records. | P1 High |
| Newsletter privacy workflow | Partial | No consent, confirmation, unsubscribe, preferences, delivery provider strategy or rate limit. | P1 High |
| Search | Partial | Basic `icontains`; add first-party PostgreSQL full-text search when moving to Postgres. | P2 Medium |
| SEO foundations | Missing | Metadata, canonical, sitemap/robots, schema and social preview support absent. | P1 High |
| Media platform | Partial | Series exist; no robust audio/video delivery strategy, provider validation, transcripts or metadata. | P2 Medium |
| Roles/permissions | Partial | Admin/author/member work, but editor/content admin/media manager need deliberate Django-group permissions. | P2 Medium |

## 5. Backend Findings

Strengths:

- Public views consistently filter `ReviewableContent` on published status. Article tests confirm draft/pending content is not exposed publicly.
- `role_required` in `apps/dashboard/access.py` correctly redirects anonymous users and raises 403 for authenticated users lacking a role.
- `select_related` is used for bookmark/RSVP screens and video feature; `Prefetch(..., to_attr=...)` prevents episode/video-series N+1 queries.
- The generic `CONTENT_REGISTRY` avoids four nearly identical author/admin workflow implementations.

Findings:

- `ReviewableContent` has no `scheduled` or `archived` state, no `scheduled_at`, no publication author/editor audit history, and no transaction around state transitions. Its current four-state model is suitable for an MVP but not the requested editorial lifecycle.
- `apps/dashboard/views.py` centralizes queues, state changes, profile roles, member submissions and public actions. It is not yet unmanageable, but should gain focused query/service helpers before more content types are added.
- `Article.related_articles()` is newest-content fallback, not related-content logic. It will become less useful as the library grows.
- `Devotion` has a slug but has no detail route or template; archive items are not individually addressable. Its `date` is globally unique, which is a reasonable “daily” constraint but prevents more than one devotion per day across languages/content variants.
- The `Author` entity is decoupled from the authenticating `User`, which is sensible for guest contributors but means author accounts cannot yet maintain their own public profile/bio/photo and can be assigned only manually.
- Events need a `clean()` validation that start precedes end. The homepage fallback deliberately returns the last past event when no upcoming event exists, contrary to the stated requirement not to feature expired events (`apps/core/views.py`, `_next_gathering`).
- `SiteSettings.load()` does a `get_or_create` in a context processor. It is convenient but makes a database write possible during any first page request and hard-codes a singleton convention without a database check constraint.

## 6. Frontend / UI Findings

Strengths:

- The palette and typography are consistent, distinctive and suitable for the ministry; the implementation is not a copy of another ministry site.
- Shared base, navigation, footer, search overlay and article-card partials provide a useful starting component boundary.
- The dashboard shell now uses real drawer controls and responsive mobile card markup, rather than inaccessible CSS-only hiding.

Findings:

- Large inline style usage in page templates makes responsive and design-token maintenance harder; examples are common in `templates/home/home.html` and content detail/list templates.
- The main navigation does not yet reflect the planned resource structure: no Gatherings link, Watch/Listen/About sub-navigation, teaching taxonomy, or clear Questions/Q&A label.
- The homepage hero is a hard-coded decorative SVG and JavaScript particles, not replaceable hero media. Several required sections are absent rather than merely unpopulated.
- Devotions are presented as a single expanded card/archive, so content cannot have a linkable individual devotional page.
- Podcast cards have metadata but no visible audio player, audio URL action, or transcript link. Video thumbs are non-semantic `div` click targets in the series list, so keyboard users cannot activate them.
- The current client-only language switch delivers both languages in every HTML response. This is fast for a small content set but doubles rendered content and leaves `lang="en"`, document title, metadata, search labels and sharable URLs language-inaccurate.

## 7. Responsive Design Findings

Local Chrome checks loaded 12 public routes at 320, 375, 390, 768, 1024, 1280 and 1440px: 84 checks total. All routes returned HTTP 200. At 320px, all 12 public pages had horizontal overflow (`scrollWidth=346`, viewport width 320). At all wider audited sizes the overflow test passed.

The source is the shared public nav: `.nav-tools` reaches x=345.8px on a 320px viewport. The combination of the brand, hamburger, language toggle, search control and login/dashboard link cannot fit in `.nav-row` at this width (`templates/partials/nav.html:3-35`). Fix it mobile-first by moving nonessential nav tools into the opened menu or an account/utility panel and enforcing `min-width:0`/appropriate layout rules. Do not solve it with page-level `overflow-x:hidden`, which conceals rather than resolves the inaccessible controls.

Dashboard verification performed during the preceding responsive work confirmed the admin, author and member root pages at 375, 768 and 1440px have no horizontal document overflow, drawer behavior works below `lg`, and desktop sidebar behavior works at 1440px. The dashboard work should be retained.

Additional observations:

- The public nav’s CSS breakpoint is 1080px, while dashboard behavior uses Tailwind `lg` (1024px); use an intentional breakpoint scale rather than unrelated thresholds.
- Responsive public-page assertions are not part of the test suite. Add Playwright smoke tests for 320/375/768/1024 widths and keyboard interaction with menu/search.

## 8. Content Management Findings

Django admin is a capable CMS fallback for the current schema: models are registered with useful lists, filters and search fields, and content authors can draft/submit Article, Devotion, Episode and Video via their dashboard. This should remain the base rather than introducing a separate CMS immediately.

Current limitations:

- Homepage layout/content cannot be managed as structured, reusable sections. Hero media, featured teaching, testimonies, community CTA and newsletter placement are template-driven.
- Content is missing taxonomies (category/tag/topic), SEO records, content scheduling, archive controls, language completeness checks, and an editorial audit log.
- `FAQ`, `Book`, `Gathering`, `About` records and series are admin-only, which is appropriate initially but requires permissions if non-superusers will maintain them.
- The three custom profile roles should not be expanded blindly. Use Django groups/permissions to define Super Admin, Content Editor, Author and optionally Media Manager. A general Member role is useful only when its saved-content/community features are deliberately retained.

## 9. Bilingual Architecture Findings

The current same-record paired-field model is a good fit for YTR’s immediate requirement because English and Kinyarwanda versions are written and reviewed together. It avoids duplicated status, author, cover/media, featured state and relationships. This is preferable to separate related translation records for the current small two-language ministry site.

Keep paired fields for the shared lifecycle models, but improve the pattern:

- Add a bilingual-content mixin/field convention and validation that required English/Kinyarwanda fields are complete before submission/publishing.
- Add `language`/availability metadata only where one language may be legitimately absent (for example external video/audio).
- Use language-aware server responses and language-specific canonical URLs only if SEO/shareability becomes a priority. A future translation-record model is justified only for more languages, independently scheduled translations, or substantially divergent localized content.
- Apply the same paired-field convention to events, series descriptions, resources, Q&A and managed pages. Do not use machine translation as publishing output.

## 10. Security Findings

### Critical

1. **Production secret can silently fall back to a known insecure value.** `config/settings/base.py:15` supplies `django-insecure-change-me-in-.env`; `prod.py` requires hosts but does not require a non-placeholder secret. A production deployment missing its secret can use a publicly known signing key. Require `SECRET_KEY` with no default in production and reject short/insecure values at startup.

### High

1. **The working Django project is untracked.** `git ls-files` returned only `ytr.html`; all apps, settings, requirements and templates appear as untracked files. This is a release-integrity and recovery risk. Establish a clean Git baseline, review it, protect the default branch, and ensure `.env`, SQLite and media remain excluded.
2. **Open redirect through user-controlled `next`.** `apps/dashboard/views.py:327` and `:340` redirect directly to `request.POST["next"]`. An authenticated user can be sent to an external phishing target. Restrict with `url_has_allowed_host_and_scheme` or use Django’s safe redirect pattern.
3. **Public registration/contact/newsletter endpoints have no rate limiting, honeypot or CAPTCHA.** They are straightforward spam and mail-amplification targets. Add layered throttling (reverse proxy plus app-level rate limit), a privacy-preserving bot control/honeypot, and monitoring.
4. **File uploads lack explicit size/type/extension rules.** `apps/podcasts/models.py:58` and `apps/videos/models.py:47` use unrestricted `FileField`; uploads are accepted from Author forms. Define allowed formats, maximum sizes, content-type verification, private/quarantined storage where appropriate, and serve media from a non-executable host.
5. **Newsletter processing has no consent lifecycle.** `NewsletterSubscriber` stores only email/confirmed flag and never sends confirmation/unsubscribe controls. Do not email lists from this model until opt-in, unsubscribe and preference/audit requirements are implemented.

### Medium

1. `send_mail(..., fail_silently=True)` in `apps/engagement/views.py` discards delivery failures while reporting success. Log and surface an operational alert; keep user messaging privacy-safe.
2. No Content Security Policy, `SECURE_REFERRER_POLICY`, `CSRF_TRUSTED_ORIGINS` production documentation, session expiry policy, login attempt throttling, or explicit `SECURE_PROXY_SSL_HEADER` guidance exists. The existing HTTPS/HSTS and secure-cookie settings in `config/settings/prod.py:8-13` are a good start.
3. External media/resource URLs are generic URL fields without provider/domain allowlists. Use a YouTube ID or allowlisted URL validator for YouTube, and a deliberate allowlist for external library links.
4. Testimony, prayer, contact and subscriber data have no retention, consent, access-audit or deletion procedures. Prayer requests in particular need restricted admin permissions and minimal logging.

### Low

1. The local `.env` was inspected without exposing values: it is ignored and not tracked, and a secret is present rather than the documented placeholder. Keep it that way.
2. `ImageField` gives Pillow-level image validation, and Django template autoescaping/CSRF middleware are enabled. These are positive controls, not substitutes for an upload policy.

## 11. Performance Findings

- Good: published media series use `Prefetch`; video feature uses `select_related`; devotion archive uses `Paginator(…, 10)`; public content filtering avoids rendering drafts.
- `Article.related_articles()` runs an additional query and offers no category relevance; acceptable now but should be reviewed with taxonomy.
- Admin queues and author dashboard gather four querysets in Python and sort in memory (`apps/dashboard/views.py:108-114`, `203-209`). Fine for small queues; paginate and use a unified query/activity model if volume grows.
- List views lack pagination for articles, media series, FAQs, library and admin messages. Add it before large content libraries.
- Remote Google fonts and no image resizing/WebP generation are likely mobile-network costs. Add responsive image derivatives, `loading="lazy"` for noncritical images, dimensions to prevent layout shift, and self-host fonts only if the performance/privacy trade-off warrants it.
- No caching is necessary yet. Start with per-view/template fragment caching after profiling repeated public queries, especially `SiteSettings.load()` and homepage collections.

## 12. SEO Findings

Only basic HTML titles and article slugs are implemented. `templates/base.html:3-12` has no meta description, canonical link, Open Graph/Twitter tags, robots directive, or favicon metadata. There is no `robots.txt`, XML sitemap, structured data, 404 template, redirect policy, or social-sharing image implementation.

Recommended foundation:

1. Add a reusable metadata context/template block with a site default and per-model title, description, canonical URL and OG image.
2. Add `django.contrib.sitemaps`, a sitemap for published public records, and static `robots.txt`.
3. Implement JSON-LD for Organization/WebSite, Article, VideoObject when verified data exists, PodcastEpisode where relevant, and Event for public gatherings.
4. Add individual devotion, event, media and Q&A URLs before claiming those entities in search/sitemap/schema.
5. Ensure language selection is reflected in metadata before exposing bilingual SEO URLs.

## 13. Accessibility Findings

Positive practices include a skip link, `main` landmark, semantic header/footer, labels generated for Django form fields, focus-visible styling, live toast status, menu/search button labels, and `rel="noopener"` on external links.

Issues to address:

- The search overlay lacks dialog semantics, focus trapping, focus restoration and inert/background behavior. It should be a keyboard-safe modal pattern.
- Public nav toggle controls only `aria-expanded`; it does not set `aria-controls`, close after link selection, or manage focus. The dashboard drawer is better and can guide this implementation.
- Videos in a series are clickable `div` elements (`templates/videos/video_list.html`), inaccessible by keyboard. Use buttons or links with clear names.
- Informative covers and author avatars have empty `alt` text. Use empty alt only for truly decorative images; otherwise provide meaningful authored alt text.
- Several interactions rely on color/state without robust text or state communication. Test color contrast and keyboard focus in the browser, including the dawn-on-night combinations.
- There is no automated accessibility linting or keyboard/browser smoke coverage.

## 14. Database Findings

| Model/domain | Strengths | Gaps / integrity concerns |
| --- | --- | --- |
| Profile | One-to-one relationship and timestamps; signal guarantees creation on normal user creation. | Role is custom string rather than Django permissions/groups; no language/preferences. |
| Article / Author | Slug uniqueness, lifecycle metadata, byline relationship, timestamps. | No tags/categories/read time/SEO/author social/full profile. Related content has no topic relation. |
| Devotion | Unique date and slug, bilingual verse/reflection/prayer, workflow. | No title, author, intro, body detail, topics, image, read time, schedule/archive. |
| Podcast / Video | Series relationships, workflow and ordering. | No provider IDs/validation, speaker/topics/language/status on series, publication metadata surfaced to readers, transcript. File fields have no policy. |
| Gathering | Basic start/end/location and timestamps. | No status, flyer, registration/map/featured, language fields, past activity, and no start/end validation. |
| Testimony / Prayer | Correct member ownership and moderation state. | Testimony has no explicit consent/public visibility/media language; prayer has no retention/access audit. |
| Newsletter / Contact | Email uniqueness and timestamps. | No consent proof/token/unsubscribe/preferences; no message retention/status beyond unread. |
| FAQ / Book / About | Bilingual curated content and ordering are simple. | Missing taxonomy/status/SEO/detail routes; pillars and structured founder/profile content absent. |

`makemigrations --check --dry-run` reported no changes, so the current model/migration state is consistent. No migration conflicts or destructive migrations were identified. Consider indexes for common filters as content grows: `(status, published_at)`, `(status, is_featured)`, event start/end, and searchable/taxonomy fields. Add them only after PostgreSQL/query profiling where appropriate.

## 15. Testing Findings

Verification run:

| Command | Result |
| --- | --- |
| `python manage.py check` | Passed; no issues. |
| `python manage.py makemigrations --check --dry-run` | Passed; no model changes detected. |
| `python manage.py test -v 1` | Passed: **49 passed, 0 failed, 0 skipped**. |
| `python -m pip check` | Passed; no broken requirements. |
| `npm run build:css` | Passed; Browserslist database is outdated warning only. |
| `npm audit --json` | 0 known npm vulnerabilities. |
| `npm run build` | Not defined in `package.json`. |
| `pytest` | Not installed/configured. |
| `manage.py check --deploy --settings=config.settings.prod` | One warning due to intentionally short audit-only secret; production requires a real 50+ character generated secret. |

The suite correctly covers core article visibility, registration approval, profile signal, dashboard role gating, article review transitions, bookmarking, basic page loads, contact persistence/mail invocation, newsletter deduplication, and basic podcast/video/library/FAQ behavior.

Important missing tests: CSRF/method enforcement for all state actions; safe redirects; unauthorized access to every action endpoint; file validation; email failure behavior; newsletter confirmation/unsubscribe; testimony/prayer privacy; event edge cases; media URL validation; devotion publication visibility and pagination; SEO/error pages; language state; responsive/public nav keyboard behavior; admin CRUD permissions; and production settings.

## 16. Technical Debt

- Entire application source is currently untracked by Git.
- `apps/dashboard/models.py` is empty and `PermissionDenied` is imported unused in dashboard views.
- The standalone `ytr.html` prototype duplicates a large amount of implemented site content and can drift from Django templates. Keep it clearly designated as an archival design reference or remove it from deployable source once the Git baseline is safe.
- Many templates have inline styles and page-specific markup that should become small reusable presentational partials after core functionality stabilizes.
- Hard-coded content in the homepage/hero and template text conflicts with an administrator-managed ministry content plan.
- No deployment automation, logs, health endpoint, backup policy or dependency-update process is documented.
- Two literal mojibake strings found in dashboard templates were normalized during Phase 0; the remaining source files are UTF-8.

## 17. Production Readiness

**Classification: Early Development.**

The project is runnable, migration-clean, test-backed in key areas, and provides real public/admin workflows. It should not be deployed to a public production audience until the P0/P1 security, source-control, responsive-nav, privacy, SEO and deployment-operability foundations are addressed. A controlled staging deployment can follow those fixes, using PostgreSQL, object storage/media delivery, a real SMTP/provider integration, and a deployment runbook.

## 18. Recommended Architecture

Keep the Django monolith, existing app boundaries, Django admin, paired bilingual fields, `ReviewableContent`, and server-rendered frontend. Do not add a SPA, headless CMS, Elasticsearch, Meilisearch or a general service layer now.

Target improvements:

- Add a small shared content foundation: publication state including scheduled/archived, timestamped state transitions, author/editor attribution, optional SEO metadata, topic/category/tag relations, and publish validation.
- Add a `pages`/content-block approach only for editable composed areas such as homepage hero/sections and About content; retain simple structured models for beliefs, pillars, mountains and timelines.
- Keep `Author` independent from `User`, but optionally link it to a user profile and add public author URLs. This supports both ministry contributors and authors without accounts.
- Use PostgreSQL full-text search (`SearchVector`, ranking and indexes) when PostgreSQL is the deployed database. It is sufficient before external search infrastructure.
- Use Django Groups/permissions for editorial authority, retaining a narrow number of roles: Super Admin, Editor, Author, optional Media Manager. Avoid creating a new role for every page.
- Store media outside the web process in production (object storage/CDN or a managed media host). Prefer YouTube embeds/IDs over uploaded videos for the initial phase.

## 19. Recommended Development Roadmap

### Phase 0 — Critical Fixes

**Objective:** Make the repository safe, reproducible and mobile-safe enough for staging.

- Commit the actual project source with a reviewed `.gitignore`; verify no secrets, DBs or user media enter history.
- Make production settings fail closed for secret key/config; document required environment variables and proxy settings.
- Fix public 320px navigation overflow and add viewport/browser regression tests.
- Validate internal `next` redirects; add upload rules; add request throttling/spam control; log mail failures.
- Add branded 400/403/404/500 templates and structured application logging.

**Dependencies:** None beyond source-control and deployment decisions.  
**Expected result:** Secure, reproducible staging baseline.

### Phase 1 — Core Content Platform

**Objective:** Turn the current content MVP into an editorial system for devotions, articles, pages and events.

- Extend review workflow with scheduled/archived states, transition validation and editorial history.
- Complete devotional model/detail/archive/filter experience; expand article taxonomy, reading time, rich safe content strategy and author pages.
- Add structured editable homepage/About records: hero, pillars, founder call timeline, beliefs and influence areas.
- Establish bilingual completeness/review policy and language-aware metadata strategy.
- Build public gatherings list/detail and prevent expired events from being promoted as upcoming.

**Dependencies:** Phase 0 security/config baseline.  
**Expected result:** Administrators can publish the core YTR resource platform without code edits.

### Phase 2 — Media Platform

**Objective:** Deliver reliable video and podcast resources without unnecessary self-hosting.

- Store/validate YouTube provider IDs and embed with privacy/performance-conscious lazy loading.
- Add series metadata, speaker/topics, publication dates, transcripts/descriptions and detail pages.
- Add audio playback/link strategy; validate uploads only where hosting files is required.
- Add responsive image variants and media management guidance.

**Dependencies:** Phase 1 taxonomy/content metadata.  
**Expected result:** Discoverable, mobile-friendly teaching media organized by series/topic.

### Phase 3 — Community

**Objective:** Safely support participation and moderated submissions.

- Build consent-aware public testimony publication workflow; retain strict private prayer request access and retention policy.
- Add submitted-question model and review/answer/publish/reject workflow rather than exposing FAQ submissions directly.
- Implement newsletter double opt-in, unsubscribe/preferences, consent record and delivery provider integration.
- Add event registration/recaps only after requirements for data collection are settled.

**Dependencies:** Phase 0 abuse/privacy controls and Phase 1 content lifecycle.  
**Expected result:** Community contributions are useful without exposing pastoral or personal data.

### Phase 4 — User Experience

**Objective:** Improve discovery only where it serves readers.

- Implement PostgreSQL full-text search across published public entities, ranked and filtered by type/topic/language.
- Add SEO/sitemap/schema/social-preview foundation and accessible menu/search interactions.
- Evolve accounts only for proven needs: saved devotionals/videos, language preference and notification preferences.
- Add analytics only with a privacy policy and minimal data collection.

**Dependencies:** PostgreSQL production database and stable public detail routes.  
**Expected result:** Strong content discoverability without premature infrastructure complexity.

### Phase 5 — Production Hardening

**Objective:** Operate the site reliably in production.

- Add Docker/Coolify deployment artifacts, migrations/collectstatic release process, health checks and backups/restore drills.
- Configure CDN/object storage/media backups, monitoring/error reporting and log retention.
- Add rate limits, CSP after testing, security headers, dependency update cadence and incident runbook.
- Add targeted integration/browser/accessibility tests for critical journeys.

**Dependencies:** Staging environment and approved hosting/media/email providers.  
**Expected result:** A maintainable and observable public ministry platform.

## 20. Top 20 Recommended Actions

1. `[P0]` Commit the complete Django project into Git, verify history contains no secret/DB/media files, and protect the primary branch.
2. `[P0]` Remove the production `SECRET_KEY` fallback and fail startup when it is unset, short or insecure.
3. `[P0]` Fix the shared public navigation so it has no horizontal overflow at 320px; add browser regression coverage.
4. `[P0]` Validate all `next` redirects with Django’s allowed-host checker.
5. `[P0]` Add upload extension/MIME/size validation and a production media-serving policy.
6. `[P1]` Add rate limiting and bot mitigation to registration, contact and newsletter endpoints.
7. `[P1]` Implement newsletter double opt-in, unsubscribe, preference and consent/audit fields before mailing subscribers.
8. `[P1]` Add production logging, mail-failure monitoring, branded 400/403/404/500 templates, and a health endpoint.
9. `[P1]` Complete devotional title/detail/author/topic/schedule/archive support.
10. `[P1]` Add categories/topics/tags, reading time, SEO metadata and safe rich-content blocks to articles.
11. `[P1]` Build editable homepage hero/sections and structured About/Pillars content in the existing Django admin.
12. `[P1]` Add event status, flyer, public list/detail, start/end validation and a true upcoming-vs-past archive.
13. `[P1]` Add reusable SEO metadata, canonical URLs, sitemap, robots.txt, Open Graph and basic schema.
14. `[P1]` Build consent-aware testimony and submitted-question moderation workflows.
15. `[P2]` Adopt Django groups/permissions for Super Admin, Editor, Author and optional Media Manager.
16. `[P2]` Add provider allowlists/IDs for YouTube and approved external resource URLs.
17. `[P2]` Implement accessible modal search and keyboard-operable video cards; audit meaningful image alt text.
18. `[P2]` Add pagination to growing content/admin lists and profile queries before data volume rises.
19. `[P2]` Move production to PostgreSQL and add PostgreSQL full-text search when the content catalog warrants it.
20. `[P3]` Add Docker/Coolify deployment documentation, backup/restore drills, monitoring and an operational runbook.
