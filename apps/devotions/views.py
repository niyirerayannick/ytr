from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from apps.core.models import SiteSettings
from apps.core.pwa import mark_public_cacheable

from . import share_cards
from .models import Devotion


def devotion_list(request):
    published = Devotion.objects.filter(status=Devotion.STATUS_PUBLISHED)
    today = published.filter(is_featured=True).first() or published.order_by("-date").first()

    archive_qs = published.order_by("-date")
    if today:
        archive_qs = archive_qs.exclude(pk=today.pk)

    paginator = Paginator(archive_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    response = render(request, "devotions/devotion_list.html", {
        "today": today,
        "page_obj": page_obj,
    })
    if not request.GET.get("page"):
        response = mark_public_cacheable(response, request)
    return response


_SHARE_COPY = {
    "en": {
        "heading": "Today's Youth Time Revival Devotion",
        "read_line": "Read the full devotion:",
        "share_text": "Today's Youth Time Revival Devotion — {ref}",
        "email_subject": "Youth Time Revival Devotion — {ref}",
    },
    "rw": {
        "heading": "Igitekerezo cy'uyu munsi cya Youth Time Revival",
        "read_line": "Soma igitekerezo cyose:",
        "share_text": "Igitekerezo cy'uyu munsi cya Youth Time Revival — {ref}",
        "email_subject": "Igitekerezo cya Youth Time Revival — {ref}",
    },
}


def _share_payload(request, devotion):
    canonical_url = request.build_absolute_uri(devotion.get_absolute_url())
    has_rw = devotion.has_language("rw")

    text = {}
    whatsapp = {}
    email = {}
    for lang in ("en", "rw"):
        if lang == "rw" and not has_rw:
            continue
        copy = _SHARE_COPY[lang]
        ref = devotion.verse_ref
        text[lang] = copy["share_text"].format(ref=ref)
        whatsapp[lang] = f"{copy['heading']}\n\n{ref}\n\n{copy['read_line']}\n{canonical_url}"
        email[lang] = {
            "subject": copy["email_subject"].format(ref=ref),
            "body": f"{ref}\n\n{devotion.share_excerpt(lang, max_words=40)}\n\n{copy['read_line']}\n{canonical_url}",
        }

    return {
        "url": canonical_url,
        "verse_ref": devotion.verse_ref,
        "has_rw": has_rw,
        "share_image_base": request.build_absolute_uri(
            f"/devotions/{devotion.slug}/share-image.png"
        ),
        "text": text,
        "whatsapp": whatsapp,
        "email": email,
    }


def devotion_detail(request, slug):
    devotion = get_object_or_404(Devotion, slug=slug, status=Devotion.STATUS_PUBLISHED)
    canonical_url = request.build_absolute_uri(devotion.get_absolute_url())
    share_payload = _share_payload(request, devotion)
    response = render(request, "devotions/devotion_detail.html", {
        "devotion": devotion,
        "has_rw": share_payload["has_rw"],
        "canonical_url": canonical_url,
        "og_description": devotion.share_excerpt("en", max_words=30),
        "og_image_url": f"{share_payload['share_image_base']}?lang=en&format=square",
        "share_payload": share_payload,
    })
    return mark_public_cacheable(response, request)


def devotion_share_image(request, slug):
    """Branded PNG for this devotion — used as the og:image and as the
    "repost" image the share sheet lets a visitor save/share.

    Strictly validates `lang`/`format` against fixed allow-lists (never
    arbitrary strings) and only ever serves a `published` devotion, so a
    draft/pending/rejected one can't be reached even by guessing its slug.
    """
    language = request.GET.get("lang", "en")
    fmt = request.GET.get("format", share_cards.SQUARE)
    if language not in share_cards.LANGUAGES:
        return HttpResponseBadRequest("Unsupported lang")
    if fmt not in share_cards.FORMATS:
        return HttpResponseBadRequest("Unsupported format")

    devotion = get_object_or_404(Devotion, slug=slug, status=Devotion.STATUS_PUBLISHED)
    if not devotion.has_language(language):
        return HttpResponseBadRequest("No content in that language for this devotion")

    site_settings = SiteSettings.load()
    key = share_cards.cache_key(devotion, language, fmt, site_settings)
    png = cache.get(key)
    if png is None:
        png = share_cards.render_devotion_card(devotion, language, site_settings, fmt=fmt)
        cache.set(key, png, timeout=None)

    response = HttpResponse(png, content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    response["ETag"] = key
    return response
