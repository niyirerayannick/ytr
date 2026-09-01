from django.shortcuts import render

from .models import Book


def book_list(request):
    return render(request, "library/book_list.html", {"books": Book.objects.all()})
