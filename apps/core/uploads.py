"""Small, dependency-free validation helpers for author-controlled media uploads."""
from pathlib import Path

from django.core.exceptions import ValidationError


def validate_uploaded_media(upload, *, extensions, mime_types, max_bytes, label):
    if not upload:
        return
    extension = Path(upload.name).suffix.lower()
    if extension not in extensions:
        raise ValidationError(f"Upload a supported {label} file ({', '.join(sorted(extensions))}).")
    if upload.size > max_bytes:
        max_megabytes = max_bytes // (1024 * 1024)
        raise ValidationError(f"{label.title()} files must be {max_megabytes} MB or smaller.")
    content_type = getattr(upload, "content_type", "")
    if content_type and content_type.lower() not in mime_types:
        raise ValidationError(f"Upload a valid {label} file.")


def validate_audio_upload(upload):
    validate_uploaded_media(
        upload, extensions={".mp3", ".m4a", ".wav"},
        mime_types={"audio/mpeg", "audio/mp4", "audio/x-m4a", "audio/wav", "audio/x-wav"},
        max_bytes=25 * 1024 * 1024, label="audio",
    )


def validate_video_upload(upload):
    validate_uploaded_media(
        upload, extensions={".mp4", ".webm"}, mime_types={"video/mp4", "video/webm"},
        max_bytes=100 * 1024 * 1024, label="video",
    )
