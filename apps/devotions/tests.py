from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Devotion

User = get_user_model()


class DevotionModelTests(TestCase):
    def test_slug_is_auto_generated(self):
        devotion = Devotion.objects.create(
            date="2024-01-01", verse_ref="Psalm 46:10",
            verse_text_en="v", verse_text_rw="v",
            reflection_en="r", reflection_rw="r",
            prayer_en="p", prayer_rw="p",
        )
        self.assertTrue(devotion.slug)


class DevotionListViewTests(TestCase):
    def test_devotion_list_loads(self):
        Devotion.objects.create(
            date="2024-01-01", verse_ref="Psalm 46:10", is_featured=True,
            verse_text_en="Be still.", verse_text_rw="Ba amahoro.",
            reflection_en="r", reflection_rw="r",
            prayer_en="p", prayer_rw="p",
            status=Devotion.STATUS_PUBLISHED,
        )
        response = self.client.get(reverse("devotions:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Psalm 46:10")

    def test_devotion_list_loads_when_empty(self):
        response = self.client.get(reverse("devotions:list"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_devotion_list_is_marked_cacheable_for_offline_reading(self):
        response = self.client.get(reverse("devotions:list"))
        self.assertEqual(response.headers.get("X-YTR-Public-Cache"), "1")

    def test_authenticated_devotion_list_is_never_marked_cacheable(self):
        User.objects.create_user("reader", "reader@example.com", "password123", is_active=True)
        self.client.force_login(User.objects.get(username="reader"))
        response = self.client.get(reverse("devotions:list"))
        self.assertNotIn("X-YTR-Public-Cache", response.headers)

    def test_paginated_devotion_list_is_never_marked_cacheable(self):
        response = self.client.get(reverse("devotions:list"), {"page": "1"})
        self.assertNotIn("X-YTR-Public-Cache", response.headers)
