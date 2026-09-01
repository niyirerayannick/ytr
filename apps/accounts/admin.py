from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Bookmark, PrayerRequest, Profile, RSVP, Testimony


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = ("username", "email", "first_name", "last_name", "is_active", "role")
    list_filter = ("is_active", "is_staff", "profile__role")

    def role(self, obj):
        return getattr(obj.profile, "role", "")


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("member", "article", "created_at")
    search_fields = ("member__username", "article__title_en")


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ("member", "gathering", "created_at")
    search_fields = ("member__username", "gathering__title")


@admin.register(Testimony)
class TestimonyAdmin(admin.ModelAdmin):
    list_display = ("title", "member", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "body", "member__username")


@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = ("member", "status", "created_at")
    list_filter = ("status",)
