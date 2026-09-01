from django.test import TestCase
from django.urls import reverse

from apps.articles.models import Article
from apps.core.models import SiteSettings


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
