from django.contrib import admin

from .models import ContactMessage, NewsletterSubscriber


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "subscribed_at", "confirmed")
    list_filter = ("confirmed",)
    search_fields = ("email",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "message")
