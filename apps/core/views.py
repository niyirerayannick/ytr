import logging

from django.db import connections
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from apps.articles.models import Article
from apps.devotions.models import Devotion
from apps.faq.models import FAQ

from .models import Gathering

logger = logging.getLogger(__name__)


def _todays_devotion():
    published = Devotion.objects.filter(status=Devotion.STATUS_PUBLISHED)
    devotion = published.filter(is_featured=True).first()
    if devotion:
        return devotion
    return published.order_by("-date").first()


def _next_gathering():
    now = timezone.now()
    return Gathering.objects.filter(end_datetime__gte=now).order_by("start_datetime").first()


def service_worker(request):
    """Serve the PWA service worker from the origin root.

    Registering from "/" (rather than a /static/... path) gives the worker a
    default scope covering the whole site, which it needs to intercept public
    page navigations. Rendered as a template (not a plain static file) so the
    shell asset list always points at the current, correctly hashed static URLs.
    """
    response = render(request, "service-worker.js", content_type="text/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


def health(request):
    """A small, non-sensitive readiness response for a reverse proxy."""
    try:
        connections["default"].cursor().execute("SELECT 1")
    except Exception:
        logger.exception("Health check database query failed")
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def _error_response(request, template_name, status):
    return render(request, template_name, status=status)


def error_400(request, exception=None):
    return _error_response(request, "errors/400.html", 400)


def error_403(request, exception=None):
    return _error_response(request, "errors/403.html", 403)


def error_404(request, exception=None):
    return _error_response(request, "errors/404.html", 404)


def error_500(request):
    return _error_response(request, "errors/500.html", 500)


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
