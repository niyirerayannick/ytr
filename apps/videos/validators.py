from urllib.parse import urlparse

from django.core.exceptions import ValidationError


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}


def validate_youtube_url(value):
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in YOUTUBE_HOSTS:
        raise ValidationError("Enter a valid HTTPS YouTube or youtu.be URL.")
