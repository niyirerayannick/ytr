from django.test import TestCase
from django.urls import reverse

from .models import Video, VideoSeries


class VideoListViewTests(TestCase):
    def test_video_list_loads_when_empty(self):
        response = self.client.get(reverse("videos:list"))
        self.assertEqual(response.status_code, 200)

    def test_video_list_shows_series_and_videos(self):
        series = VideoSeries.objects.create(title_en="Sunday Gatherings", title_rw="Amateraniro")
        Video.objects.create(
            series=series, title_en="The Altar Life", title_rw="Ubuzima bw'Igicaniro", is_featured=True,
            status=Video.STATUS_PUBLISHED,
        )
        response = self.client.get(reverse("videos:list"))
        self.assertContains(response, "Sunday Gatherings")
        self.assertContains(response, "The Altar Life")
