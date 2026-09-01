from django.contrib import admin

from .models import BeliefPoint, CallTimelineEntry, SevenMountain


@admin.register(SevenMountain)
class SevenMountainAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_rw", "icon", "order")
    search_fields = ("name_en", "name_rw")


@admin.register(BeliefPoint)
class BeliefPointAdmin(admin.ModelAdmin):
    list_display = ("title_en", "title_rw", "order")
    search_fields = ("title_en", "title_rw")


@admin.register(CallTimelineEntry)
class CallTimelineEntryAdmin(admin.ModelAdmin):
    list_display = ("year", "order")
    search_fields = ("year", "body_en", "body_rw")
