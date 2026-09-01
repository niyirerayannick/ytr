from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Episode, PodcastSeries
from apps.core.uploads import validate_audio_upload


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


class EpisodeValidationTests(TestCase):
    def test_audio_upload_accepts_supported_file(self):
        validate_audio_upload(SimpleNamespace(name="episode.mp3", size=1024, content_type="audio/mpeg"))

    def test_audio_upload_rejects_invalid_file_type(self):
        series = PodcastSeries.objects.create(title_en="Series", title_rw="Urukurikirane")
        episode = Episode(
            series=series, title_en="Episode", title_rw="Igice",
            audio_file=SimpleUploadedFile("audio.exe", b"not audio", content_type="application/octet-stream"),
        )
        with self.assertRaises(ValidationError):
            episode.full_clean()

    def test_audio_upload_rejects_oversized_file(self):
        oversized = SimpleNamespace(
            name="episode.mp3", size=25 * 1024 * 1024 + 1, content_type="audio/mpeg",
        )
        with self.assertRaises(ValidationError):
            validate_audio_upload(oversized)
