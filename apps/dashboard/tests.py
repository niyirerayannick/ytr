from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Bookmark, PrayerRequest, Profile, RSVP, Testimony
from apps.articles.models import Article
from apps.core.models import Gathering
from apps.devotions.models import Devotion
from apps.engagement.models import ContactMessage, NewsletterSubscriber
from apps.morning_devotions.models import MorningDevotionSession
from apps.podcasts.models import Episode, PodcastSeries
from apps.videos.models import Video, VideoSeries

from . import services

User = get_user_model()


def make_user(username, role, is_active=True):
    user = User.objects.create_user(username, f"{username}@example.com", "password123", is_active=is_active)
    user.profile.role = role
    user.profile.save()
    return user


class RoleGatingTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin1", Profile.ROLE_ADMIN)
        self.author = make_user("author1", Profile.ROLE_AUTHOR)
        self.member = make_user("member1", Profile.ROLE_MEMBER)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("dashboard:admin"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_member_gets_403_on_admin_dashboard(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("dashboard:admin"))
        self.assertEqual(response.status_code, 403)

    def test_member_gets_403_on_author_dashboard(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("dashboard:author"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_reach_admin_dashboard(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:admin"))
        self.assertEqual(response.status_code, 200)

    def test_home_redirects_by_role(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, reverse("dashboard:author"))


class SignupApprovalTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin1", Profile.ROLE_ADMIN)
        self.pending = make_user("pendingperson", Profile.ROLE_MEMBER, is_active=False)

    def test_approve_signup_activates_user(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:approve_signup", args=[self.pending.id]))
        self.pending.refresh_from_db()
        self.assertTrue(self.pending.is_active)

    def test_reject_signup_deletes_user(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:reject_signup", args=[self.pending.id]))
        self.assertFalse(User.objects.filter(id=self.pending.id).exists())

    def test_member_cannot_approve_signups(self):
        member = make_user("regularmember", Profile.ROLE_MEMBER)
        self.client.force_login(member)
        response = self.client.post(reverse("dashboard:approve_signup", args=[self.pending.id]))
        self.assertEqual(response.status_code, 403)
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.is_active)


class ContentReviewWorkflowTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin1", Profile.ROLE_ADMIN)
        self.author = make_user("author1", Profile.ROLE_AUTHOR)
        self.article = Article.objects.create(
            title_en="Draft Piece", title_rw="Umushinga",
            hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            submitted_by=self.author, status=Article.STATUS_DRAFT,
        )

    def test_author_can_submit_for_review(self):
        self.client.force_login(self.author)
        self.client.post(reverse("dashboard:author_content_submit", args=["article", self.article.id]))
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, Article.STATUS_PENDING)

    def test_author_cannot_edit_once_pending(self):
        # Redirects to the role-based `dashboard:home` router (itself a
        # further redirect to author_home for this role) rather than
        # straight to author_home, since this view is also reachable by
        # Admins now — see docs/admin-command-center.md.
        self.article.submit_for_review(self.author)
        self.client.force_login(self.author)
        response = self.client.get(reverse("dashboard:author_content_edit", args=["article", self.article.id]))
        self.assertRedirects(response, reverse("dashboard:home"), target_status_code=302)

    def test_admin_approve_publishes_article(self):
        self.article.submit_for_review(self.author)
        self.client.force_login(self.admin)
        self.client.post(
            reverse("dashboard:review_content", args=["article", self.article.id]),
            {"action": "approve"},
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, Article.STATUS_PUBLISHED)
        self.assertIsNotNone(self.article.published_at)
        self.assertEqual(self.article.reviewed_by, self.admin)

    def test_admin_reject_requires_note_and_sets_status(self):
        self.article.submit_for_review(self.author)
        self.client.force_login(self.admin)
        self.client.post(
            reverse("dashboard:review_content", args=["article", self.article.id]),
            {"action": "reject", "review_note": "Please add a scripture reference."},
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, Article.STATUS_REJECTED)
        self.assertEqual(self.article.review_note, "Please add a scripture reference.")

    def test_published_article_never_returned_by_author_own_draft_edit(self):
        self.article.approve(self.admin)
        self.client.force_login(self.author)
        response = self.client.get(reverse("dashboard:author_content_edit", args=["article", self.article.id]))
        self.assertRedirects(response, reverse("dashboard:home"), target_status_code=302)


class BookmarkToggleTests(TestCase):
    def setUp(self):
        self.member = make_user("member1", Profile.ROLE_MEMBER)
        self.article = Article.objects.create(
            title_en="An Article", title_rw="Igyanditswe",
            hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            status=Article.STATUS_PUBLISHED, published_at="2024-01-01T00:00:00Z",
        )

    def test_toggle_creates_then_removes_bookmark(self):
        self.client.force_login(self.member)
        url = reverse("dashboard:toggle_bookmark", args=[self.article.id])
        self.client.post(url)
        self.assertTrue(Bookmark.objects.filter(member=self.member, article=self.article).exists())
        self.client.post(url)
        self.assertFalse(Bookmark.objects.filter(member=self.member, article=self.article).exists())

    def test_anonymous_redirected_to_login(self):
        url = reverse("dashboard:toggle_bookmark", args=[self.article.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_bookmark_next_only_allows_internal_url(self):
        self.client.force_login(self.member)
        url = reverse("dashboard:toggle_bookmark", args=[self.article.id])
        for target in ("https://evil.example.com", "//evil.example.com", "http://evil.example.com"):
            response = self.client.post(url, {"next": target})
            self.assertEqual(response.url, self.article.get_absolute_url())

    def test_bookmark_internal_next_and_missing_next_use_safe_destinations(self):
        self.client.force_login(self.member)
        url = reverse("dashboard:toggle_bookmark", args=[self.article.id])
        self.assertEqual(self.client.post(url, {"next": "/articles/"}).url, "/articles/")
        self.assertEqual(self.client.post(url).url, self.article.get_absolute_url())

    def test_rsvp_next_only_allows_internal_url(self):
        self.client.force_login(self.member)
        gathering = Gathering.objects.create(
            title="Friday", location="Kigali",
            start_datetime="2030-01-01T18:00:00Z", end_datetime="2030-01-01T20:00:00Z",
        )
        url = reverse("dashboard:toggle_rsvp", args=[gathering.id])
        response = self.client.post(url, {"next": "//evil.example.com"})
        self.assertEqual(response.url, reverse("core:home"))
        self.assertTrue(RSVP.objects.filter(member=self.member, gathering=gathering).exists())


class MemberDashboardBilingualMediaTilesTests(TestCase):
    """Regression coverage for the "Explore your space" Read/Listen/Watch
    tiles, which used to reference a nonexistent `.title` attribute on
    Episode/Video (only `title_en`/`title_rw` exist) and rendered empty."""

    def setUp(self):
        pod_series = PodcastSeries.objects.create(title_en="Series", title_rw="Urukurikirane")
        self.episode = Episode.objects.create(
            series=pod_series, title_en="English Episode Title", title_rw="Umutwe wa Kinyarwanda",
            status=Episode.STATUS_PUBLISHED,
        )
        vid_series = VideoSeries.objects.create(title_en="Series", title_rw="Urukurikirane")
        self.video = Video.objects.create(
            series=vid_series, title_en="English Video Title", title_rw="Umutwe wa Videwo",
            status=Video.STATUS_PUBLISHED,
        )
        self.article = Article.objects.create(
            title_en="English Article Title", title_rw="Umutwe wa Inyandiko",
            hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            status=Article.STATUS_PUBLISHED,
        )

    def _member(self, preferred_language):
        user = make_user("tileuser_" + preferred_language, Profile.ROLE_MEMBER)
        user.profile.preferred_language = preferred_language
        user.profile.save()
        return user

    def test_english_preference_shows_english_titles(self):
        self.client.force_login(self._member("en"))
        response = self.client.get(reverse("dashboard:member_home"))
        self.assertContains(response, "English Episode Title")
        self.assertContains(response, "English Video Title")
        self.assertContains(response, "English Article Title")

    def test_kinyarwanda_preference_shows_kinyarwanda_titles(self):
        self.client.force_login(self._member("rw"))
        response = self.client.get(reverse("dashboard:member_home"))
        self.assertContains(response, "Umutwe wa Kinyarwanda")
        self.assertContains(response, "Umutwe wa Videwo")
        self.assertContains(response, "Umutwe wa Inyandiko")

    def test_kinyarwanda_preference_falls_back_to_english_when_rw_blank(self):
        self.episode.title_rw = ""
        self.episode.save()
        self.client.force_login(self._member("rw"))
        response = self.client.get(reverse("dashboard:member_home"))
        self.assertContains(response, "English Episode Title")


# =========================================================== Command Center

class CommandCenterAuthorizationTests(TestCase):
    """Every new admin Command Center surface must enforce the same
    anonymous->login, wrong-role->403, admin->200 policy as the rest of the
    dashboard — hiding a sidebar link is never the actual authorization."""

    def setUp(self):
        self.admin = make_user("cc_admin", Profile.ROLE_ADMIN)
        self.author = make_user("cc_author", Profile.ROLE_AUTHOR)
        self.member = make_user("cc_member", Profile.ROLE_MEMBER)

    def test_anonymous_redirected_to_login(self):
        for url in (reverse("dashboard:admin"), reverse("dashboard:content_workspace"), reverse("dashboard:command_search")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn(reverse("accounts:login"), response.url)

    def test_member_gets_403(self):
        self.client.force_login(self.member)
        for url in (reverse("dashboard:admin"), reverse("dashboard:content_workspace"), reverse("dashboard:command_search")):
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_author_gets_403(self):
        self.client.force_login(self.author)
        for url in (reverse("dashboard:admin"), reverse("dashboard:content_workspace"), reverse("dashboard:command_search")):
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_admin_can_reach_every_surface(self):
        self.client.force_login(self.admin)
        for url in (reverse("dashboard:admin"), reverse("dashboard:content_workspace"), reverse("dashboard:command_search")):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_admin_can_now_create_content_directly(self):
        """Deliberate, server-side widening (not just a UI link) — see
        docs/admin-command-center.md — Admins can use the same
        author_content_create/edit/submit views Authors use."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:author_content_create", kwargs={"content_type": "article"}))
        self.assertEqual(response.status_code, 200)


class OverviewKPITests(TestCase):
    def setUp(self):
        self.admin = make_user("kpi_admin", Profile.ROLE_ADMIN)
        self.client.force_login(self.admin)

    def test_published_resources_kpi_counts_across_all_four_types(self):
        Article.objects.create(
            title_en="A", title_rw="A", hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            status=Article.STATUS_PUBLISHED,
        )
        Devotion.objects.create(
            date=timezone.now().date(), verse_ref="Psalm 1:1",
            verse_text_en="v", verse_text_rw="v", reflection_en="r", reflection_rw="r",
            prayer_en="p", prayer_rw="p", status=Devotion.STATUS_PUBLISHED,
        )
        response = self.client.get(reverse("dashboard:admin"))
        kpi_by_label = {kpi["label"]: kpi["value"] for kpi in response.context["kpis"]}
        self.assertEqual(kpi_by_label["Published resources"], 2)

    def test_draft_and_pending_content_excluded_from_published_count(self):
        Article.objects.create(
            title_en="Draft", title_rw="D", hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            status=Article.STATUS_DRAFT,
        )
        response = self.client.get(reverse("dashboard:admin"))
        kpi_by_label = {kpi["label"]: kpi["value"] for kpi in response.context["kpis"]}
        self.assertEqual(kpi_by_label["Published resources"], 0)

    def test_members_kpi_excludes_authors_and_admins(self):
        make_user("member_x", Profile.ROLE_MEMBER)
        response = self.client.get(reverse("dashboard:admin"))
        kpi_by_label = {kpi["label"]: kpi["value"] for kpi in response.context["kpis"]}
        # cc_admin (setUp) is an admin, so only member_x counts as a Member.
        self.assertEqual(kpi_by_label["Members"], 1)

    def test_pending_review_kpi_matches_content_queue(self):
        Article.objects.create(
            title_en="Pending one", title_rw="P", hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            status=Article.STATUS_PENDING,
        )
        response = self.client.get(reverse("dashboard:admin"))
        kpi_by_label = {kpi["label"]: kpi["value"] for kpi in response.context["kpis"]}
        self.assertEqual(kpi_by_label["Pending review"], 1)


class MorningDevotionOverviewTests(TestCase):
    def setUp(self):
        self.admin = make_user("md_admin", Profile.ROLE_ADMIN)
        self.client.force_login(self.admin)

    def test_no_session_shows_schedule_prompt(self):
        response = self.client.get(reverse("dashboard:admin"))
        self.assertContains(response, "No Morning Devotion scheduled yet.")
        self.assertContains(response, "Schedule Morning Devotion")

    def test_finished_session_missing_content_shows_completion_checklist(self):
        now = timezone.now()
        MorningDevotionSession.objects.create(
            title_en="Yesterday's Session", title_rw="Y",
            start_datetime=now - timedelta(hours=25), end_datetime=now - timedelta(hours=24),
            status=MorningDevotionSession.STATUS_PUBLISHED,
        )
        response = self.client.get(reverse("dashboard:admin"))
        self.assertContains(response, "Complete today's devotion")
        self.assertContains(response, "Yesterday&#x27;s Session")

    def test_live_session_shows_join_meet_action(self):
        now = timezone.now()
        MorningDevotionSession.objects.create(
            title_en="Live Now", title_rw="L",
            start_datetime=now - timedelta(minutes=5), end_datetime=now + timedelta(minutes=55),
            meet_url="https://meet.google.com/abc-defg-hij",
            status=MorningDevotionSession.STATUS_PUBLISHED,
        )
        response = self.client.get(reverse("dashboard:admin"))
        self.assertContains(response, "Live Now")
        self.assertContains(response, "Join Meet")
        self.assertContains(response, "https://meet.google.com/abc-defg-hij")


class SensitiveDataNotLeakedOnOverviewTests(TestCase):
    """Prayer requests and contact messages are private — the overview may
    show counts, never the actual private text (section 21/26)."""

    def test_prayer_request_body_never_appears_on_overview(self):
        admin = make_user("privacy_admin", Profile.ROLE_ADMIN)
        member = make_user("privacy_member", Profile.ROLE_MEMBER)
        PrayerRequest.objects.create(member=member, body="A very private and specific prayer need XYZZY123.")
        self.client.force_login(admin)
        response = self.client.get(reverse("dashboard:admin"))
        self.assertNotContains(response, "XYZZY123")
        self.assertContains(response, "1 prayer request unreviewed")

    def test_contact_message_body_never_appears_on_overview(self):
        admin = make_user("privacy_admin2", Profile.ROLE_ADMIN)
        ContactMessage.objects.create(name="Someone", email="a@example.com", message="Secret message body ABCDEF999.")
        self.client.force_login(admin)
        response = self.client.get(reverse("dashboard:admin"))
        self.assertNotContains(response, "ABCDEF999")
        self.assertContains(response, "1 unread contact message")


class ContentWorkspaceFilterTests(TestCase):
    def setUp(self):
        self.admin = make_user("workspace_admin", Profile.ROLE_ADMIN)
        self.client.force_login(self.admin)
        self.published_article = Article.objects.create(
            title_en="Published Piece", title_rw="P", hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            status=Article.STATUS_PUBLISHED,
        )
        self.draft_article = Article.objects.create(
            title_en="Draft Piece", title_rw="", hook_en="h", hook_rw="h", body_en="b", body_rw="",
            status=Article.STATUS_DRAFT,
        )
        series = PodcastSeries.objects.create(title_en="S", title_rw="S")
        self.episode = Episode.objects.create(
            series=series, title_en="Published Episode", title_rw="E", status=Episode.STATUS_PUBLISHED,
        )

    def test_status_filter_excludes_other_statuses(self):
        response = self.client.get(reverse("dashboard:content_workspace"), {"status": "published"})
        titles = [i["title"] for i in response.context["page_obj"]]
        self.assertIn("Published Piece", titles)
        self.assertNotIn("Draft Piece", titles)

    def test_type_filter_restricts_to_one_content_type(self):
        response = self.client.get(reverse("dashboard:content_workspace"), {"type": "article"})
        types = {i["type"] for i in response.context["page_obj"]}
        self.assertEqual(types, {"article"})

    def test_search_matches_title(self):
        response = self.client.get(reverse("dashboard:content_workspace"), {"q": "Published Episode"})
        titles = [i["title"] for i in response.context["page_obj"]]
        self.assertIn("Published Episode", titles)
        self.assertNotIn("Published Piece", titles)

    def test_language_missing_filter_finds_incomplete_translation(self):
        response = self.client.get(reverse("dashboard:content_workspace"), {"language": "missing"})
        titles = [i["title"] for i in response.context["page_obj"]]
        self.assertIn("Draft Piece", titles)
        self.assertNotIn("Published Piece", titles)

    def test_htmx_request_returns_partial_not_full_page(self):
        response = self.client.get(
            reverse("dashboard:content_workspace"), {"status": "published"}, HTTP_HX_REQUEST="true",
        )
        self.assertNotContains(response, "<!DOCTYPE html>")
        self.assertContains(response, "Published Piece")


class CommandSearchTests(TestCase):
    def setUp(self):
        self.admin = make_user("search_admin", Profile.ROLE_ADMIN)
        self.client.force_login(self.admin)
        Article.objects.create(
            title_en="Findable Title", title_rw="F", hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            status=Article.STATUS_DRAFT,  # drafts ARE searchable here — this is an admin tool, not the public search
        )

    def test_finds_draft_content_by_title(self):
        response = self.client.get(reverse("dashboard:command_search"), {"q": "Findable"})
        data = response.json()
        self.assertTrue(any(r["title"] == "Findable Title" for r in data["results"]))

    def test_short_query_returns_no_results(self):
        response = self.client.get(reverse("dashboard:command_search"), {"q": "F"})
        self.assertEqual(response.json()["results"], [])

    def test_non_admin_cannot_use_command_search(self):
        member = make_user("search_member", Profile.ROLE_MEMBER)
        self.client.force_login(member)
        response = self.client.get(reverse("dashboard:command_search"), {"q": "Findable"})
        self.assertEqual(response.status_code, 403)

    def test_results_link_to_django_admin_not_public_urls(self):
        response = self.client.get(reverse("dashboard:command_search"), {"q": "Findable"})
        data = response.json()
        result = next(r for r in data["results"] if r["title"] == "Findable Title")
        self.assertTrue(result["url"].startswith("/admin/"))


class BilingualHealthServiceTests(TestCase):
    def test_complete_bilingual_article_counts_as_complete(self):
        Article.objects.create(
            title_en="A", title_rw="A", hook_en="h", hook_rw="h", body_en="b", body_rw="b",
            status=Article.STATUS_PUBLISHED,
        )
        health = services.bilingual_health()
        self.assertEqual(health["complete"], 1)
        self.assertEqual(health["needs_translation"], 0)

    def test_english_only_article_counts_as_needing_translation(self):
        Article.objects.create(
            title_en="A", title_rw="", hook_en="h", hook_rw="h", body_en="b", body_rw="",
            status=Article.STATUS_PUBLISHED,
        )
        health = services.bilingual_health()
        self.assertEqual(health["en_only"], 1)
        self.assertEqual(health["needs_translation"], 1)

    def test_draft_content_excluded_from_bilingual_health(self):
        Article.objects.create(
            title_en="A", title_rw="", hook_en="h", hook_rw="h", body_en="b", body_rw="",
            status=Article.STATUS_DRAFT,
        )
        health = services.bilingual_health()
        self.assertEqual(health["total"], 0)
