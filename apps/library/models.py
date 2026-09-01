from django.db import models

from apps.core.icons import ICON_CHOICES


class Book(models.Model):
    title_en = models.CharField(max_length=200)
    title_rw = models.CharField(max_length=200)
    description_en = models.TextField(blank=True)
    description_rw = models.TextField(blank=True)

    cover_image = models.ImageField(upload_to="books/", blank=True, null=True)
    icon = models.CharField(max_length=30, choices=ICON_CHOICES, default="book")
    color = models.CharField(max_length=20, default="#241A3D")

    external_link = models.URLField(blank=True, null=True)
    link_label_en = models.CharField(max_length=100, blank=True)
    link_label_rw = models.CharField(max_length=100, blank=True)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title_en"]

    def __str__(self):
        return self.title_en
