import io

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.core.models import SiteSettings

from . import share_cards
from .models import Devotion

User = get_user_model()


def _make_devotion(**overrides):
    defaults = dict(
        date="2024-01-01",
        verse_ref="Psalm 91:1",
        verse_text_en="He who dwells in the shelter of the Most High.",
        verse_text_rw="Uwiyegereza Isumbabyose.",
        reflection_en="There is a place of hiddenness with God, before the platform.",
        reflection_rw="Hari ahantu h'ibanga hari Imana, mbere y'urwuri.",
        prayer_en="Lord, teach me to dwell.",
        prayer_rw="Mwami, nyigisha kuba.",
        status=Devotion.STATUS_PUBLISHED,
    )
    defaults.update(overrides)
    return Devotion.objects.create(**defaults)


class DevotionModelTests(TestCase):
    def test_slug_is_auto_generated(self):
        devotion = Devotion.objects.create(
            date="2024-01-01", verse_ref="Psalm 46:10",
            verse_text_en="v", verse_text_rw="v",
            reflection_en="r", reflection_rw="r",
            prayer_en="p", prayer_rw="p",
        )
        self.assertTrue(devotion.slug)

    def test_get_absolute_url_uses_slug(self):
        devotion = _make_devotion()
        self.assertEqual(devotion.get_absolute_url(), f"/devotions/{devotion.slug}/")

    def test_has_language_true_when_both_fields_present(self):
        devotion = _make_devotion()
        self.assertTrue(devotion.has_language("en"))
        self.assertTrue(devotion.has_language("rw"))

    def test_has_language_false_when_translation_missing(self):
        devotion = _make_devotion(verse_text_rw="", reflection_rw="")
        self.assertFalse(devotion.has_language("rw"))
        self.assertTrue(devotion.has_language("en"))

    def test_has_language_false_for_unknown_language(self):
        devotion = _make_devotion()
        self.assertFalse(devotion.has_language("fr"))

    def test_share_excerpt_returns_full_text_when_short(self):
        devotion = _make_devotion(reflection_en="Short reflection text.")
        self.assertEqual(devotion.share_excerpt("en"), "Short reflection text.")

    def test_share_excerpt_truncates_long_text_with_ellipsis(self):
        long_text = " ".join(f"word{i}" for i in range(80))
        devotion = _make_devotion(reflection_en=long_text)
        excerpt = devotion.share_excerpt("en", max_words=10)
        self.assertTrue(excerpt.endswith("…"))
        self.assertEqual(len(excerpt.rstrip("…").split()), 10)

    def test_share_excerpt_does_not_fall_back_across_languages(self):
        devotion = _make_devotion(reflection_en="English only reflection.", reflection_rw="")
        # No machine-translation fallback: an empty rw field stays empty,
        # it never silently substitutes the English text under an rw label.
        self.assertEqual(devotion.share_excerpt("rw"), "")


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

    def test_anonymous_devotion_list_is_marked_cacheable_for_offline_reading(self):
        response = self.client.get(reverse("devotions:list"))
        self.assertEqual(response.headers.get("X-YTR-Public-Cache"), "1")

    def test_authenticated_devotion_list_is_never_marked_cacheable(self):
        User.objects.create_user("reader", "reader@example.com", "password123", is_active=True)
        self.client.force_login(User.objects.get(username="reader"))
        response = self.client.get(reverse("devotions:list"))
        self.assertNotIn("X-YTR-Public-Cache", response.headers)

    def test_paginated_devotion_list_is_never_marked_cacheable(self):
        response = self.client.get(reverse("devotions:list"), {"page": "1"})
        self.assertNotIn("X-YTR-Public-Cache", response.headers)


