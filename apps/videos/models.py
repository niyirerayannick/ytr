from django.db import models
from django.utils.text import slugify

from apps.core.icons import ICON_CHOICES
from apps.core.models import ReviewableContent
from apps.core.uploads import validate_video_upload
from .validators import validate_youtube_url


class VideoSeries(models.Model):
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    title_en = models.CharField(max_length=150)
    title_rw = models.CharField(max_length=150)
    icon = models.CharField(max_length=30, choices=ICON_CHOICES, default="flame")
    color = models.CharField(max_length=20, default="#241A3D")

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title_en"]
        verbose_name_plural = "Video series"

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_en)
            slug = base
            i = 1
            while VideoSeries.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)


class Video(ReviewableContent):
    series = models.ForeignKey(VideoSeries, on_delete=models.CASCADE, related_name="videos")

    title_en = models.CharField(max_length=200)
    title_rw = models.CharField(max_length=200)

    youtube_url = models.URLField(blank=True, null=True, validators=[validate_youtube_url])
    video_file = models.FileField(upload_to="videos/", blank=True, null=True, validators=[validate_video_upload])

    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.series.title_en} — {self.title_en}"
