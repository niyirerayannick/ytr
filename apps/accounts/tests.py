from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile

User = get_user_model()


class RegistrationTests(TestCase):
    def test_registration_creates_inactive_member(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "newperson",
            "email": "newperson@example.com",
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newperson")
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.role, Profile.ROLE_MEMBER)

    def test_inactive_user_cannot_log_in(self):
        self.client.post(reverse("accounts:register"), {
            "username": "newperson",
            "email": "newperson@example.com",
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
        })
        response = self.client.post(reverse("accounts:login"), {
            "username": "newperson", "password": "a-strong-password-123",
        })
        # Login form re-renders with an error rather than redirecting.
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)


class ProfileSignalTests(TestCase):
    def test_superuser_gets_admin_profile(self):
        superuser = User.objects.create_superuser("root", "root@example.com", "password123")
        self.assertEqual(superuser.profile.role, Profile.ROLE_ADMIN)

    def test_regular_user_gets_member_profile(self):
        user = User.objects.create_user("someone", "someone@example.com", "password123")
        self.assertEqual(user.profile.role, Profile.ROLE_MEMBER)
