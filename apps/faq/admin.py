from django.contrib import admin

from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question_en", "question_rw", "is_highlighted", "order")
    list_filter = ("is_highlighted",)
    search_fields = ("question_en", "question_rw", "answer_en", "answer_rw")
