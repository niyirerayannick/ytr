from django.contrib import admin

from .models import Episode, PodcastSeries


class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 1
    fields = ("order", "title_en", "title_rw", "duration", "audio_url", "audio_file", "status")


@admin.register(PodcastSeries)
class PodcastSeriesAdmin(admin.ModelAdmin):
    list_display = ("title_en", "title_rw", "order", "spotify_url", "apple_url")
    search_fields = ("title_en", "title_rw", "subtitle_en", "subtitle_rw")
    prepopulated_fields = {"slug": ("title_en",)}
    inlines = [EpisodeInline]


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ("title_en", "series", "status", "submitted_by", "duration", "order")
    list_filter = ("status", "series")
    search_fields = ("title_en", "title_rw", "description_en", "description_rw")
    readonly_fields = ("submitted_at", "reviewed_at")
