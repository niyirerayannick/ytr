from django.contrib import admin

from .models import Devotion


@admin.register(Devotion)
class DevotionAdmin(admin.ModelAdmin):
    list_display = ("date", "verse_ref", "status", "is_featured", "submitted_by", "updated_at")
    list_filter = ("status", "is_featured")
    search_fields = ("verse_ref", "verse_text_en", "verse_text_rw", "reflection_en", "reflection_rw")
    date_hierarchy = "date"
    prepopulated_fields = {"slug": ("verse_ref",)}
    readonly_fields = ("submitted_at", "reviewed_at")
