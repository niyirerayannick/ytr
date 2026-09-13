"""Server-side rendering of branded, shareable devotional images.

Why server-side (not a client-side <canvas> export, which is what the old
"Download to repost" button used): the same PNG needs to double as the
og:image for link previews, and social-media crawlers never execute JS, so
the canonical version of this image has to exist as a real URL a crawler can
fetch. Rendering it once in Python with Pillow (already a dependency, used
for uploads) also gives predictable typography across every visitor's device
instead of depending on whatever fonts/canvas quirks their browser has.

Output is deterministic and cached (see `cache_key`) — the same devotion,
language, format, and SiteSettings content always produce byte-identical
output, so a CDN/browser can cache it and we don't re-render on every hit.

The generic Pillow plumbing (fonts, word-wrap, gradient, contact footer) lives
in `apps.core.card_rendering` and is shared with the Morning Devotion cover
renderer (`apps.morning_devotions.cover`); this module only holds the layout
that's specific to a devotion share card.
"""
import hashlib
import io

from PIL import Image, ImageDraw

from apps.core.card_rendering import (  # noqa: F401 — re-exported for callers/tests
    DAWN,
    EMBER_DIM,
    FORMATS,
    ITALIC_FONT,
    LANGUAGES,
    NIGHT,
    NIGHT_2,
    PAPER,
    REGULAR_FONT,
    SQUARE,
    fit_lines,
    footer_lines,
    font as _font,
    paste_logo,
    vertical_gradient,
)


class UnsupportedShareRequest(ValueError):
    """Raised for a validated-but-unrenderable combination (e.g. missing translation)."""


_COPY = {
    "en": {
        "kicker": "TODAY'S DEVOTION",
        "cta": "Read today's devotion on Youth Time Revival",
        "brand": "YOUTH TIME REVIVAL",
    },
    "rw": {
        "kicker": "IGITEKEREZO CY'UYU MUNSI",
        "cta": "Soma iyubahiro ry'uyu munsi kuri Youth Time Revival",
        "brand": "YOUTH TIME REVIVAL",
    },
}


def render_devotion_card(devotion, language, site_settings, fmt=SQUARE):
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language!r}")
    if fmt not in FORMATS:
        raise ValueError(f"Unsupported format: {fmt!r}")
    if not devotion.has_language(language):
        raise UnsupportedShareRequest(f"No {language} content for this devotion")

    size = FORMATS[fmt]
    width, height = size
    margin = 84

    img = vertical_gradient(size, [NIGHT, NIGHT_2, EMBER_DIM]).convert("RGBA")

    copy = _COPY[language]

    logo_size = 88
    paste_logo(img, margin, top=76, logo_size=logo_size)

    # Everything else is drawn on a transparent overlay and alpha-composited
    # at the end: Pillow's ImageDraw overwrites pixels rather than blending,
    # so a translucent fill drawn straight onto `img` would come out as a
    # literal semi-transparent hole once flattened to RGB, not a softened
    # color over the gradient.
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = _font(REGULAR_FONT, 28, weight=700)
    kicker_font = _font(REGULAR_FONT, 20, weight=600)
    text_x = margin + logo_size + 24
    draw.text((text_x, 88), copy["brand"], font=brand_font, fill=(*DAWN, 255))
    draw.text((text_x, 126), copy["kicker"], font=kicker_font, fill=(255, 255, 255, 178))

    content_width = width - 2 * margin
    header_bottom = 200
    footer_top = height - 168

    title_font, title_lines = fit_lines(
        draw, devotion.verse_ref, REGULAR_FONT, 64, content_width, max_lines=2, weight=700, min_size=40,
    )
    title_line_height = title_font.size + 12

    excerpt = devotion.share_excerpt(language, max_words=45)
    quote_font, quote_lines = fit_lines(
        draw, f"“{excerpt}”", ITALIC_FONT, 38, content_width, max_lines=6, min_size=28,
    )
    quote_line_height = quote_font.size + 16

    block_height = (
        title_line_height * len(title_lines) + 28
        + quote_line_height * len(quote_lines)
    )
    available = footer_top - header_bottom
    y = header_bottom + max(0, (available - block_height) // 2)

    for line in title_lines:
        draw.text((margin, y), line, font=title_font, fill=(*PAPER, 255))
        y += title_line_height
    y += 28

    for line in quote_lines:
        draw.text((margin, y), line, font=quote_font, fill=(251, 247, 240, 235))
        y += quote_line_height

    # ---- footer ----
    draw.line([(margin, footer_top), (width - margin, footer_top)], fill=(255, 255, 255, 46), width=1)

    cta_font = _font(REGULAR_FONT, 24, weight=600)
    draw.text((margin, footer_top + 22), copy["cta"], font=cta_font, fill=(*DAWN, 255))

    contact_font = _font(REGULAR_FONT, 22)
    contact_y = footer_top + 66
    for line in footer_lines(site_settings):
        draw.text((margin, contact_y), line, font=contact_font, fill=(255, 255, 255, 191))
        contact_y += 30

    flattened = Image.alpha_composite(img, overlay).convert("RGB")
    buffer = io.BytesIO()
    flattened.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def cache_key(devotion, language, fmt, site_settings):
    raw = "|".join([
        "devotion-share-card",
        str(devotion.pk),
        language,
        fmt,
        devotion.updated_at.isoformat(),
        site_settings.updated_at.isoformat(),
    ])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"devotion-share-card:{digest}"
