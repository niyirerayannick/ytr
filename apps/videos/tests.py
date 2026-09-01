from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
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


class VideoValidationTests(TestCase):
    def setUp(self):
        self.series = VideoSeries.objects.create(title_en="Series", title_rw="Urukurikirane")

    def test_youtube_url_must_be_https_youtube(self):
        video = Video(series=self.series, title_en="Video", title_rw="Videwo", youtube_url="https://evil.example.com/watch")
        with self.assertRaises(ValidationError):
            video.full_clean()

    def test_youtube_url_accepts_youtube(self):
        video = Video(series=self.series, title_en="Video", title_rw="Videwo", youtube_url="https://youtu.be/abc123")
        video.full_clean()

    def test_video_upload_rejects_invalid_file_type(self):
        video = Video(
            series=self.series, title_en="Video", title_rw="Videwo",
            video_file=SimpleUploadedFile("video.exe", b"not a video", content_type="application/octet-stream"),
        )
        with self.assertRaises(ValidationError):
            video.full_clean()
