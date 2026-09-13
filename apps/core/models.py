from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class SiteSettings(models.Model):
    """Singleton model holding sitewide contact/social details."""

    contact_email = models.EmailField(default="hello@youthtimerevival.rw")
    phone = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=255, blank=True)
    website_url = models.URLField(
        blank=True,
        help_text="Shown in the footer of generated devotional share images, e.g. https://youthtimerevival.rw",
    )

    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    morning_devotion_url = models.URLField(blank=True)

    mission_en = models.TextField(blank=True)
    mission_rw = models.TextField(blank=True)
    vision_en = models.TextField(blank=True)
    vision_rw = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def clean(self):
        if SiteSettings.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one SiteSettings instance may exist.")

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Gathering(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    recurring = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return f"{self.title} — {self.start_datetime:%Y-%m-%d %H:%M}"

    @property
    def is_upcoming(self):
        return self.end_datetime >= timezone.now()

    def clean(self):
        super().clean()
        if self.start_datetime and self.end_datetime and self.end_datetime < self.start_datetime:
            raise ValidationError({"end_datetime": "The end time must be on or after the start time."})


class ReviewableContent(models.Model):
    """Abstract base for content that goes through the Author -> Admin review workflow.

    Public-facing views must always filter on ``status=STATUS_PUBLISHED`` —
    drafts, pending, and rejected content is never shown on the public site.
    """

    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_PUBLISHED = "published"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending review"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_REJECTED, "Rejected"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s_submitted",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s_reviewed",
    )
    review_note = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def submit_for_review(self, user):
        self.status = self.STATUS_PENDING
        self.submitted_by = user
        self.submitted_at = timezone.now()
        self.save()

    def approve(self, reviewer):
        self.status = self.STATUS_PUBLISHED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.published_at = timezone.now()
        self.review_note = ""
        self.save()

    def reject(self, reviewer, note):
        self.status = self.STATUS_REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_note = note
        self.save()
