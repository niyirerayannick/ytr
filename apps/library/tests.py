from django.test import TestCase
from django.urls import reverse

from .models import Book


class BookListViewTests(TestCase):
    def test_book_list_loads_when_empty(self):
        response = self.client.get(reverse("library:list"))
        self.assertEqual(response.status_code, 200)

    def test_book_list_shows_books(self):
        Book.objects.create(title_en="Bibiliya Yera (The Bible)", title_rw="Bibiliya Yera")
        response = self.client.get(reverse("library:list"))
        self.assertContains(response, "Bibiliya Yera")
