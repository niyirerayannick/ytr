# Brand refresh completion report

## Logo

| Surface | Implementation |
|---|---|
| Main logo | `static/branding/ytr-logo.png`, complete official artwork |
| Navbar | Optimized 256px source, 64px desktop / 48px mobile |
| Dashboard | Full logo in expanded sidebar; YTR text in collapsed mode; member/author logos |
| Footer | Official logo alongside ministry identity on deep brown |
| Authentication | Official logo on login, signup, and password-reset screens |
| PWA | Complete logo, white padding, ordinary and maskable derivatives |
| Social cards | Official logo in header and contact footer |

## Final brand palette

| Role | HEX |
|---|---|
| Primary | #7c2d07 |
| Primary dark | #4a1a05 |
| Accent | #f4a029 |
| Secondary | #9ee1f8 |
| Surface | #fefefe |
| Text | #0d0d0d |
| Muted text | #625b57 |
| Border | #e6ddd7 |

Warm neutral surface is #f8f5f2; accessible warm emphasis is #995934. Existing semantic success/warning/error states are retained. Web color values live centrally in CSS; Tailwind references those variables. Pillow has shared semantic equivalents.

## Public site

Navbar, homepage hero, Devotions, Morning Devotion, Articles, Podcasts, Videos, authentication, footer, and offline fallback use the refreshed identity. Reading surfaces remain bright; the existing animated hero uses brown/orange. The original typography and application architecture are retained. Default social artwork uses the official identity; dedicated content artwork takes precedence.

## Dashboard

Deep-brown sidebar, official logo, orange active border, white neutral KPI/workspace cards, brown primary buttons. Sidebar collapse, mobile drawer, command palette, quick-create dropdown, and notification dropdown are exercised by the visual QA test with an authenticated admin session. No content publishing or external actions were triggered.

## PWA

Theme #7c2d07; background #fefefe. Existing 192px/512px icon routes and Apple touch route are preserved. Both maskable sizes have a padded official seal. Favicon includes 16px/32px/48px entries derived from the existing cross-and-dove artwork, with no new drawing. Shell/page cache versions are v2. Explicit localhost registration in tests exercises the worker while retaining production's development-host guard.

Physical installation and OS splash rendering were not tested on an actual phone. Browser tests verify manifest/icon delivery, registration, caching, install-promotion events, updates, and offline/private-page behavior.

## Share images

Devotional cards: EN and RW, Square and Story/Status; long RW input has a rendering regression test. The export dialog offers both image formats. Morning Devotion cover URLs support EN/RW and Square/Story; both languages and the new format are tested. Generated imagery uses full logos, brown headings, black text, orange rules, pale-blue detail, and existing SiteSettings contacts. Brand-versioned cache keys invalidate older artwork.

There were no Morning Devotion sessions in the local database. Public empty-state rendering was checked in-browser; representative cover samples used an unsaved session, and session behavior remains covered by Django tests. Live Meet/audio/video external services were not contacted.

## Responsive QA

| Width | Public site | Admin dashboard | Auth | Horizontal overflow |
|---:|---|---|---|---|
| 320 | Pass | Pass | Pass | 0px |
| 390 | Pass | Pass | Pass | 0px |
| 768 | Pass | Pass | Pass | 0px |
| 1024 | Pass | Pass | Pass | 0px |
| 1440 | Pass | Pass | Pass | 0px |

375px also passes. Nine public/auth pages and the authenticated administration dashboard were checked at each width. Screenshots were captured and representative mobile/desktop public, auth, dashboard, and generated-card layouts visually reviewed. Browser QA blocks remote Google Font requests for deterministic layout; the declared typography is unchanged. Evidence is in `test-results/brand-responsive.json` and `test-results/brand-*.png`.

## Tests

Before: 213 Django tests passed.
After: 215 Django tests passed; no failures or skips. Targeted Playwright suite: 16 passed, 0 failed, 0 skipped.

Required checks: Django system check passes; no migrations detected; pip check passes; CSS build passes; git diff check passes.

The initial post-change assertion for the old theme color was updated. Existing PWA tests required explicit localhost worker registration and a corrected logout-navigation wait. These test-only fixes are included.

`npm audit`: 5 high-severity transitive findings in braces/chokidar/micromatch/fast-glob/Tailwind. No dependency changes were made. The suggested force fix upgrades Tailwind to a breaking major version, which is outside the branding refresh. CSS build also reports an outdated Browserslist data warning.

## Documentation

`docs/brand-system.md` records the logo paths, exact palette, compatibility mapping, usage, contrast ratios, PWA assets, favicon derivation, configuration, and do/don't guidance. No database migration was added. Plain-text verification/reset email behavior is preserved; there was no existing HTML email system to rebrand.
