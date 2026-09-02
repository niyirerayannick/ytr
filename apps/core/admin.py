from django.contrib import admin

from .models import Gathering, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("contact_email", "phone", "address", "morning_devotion_url", "updated_at")

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Gathering)
class GatheringAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "start_datetime", "end_datetime", "recurring")
    list_filter = ("recurring",)
    search_fields = ("title", "location", "description")
    date_hierarchy = "start_datetime"
