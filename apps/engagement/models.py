from django.db import models


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.created_at:%Y-%m-%d}"
