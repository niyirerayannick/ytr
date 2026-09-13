"""Extract a YouTube video ID for a privacy-conscious youtube-nocookie.com
embed on the Morning Devotion detail page. Scoped to this app only — the
public Videos app doesn't have detail/embed pages yet (see
docs/roadmaps/digital-discipleship-platform.md, Phase D), so this isn't
duplicating an existing capability.
"""
from urllib.parse import parse_qs, urlparse

_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
_SHORT_HOSTS = {"youtu.be", "www.youtu.be"}


def youtube_embed_id(url):
    if not url:
        return ""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host in _SHORT_HOSTS:
        return parsed.path.lstrip("/")
    if host in _HOSTS:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [""])[0]
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/embed/", 1)[-1]
    return ""
