from django.test import TestCase
from django.urls import reverse

from .models import Episode, PodcastSeries


class PodcastListViewTests(TestCase):
    def test_podcast_list_loads_when_empty(self):
        response = self.client.get(reverse("podcasts:list"))
        self.assertEqual(response.status_code, 200)

    def test_podcast_list_shows_series_and_episodes(self):
        series = PodcastSeries.objects.create(
            title_en="Kanguka", title_rw="Kanguka",
            subtitle_en="Wake up", subtitle_rw="Kangurwa",
        )
        Episode.objects.create(
            series=series, title_en="Wake Up First", title_rw="Banza Ukangurwe", duration="11 min",
            status=Episode.STATUS_PUBLISHED,
        )
        response = self.client.get(reverse("podcasts:list"))
        self.assertContains(response, "Kanguka")
        self.assertContains(response, "Wake Up First")
