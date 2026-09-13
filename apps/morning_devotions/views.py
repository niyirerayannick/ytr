from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from apps.core.card_rendering import FORMATS, SQUARE
from apps.core.models import SiteSettings
from apps.core.pwa import mark_public_cacheable

from . import cover
from .models import MorningDevotionSession
from .youtube import youtube_embed_id

FILTER_CHOICES = {"all", "en", "rw"}

_SHARE_COPY = {
    "en": {
        "heading": "Morning Devotion — Youth Time Revival",
        "read_line": "Listen:",
        "share_text": "Morning Devotion — Youth Time Revival: {title}",
        "email_subject": "Morning Devotion — {title}",
    },
    "rw": {
        "heading": "Isengesho ryo mu Gitondo — Youth Time Revival",
        "read_line": "Umva:",
        "share_text": "Isengesho ryo mu gitondo — Youth Time Revival: {title}",
        "email_subject": "Isengesho ryo mu Gitondo — {title}",
    },
}


def morning_devotion_list(request):
    sessions = MorningDevotionSession.objects.filter(
        status=MorningDevotionSession.STATUS_PUBLISHED,
    ).select_related("speaker", "recording_episode", "recording_video")

    active_filter = request.GET.get("filter", "all")
    if active_filter not in FILTER_CHOICES:
        active_filter = "all"
    if active_filter in ("en", "rw"):
        sessions = sessions.filter(language__in=[active_filter, MorningDevotionSession.LANGUAGE_BILINGUAL])

    paginator = Paginator(sessions, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    response = render(request, "morning_devotions/session_list.html", {
        "page_obj": page_obj,
        "active_filter": active_filter,
    })
    if not request.GET.get("page"):
        response = mark_public_cacheable(response, request)
    return response


def _share_payload(request, session):
    canonical_url = request.build_absolute_uri(session.get_absolute_url())
    text = {}
    whatsapp = {}
    email = {}
    for lang in ("en", "rw"):
        copy = _SHARE_COPY[lang]
        title = session.title_rw if lang == "rw" and session.title_rw else session.title_en
        text[lang] = copy["share_text"].format(title=title)
        whatsapp[lang] = (
            f"{copy['heading']}\n\n{title}\n{session.scripture_reference}\n\n"
            f"{copy['read_line']}\n{canonical_url}"
        )
        email[lang] = {
            "subject": copy["email_subject"].format(title=title),
            "body": f"{title}\n{session.scripture_reference}\n\n{copy['read_line']}\n{canonical_url}",
        }
    return {"url": canonical_url, "text": text, "whatsapp": whatsapp, "email": email}


def morning_devotion_detail(request, slug):
    session = get_object_or_404(
        MorningDevotionSession.objects.select_related("speaker", "recording_episode", "recording_video", "related_devotion"),
        slug=slug, status=MorningDevotionSession.STATUS_PUBLISHED,
    )
    canonical_url = request.build_absolute_uri(session.get_absolute_url())
    video_embed_id = ""
    if session.has_video and session.recording_video.youtube_url:
        video_embed_id = youtube_embed_id(session.recording_video.youtube_url)

    response = render(request, "morning_devotions/session_detail.html", {
        "session": session,
        "canonical_url": canonical_url,
        "og_description": session.description_en or session.summary_en or session.scripture_reference,
        "og_image_url": request.build_absolute_uri(f"/morning-devotions/{session.slug}/cover.png"),
        "share_payload": _share_payload(request, session),
        "video_embed_id": video_embed_id,
    })
    return mark_public_cacheable(response, request)


def morning_devotion_cover(request, slug):
    fmt = request.GET.get("format", SQUARE)
    if fmt not in FORMATS:
        return HttpResponseBadRequest("Unsupported format")

    session = get_object_or_404(MorningDevotionSession, slug=slug, status=MorningDevotionSession.STATUS_PUBLISHED)
    site_settings = SiteSettings.load()
    key = cover.cache_key(session, fmt, site_settings)
    png = cache.get(key)
    if png is None:
        png = cover.render_session_cover(session, site_settings, fmt=fmt)
        cache.set(key, png, timeout=None)

    response = HttpResponse(png, content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    response["ETag"] = key
    return response
