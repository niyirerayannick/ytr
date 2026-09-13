import io
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from apps.podcasts.models import Episode, PodcastSeries
from apps.videos.models import Video, VideoSeries

from .models import MorningDevotionSession
from .validators import validate_meet_url

User = get_user_model()


def _make_session(**overrides):
    now = timezone.now()
    defaults = dict(
        title_en="Walking by Faith",
        title_rw="Kugendera mu Kwizera",
        scripture_reference="Hebrews 11:1",
        start_datetime=now + timedelta(days=1),
        end_datetime=now + timedelta(days=1, hours=1),
        status=MorningDevotionSession.STATUS_PUBLISHED,
    )
    defaults.update(overrides)
    return MorningDevotionSession.objects.create(**defaults)


def _make_published_episode():
    series = PodcastSeries.objects.create(title_en="Series", title_rw="Series")
    return Episode.objects.create(
        series=series, title_en="Recording", title_rw="Recording",
        duration="18 min", audio_url="https://example.com/audio.mp3",
        status=Episode.STATUS_PUBLISHED,
    )


def _make_published_video():
    series = VideoSeries.objects.create(title_en="Series", title_rw="Series")
    return Video.objects.create(
        series=series, title_en="Recording", title_rw="Recording",
        youtube_url="https://youtu.be/dQw4w9WgXcQ",
        status=Video.STATUS_PUBLISHED,
    )


class MeetUrlValidatorTests(TestCase):
    def test_blank_is_allowed(self):
        validate_meet_url("")  # no exception

    def test_valid_meet_url_passes(self):
        validate_meet_url("https://meet.google.com/abc-defg-hij")  # no exception

    def test_http_scheme_rejected(self):
        with self.assertRaises(ValidationError):
            validate_meet_url("http://meet.google.com/abc-defg-hij")

    def test_non_meet_host_rejected(self):
        with self.assertRaises(ValidationError):
            validate_meet_url("https://zoom.us/j/123456")

    def test_root_path_rejected(self):
        with self.assertRaises(ValidationError):
            validate_meet_url("https://meet.google.com/")

    def test_lookalike_host_rejected(self):
        with self.assertRaises(ValidationError):
            validate_meet_url("https://meet.google.com.evil.com/abc-defg-hij")


class SessionStateBoundaryTests(TestCase):
    """Exact-instant boundary checks (not just "a few minutes either side"),
    per docs/roadmaps/digital-discipleship-platform.md's Phase C state
    machine: upcoming / starting_soon / live / finished must each own their
    boundary consistently, using timezone-aware comparisons throughout (no
    hardcoded UTC offset — Africa/Kigali has no DST, but the comparison
    itself works the same regardless of TIME_ZONE since both operands are
    timezone-aware)."""

    def test_exactly_at_the_15_minute_window_is_starting_soon_not_upcoming(self):
        now = timezone.now()
        session = _make_session(start_datetime=now + timedelta(minutes=15), end_datetime=now + timedelta(minutes=75))
        self.assertEqual(session.session_state, "starting_soon")

    def test_one_second_before_the_15_minute_window_is_upcoming(self):
        now = timezone.now()
        session = _make_session(
            start_datetime=now + timedelta(minutes=15, seconds=1), end_datetime=now + timedelta(minutes=75, seconds=1),
        )
        self.assertEqual(session.session_state, "upcoming")

    def test_exactly_at_start_time_is_live(self):
        # `session_state` calls timezone.now() itself, so asserting an exact
        # equality boundary against the real clock would race — by the time
        # the property runs, real time has already moved past `now`. Freeze
        # it instead of relying on wall-clock timing being fast enough.
        now = timezone.now()
        session = _make_session(start_datetime=now, end_datetime=now + timedelta(hours=1))
        with mock.patch("apps.morning_devotions.models.timezone.now", return_value=now):
            self.assertEqual(session.session_state, "live")

    def test_exactly_at_end_time_is_still_live(self):
        now = timezone.now()
        session = _make_session(start_datetime=now - timedelta(hours=1), end_datetime=now)
        with mock.patch("apps.morning_devotions.models.timezone.now", return_value=now):
            self.assertEqual(session.session_state, "live")

    def test_one_second_after_end_time_is_finished(self):
        now = timezone.now()
        session = _make_session(start_datetime=now - timedelta(hours=1, seconds=1), end_datetime=now - timedelta(seconds=1))
        self.assertEqual(session.session_state, "finished")


