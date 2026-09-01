from django.test import TestCase
from django.urls import reverse

from .models import FAQ


class FAQListViewTests(TestCase):
    def test_faq_list_loads_when_empty(self):
        response = self.client.get(reverse("faq:list"))
        self.assertEqual(response.status_code, 200)

    def test_highlighted_faq_is_shown(self):
        FAQ.objects.create(
            question_en="What is YTR?", question_rw="YTR ni iki?",
            answer_en="a", answer_rw="a", is_highlighted=True,
        )
        response = self.client.get(reverse("faq:list"))
        self.assertContains(response, "What is YTR?")
