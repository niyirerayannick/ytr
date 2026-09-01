from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage, NewsletterSubscriber


class ContactFormTests(TestCase):
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


class NewsletterFormTests(TestCase):
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