class SessionStateTests(TestCase):
    def test_far_future_session_is_upcoming(self):
        session = _make_session(
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=1),
        )
        self.assertEqual(session.session_state, "upcoming")
        self.assertFalse(session.can_join_live)

    def test_session_starting_within_window_is_starting_soon(self):
        session = _make_session(
            start_datetime=timezone.now() + timedelta(minutes=5),
            end_datetime=timezone.now() + timedelta(minutes=65),
        )
        self.assertEqual(session.session_state, "starting_soon")

    def test_session_in_progress_is_live(self):
        session = _make_session(
            start_datetime=timezone.now() - timedelta(minutes=10),
            end_datetime=timezone.now() + timedelta(minutes=50),
        )
        self.assertEqual(session.session_state, "live")

    def test_session_after_end_is_finished(self):
        session = _make_session(
            start_datetime=timezone.now() - timedelta(hours=2),
            end_datetime=timezone.now() - timedelta(hours=1),
        )
        self.assertEqual(session.session_state, "finished")
        self.assertFalse(session.can_join_live)

    def test_can_join_live_requires_meet_url(self):
        session = _make_session(
            start_datetime=timezone.now() - timedelta(minutes=5),
            end_datetime=timezone.now() + timedelta(minutes=55),
            meet_url="",
        )
        self.assertEqual(session.session_state, "live")
        self.assertFalse(session.can_join_live)

    def test_can_join_live_true_when_live_with_meet_url(self):
        session = _make_session(
            start_datetime=timezone.now() - timedelta(minutes=5),
            end_datetime=timezone.now() + timedelta(minutes=55),
            meet_url="https://meet.google.com/abc-defg-hij",
        )
        self.assertTrue(session.can_join_live)

    def test_end_before_start_is_rejected_by_clean(self):
        session = MorningDevotionSession(
            title_en="Bad", title_rw="Bad",
            start_datetime=timezone.now(),
            end_datetime=timezone.now() - timedelta(hours=1),
        )
        with self.assertRaises(ValidationError):
            session.full_clean()


class MediaAvailabilityTests(TestCase):
    def test_has_audio_false_without_recording(self):
        session = _make_session()
        self.assertFalse(session.has_audio)
        self.assertEqual(session.audio_duration, "")

    def test_has_audio_true_with_published_episode(self):
        episode = _make_published_episode()
        session = _make_session(recording_episode=episode)
        self.assertTrue(session.has_audio)
        self.assertEqual(session.audio_duration, "18 min")

    def test_has_audio_false_when_episode_not_published(self):
        episode = _make_published_episode()
        episode.status = Episode.STATUS_DRAFT
        episode.save()
        session = _make_session(recording_episode=episode)
        self.assertFalse(session.has_audio)

    def test_has_video_true_with_published_video(self):
        video = _make_published_video()
        session = _make_session(recording_video=video)
        self.assertTrue(session.has_video)

    def test_has_summary_false_when_blank(self):
        session = _make_session()
        self.assertFalse(session.has_summary)

    def test_has_summary_true_when_either_language_present(self):
        session = _make_session(summary_en="Great session today.")
        self.assertTrue(session.has_summary)

    def test_has_any_content_false_with_nothing_attached(self):
        session = _make_session()
        self.assertFalse(session.has_any_content)

    def test_has_any_content_true_with_only_a_summary(self):
        session = _make_session(summary_en="Great session today.")
        self.assertTrue(session.has_any_content)


