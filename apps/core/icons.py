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
    # Share-sheet icons — brand marks (Simple Icons, CC0) rendered as flat
    # currentColor shapes (call with stroke=False) so they pick up our own
    # palette instead of each platform's brand color; UI icons (Feather, MIT)
    # rendered stroked (default) to match the rest of this file's line-icon style.
    "whatsapp": '<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z" fill="currentColor"/>',
    "facebook": '<path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z" fill="currentColor"/>',
    "x-logo": '<path d="M14.234 10.162 22.977 0h-2.072l-7.591 8.824L7.251 0H.258l9.168 13.343L.258 24H2.33l8.016-9.318L16.749 24h6.993l-9.51-13.838Zm-2.837 3.299-.929-1.329L3.076 1.56h3.182l5.965 8.532.929 1.329 7.754 11.09h-3.182Z" fill="currentColor"/>',
    "telegram": '<path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" fill="currentColor"/>',
    "mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke-linecap="round" stroke-linejoin="round"/><path d="m22 6-10 7L2 6" stroke-linecap="round" stroke-linejoin="round"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke-linecap="round" stroke-linejoin="round"/>',
    "share2": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 10.5 6.8-3.9M8.6 13.5l6.8 3.9" stroke-linecap="round"/>',
    "more-horizontal": '<circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1" fill="currentColor" stroke="none"/><circle cx="5" cy="12" r="1" fill="currentColor" stroke="none"/>',
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
