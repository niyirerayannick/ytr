from django.db import models
from django.urls import reverse
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

    def get_absolute_url(self):
        return reverse("devotions:detail", kwargs={"slug": self.slug})

    def has_language(self, lang):
        """Whether this devotion has real (non-empty) authored content in ``lang``.

        Used to gate sharing/repost so a missing translation degrades to
        "unavailable" instead of silently falling back to English text under
        a Kinyarwanda label.
        """
        if lang == "en":
            return bool(self.verse_text_en.strip() and self.reflection_en.strip())
        if lang == "rw":
            return bool(self.verse_text_rw.strip() and self.reflection_rw.strip())
        return False

    def share_excerpt(self, lang, max_words=45):
        """A short, word-wrapped excerpt of the reflection for share text/cards."""
        text = self.reflection_rw if lang == "rw" else self.reflection_en
        words = text.split()
        if len(words) <= max_words:
            return text.strip()
        return " ".join(words[:max_words]) + "…"
