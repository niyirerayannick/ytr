from django.db import models
from django.utils.text import slugify

from apps.core.models import ReviewableContent


class Devotion(ReviewableContent):
    date = models.DateField(unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    verse_ref = models.CharField(max_length=120)
    verse_text_en = models.TextField()
    verse_text_rw = models.TextField()

    reflection_en = models.TextField()
    reflection_rw = models.TextField()

    prayer_en = models.TextField()
    prayer_rw = models.TextField()

    is_featured = models.BooleanField(
        default=False,
        help_text="Mark as 'Today's Devotion'. If none is marked, the most recent by date is used.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} — {self.verse_ref}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.date}-{self.verse_ref}")
            slug = base
            i = 1
            while Devotion.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)
