from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Profile

User = get_user_model()


class RegistrationTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_registration_creates_unverified_member_with_profile_details(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "newperson",
            "full_name": "New Person",
            "email": "newperson@example.com",
            "phone_number": "+250788123456",
            "preferred_language": "en",
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
            "privacy_accepted": "on",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newperson")
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.role, Profile.ROLE_MEMBER)
        self.assertEqual(user.profile.full_name, "New Person")
        self.assertEqual(user.profile.phone_number, "+250788123456")
        self.assertEqual(user.profile.preferred_language, "en")
        self.assertIsNotNone(user.profile.privacy_accepted_at)
        self.assertTrue(user.profile.privacy_policy_version)

    def test_email_verification_activates_account(self):
        self.client.post(reverse("accounts:register"), {
            "username": "verifyme",
            "full_name": "Verify Me",
            "email": "verifyme@example.com",
            "preferred_language": "rw",
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
            "privacy_accepted": "on",
        })
        user = User.objects.get(username="verifyme")
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = self.client.get(reverse("accounts:verify_email", args=[uid, token]))
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_inactive_user_cannot_log_in(self):
        self.client.post(reverse("accounts:register"), {
            "username": "newperson",
            "full_name": "New Person",
            "email": "newperson@example.com",
            "preferred_language": "en",
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
            "privacy_accepted": "on",
        })
        response = self.client.post(reverse("accounts:login"), {
            "username": "newperson",
            "password": "a-strong-password-123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)

    def test_registration_honeypot_rejects_bot_submission(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "botperson",
            "full_name": "Bot Person",
            "email": "bot@example.com",
            "preferred_language": "en",
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
            "website": "filled",
            "privacy_accepted": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="botperson").exists())

    @override_settings(RATELIMIT_REGISTRATION_LIMIT=1, RATELIMIT_WINDOW_SECONDS=3600)
    def test_registration_is_rate_limited(self):
        payload = {
            "username": "firstperson",
            "full_name": "First Person",
            "email": "first@example.com",
            "preferred_language": "en",
            "password1": "a-strong-password-123",
            "password2": "a-strong-password-123",
            "privacy_accepted": "on",
        }
        self.assertEqual(self.client.post(reverse("accounts:register"), payload).status_code, 302)
        payload["username"] = "secondperson"
        payload["email"] = "second@example.com"
        self.assertEqual(self.client.post(reverse("accounts:register"), payload).status_code, 429)


class ProfileSignalTests(TestCase):
    def test_superuser_gets_admin_profile(self):
        superuser = User.objects.create_superuser("root", "root@example.com", "password123")
        self.assertEqual(superuser.profile.role, Profile.ROLE_ADMIN)

    def test_regular_user_gets_member_profile(self):
        user = User.objects.create_user("someone", "someone@example.com", "password123")
        self.assertEqual(user.profile.role, Profile.ROLE_MEMBER)
