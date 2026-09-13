from urllib.parse import urlparse

from django.core.exceptions import ValidationError

# Per docs/roadmaps/digital-discipleship-platform.md (Phase C): only HTTPS
# meet.google.com links are accepted, with a real meeting path — never an
# arbitrary submitted URL, and the view never redirects through this field,
# it's only ever rendered as a plain outbound <a href>.
MEET_HOSTS = {"meet.google.com"}


def validate_meet_url(value):
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in MEET_HOSTS:
        raise ValidationError("Enter a valid HTTPS meet.google.com URL.")
    if not parsed.path or parsed.path == "/":
        raise ValidationError(
            "Enter the full Google Meet link for this session, e.g. https://meet.google.com/abc-defg-hij."
        )
