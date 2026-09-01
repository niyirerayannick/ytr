"""Inline SVG icon library shared across the site (ports the prototype's ICONS map)."""

ICON_CHOICES = [
    ("flame", "Flame"),
    ("river", "River"),
    ("mountain", "Mountain"),
    ("book", "Book"),
    ("mic", "Microphone"),
    ("gavel", "Gavel"),
    ("mask", "Mask"),
    ("cap", "Graduation cap"),
    ("heart", "Heart"),
    ("coin", "Coin"),
    ("shield", "Shield"),
    ("wave", "Wave"),
    ("pin", "Pin"),
    ("play", "Play"),
    ("chevdown", "Chevron down"),
]

ICONS = {
    "flame": '<path d="M12 2c1 3-2 4-2 7a4 4 0 1 0 8 0c0-1.5-1-2-1.5-3 1.5 1 3 3 3 6a6.5 6.5 0 1 1-13 0c0-4.5 3.5-6 5.5-10z" fill="currentColor"/>',
    "river": '<path d="M2 9c2 0 2 2 4 2s2-2 4-2 2 2 4 2 2-2 4-2 2 2 4 2"/><path d="M2 15c2 0 2 2 4 2s2-2 4-2 2 2 4 2 2-2 4-2 2 2 4 2"/>',
    "mountain": '<path d="M2 19 9 6l4 6 2-3 7 10z"/>',
    "book": '<path d="M4 5.5C4 4.7 4.7 4 5.5 4H12v16H5.5A1.5 1.5 0 0 1 4 18.5z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H12v16h6.5a1.5 1.5 0 0 0 1.5-1.5z"/>',
    "mic": '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
    "gavel": '<path d="m14 4 6 6M6.5 11.5l6 6M3 21l7-7M12.5 5.5l6 6-3 3-6-6z"/>',
    "mask": '<path d="M4 5c4 3 12 3 16 0-1 8-4 14-8 14S5 13 4 5Z"/><circle cx="9" cy="9" r=".8" fill="currentColor" stroke="none"/><circle cx="15" cy="9" r=".8" fill="currentColor" stroke="none"/>',
    "cap": '<path d="M12 4 2 9l10 5 10-5z"/><path d="M6 11.5V17c0 1 3 2.5 6 2.5s6-1.5 6-2.5v-5.5"/>',
    "heart": '<path d="M12 20s-7-4.4-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 5c-2.5 4.6-9.5 9-9.5 9Z"/><path d="M6 12h3l1.5-3L13 15l1.5-3H18"/>',
    "coin": '<ellipse cx="12" cy="7" rx="8" ry="3.5"/><path d="M4 7v10c0 1.9 3.6 3.5 8 3.5s8-1.6 8-3.5V7"/><path d="M4 12c0 1.9 3.6 3.5 8 3.5s8-1.6 8-3.5"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>',
    "wave": '<path d="M2 8h4l3-4 4 12 3-8h6"/>',
    "pin": '<path d="M12 22s7-6.4 7-12a7 7 0 1 0-14 0c0 5.6 7 12 7 12Z"/><circle cx="12" cy="10" r="2.5"/>',
    "play": '<path d="M8 5v14l11-7z" fill="currentColor"/>',
    "chevdown": '<path d="m6 9 6 6 6-6"/>',
}


def icon_svg(name, size=24, stroke=True):
    body = ICONS.get(name, ICONS["flame"])
    stroke_attrs = 'stroke="currentColor" stroke-width="1.6"' if stroke and name != "play" else ""
    fill = "none" if stroke else "currentColor"
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="{fill}" {stroke_attrs}>{body}</svg>'
    )


def icon_tile_svg(name, bg="#241A3D", size="100%"):
    """Reproduces the prototype's iconWrap(): a colored square tile with a centered icon.

    Positioned absolute+inset-0 so it fills a non-square `position:relative` parent
    (e.g. a 16:10 thumbnail box) by cropping instead of stretching or letterboxing —
    percentage height on an in-flow child of an `aspect-ratio` box resolves against
    an indefinite containing block, which would otherwise force the parent square.
    """
    body = ICONS.get(name, ICONS["flame"])
    return (
        f'<svg viewBox="0 0 100 100" width="{size}" height="{size}" preserveAspectRatio="xMidYMid slice" '
        f'style="position:absolute;inset:0;">'
        f'<rect width="100" height="100" fill="{bg}"/>'
        f'<g transform="translate(32,32)" fill="none" stroke="#fff" stroke-width="1.6" color="#fff" style="opacity:.9">'
        f'<svg width="36" height="36" viewBox="0 0 24 24">{body}</svg>'
        f'</g></svg>'
    )
