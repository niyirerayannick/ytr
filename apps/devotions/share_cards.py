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
"""
import hashlib
import io
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

SQUARE = "square"
FORMATS = {
    SQUARE: (1080, 1080),
}
LANGUAGES = ("en", "rw")

_FONT_DIR = Path(settings.BASE_DIR) / "static" / "fonts"
_REGULAR_FONT = _FONT_DIR / "WorkSans-Variable.ttf"
_ITALIC_FONT = _FONT_DIR / "WorkSans-Italic-Variable.ttf"

_NIGHT = (26, 18, 48)
_NIGHT_2 = (36, 26, 61)
_EMBER_DIM = (194, 74, 36)
_DAWN = (246, 185, 59)
_PAPER = (251, 247, 240)


class UnsupportedShareRequest(ValueError):
    """Raised for a validated-but-unrenderable combination (e.g. missing translation)."""


def _font(path, size, weight=None):
    font = ImageFont.truetype(str(path), size)
    if weight is not None:
        font.set_variation_by_axes([weight])
    return font


def _wrap_lines(draw, text, font, max_width):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _fit_lines(draw, text, font_path, start_size, max_width, max_lines, weight=None, min_size=32):
    """Word-wrap `text`, shrinking the font within [min_size, start_size] until
    it fits in `max_lines`; if it still doesn't fit at the floor size, the last
    line is truncated with an ellipsis rather than shrinking further."""
    size = start_size
    while size >= min_size:
        font = _font(font_path, size, weight=weight)
        lines = _wrap_lines(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 4
    font = _font(font_path, min_size, weight=weight)
    lines = _wrap_lines(draw, text, font, max_width)[:max_lines]
    if lines:
        last = lines[-1]
        while last and draw.textlength(last + "…", font=font) > max_width:
            last = last[:-1].rstrip()
        lines[-1] = last + "…"
    return font, lines


def _vertical_gradient(size, stops):
    width, height = size
    base = Image.new("RGB", (1, height))
    n = len(stops) - 1
    for y in range(height):
        t = y / max(height - 1, 1)
        seg = min(int(t * n), n - 1)
        seg_t = (t * n) - seg
        c0, c1 = stops[seg], stops[seg + 1]
        color = tuple(int(c0[i] + (c1[i] - c0[i]) * seg_t) for i in range(3))
        base.putpixel((0, y), color)
    return base.resize((width, height))


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


def footer_lines(site_settings):
    """Contact lines to print at the bottom — only fields that are actually
    configured; never a placeholder for a missing one (see docs/devotional-sharing.md)."""
    lines = []
    if site_settings.website_url:
        website = site_settings.website_url
        for prefix in ("https://", "http://"):
            if website.startswith(prefix):
                website = website[len(prefix):]
        lines.append(website.rstrip("/"))
    if site_settings.contact_email:
        lines.append(site_settings.contact_email)
    if site_settings.phone:
        lines.append(site_settings.phone)
    return lines


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

    img = _vertical_gradient(size, [_NIGHT, _NIGHT_2, _EMBER_DIM]).convert("RGBA")

    copy = _COPY[language]

    # Brand mark: the app icon already ships as a night-colored square tile
    # with the flame mark on it, so it drops in as a self-contained badge.
    # Pasted directly onto the opaque base (not the translucent overlay
    # below) since Image.paste(..., mask) alpha-blends correctly on its own.
    logo_path = Path(settings.BASE_DIR) / "static" / "icons" / "ytr-192.png"
    logo_size = 88
    try:
        logo = Image.open(logo_path).convert("RGBA").resize((logo_size, logo_size))
        img.paste(logo, (margin, 76), logo)
    except FileNotFoundError:
        pass

    # Everything else is drawn on a transparent overlay and alpha-composited
    # at the end: Pillow's ImageDraw overwrites pixels rather than blending,
    # so a translucent fill drawn straight onto `img` would come out as a
    # literal semi-transparent hole once flattened to RGB, not a softened
    # color over the gradient.
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = _font(_REGULAR_FONT, 28, weight=700)
    kicker_font = _font(_REGULAR_FONT, 20, weight=600)
    text_x = margin + logo_size + 24
    draw.text((text_x, 88), copy["brand"], font=brand_font, fill=(*_DAWN, 255))
    draw.text((text_x, 126), copy["kicker"], font=kicker_font, fill=(255, 255, 255, 178))

    content_width = width - 2 * margin
    header_bottom = 200
    footer_top = height - 168

    title_font, title_lines = _fit_lines(
        draw, devotion.verse_ref, _REGULAR_FONT, 64, content_width, max_lines=2, weight=700, min_size=40,
    )
    title_line_height = title_font.size + 12

    excerpt = devotion.share_excerpt(language, max_words=45)
    quote_font, quote_lines = _fit_lines(
        draw, f"“{excerpt}”", _ITALIC_FONT, 38, content_width, max_lines=6, min_size=28,
    )
    quote_line_height = quote_font.size + 16

    block_height = (
        title_line_height * len(title_lines) + 28
        + quote_line_height * len(quote_lines)
    )
    available = footer_top - header_bottom
    y = header_bottom + max(0, (available - block_height) // 2)

    for line in title_lines:
        draw.text((margin, y), line, font=title_font, fill=(*_PAPER, 255))
        y += title_line_height
    y += 28

    for line in quote_lines:
        draw.text((margin, y), line, font=quote_font, fill=(251, 247, 240, 235))
        y += quote_line_height

    # ---- footer ----
    draw.line([(margin, footer_top), (width - margin, footer_top)], fill=(255, 255, 255, 46), width=1)

    cta_font = _font(_REGULAR_FONT, 24, weight=600)
    draw.text((margin, footer_top + 22), copy["cta"], font=cta_font, fill=(*_DAWN, 255))

    contact_font = _font(_REGULAR_FONT, 22)
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
