from datetime import timedelta
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.articles.models import Article
from apps.core.models import Gathering, SiteSettings
from apps.morning_devotions.models import MorningDevotionSession
from . import views

User = get_user_model()


class HomeViewTests(TestCase):
    def test_home_loads(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Youth Time Revival")
        self.assertContains(response, "Morning Devotion")

    def test_home_shows_featured_articles(self):
        Article.objects.create(
            title_en="Test Article", title_rw="Ikizamini",
            hook_en="hook en", hook_rw="hook rw",
            body_en="Paragraph one.", body_rw="Paragraph rw.",
            is_featured=True, status=Article.STATUS_PUBLISHED, published_at="2024-01-01T00:00:00Z",
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Test Article")

    def test_home_shows_live_morning_devotion_join_link(self):
        """The homepage's "Morning Devotion" card is powered by the real
        MorningDevotionSession model, not the generic Gathering + a raw
        SiteSettings URL — see docs/morning-devotion.md."""
        now = timezone.now()
        MorningDevotionSession.objects.create(
            title_en="Walking by Faith", title_rw="Kugendera mu Kwizera",
            start_datetime=now - timedelta(minutes=5), end_datetime=now + timedelta(minutes=55),
            meet_url="https://meet.google.com/abc-defg-hij",
            status=MorningDevotionSession.STATUS_PUBLISHED,
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Join Morning Devotion")
        self.assertContains(response, "https://meet.google.com/abc-defg-hij")
        self.assertContains(response, "Walking by Faith")

    def test_home_upcoming_morning_devotion_has_no_join_link_yet(self):
        now = timezone.now()
        MorningDevotionSession.objects.create(
            title_en="Next Week Session", title_rw="Isengesho ry'Icyumweru Gitaha",
            start_datetime=now + timedelta(days=3), end_datetime=now + timedelta(days=3, hours=1),
            meet_url="https://meet.google.com/abc-defg-hij",
            status=MorningDevotionSession.STATUS_PUBLISHED,
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Next Week Session")
        self.assertNotContains(response, "Join Morning Devotion")

    def test_home_with_no_morning_devotion_shows_empty_state(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "No Morning Devotion scheduled yet")

    def test_home_gathering_renders_in_its_own_section_not_as_morning_devotion(self):
        """A Gathering (fellowship/community event) must never masquerade as
        the Morning Devotion card — they're separate concepts with separate
        homepage sections now."""
        now = timezone.now() + timedelta(hours=1)
        Gathering.objects.create(
            title="Friday Fellowship Night", location="Kigali",
            start_datetime=now, end_datetime=now + timedelta(hours=2),
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Upcoming Gathering")
        self.assertContains(response, "Friday Fellowship Night")
        # The empty-state copy for Morning Devotion still shows, since the
        # Gathering above must not be presented as if it were one.
        self.assertContains(response, "No Morning Devotion scheduled yet")

    def test_home_with_no_gathering_omits_the_gathering_section(self):
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "Upcoming Gathering")


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


class MarkPublicCacheableTests(TestCase):
    """Direct unit coverage of the header contract, independent of any one view.

    apps.articles.views and apps.devotions.views are the only current callers,
    but this locks the helper's own behaviour down so a future caller can't
    accidentally mark an authenticated response cacheable by the worker.
    """

    def setUp(self):
        from apps.core.pwa import PUBLIC_CACHE_HEADER, mark_public_cacheable

        self.header = PUBLIC_CACHE_HEADER
        self.mark = mark_public_cacheable
        self.factory = RequestFactory()

    def test_anonymous_request_is_marked_cacheable(self):
        from django.contrib.auth.models import AnonymousUser
        from django.http import HttpResponse

        request = self.factory.get("/articles/some-article/")
        request.user = AnonymousUser()
        response = self.mark(HttpResponse("ok"), request)
        self.assertEqual(response[self.header], "1")

    def test_authenticated_request_is_never_marked_cacheable(self):
        from django.http import HttpResponse

        user = User.objects.create_user("cache-guard", "cache-guard@example.com", "password123", is_active=True)
        request = self.factory.get("/articles/some-article/")
        request.user = user
        response = self.mark(HttpResponse("ok"), request)
        self.assertNotIn(self.header, response)


class PwaManifestTests(TestCase):
    def test_manifest_file_exists_and_is_valid_json(self):
        manifest_path = finders.find("manifest.webmanifest")
        self.assertIsNotNone(manifest_path, "static/manifest.webmanifest must exist")
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["name"], "Youth Time Revival")
        self.assertEqual(manifest["short_name"], "YTR")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["start_url"], "/")

    def test_manifest_declares_required_icon_sizes_and_a_maskable_variant(self):
        manifest_path = finders.find("manifest.webmanifest")
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)
        sizes = {icon["sizes"] for icon in manifest["icons"]}
        purposes = {icon.get("purpose") for icon in manifest["icons"]}
        self.assertIn("192x192", sizes)
        self.assertIn("512x512", sizes)
        self.assertIn("maskable", purposes)
        for icon in manifest["icons"]:
            self.assertIsNotNone(finders.find(icon["src"].lstrip("/").removeprefix("static/")))

    def test_webmanifest_extension_resolves_to_the_correct_mime_type(self):
        content_type, _ = mimetypes.guess_type("manifest.webmanifest")
        self.assertEqual(content_type, "application/manifest+json")


class ServiceWorkerViewTests(TestCase):
    def test_service_worker_is_served_from_the_origin_root(self):
        response = self.client.get("/service-worker.js")
        self.assertEqual(response.status_code, 200)

    def test_service_worker_has_a_javascript_content_type(self):
        response = self.client.get("/service-worker.js")
        self.assertIn("javascript", response.headers["Content-Type"])

    def test_service_worker_allows_full_site_scope(self):
        response = self.client.get("/service-worker.js")
        self.assertEqual(response.headers.get("Service-Worker-Allowed"), "/")

    def test_service_worker_source_treats_dashboard_accounts_and_admin_as_private(self):
        response = self.client.get("/service-worker.js")
        body = response.content.decode("utf-8")
        self.assertIn("dashboard", body)
        self.assertIn("accounts", body)
        self.assertIn("admin", body)
        self.assertIn("isPrivatePath", body)

    def test_service_worker_shell_list_resolves_static_urls(self):
        response = self.client.get("/service-worker.js")
        body = response.content.decode("utf-8")
        self.assertIn("/static/css/", body)
        self.assertIn("/static/js/site", body)
        self.assertIn("/static/offline.html", body)


class OfflineFallbackTests(TestCase):
    def test_offline_page_exists_and_is_branded(self):
        offline_path = finders.find("offline.html")
        self.assertIsNotNone(offline_path, "static/offline.html must exist")
        with open(offline_path, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("Youth Time Revival", content)
        self.assertIn("You're offline", content)


class BaseTemplatePwaMetadataTests(TestCase):
    def test_home_page_includes_manifest_link_and_theme_color(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, 'rel="manifest"')
        self.assertContains(response, 'name="theme-color" content="#1a1230"')
        self.assertContains(response, 'rel="apple-touch-icon"')

    def test_home_page_includes_install_and_update_partials(self):
        # The install promotion and update banner are for every visitor, installed
        # or not, authenticated or not — installing the app is orthogonal to login.
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, 'id="pwaInstallCard"')
        self.assertContains(response, 'id="pwaUpdate"')

    def test_dashboard_shell_does_not_include_the_public_install_card(self):
        # The dashboard renders its own shell template (templates/dashboard/_shell.html)
        # rather than extending base.html, so Phase A's public install UI has no
        # reason to appear there and was not added to it.
        User.objects.create_user("member", "member@example.com", "password123", is_active=True)
        self.client.force_login(User.objects.get(username="member"))
        response = self.client.get(reverse("dashboard:home"), follow=True)
        self.assertNotContains(response, "pwa-install-section")


class MemberBottomNavAuthBoundaryTests(TestCase):
    """The app-style bottom nav is for the authenticated My YTR experience only.

    An installed-but-logged-out visitor must see the ordinary public site, not
    a half-authenticated app shell — "installed" and "authenticated" are
    independent states. The check is on the rendered HTML (the template's
    `{% if request.user.is_authenticated %}` removes the markup entirely), not
    a CSS class, so there's nothing for a logged-out visitor to unhide via
    devtools or a slow stylesheet load.
    """

    def test_anonymous_visitor_does_not_receive_the_member_bottom_nav(self):
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "pwa-bottom-nav")
        self.assertNotContains(response, "pwaMoreSheet")

    def test_anonymous_visitor_sees_login_and_register_entry_points(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, reverse("accounts:login"))
        self.assertContains(response, reverse("accounts:register"))

    def test_authenticated_member_receives_the_bottom_nav_with_expected_destinations(self):
        User.objects.create_user("member2", "member2@example.com", "password123", is_active=True)
        self.client.force_login(User.objects.get(username="member2"))
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, 'class="pwa-bottom-nav"')
        self.assertContains(response, reverse("dashboard:member_home"))
        self.assertContains(response, reverse("devotions:list"))
        self.assertContains(response, reverse("podcasts:list"))
        self.assertContains(response, reverse("videos:list"))
        self.assertContains(response, 'id="pwaMoreSheet"')
        self.assertContains(response, reverse("library:list"))
        self.assertContains(response, reverse("accounts:logout"))


class BilingualFieldHelperTests(TestCase):
    def test_english_reads_en_field(self):
        from apps.core.i18n import bilingual_field

        obj = SimpleNamespace(title_en="English", title_rw="Kinyarwanda")
        self.assertEqual(bilingual_field(obj, "title", "en"), "English")

    def test_kinyarwanda_reads_rw_field(self):
        from apps.core.i18n import bilingual_field

        obj = SimpleNamespace(title_en="English", title_rw="Kinyarwanda")
        self.assertEqual(bilingual_field(obj, "title", "rw"), "Kinyarwanda")

    def test_kinyarwanda_falls_back_to_english_when_blank(self):
        from apps.core.i18n import bilingual_field

        obj = SimpleNamespace(title_en="English", title_rw="")
        self.assertEqual(bilingual_field(obj, "title", "rw"), "English")

    def test_viewer_language_defaults_to_english_without_profile(self):
        from apps.core.i18n import viewer_language

        self.assertEqual(viewer_language(SimpleNamespace()), "en")

    def test_viewer_language_reads_profile_preference(self):
        from apps.core.i18n import viewer_language

        user = SimpleNamespace(profile=SimpleNamespace(preferred_language="rw"))
        self.assertEqual(viewer_language(user), "rw")
