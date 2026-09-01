from django.test import TestCase
from django.urls import reverse

from .models import Devotion


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