class CurrentOrNextTests(TestCase):
    """Priority ladder used by both the homepage and My YTR:
    live > starting soon > next upcoming > latest finished-with-content > None."""

    def test_live_session_is_preferred_over_upcoming(self):
        now = timezone.now()
        live = _make_session(start_datetime=now - timedelta(minutes=5), end_datetime=now + timedelta(minutes=55))
        _make_session(start_datetime=now + timedelta(days=1), end_datetime=now + timedelta(days=1, hours=1))
        self.assertEqual(MorningDevotionSession.current_or_next(), live)

    def test_starting_soon_session_is_preferred_over_later_upcoming(self):
        now = timezone.now()
        soon = _make_session(start_datetime=now + timedelta(minutes=5), end_datetime=now + timedelta(minutes=65))
        _make_session(start_datetime=now + timedelta(days=1), end_datetime=now + timedelta(days=1, hours=1))
        self.assertEqual(MorningDevotionSession.current_or_next(), soon)

    def test_earliest_upcoming_session_is_selected_when_none_are_live(self):
        now = timezone.now()
        first = _make_session(start_datetime=now + timedelta(days=1), end_datetime=now + timedelta(days=1, hours=1))
        _make_session(start_datetime=now + timedelta(days=2), end_datetime=now + timedelta(days=2, hours=1))
        self.assertEqual(MorningDevotionSession.current_or_next(), first)

    def test_finished_session_with_content_is_selected_when_nothing_upcoming(self):
        now = timezone.now()
        finished = _make_session(
            start_datetime=now - timedelta(days=1, hours=1), end_datetime=now - timedelta(days=1),
            summary_en="Recap of yesterday's session.",
        )
        self.assertEqual(MorningDevotionSession.current_or_next(), finished)

    def test_finished_session_with_no_content_is_skipped_for_an_earlier_one_that_has_it(self):
        now = timezone.now()
        with_content = _make_session(
            start_datetime=now - timedelta(days=2, hours=1), end_datetime=now - timedelta(days=2),
            summary_en="Older, but has a summary.",
        )
        _make_session(
            start_datetime=now - timedelta(days=1, hours=1), end_datetime=now - timedelta(days=1),
        )  # more recent, but nothing attached yet
        self.assertEqual(MorningDevotionSession.current_or_next(), with_content)

    def test_returns_none_when_every_finished_session_lacks_content(self):
        now = timezone.now()
        _make_session(start_datetime=now - timedelta(days=1, hours=1), end_datetime=now - timedelta(days=1))
        self.assertIsNone(MorningDevotionSession.current_or_next())

    def test_returns_none_with_no_sessions_at_all(self):
        self.assertIsNone(MorningDevotionSession.current_or_next())

    def test_draft_and_cancelled_sessions_are_never_selected(self):
        now = timezone.now()
        _make_session(
            status=MorningDevotionSession.STATUS_DRAFT,
            start_datetime=now - timedelta(minutes=5), end_datetime=now + timedelta(minutes=55),
        )
        _make_session(
            status=MorningDevotionSession.STATUS_CANCELLED,
            start_datetime=now + timedelta(days=1), end_datetime=now + timedelta(days=1, hours=1),
        )
        self.assertIsNone(MorningDevotionSession.current_or_next())


