from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .validators import validate_meet_url

STARTING_SOON_WINDOW = timezone.timedelta(minutes=15)

STATE_UPCOMING = "upcoming"
STATE_STARTING_SOON = "starting_soon"
STATE_LIVE = "live"
STATE_FINISHED = "finished"


class MorningDevotionSession(models.Model):
    """A scheduled Morning Devotion — live Google Meet session plus whatever
    read/listen/watch material gets attached before or after it.

    Deliberately NOT a `ReviewableContent`: per
    docs/roadmaps/digital-discipleship-platform.md (Phase C), this is
    admin-scheduled ministry content, not an Author-submitted/Admin-reviewed
    editorial piece, so it gets a simpler draft/published/cancelled status
    instead of the Author submit -> Admin approve workflow used by
    Article/Devotion/Episode/Video.
    """

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    LANGUAGE_EN = "en"
    LANGUAGE_RW = "rw"
    LANGUAGE_BILINGUAL = "bilingual"
    LANGUAGE_CHOICES = [
        (LANGUAGE_EN, "English"),
        (LANGUAGE_RW, "Kinyarwanda"),
        (LANGUAGE_BILINGUAL, "Bilingual"),
    ]

    slug = models.SlugField(max_length=220, unique=True, blank=True)
    title_en = models.CharField(max_length=200)
    title_rw = models.CharField(max_length=200)
    scripture_reference = models.CharField(max_length=120, blank=True)
    description_en = models.TextField(blank=True, help_text="Shown before the session — what to expect.")
    description_rw = models.TextField(blank=True)
    summary_en = models.TextField(blank=True, help_text="Written afterward, once the session is finished.")
    summary_rw = models.TextField(blank=True)

    speaker = models.ForeignKey(
        "articles.Author", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="morning_devotion_sessions",
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    meet_url = models.URLField(blank=True, validators=[validate_meet_url])

    # Identifies the language of the attached recording, not a translation of
    # this record's own text. One session -> one recording for now (see
    # docs/morning-devotion.md for the documented path to per-language
    # recordings later without a schema rewrite).
    language = models.CharField(max_length=12, choices=LANGUAGE_CHOICES, default=LANGUAGE_EN)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    related_devotion = models.ForeignKey(
        "devotions.Devotion", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="morning_devotion_sessions",
    )
    # Reuse the existing podcast/video content types instead of storing audio
    # or video files on this model directly — they already have the upload
    # validation, publishing workflow, and playback fields this needs.
    recording_episode = models.ForeignKey(
        "podcasts.Episode", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="morning_devotion_sessions",
    )
    recording_video = models.ForeignKey(
        "videos.Video", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="morning_devotion_sessions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_datetime"]
        verbose_name = "Morning Devotion session"
        verbose_name_plural = "Morning Devotion sessions"

    def __str__(self):
        return f"{self.title_en} — {self.start_datetime:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.start_datetime:%Y-%m-%d}-{self.title_en}")
            slug = base
            i = 1
            while MorningDevotionSession.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.start_datetime and self.end_datetime and self.end_datetime < self.start_datetime:
            raise ValidationError({"end_datetime": "The end time must be on or after the start time."})

    def get_absolute_url(self):
        return reverse("morning_devotions:detail", kwargs={"slug": self.slug})

    @classmethod
    def current_or_next(cls):
        """The session My YTR / the homepage should feature right now:

            live > starting soon > next upcoming > latest finished session
            that actually has something to show > None

        A finished session with no summary/audio/video yet is skipped in
        favor of an earlier one that does, rather than surfaced as a dead
        end with no valid action to offer — callers should treat `None` as
        "omit the block", not render an empty card.
        """
        published = cls.objects.filter(status=cls.STATUS_PUBLISHED).select_related(
            "recording_episode", "recording_video",
        )
        upcoming_or_live = published.filter(end_datetime__gte=timezone.now()).order_by("start_datetime").first()
        if upcoming_or_live:
            return upcoming_or_live
        for candidate in published.order_by("-start_datetime"):
            if candidate.has_any_content:
                return candidate
        return None

    @property
    def session_state(self):
        """Computed, not stored — never trust a persisted "is_live" flag
        against a clock that keeps moving. See roadmap Phase C."""
        now = timezone.now()
        if now < self.start_datetime - STARTING_SOON_WINDOW:
            return STATE_UPCOMING
        if now < self.start_datetime:
            return STATE_STARTING_SOON
        if now <= self.end_datetime:
            return STATE_LIVE
        return STATE_FINISHED

    @property
    def can_join_live(self):
        return bool(self.meet_url) and self.session_state in (STATE_STARTING_SOON, STATE_LIVE)

    @property
    def has_summary(self):
        return bool(self.summary_en.strip() or self.summary_rw.strip())

    @property
    def has_audio(self):
        return (
            self.recording_episode_id is not None
            and self.recording_episode.status == self.recording_episode.STATUS_PUBLISHED
        )

    @property
    def has_video(self):
        return (
            self.recording_video_id is not None
            and self.recording_video.status == self.recording_video.STATUS_PUBLISHED
        )

    @property
    def audio_duration(self):
        return self.recording_episode.duration if self.has_audio else ""

    @property
    def has_any_content(self):
        """Whether there's anything worth showing beyond "join the live call"
        — a written summary, audio, or video. Used to decide whether a
        finished session is still worth surfacing as an archive/resume
        card (homepage, My YTR) instead of a dead end."""
        return self.has_summary or self.has_audio or self.has_video
