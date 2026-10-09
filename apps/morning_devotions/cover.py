"""Branded Morning Devotion cover art — same Pillow foundation as the
devotion share cards (`apps.core.card_rendering`), so editors never need to
design a new image for each morning's session (spec section 11).
"""
import hashlib
import io

from PIL import Image, ImageDraw

from apps.core.card_rendering import (
    BRAND, TEXT, MUTED_TEXT, ACCENT, CARD_BACKGROUND,
    DAWN,
    EMBER_DIM,
    FORMATS,
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


def render_session_cover(session, site_settings, fmt=SQUARE, language="en"):
    if fmt not in FORMATS:
        raise ValueError(f"Unsupported format: {fmt!r}")

    if language not in LANGUAGES:
        raise ValueError("Unsupported language")

    size = FORMATS[fmt]
    width, height = size
    margin = 84

    img = vertical_gradient(size, CARD_BACKGROUND).convert("RGBA")

    logo_size = 112
    paste_logo(img, margin, top=76, logo_size=logo_size)

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = _font(REGULAR_FONT, 24, weight=700)
    kicker_font = _font(REGULAR_FONT, 20, weight=600)
    text_x = margin + logo_size + 24
    draw.text((text_x, 92), "YOUTH TIME REVIVAL", font=brand_font, fill=(*BRAND, 255))
    draw.text((text_x, 128), ("MORNING DEVOTION" if language == "en" else "IGITEKEREZO CYA MU GITONDO"), font=kicker_font, fill=(*MUTED_TEXT, 255))

    content_width = width - 2 * margin
    header_bottom = 210
    footer_top = height - 130

    title_font, title_lines = fit_lines(
        draw, getattr(session, f"title_{language}"), REGULAR_FONT, 60, content_width, max_lines=3, weight=700, min_size=36,
    )
    title_line_height = title_font.size + 12

    scripture_font = _font(REGULAR_FONT, 32, weight=600)
    date_font = _font(REGULAR_FONT, 24)

    block_height = title_line_height * len(title_lines)
    if session.scripture_reference:
        block_height += 20 + scripture_font.size
    block_height += 30 + date_font.size

    available = footer_top - header_bottom
    y = header_bottom + max(0, (available - block_height) // 2)

    for line in title_lines:
        draw.text((margin, y), line, font=title_font, fill=(*BRAND, 255))
        y += title_line_height

    if session.scripture_reference:
        y += 20
        draw.text((margin, y), session.scripture_reference, font=scripture_font, fill=(*BRAND, 255))
        y += scripture_font.size

    y += 30
    # strftime's non-padded-day flag differs by platform (%-d on Linux/macOS,
    # %#d on Windows); building the string manually is portable across both,
    # which matters since this renders in a Linux container in prod but is
    # also exercised locally (dev, tests) on Windows.
    session_date = f"{session.start_datetime:%B} {session.start_datetime.day}, {session.start_datetime:%Y}"
    draw.text((margin, y), session_date, font=date_font, fill=(*MUTED_TEXT, 255))

    draw.line([(margin, footer_top), (width - margin, footer_top)], fill=(*ACCENT, 255), width=1)
    contact_font = _font(REGULAR_FONT, 22)
    contact_y = footer_top + 22
    for line in footer_lines(site_settings):
        fitted_font, fitted_lines = fit_lines(draw, line, REGULAR_FONT, 22, content_width - 132, max_lines=1, min_size=14)
        draw.text((margin, contact_y), fitted_lines[0], font=fitted_font, fill=(*MUTED_TEXT, 255))
        contact_y += 30

    flattened = Image.alpha_composite(img, overlay).convert("RGB")
    paste_logo(flattened, width - margin - 104, top=footer_top + 20, logo_size=104)
    buffer = io.BytesIO()
    flattened.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def cache_key(session, fmt, site_settings, language="en"):
    raw = "|".join([
        "morning-devotion-cover-brand-v2",
        str(session.pk),
        fmt,
        language,
        session.updated_at.isoformat(),
        site_settings.updated_at.isoformat(),
    ])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"morning-devotion-cover:{digest}"
