from datetime import timedelta
import os
from pathlib import Path
import subprocess
import sys

from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.articles.models import Article
from apps.core.models import Gathering, SiteSettings
from . import views


class HomeViewTests(TestCase):
    def test_home_loads(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Youth Time Revival")

    def test_home_shows_featured_articles(self):
        Article.objects.create(
            title_en="Test Article", title_rw="Ikizamini",
            hook_en="hook en", hook_rw="hook rw",
            body_en="Paragraph one.", body_rw="Paragraph rw.",
            is_featured=True, status=Article.STATUS_PUBLISHED, published_at="2024-01-01T00:00:00Z",
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Test Article")


class SiteSettingsSingletonTests(TestCase):
    def test_only_one_instance_can_exist(self):
        first = SiteSettings.load()
        second = SiteSettings.load()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(SiteSettings.objects.count(), 1)


class SearchViewTests(TestCase):
    def test_search_returns_matching_article(self):
        Article.objects.create(
            title_en="Not in the Masses", title_rw="Ntibiri mu Bwinshi",
            hook_en="hook", hook_rw="hook",
            body_en="Body.", body_rw="Body.",
            status=Article.STATUS_PUBLISHED, published_at="2024-01-01T00:00:00Z",
        )
        response = self.client.get(reverse("core:search"), {"q": "Masses"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["kind"], "Article")

    def test_search_with_no_query_returns_empty(self):
        response = self.client.get(reverse("core:search"))
        self.assertEqual(response.json(), {"results": []})


class HealthAndErrorViewTests(TestCase):
    def test_health_returns_non_sensitive_ok_response(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_error_views_return_branded_responses(self):
        request = RequestFactory().get("/missing/")
        for view, status in ((views.error_400, 400), (views.error_403, 403), (views.error_404, 404), (views.error_500, 500)):
            response = view(request)
            self.assertEqual(response.status_code, status)
            self.assertContains(response, "Go to homepage", status_code=status)


class GatheringTests(TestCase):
    def test_next_gathering_never_returns_expired_event(self):
        now = timezone.now()
        Gathering.objects.create(
            title="Last week", location="Kigali",
            start_datetime=now - timedelta(days=8), end_datetime=now - timedelta(days=7),
        )
        self.assertIsNone(views._next_gathering())

    def test_next_gathering_returns_earliest_upcoming_event(self):
        now = timezone.now()
        first = Gathering.objects.create(
            title="First", location="Kigali",
            start_datetime=now + timedelta(days=1), end_datetime=now + timedelta(days=1, hours=2),
        )
        Gathering.objects.create(
            title="Later", location="Kigali",
            start_datetime=now + timedelta(days=2), end_datetime=now + timedelta(days=2, hours=2),
        )
        self.assertEqual(views._next_gathering(), first)

    def test_gathering_rejects_end_before_start(self):
        now = timezone.now()
        gathering = Gathering(
            title="Invalid", location="Kigali",
            start_datetime=now, end_datetime=now - timedelta(minutes=1),
        )
        with self.assertRaises(ValidationError):
            gathering.full_clean()


class ProductionSettingsTests(TestCase):
    project_root = Path(__file__).resolve().parents[2]

    def _run_production_check(self, secret_key):
        environment = os.environ.copy()
        environment["ALLOWED_HOSTS"] = "audit.example"
        environment["SECRET_KEY"] = secret_key
        return subprocess.run(
            [sys.executable, "manage.py", "check", "--settings=config.settings.prod"],
            cwd=self.project_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_production_rejects_missing_secret_key(self):
        result = self._run_production_check("")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("strong SECRET_KEY", result.stderr)

    def test_production_rejects_placeholder_secret_key(self):
        result = self._run_production_check("change-me-this-is-not-a-real-production-secret-key-value-123")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("strong SECRET_KEY", result.stderr)
