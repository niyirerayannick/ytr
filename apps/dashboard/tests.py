from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Bookmark, Profile
from apps.articles.models import Article

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
        self.article.submit_for_review(self.author)
        self.client.force_login(self.author)
        response = self.client.get(reverse("dashboard:author_content_edit", args=["article", self.article.id]))
        self.assertRedirects(response, reverse("dashboard:author_home"))

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
        self.assertRedirects(response, reverse("dashboard:author_home"))


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
