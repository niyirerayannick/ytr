from django.test import TestCase
from django.urls import reverse

from .models import SevenMountain


class AboutViewTests(TestCase):
    def test_about_loads(self):
        response = self.client.get(reverse("about:about"))
        self.assertEqual(response.status_code, 200)

    def test_about_shows_mountains(self):
        SevenMountain.objects.create(
            name_en="Politics", name_rw="Politiki",
            description_en="d", description_rw="d",
        )
        response = self.client.get(reverse("about:about"))
        self.assertContains(response, "Politics")
