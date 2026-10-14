# YTR animated hero logo

## Asset preparation
- White background removed: the generated SVG contains only traced artwork paths, with no white background rectangle or embedded raster.
- Transparent format: `static/branding/ytr-logo-layered.svg`. The original PNG remains intact.
- Structure: twelve color/semantic groups traced from the official 1080px logo, plus a separate SVG light overlay. This is a faithful color-reduced trace, not the original editable vector master. At overlapping silhouettes, geographic regions are used to separate map and people; these are not fully reconstructed independent drawings.
- A circular warm hero halo behind the transparent artwork preserves the readability of the official black silhouettes; there is no rectangular white field.

## Animation elements
- Cross: slow gold radiance with a restrained central light accent.
- Bible: soft illumination from the open pages.
- Fire / ash: orange and yellow flame shimmer, five descending sparks and two rising ash points.
- Globe: blue line shimmer and slowly travelling mission arcs.
- Africa: subtle edge glow; its original outline is preserved.
- People: coordinated 1.5px breathing motion, with clothing detail moving together.
- Roots: gentle glow and travelling light along three root accents.
- Dove: 3px float with warm radiance, without wing flapping.

## Hero integration
- Desktop: reserved right visual column; text and calls to action retain their own space.
- Through 900px: artwork moves below the content, centered at 230?360px. No symbols are removed. Only three particles remain on mobile, and mission arcs stop moving.
- Reduced motion: all hero animations and transitions stop, with static light and visible sparks.
- Accessibility: both decorative SVGs are hidden by an aria-hidden wrapper and are non-focusable. The bilingual heading and existing devotion CTA behavior remain intact.

## Technical
- Reusable partials: hero_logo_art.html, hero_logo_light.html, hero_spiritual_background.html and hero.html.
- CSS owns all animation. Existing hero-spiritual.js pauses motion offscreen and in hidden tabs. No animation library, GIF, video, canvas or additional runtime JavaScript is required.
- Inline SVG is approximately 116KB uncompressed; normal HTTP compression can reduce repeated path markup. Seven fixed particles avoid runtime spawning. Small SVG filters provide restrained glow.
- Fallback: artwork is already present in the HTML and remains a complete static composition if JavaScript is unavailable or animations are unsupported. The standalone SVG is also usable without the hero styles.
- Rebuild artwork: `venv/Scripts/python.exe scripts/prepare-hero-logo.py` (build-only Pillow, numpy and opencv-python-headless). Then run `npm run build:css`.

## QA
The Playwright hero suite covers 320, 375, 390, 768, 1024 and 1440px, normal/reduced motion and live/upcoming/no-session CTA states. It checks symbol paths, layout separation, aspect ratio, horizontal overflow, keyboard focus, animation pause and console/page errors. Screenshot artifacts are in test-results. Physical device performance is not benchmarked.

Verified result: all 12 Chromium hero tests passed across the six widths and both motion preferences, including all three CTA states. No horizontal overflow or console/page errors. Desktop (1024/1440) and mobile (320) screenshots visually reviewed. Django system check, CSS build and git diff whitespace check passed. CSS build reports the existing outdated Browserslist database notice.

## Increased animation pass
Flames now move independently with staggered 4?7 second cycles, stretching gently and swaying at their tips. The cross has stronger slow radiance; the dove floats 7px. The Bible releases moving light streams and a breathing bloom; two expanding mission waves pass across Africa toward the globe. Torch halos respond in a staggered sequence, sparks fall more visibly, and brighter light travels down the roots. Mobile retains independent flames and one expanding wave, with fewer overlay effects. Reduced motion disables all new animation; offscreen pausing applies to the new layers as well.
