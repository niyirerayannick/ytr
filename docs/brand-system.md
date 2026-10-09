# YTR brand system

## Official logo

The supplied 1080px JPEG (`static/image/logo.jpeg`) is retained untouched as the source. Production uses `static/branding/ytr-logo.png` (1080px) and `ytr-logo-small.png` (256px). Both preserve all artwork, proportions, and the white field. The optimized small logo serves navigation, authentication, dashboard, footer, and offline screens. Public navigation renders at 64px desktop and 48px mobile. Explicit intrinsic dimensions prevent layout shift.

The expanded admin sidebar displays the full logo, ministry name, and Command Center label. Collapsed navigation uses a plain YTR text label rather than shrinking the complex artwork. Member and author sidebars also use the official logo. Existing Fraunces headings and Work Sans interface fonts remain.

## Color palette and semantic mapping

The authoritative web palette is in `static/css/input.css`; Tailwind colors reference its variables rather than duplicating HEX values. Pillow equivalents are centralized in `apps/core/card_rendering.py`.

| Role | Token | HEX |
|---|---|---|
| Primary | `--color-brand`, `--ytr-brown-700` | #7c2d07 |
| Primary dark | `--color-brand-dark`, `--ytr-brown-900` | #4a1a05 |
| Accessible warm emphasis | `--ytr-brown-500` | #995934 |
| Accent | `--color-accent`, `--ytr-orange-500` | #f4a029 |
| Accent surface | `--ytr-orange-100` | #fff3df |
| Secondary | `--color-secondary`, `--ytr-blue-400` | #9ee1f8 |
| Information surface | `--ytr-blue-100` | #e8f8fd |
| Surface | `--color-bg`, `--ytr-white` | #fefefe |
| Muted surface | `--color-bg-muted` | #f8f5f2 |
| Text | `--color-text`, `--ytr-black` | #0d0d0d |
| Muted text | `--color-text-muted` | #625b57 |
| Border | `--color-border` | #e6ddd7 |
| Error | `--color-error` | #b42318 |

Compatibility mapping keeps existing templates stable: Night = deep brown; Night 2 = primary brown; Dawn = flame orange; Paper = white; Paper 2 = warm white; Ink = near black. Ember historically served small text and white-text buttons, so its compatibility alias uses accessible warm brown (#995934), not light orange. New fire/live states explicitly use `--color-accent`. Ember Dim = primary dark. River retains semantic success teal (#1e6e71). Existing warning, success, and rejected/error states retain status meanings. Generated-card legacy exports remain for callers; current layouts use semantic color constants.

## Usage

- Primary actions use brown with white text; hover darkens to deep brown. Outline actions retain brown borders. Keyboard focus uses brown on light surfaces and orange in dark sections.
- The public header is white; the homepage keeps its animated landscape hero with brown/orange colors. Articles, resources, and white reading cards inherit the shared tokens. The footer anchors the platform in deep brown.
- Devotional reading cards are white with brown Scripture headings, black copy, and subtle orange detail. Scripture callouts use a sky-blue background.
- Morning Devotion uses deep brown cards and detail panels, orange LIVE and playing states, and dark text on orange Join Live actions. Read/listen/watch/share behavior remains unchanged.
- Dashboard cards stay neutral. Orange accents identify selected navigation, with brown primary actions and a deep-brown sidebar. Existing mobile drawer, collapse, palette, quick-create and notification controls are retained.
- Login/register and password-reset/request/completion screens use the official logo and shared buttons. Verification continues its existing redirect/message flow into branded screens.
- Devotion share cards and Morning Devotion covers use white-to-warm-to-blue backgrounds, brown headings, black copy, orange footer rules, full official logos, and configured contact details. Both support square (1080x1080) and story (1080x1920). Devotion export offers a Square / Story selector. Morning cover URLs accept `?lang=en|rw&format=square|story`, defaulting to English square. Cache keys include branding version and language.
- Default Open Graph artwork is `static/branding/social-default.png`. Dedicated devotional/Morning artwork and article cover images take precedence.
- Existing verification/reset emails are plain text. Their fallback content and sending behavior are retained; no HTML email system was introduced.

## Accessibility

Measured WCAG contrast ratios:

| Foreground / background | Ratio | Usage |
|---|---:|---|
| Primary brown / white | 9.31:1 | Primary actions and headings |
| Deep brown / white | 14.45:1 | Dark surfaces |
| Warm emphasis brown / white | 5.43:1 | Small emphasis text |
| Muted text / white | 6.60:1 | Supporting copy |
| Near black / orange | 9.17:1 | Live actions |
| White / orange | 2.10:1 | Do not use for normal text |
| Near black / pale blue | 17.84:1 | Information surfaces |

Light blue and orange are accents, not body text on white. Small sidebar section labels use translucent white at 75% rather than the former low-opacity labels. Error text retains red. Logo images next to visible ministry names have empty alt text; standalone authentication images use Youth Time Revival. The header link provides its own accessible name.

## PWA assets

Existing manifest/icon URLs remain stable:

- `static/icons/ytr-192.png` and `ytr-512.png`: official full logo fitted into a white square at 92% width.
- `static/icons/ytr-maskable-192.png` and `ytr-maskable-512.png`: artwork fitted to 70% width, entirely inside the centered 80%-diameter safe circle.
- Apple touch uses `icons/ytr-192.png`.
- `static/branding/favicon.ico`: 16, 32, and 48px entries. The complete detailed seal becomes illegible at tiny tab sizes, so favicon artwork extracts the existing cross and dove from source coordinates (480,48)-(601,230), with white padding. `ytr-favicon-mark.png` records that derivative. No replacement symbol is drawn.
- Theme color: #7c2d07. Background: #fefefe.
- Shell and public-page caches use v2 to invalidate old identity. The small official logo is included in the offline shell.

Install promotion, iOS instructions, update handling, and offline caching remain covered by the existing Playwright suite. Automated tests exercise install events; actual OS installation/splash appearance requires a physical device check.

## Configuration

Contact email, phone, website URL, and social links reuse the existing SiteSettings singleton. The official logo and ministry name are deployment branding assets; no duplicate database fields or migration were added.

## Do / don't

Do preserve aspect ratio, leave breathing room, retain the white logo field, and use the full logo on institutional surfaces. Use controlled orange and blue highlights around neutral content.

Do not recolor or distort artwork, remove meaningful elements from the full seal, place it on a noisy field, spin it as a loading indicator, flood the interface with orange, or invent new ministry marks. The favicon extraction is limited to the existing cross and dove for tiny tab sizes.

## Legacy color audit

Legacy purple UI tokens, neutral shadows/overlays, the hero illustration, anonymous author tiles, and decorative flame accents were classified as brand styling and migrated. CSS mask black/white values are functional masks and remain. Success teal, error red, and warning amber retain their semantic roles. Model color fields, existing content records, demonstration seed artwork, and historical migrations are authored content colors/schema history, so they remain unchanged. Default UI icon tiles now reference the shared brand-dark variable. No database-wide recoloring or migrations were performed.

The spiritual homepage hero also uses `static/branding/ytr-logo-hero.webp`, a 512px, approximately 60KB optimized derivative of the complete official seal. It retains the full white field and original artwork. The decorative watermark is upper-centered, behind the readability overlay, with opacity-only motion and a static reduced-motion state. Mobile reuses the existing small logo through srcset.
