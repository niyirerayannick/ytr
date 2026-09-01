from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.core.icons import ICON_CHOICES
from apps.core.models import ReviewableContent


class Author(models.Model):
    name = models.CharField(max_length=150)
    bio_en = models.TextField(blank=True)
    bio_rw = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="authors/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Article(ReviewableContent):
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    title_en = models.CharField(max_length=200)
    title_rw = models.CharField(max_length=200)
    hook_en = models.CharField(max_length=300)
    hook_rw = models.CharField(max_length=300)

    body_en = models.TextField(help_text="Paragraphs separated by a blank line.")
    body_rw = models.TextField(help_text="Paragraphs separated by a blank line.")

    verse_text_en = models.TextField(blank=True)
    verse_text_rw = models.TextField(blank=True)
    verse_ref_en = models.CharField(max_length=120, blank=True)
    verse_ref_rw = models.CharField(max_length=120, blank=True)

    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles")

    cover_image = models.ImageField(upload_to="articles/", blank=True, null=True)
    icon = models.CharField(max_length=30, choices=ICON_CHOICES, default="flame")
    color = models.CharField(max_length=20, default="#241A3D", help_text="Hex color used behind the icon when there is no cover image.")

    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_en)
            slug = base
            i = 1
            while Article.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("articles:detail", kwargs={"slug": self.slug})

    def body_paragraphs_en(self):
        return [p.strip() for p in self.body_en.split("\n\n") if p.strip()]

    def body_paragraphs_rw(self):
        return [p.strip() for p in self.body_rw.split("\n\n") if p.strip()]

    def related_articles(self, count=3):
        return (
            Article.objects.filter(status=Article.STATUS_PUBLISHED)
            .exclude(pk=self.pk)
            .order_by("-published_at")[:count]
        )
