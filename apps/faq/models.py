from django.db import models


class FAQ(models.Model):
    question_en = models.CharField(max_length=300)
    question_rw = models.CharField(max_length=300)
    answer_en = models.TextField()
    answer_rw = models.TextField()

    is_highlighted = models.BooleanField(
        default=False, help_text="Shown as the 'Most Asked' highlight card. Only one should be marked."
    )
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question_en
