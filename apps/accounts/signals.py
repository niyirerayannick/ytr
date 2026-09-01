from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    """Every User gets a Profile. Superusers (incl. `createsuperuser`) get role=admin."""
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={"role": Profile.ROLE_ADMIN if instance.is_superuser else Profile.ROLE_MEMBER},
        )