class DevotionDetailViewTests(TestCase):
    def test_published_devotion_detail_loads_with_canonical_share_url(self):
        devotion = _make_devotion()
        response = self.client.get(devotion.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, devotion.verse_ref)
        canonical_url = f"http://testserver{devotion.get_absolute_url()}"
        self.assertContains(response, f'<link rel="canonical" href="{canonical_url}">')
        self.assertContains(response, '<meta property="og:type" content="article">')
        self.assertContains(response, f'<meta property="og:url" content="{canonical_url}">')

    def test_draft_devotion_detail_is_not_exposed(self):
        devotion = _make_devotion(status=Devotion.STATUS_DRAFT, date="2024-02-01")
        response = self.client.get(f"/devotions/{devotion.slug}/")
        self.assertEqual(response.status_code, 404)

    def test_pending_devotion_detail_is_not_exposed(self):
        devotion = _make_devotion(status=Devotion.STATUS_PENDING, date="2024-02-02")
        response = self.client.get(f"/devotions/{devotion.slug}/")
        self.assertEqual(response.status_code, 404)

    def test_rejected_devotion_detail_is_not_exposed(self):
        devotion = _make_devotion(status=Devotion.STATUS_REJECTED, date="2024-02-03")
        response = self.client.get(f"/devotions/{devotion.slug}/")
        self.assertEqual(response.status_code, 404)

    def test_unknown_slug_is_404(self):
        response = self.client.get("/devotions/no-such-devotion/")
        self.assertEqual(response.status_code, 404)

    def test_detail_page_shares_the_devotion_data_payload_for_js(self):
        devotion = _make_devotion()
        response = self.client.get(devotion.get_absolute_url())
        self.assertContains(response, "devotionShareData")
        self.assertContains(response, devotion.verse_ref)


class DevotionShareImageViewTests(TestCase):
    def _url(self, devotion, **params):
        base = reverse("devotions:share_image", kwargs={"slug": devotion.slug})
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            return f"{base}?{query}"
        return base

    def test_valid_request_returns_png_at_expected_size(self):
        devotion = _make_devotion()
        response = self.client.get(self._url(devotion, lang="en", format="square"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(image.size, (1080, 1080))

    def test_defaults_to_english_square_when_no_params_given(self):
        devotion = _make_devotion()
        response = self.client.get(self._url(devotion))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_rw_language_renders_when_translation_present(self):
        devotion = _make_devotion()
        response = self.client.get(self._url(devotion, lang="rw", format="square"))
        self.assertEqual(response.status_code, 200)

    def test_invalid_language_is_rejected(self):
        devotion = _make_devotion()
        response = self.client.get(self._url(devotion, lang="fr", format="square"))
        self.assertEqual(response.status_code, 400)

    def test_invalid_format_is_rejected(self):
        devotion = _make_devotion()
        response = self.client.get(self._url(devotion, lang="en", format="banner"))
        self.assertEqual(response.status_code, 400)

    def test_missing_translation_is_rejected_not_faked(self):
        devotion = _make_devotion(verse_text_rw="", reflection_rw="")
        response = self.client.get(self._url(devotion, lang="rw", format="square"))
        self.assertEqual(response.status_code, 400)

    def test_unpublished_devotion_share_image_is_not_exposed(self):
        devotion = _make_devotion(status=Devotion.STATUS_DRAFT, date="2024-03-01")
        response = self.client.get(self._url(devotion, lang="en", format="square"))
        self.assertEqual(response.status_code, 404)

    def test_share_image_is_publicly_cacheable(self):
        devotion = _make_devotion()
        response = self.client.get(self._url(devotion, lang="en", format="square"))
        self.assertIn("public", response["Cache-Control"])
        self.assertTrue(response.has_header("ETag"))


class ShareCardFooterLinesTests(TestCase):
    def test_all_lines_present_when_configured(self):
        settings_obj = SiteSettings(
            contact_email="hello@youthtimerevival.rw",
            phone="+250 788 000 000",
            website_url="https://youthtimerevival.rw",
        )
        lines = share_cards.footer_lines(settings_obj)
        self.assertEqual(lines, ["youthtimerevival.rw", "hello@youthtimerevival.rw", "+250 788 000 000"])

    def test_missing_fields_are_omitted_not_faked(self):
        settings_obj = SiteSettings(contact_email="", phone="", website_url="")
        self.assertEqual(share_cards.footer_lines(settings_obj), [])

    def test_partial_configuration_only_shows_configured_fields(self):
        settings_obj = SiteSettings(contact_email="hello@youthtimerevival.rw", phone="", website_url="")
        self.assertEqual(share_cards.footer_lines(settings_obj), ["hello@youthtimerevival.rw"])

    def test_website_url_strips_scheme(self):
        settings_obj = SiteSettings(contact_email="", phone="", website_url="https://youthtimerevival.rw/")
        self.assertEqual(share_cards.footer_lines(settings_obj), ["youthtimerevival.rw"])
