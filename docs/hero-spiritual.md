# Spiritual homepage hero

## Hero

- **Main light:** warm-white radial light above the right/central hero area, surrounded by the shared deep-brown and warm-brand palette. A gentle 18-second breathing cycle lifts the scene toward light.
- **Light rays:** blurred, naturally fading rays drift over a 24-second cycle. A dedicated readability overlay protects content above them.
- **Cross:** intersecting low-opacity light contours, slowly breathing over 21 seconds; no black cross or flashing.
- **Dove:** a single faint outline floats by 8px over 22 seconds. It is a background motif, not a modification of the official logo.
- **Revival particles:** eight fixed, tiny orange/white points rise slowly over 19-26 seconds. No random spawning, emoji, or literal fire animation.
- **Globe motif:** three curved globe contours in sky blue drift gently over 25 seconds.
- **Word and roots:** faint open-book contours below the light and restrained organic root lines near the bottom, both static.
- **Text animation:** ministry label, approved heading, supporting copy, and CTAs gently rise 8px over about 1.3 seconds total. They start at 85% opacity and remain interactive immediately. Existing EN/RW ministry copy is preserved.
- **Morning Devotion CTA:** live/starting-soon sessions with a configured meeting URL offer Join Morning Devotion; live sessions without a meeting offer their actual session page. Upcoming published sessions show their date/time and View Morning Devotion. No upcoming session falls back to the existing Our story action. Draft sessions never appear publicly. Today's Devotion remains the primary action.

Existing rotating topic pills are retained as static ministry themes, avoiding a second attention-demanding animation. The old random JavaScript ember generator and its unused CSS were removed.

## Implementation and performance

Reusable partials:

- `templates/home/partials/hero.html`
- `templates/home/partials/hero_spiritual_background.html`

Centralized styles: the spiritual-hero block in `static/css/input.css` (6,153 source bytes). Background SVG/HTML is 2,357 bytes. Added JS is 576 bytes in `static/js/hero-spiritual.js`, loaded only by the homepage.

No external animation libraries, canvas, video, remote artwork, continuous JavaScript timers, or requestAnimationFrame loops were introduced. Transform/opacity animate the layers; blur is static and limited to the rays and cross. IntersectionObserver and page visibility pause animations when offscreen or hidden.

Mobile hides dove/book/roots, stops globe drift, reduces ray blur, and displays only three particles. The light and cross remain. Tablet has a stronger readability overlay. At reduced motion every hero animation/transition is disabled, text is immediately visible, and the light/motifs/particles form a deliberate static composition.

Layering: background 0; globe 1; source/rays 2; motifs 3; particles 4; readability overlay 5; content 10. The hero/background clip their own decoration; there is no new document-level overflow hiding. Decorative layers have pointer-events disabled.

No hero video existed in the current template, so no ministry footage was removed. Physical Android frame-rate/CPU measurements were not taken; performance observations describe implementation properties rather than device benchmarks.

## Responsive QA

| Width | Visual | Readability | Animation / reduced motion | Overflow |
|---:|---|---|---|---|
| 320 | Reviewed | Pass | Pass | 0px |
| 390 | Reviewed | Pass | Pass | 0px |
| 768 | Reviewed | Pass | Pass | 0px |
| 1024 | Reviewed | Pass | Pass | 0px |
| 1440 | Reviewed | Pass | Pass | 0px |

375px is also covered. Playwright captures initial and mid-animation states, live/upcoming/no-session variants, and reduced-motion variants. Deterministic mid-animation screenshots seek the CSS animation timeline rather than waiting ten seconds per image. Images are stored as `test-results/hero-*.png`.

The fixture renderer (`scripts/render-hero-qa.py`) renders real Django homepage templates with unsaved sessions and a mocked session selector; it does not mutate ministry content or create fake meetings in the database. Fonts served remotely by Google are omitted from QA fixture HTML to avoid network-dependent screenshots; declared production font families remain unchanged.

## Accessibility

The complete decoration wrapper is aria-hidden; each decorative SVG is non-focusable. Heading/copy/buttons remain real HTML. Keyboard focus is verified and remains visibly orange against dark surfaces. There are no flashes or abrupt brightness changes.

White copy sits over the brown readability overlay, with the brightest light placed away from the main text. Primary white-on-brown CTA contrast is 9.31:1; live near-black-on-orange contrast is 9.17:1. Contrast over the changing background is protected by the overlay and visually reviewed; the reported numerical ratios apply to the solid CTA color pairs.

Reduced-motion tests assert there are no active hero animations. Offscreen-pause tests assert the paused class is applied. The existing approved bilingual text remains unchanged.

## Browser and technical checks

- Chromium hero suite: 12 tests covering six widths and both motion preferences.
- Zero console errors/page exceptions in the hero suite.
- Live/upcoming/no-session CTA behavior and keyboard focus verified.
- Full Django suite: 219 passing tests, including live-without-meeting and draft-session hero regressions.
- Django system check, CSS build, and git diff whitespace check pass.
- CSS build retains the existing outdated Browserslist database notice.

Actual Meet connectivity, physical device installation, and physical Android animation benchmarks were not exercised.

## Official logo watermark addition

The complete official YTR logo is now part of the background composition, upper-centered toward the light source (68% horizontal placement keeps it away from the main text). It is 280-440px on desktop and 200px on mobile. Responsive image selection uses the existing 256px asset and a 512px WebP derivative (`static/branding/ytr-logo-hero.webp`) of the complete official logo, avoiding a full-resolution PNG download for the hero.

The artwork retains its original proportions, colors, white field, and all symbolic details. Only opacity breathes gently between 13% and 19% over 22 seconds; its position and proportions remain fixed. The existing readability overlay sits above it and below content. Reduced motion freezes the watermark at 16% opacity; the existing offscreen/tab-visibility pause also covers it. Its empty alt text and aria-hidden decorative wrapper prevent duplicate screen-reader announcements. No additional JS or animation library was added.

The background's cross, dove, embers, globe, book, and root motifs remain subtle references to the official artwork. Browser QA additionally checks successful logo loading and an undistorted aspect ratio at every tested width and motion preference.
