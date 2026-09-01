from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from .models import ContactMessage, NewsletterSubscriber


class ContactFormTests(TestCase):
    def setUp(self):
        cache.clear()
    def test_contact_form_saves_message(self):
        response = self.client.post(reverse("engagement:contact"), {
            "form_type": "contact",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "message": "Hello YTR!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        saved = ContactMessage.objects.first()
        self.assertEqual(saved.name, "Jane Doe")
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_contact_form_does_not_save(self):
        response = self.client.post(reverse("engagement:contact"), {
            "form_type": "contact",
            "name": "",
            "email": "not-an-email",
            "message": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_honeypot_rejects_bot_submission(self):
        response = self.client.post(reverse("engagement:contact"), {
            "form_type": "contact", "name": "Bot", "email": "bot@example.com",
            "message": "Spam", "website": "filled",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    @patch("apps.engagement.views.django_send_mail", side_effect=OSError("SMTP unavailable"))
    def test_contact_mail_failure_is_logged_without_losing_message(self, _send_mail):
        with self.assertLogs("apps.engagement.views", level="ERROR"):
            response = self.client.post(reverse("engagement:contact"), {
                "form_type": "contact", "name": "Jane", "email": "jane@example.com", "message": "Hello",
            })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

    @override_settings(RATELIMIT_CONTACT_LIMIT=1, RATELIMIT_WINDOW_SECONDS=3600)
    def test_contact_is_rate_limited(self):
        payload = {"form_type": "contact", "name": "Jane", "email": "jane@example.com", "message": "Hello"}
        self.assertEqual(self.client.post(reverse("engagement:contact"), payload).status_code, 302)
        self.assertEqual(self.client.post(reverse("engagement:contact"), payload).status_code, 429)


class NewsletterFormTests(TestCase):
    def setUp(self):
        cache.clear()
    def test_subscribe_form_saves_email(self):
        response = self.client.post(reverse("engagement:contact"), {
            "form_type": "subscribe",
            "email": "reader@example.com",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)

    def test_subscribing_twice_does_not_duplicate(self):
        self.client.post(reverse("engagement:contact"), {
            "form_type": "subscribe", "email": "reader@example.com",
        })
        self.client.post(reverse("engagement:contact"), {
            "form_type": "subscribe", "email": "reader@example.com",
        })
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)

    def test_newsletter_honeypot_rejects_bot_submission(self):
        response = self.client.post(reverse("engagement:contact"), {
            "form_type": "subscribe", "email": "bot@example.com", "website": "filled",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(NewsletterSubscriber.objects.count(), 0)

    @override_settings(RATELIMIT_NEWSLETTER_LIMIT=1, RATELIMIT_WINDOW_SECONDS=3600)
    def test_newsletter_is_rate_limited(self):
        self.assertEqual(self.client.post(reverse("engagement:contact"), {
            "form_type": "subscribe", "email": "one@example.com",
        }).status_code, 302)
        self.assertEqual(self.client.post(reverse("engagement:contact"), {
            "form_type": "subscribe", "email": "two@example.com",
        }).status_code, 429)
