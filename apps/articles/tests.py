from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Article

User = get_user_model()


class ArticleModelTests(TestCase):
    def test_slug_is_auto_generated(self):
        article = Article.objects.create(
            title_en="Sent, Not Hidden", title_rw="Twoherejwe",
            hook_en="hook", hook_rw="hook",
            body_en="Body.", body_rw="Body.",
            status=Article.STATUS_PUBLISHED, published_at="2024-01-01T00:00:00Z",
        )
        self.assertEqual(article.slug, "sent-not-hidden")

    def test_related_articles_excludes_self(self):
        a1 = Article.objects.create(
            title_en="First", title_rw="Mbere", hook_en="h", hook_rw="h",
            body_en="b", body_rw="b",
            status=Article.STATUS_PUBLISHED, published_at="2024-01-01T00:00:00Z",
        )
        a2 = Article.objects.create(
            title_en="Second", title_rw="Kabiri", hook_en="h", hook_rw="h",
            body_en="b", body_rw="b",
            status=Article.STATUS_PUBLISHED, published_at="2024-01-02T00:00:00Z",
        )
        related = list(a1.related_articles())
        self.assertIn(a2, related)
        self.assertNotIn(a1, related)

    def test_draft_is_excluded_from_related_articles(self):
        a1 = Article.objects.create(
            title_en="First", title_rw="Mbere", hook_en="h", hook_rw="h",
            body_en="b", body_rw="b",
            status=Article.STATUS_PUBLISHED, published_at="2024-01-01T00:00:00Z",
        )
        Article.objects.create(
            title_en="Draft One", title_rw="Umushinga", hook_en="h", hook_rw="h",
            body_en="b", body_rw="b", status=Article.STATUS_DRAFT,
        )
        related = list(a1.related_articles())
        self.assertEqual(related, [])


class ArticleViewTests(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title_en="Not in the Masses", title_rw="Ntibiri mu Bwinshi",
            hook_en="hook", hook_rw="hook",
            body_en="Paragraph one.\n\nParagraph two.", body_rw="Paragraph rw.",
            status=Article.STATUS_PUBLISHED, published_at="2024-01-01T00:00:00Z",
        )

    def test_article_list_loads(self):
        response = self.client.get(reverse("articles:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not in the Masses")

    def test_article_detail_loads(self):
        response = self.client.get(self.article.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paragraph one.")

    def test_article_detail_404_for_unknown_slug(self):
        response = self.client.get(reverse("articles:detail", kwargs={"slug": "does-not-exist"}))
        self.assertEqual(response.status_code, 404)

    def test_draft_article_404s_on_public_detail_page(self):
        draft = Article.objects.create(
            title_en="Draft Article", title_rw="Umushinga", hook_en="h", hook_rw="h",
            body_en="b", body_rw="b", status=Article.STATUS_DRAFT,
        )
        response = self.client.get(draft.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_pending_article_not_listed_publicly(self):
        Article.objects.create(
            title_en="Pending Article", title_rw="Umushinga", hook_en="h", hook_rw="h",
            body_en="b", body_rw="b", status=Article.STATUS_PENDING,
        )
        response = self.client.get(reverse("articles:list"))
        self.assertNotContains(response, "Pending Article")

    def test_anonymous_article_detail_is_marked_cacheable_for_offline_reading(self):
        response = self.client.get(self.article.get_absolute_url())
        self.assertEqual(response.headers.get("X-YTR-Public-Cache"), "1")

    def test_authenticated_article_detail_is_never_marked_cacheable(self):
        User.objects.create_user("reader", "reader@example.com", "password123", is_active=True)
        self.client.force_login(User.objects.get(username="reader"))
        response = self.client.get(self.article.get_absolute_url())
        self.assertNotIn("X-YTR-Public-Cache", response.headers)

    def test_draft_article_404_is_never_marked_cacheable(self):
        draft = Article.objects.create(
            title_en="Draft Article", title_rw="Umushinga", hook_en="h", hook_rw="h",
            body_en="b", body_rw="b", status=Article.STATUS_DRAFT,
        )
        response = self.client.get(draft.get_absolute_url())
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("X-YTR-Public-Cache", response.headers)

    def test_pending_article_404_is_never_marked_cacheable(self):
        pending = Article.objects.create(
            title_en="Pending Article", title_rw="Umushinga", hook_en="h", hook_rw="h",
            body_en="b", body_rw="b", status=Article.STATUS_PENDING,
        )
        response = self.client.get(reverse("articles:detail", kwargs={"slug": pending.slug}))
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("X-YTR-Public-Cache", response.headers)
