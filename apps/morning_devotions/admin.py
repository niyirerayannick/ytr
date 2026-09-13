from django.contrib import admin

from .models import MorningDevotionSession


@admin.register(MorningDevotionSession)
class MorningDevotionSessionAdmin(admin.ModelAdmin):
    list_display = (
        "title_en", "start_datetime", "status", "language",
        "speaker", "recording_episode", "recording_video",
    )
    list_filter = ("status", "language")
    search_fields = ("title_en", "title_rw", "scripture_reference", "description_en", "description_rw")
    date_hierarchy = "start_datetime"
    prepopulated_fields = {"slug": ("title_en",)}
    autocomplete_fields = ["speaker", "related_devotion", "recording_episode", "recording_video"]
    fieldsets = (
        (None, {"fields": ("title_en", "title_rw", "slug", "scripture_reference", "speaker", "language")}),
        ("Schedule", {"fields": ("start_datetime", "end_datetime", "meet_url", "status")}),
        ("Before the session", {"fields": ("description_en", "description_rw", "related_devotion")}),
        ("After the session", {"fields": ("summary_en", "summary_rw", "recording_episode", "recording_video")}),
    )
