from django.db import models

from apps.core.icons import ICON_CHOICES


class SevenMountain(models.Model):
    name_en = models.CharField(max_length=100)
    name_rw = models.CharField(max_length=100)
    description_en = models.TextField()
    description_rw = models.TextField()
    icon = models.CharField(max_length=30, choices=ICON_CHOICES, default="mountain")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name_en


class BeliefPoint(models.Model):
    title_en = models.CharField(max_length=150)
    title_rw = models.CharField(max_length=150)
    description_en = models.TextField()
    description_rw = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title_en


class CallTimelineEntry(models.Model):
    year = models.CharField(max_length=20)
    body_en = models.TextField(help_text="An independent English retelling — not a translation.")
    body_rw = models.TextField(help_text="Preserve the founder's original Kinyarwanda wording verbatim.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "year"]
        verbose_name = "Call timeline entry"
        verbose_name_plural = "Call timeline entries"

    def __str__(self):
        return self.year
