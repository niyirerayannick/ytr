from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_AUTHOR = "author"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_AUTHOR, "Author"),
        (ROLE_MEMBER, "Member"),
    ]

    LANGUAGE_EN = "en"
    LANGUAGE_RW = "rw"
    LANGUAGE_CHOICES = [
        (LANGUAGE_EN, "English"),
        (LANGUAGE_RW, "Kinyarwanda"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    full_name = models.CharField(max_length=150, blank=True, default="")
    phone_number = models.CharField(max_length=40, blank=True, default="")
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_EN)
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_version = models.CharField(max_length=40, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def display_name(self):
        return self.full_name.strip() or self.user.get_full_name() or self.user.username

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_author(self):
        return self.role == self.ROLE_AUTHOR

    @property
    def is_member(self):
        return self.role == self.ROLE_MEMBER


class Bookmark(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    article = models.ForeignKey("articles.Article", on_delete=models.CASCADE, related_name="bookmarked_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("member", "article")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.member} → {self.article}"


class RSVP(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rsvps")
    gathering = models.ForeignKey("core.Gathering", on_delete=models.CASCADE, related_name="rsvps")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("member", "gathering")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.member} → {self.gathering}"


class Testimony(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="testimonies")
    title = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="testimonies_reviewed",
    )
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Testimonies"

    def __str__(self):
        return f"{self.title} — {self.member}"

    def approve(self, reviewer):
        self.status = self.STATUS_APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_note = ""
        self.save()

    def reject(self, reviewer, note):
        self.status = self.STATUS_REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_note = note
        self.save()


class PrayerRequest(models.Model):
    """Pastoral, private. Visible only to the submitting member and Admins — never public."""

    STATUS_PENDING = "pending"
    STATUS_REVIEWED = "reviewed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_REVIEWED, "Reviewed"),
    ]

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prayer_requests")
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prayer request from {self.member}"

    def mark_reviewed(self):
        self.status = self.STATUS_REVIEWED
        self.save()
