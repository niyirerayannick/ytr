from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from apps.articles.models import Article
from apps.devotions.models import Devotion
from apps.faq.models import FAQ

from .models import Gathering


def _todays_devotion():
    published = Devotion.objects.filter(status=Devotion.STATUS_PUBLISHED)
    devotion = published.filter(is_featured=True).first()
    if devotion:
        return devotion
    return published.order_by("-date").first()


def _next_gathering():
    now = timezone.now()
    upcoming = Gathering.objects.filter(end_datetime__gte=now).order_by("start_datetime").first()
    if upcoming:
        return upcoming
    return Gathering.objects.order_by("-start_datetime").first()


def home(request):
    gathering = _next_gathering()
    is_rsvped = (
        gathering is not None
        and request.user.is_authenticated
        and gathering.rsvps.filter(member=request.user).exists()
    )
    context = {
        "devotion": _todays_devotion(),
        "gathering": gathering,
        "is_rsvped": is_rsvped,
        "articles": Article.objects.filter(status=Article.STATUS_PUBLISHED).order_by("-is_featured", "-published_at")[:10],
    }
    return render(request, "home/home.html", context)


def search(request):
    """Sitewide search JSON endpoint, consumed by the search overlay in site.js."""
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        published_articles = Article.objects.filter(status=Article.STATUS_PUBLISHED)
        for article in (published_articles.filter(title_en__icontains=query) | published_articles.filter(title_rw__icontains=query)).distinct():
            results.append({
                "kind": "Article",
                "title_en": article.title_en,
                "title_rw": article.title_rw,
                "url": article.get_absolute_url(),
            })
        for devotion in Devotion.objects.filter(status=Devotion.STATUS_PUBLISHED, verse_ref__icontains=query).distinct():
            results.append({
                "kind": "Devotion",
                "title_en": devotion.verse_ref,
                "title_rw": devotion.verse_ref,
                "url": reverse("devotions:list"),
            })
        for faq in (FAQ.objects.filter(question_en__icontains=query) | FAQ.objects.filter(question_rw__icontains=query)).distinct():
            results.append({
                "kind": "FAQ",
                "title_en": faq.question_en,
                "title_rw": faq.question_rw,
                "url": reverse("faq:list"),
            })

    return JsonResponse({"results": results})
