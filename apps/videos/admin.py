from django.contrib import admin

from .models import Video, VideoSeries


class VideoInline(admin.TabularInline):
    model = Video
    extra = 1
    fields = ("order", "title_en", "title_rw", "youtube_url", "video_file", "is_featured", "status")


@admin.register(VideoSeries)
class VideoSeriesAdmin(admin.ModelAdmin):
    list_display = ("title_en", "title_rw", "order")
    search_fields = ("title_en", "title_rw")
    prepopulated_fields = {"slug": ("title_en",)}
    inlines = [VideoInline]


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title_en", "series", "status", "submitted_by", "is_featured", "order")
    list_filter = ("status", "series", "is_featured")
    search_fields = ("title_en", "title_rw")
    readonly_fields = ("submitted_at", "reviewed_at")