class MorningDevotionListViewTests(TestCase):
    def test_published_session_appears_in_list(self):
        _make_session()
        response = self.client.get(reverse("morning_devotions:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Walking by Faith")

    def test_draft_session_does_not_appear_in_list(self):
        _make_session(status=MorningDevotionSession.STATUS_DRAFT, title_en="Hidden Draft")
        response = self.client.get(reverse("morning_devotions:list"))
        self.assertNotContains(response, "Hidden Draft")

    def test_cancelled_session_does_not_appear_in_list(self):
        _make_session(status=MorningDevotionSession.STATUS_CANCELLED, title_en="Cancelled One")
        response = self.client.get(reverse("morning_devotions:list"))
        self.assertNotContains(response, "Cancelled One")

    def test_language_filter_excludes_non_matching_language(self):
        _make_session(title_en="English Only", language=MorningDevotionSession.LANGUAGE_EN)
        _make_session(title_en="Kinyarwanda Only", language=MorningDevotionSession.LANGUAGE_RW,
                      start_datetime=timezone.now() + timedelta(days=2),
                      end_datetime=timezone.now() + timedelta(days=2, hours=1))
        response = self.client.get(reverse("morning_devotions:list"), {"filter": "en"})
        self.assertContains(response, "English Only")
        self.assertNotContains(response, "Kinyarwanda Only")


class MorningDevotionDetailViewTests(TestCase):
    def test_published_session_detail_loads_with_canonical_and_og(self):
        session = _make_session()
        response = self.client.get(session.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Walking by Faith")
        canonical_url = f"http://testserver{session.get_absolute_url()}"
        self.assertContains(response, f'<link rel="canonical" href="{canonical_url}">')
        self.assertContains(response, '<meta property="og:type" content="article">')

    def test_draft_session_detail_is_not_exposed(self):
        session = _make_session(status=MorningDevotionSession.STATUS_DRAFT)
        response = self.client.get(f"/morning-devotions/{session.slug}/")
        self.assertEqual(response.status_code, 404)

    def test_cancelled_session_detail_is_not_exposed(self):
        session = _make_session(status=MorningDevotionSession.STATUS_CANCELLED)
        response = self.client.get(f"/morning-devotions/{session.slug}/")
        self.assertEqual(response.status_code, 404)

    def test_join_live_button_only_shown_when_live_or_starting_soon(self):
        session = _make_session(
            start_datetime=timezone.now() + timedelta(days=5),
            end_datetime=timezone.now() + timedelta(days=5, hours=1),
            meet_url="https://meet.google.com/abc-defg-hij",
        )
        response = self.client.get(session.get_absolute_url())
        self.assertNotContains(response, "Join Live")

    def test_listen_panel_shown_when_audio_available(self):
        episode = _make_published_episode()
        session = _make_session(recording_episode=episode)
        response = self.client.get(session.get_absolute_url())
        self.assertContains(response, "md-audio")

    def test_no_listen_panel_when_no_audio(self):
        session = _make_session()
        response = self.client.get(session.get_absolute_url())
        self.assertNotContains(response, "md-audio")

    def test_detail_page_shares_data_payload_for_js(self):
        session = _make_session()
        response = self.client.get(session.get_absolute_url())
        self.assertContains(response, "morningDevotionShareData")


class MorningDevotionCoverViewTests(TestCase):
    def _url(self, session, **params):
        base = reverse("morning_devotions:cover", kwargs={"slug": session.slug})
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            return f"{base}?{query}"
        return base

    def test_valid_request_returns_png_at_expected_size(self):
        session = _make_session()
        response = self.client.get(self._url(session, format="square"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(image.size, (1080, 1080))

    def test_invalid_format_is_rejected(self):
        session = _make_session()
        response = self.client.get(self._url(session, format="story"))
        self.assertEqual(response.status_code, 400)

    def test_unpublished_session_cover_is_not_exposed(self):
        session = _make_session(status=MorningDevotionSession.STATUS_DRAFT)
        response = self.client.get(self._url(session))
        self.assertEqual(response.status_code, 404)

    def test_cover_is_publicly_cacheable(self):
        session = _make_session()
        response = self.client.get(self._url(session))
        self.assertIn("public", response["Cache-Control"])
        self.assertTrue(response.has_header("ETag"))


class MemberDashboardMorningDevotionTests(TestCase):
    def test_upcoming_session_shows_on_member_dashboard(self):
        _make_session(title_en="Dashboard Session")
        User.objects.create_user("reader", "reader@example.com", "password123", is_active=True)
        self.client.force_login(User.objects.get(username="reader"))
        response = self.client.get(reverse("dashboard:member_home"))
        self.assertContains(response, "Dashboard Session")

    def test_no_session_shows_empty_state(self):
        User.objects.create_user("reader2", "reader2@example.com", "password123", is_active=True)
        self.client.force_login(User.objects.get(username="reader2"))
        response = self.client.get(reverse("dashboard:member_home"))
        self.assertContains(response, "No Morning Devotion is scheduled yet.")
