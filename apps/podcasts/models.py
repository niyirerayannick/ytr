from django.db import models
from django.utils.text import slugify

from apps.core.icons import ICON_CHOICES
from apps.core.models import ReviewableContent


class PodcastSeries(models.Model):
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    title_en = models.CharField(max_length=150)
    title_rw = models.CharField(max_length=150)
    subtitle_en = models.CharField(max_length=250, blank=True)
    subtitle_rw = models.CharField(max_length=250, blank=True)
    description_en = models.TextField(blank=True)
    description_rw = models.TextField(blank=True)

    cover_image = models.ImageField(upload_to="podcasts/", blank=True, null=True)
    icon = models.CharField(max_length=30, choices=ICON_CHOICES, default="mic")
    color = models.CharField(max_length=20, default="#E4572E")

    spotify_url = models.URLField(blank=True, null=True)
    apple_url = models.URLField(blank=True, null=True)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title_en"]
        verbose_name_plural = "Podcast series"

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_en)
            slug = base
            i = 1
            while PodcastSeries.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)


class Episode(ReviewableContent):
    series = models.ForeignKey(PodcastSeries, on_delete=models.CASCADE, related_name="episodes")

    title_en = models.CharField(max_length=200)
    title_rw = models.CharField(max_length=200)
    description_en = models.TextField(blank=True)
    description_rw = models.TextField(blank=True)

    duration = models.CharField(max_length=20, blank=True, help_text="e.g. '11 min'")
    audio_file = models.FileField(upload_to="episodes/", blank=True, null=True)
    audio_url = models.URLField(blank=True, null=True)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.series.title_en} — {self.title_en}"
