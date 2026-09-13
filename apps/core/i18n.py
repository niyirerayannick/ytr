"""Bilingual-field helpers for pages rendered once per request server-side.

The public site is bilingual via an instant client-side toggle (see
`templates/base.html`'s `.i18n-en`/`.i18n-rw` convention, flipped by
`static/js/site.js` from a `localStorage` choice) — the server never knows
which language a visitor is looking at. The dashboard ("My YTR") is
different: it's authenticated and server-rendered per-request, so it can and
should use the member's own stored `Profile.preferred_language` instead.
Nothing before this used that field for anything, even though it's been
collected at registration since Phase B.
"""


def bilingual_field(obj, field, lang):
    """Read `{field}_{lang}` off `obj`, falling back to `{field}_en` when the
    Kinyarwanda copy is blank (editors don't always have it ready yet) or
    `lang` isn't "rw"."""
    if lang == "rw":
        value = getattr(obj, f"{field}_rw", "")
        if value:
            return value
    return getattr(obj, f"{field}_en", "")


def viewer_language(user):
    """The signed-in member's preferred language; "en" for anonymous
    visitors or accounts with no profile."""
    profile = getattr(user, "profile", None)
    return profile.preferred_language if profile else "en"
