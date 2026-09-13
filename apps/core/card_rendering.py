"""Shared Pillow building blocks for branded, generated PNG cards.

Extracted from the devotion share-card renderer (`apps/devotions/share_cards.py`)
so a second card type (Morning Devotion cover art) doesn't reimplement font
loading, word-wrapping, gradients, and the SiteSettings contact-footer logic.
Keep genuinely card-specific layout (what text goes where) in each app's own
module; only the mechanical Pillow plumbing lives here.
"""
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

SQUARE = "square"
FORMATS = {
    SQUARE: (1080, 1080),
}
LANGUAGES = ("en", "rw")

FONT_DIR = Path(settings.BASE_DIR) / "static" / "fonts"
REGULAR_FONT = FONT_DIR / "WorkSans-Variable.ttf"
ITALIC_FONT = FONT_DIR / "WorkSans-Italic-Variable.ttf"

NIGHT = (26, 18, 48)
NIGHT_2 = (36, 26, 61)
EMBER_DIM = (194, 74, 36)
DAWN = (246, 185, 59)
PAPER = (251, 247, 240)


def font(path, size, weight=None):
    loaded = ImageFont.truetype(str(path), size)
    if weight is not None:
        loaded.set_variation_by_axes([weight])
    return loaded


def wrap_lines(draw, text, text_font, max_width):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=text_font) <= max_width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def fit_lines(draw, text, font_path, start_size, max_width, max_lines, weight=None, min_size=32):
    """Word-wrap `text`, shrinking the font within [min_size, start_size] until
    it fits in `max_lines`; if it still doesn't fit at the floor size, the last
    line is truncated with an ellipsis rather than shrinking further."""
    size = start_size
    while size >= min_size:
        candidate_font = font(font_path, size, weight=weight)
        lines = wrap_lines(draw, text, candidate_font, max_width)
        if len(lines) <= max_lines:
            return candidate_font, lines
        size -= 4
    floor_font = font(font_path, min_size, weight=weight)
    lines = wrap_lines(draw, text, floor_font, max_width)[:max_lines]
    if lines:
        last = lines[-1]
        while last and draw.textlength(last + "…", font=floor_font) > max_width:
            last = last[:-1].rstrip()
        lines[-1] = last + "…"
    return floor_font, lines


def vertical_gradient(size, stops):
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


def paste_logo(img, margin, top=76, logo_size=88):
    """Paste the app icon (already a night-colored tile with the flame mark)
    as the brand badge in the top-left. Silently skipped if missing."""
    logo_path = Path(settings.BASE_DIR) / "static" / "icons" / "ytr-192.png"
    try:
        logo = Image.open(logo_path).convert("RGBA").resize((logo_size, logo_size))
        img.paste(logo, (margin, top), logo)
    except FileNotFoundError:
        pass


def footer_lines(site_settings):
    """Contact lines to print at the bottom of a card — only fields that are
    actually configured; never a placeholder for a missing one."""
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
