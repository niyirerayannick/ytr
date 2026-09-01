from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title_en", "title_rw", "order", "external_link")
    search_fields = ("title_en", "title_rw", "description_en", "description_rw")
