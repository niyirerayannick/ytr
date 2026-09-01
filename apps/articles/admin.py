from django.contrib import admin

from .models import Article, Author


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title_en", "title_rw", "author", "status", "is_featured", "submitted_by", "published_at")
    list_filter = ("status", "is_featured", "author")
    search_fields = ("title_en", "title_rw", "hook_en", "hook_rw", "body_en", "body_rw")
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ("title_en",)}
    readonly_fields = ("submitted_at", "reviewed_at")
