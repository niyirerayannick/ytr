"""Query/composition layer for the admin Command Center overview and content
workspace, so `views.py` stays a set of thin view functions instead of a
500-line god-function. Every number here comes from a real query — nothing
in this module is a placeholder or an invented metric.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from apps.accounts.models import PrayerRequest, Profile, Testimony
from apps.core.models import Gathering
from apps.engagement.models import ContactMessage, NewsletterSubscriber
from apps.morning_devotions.models import MorningDevotionSession

from .forms import CONTENT_REGISTRY

User = get_user_model()

STATUS_STAGES = [
    ("draft", "Draft"),
    ("pending", "Pending review"),
    ("published", "Published"),
    ("rejected", "Rejected"),
]

# How each registered content type exposes a title and EN/RW completeness —
# field names differ per model (Devotion has no `title_*`, it uses
# `verse_ref`/`verse_text_*`/`reflection_*`), so this is the one place that
# difference is bridged rather than repeated at every call site.
_CONTENT_SHAPE = {
    "article": {
        "title": lambda o: o.title_en,
        "has_en": lambda o: bool(o.title_en and o.body_en),
        "has_rw": lambda o: bool(o.title_rw and o.body_rw),
    },
    "devotion": {
        "title": lambda o: o.verse_ref,
        "has_en": lambda o: bool(o.verse_text_en and o.reflection_en),
        "has_rw": lambda o: bool(o.verse_text_rw and o.reflection_rw),
    },
    "episode": {
        "title": lambda o: o.title_en,
        "has_en": lambda o: bool(o.title_en),
        "has_rw": lambda o: bool(o.title_rw),
    },
    "video": {
        "title": lambda o: o.title_en,
        "has_en": lambda o: bool(o.title_en),
        "has_rw": lambda o: bool(o.title_rw),
    },
}


def _admin_change_url(app_label, model_name, pk):
    try:
        return reverse(f"admin:{app_label}_{model_name}_change", args=[pk])
    except NoReverseMatch:
        return None


def overview_kpis():
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    published_total = sum(
        entry["model"].objects.filter(status="published").count() for entry in CONTENT_REGISTRY.values()
    )
    pending_total = sum(
        entry["model"].objects.filter(status="pending").count() for entry in CONTENT_REGISTRY.values()
    )
    members_qs = User.objects.filter(is_active=True, profile__role=Profile.ROLE_MEMBER)
    return [
        {
            "label": "Members",
            "value": members_qs.count(),
            "trend": f"+{members_qs.filter(date_joined__gte=thirty_days_ago).count()} this month",
            "icon": "heart",
            "url": reverse("dashboard:user_management"),
        },
        {
            "label": "Published resources",
            "value": published_total,
            "icon": "book",
            "url": reverse("dashboard:content_workspace") + "?status=published",
        },
        {
            "label": "Pending review",
            "value": pending_total,
            "icon": "shield",
            "url": reverse("dashboard:content_queue"),
        },
        {
            "label": "Upcoming gatherings",
            "value": Gathering.objects.filter(start_datetime__gte=timezone.now()).count(),
            "icon": "pin",
            "url": reverse("core:home"),
        },
        {
            "label": "Newsletter subscribers",
            "value": NewsletterSubscriber.objects.count(),
            "icon": "mail",
            "url": reverse("dashboard:admin"),
        },
    ]


def admin_morning_devotion_focus():
    """Unlike `MorningDevotionSession.current_or_next()` (member-facing —
    skips a finished session with nothing attached yet), the admin card must
    surface exactly that session so there's something to prompt "complete
    the archive" for."""
    now = timezone.now()
    published = MorningDevotionSession.objects.filter(
        status=MorningDevotionSession.STATUS_PUBLISHED,
    ).select_related("recording_episode", "recording_video", "speaker")
    upcoming_or_live = published.filter(end_datetime__gte=now).order_by("start_datetime").first()
    if upcoming_or_live:
        return upcoming_or_live
    return published.order_by("-start_datetime").first()


def morning_devotions_missing_archive(window_days=30):
    now = timezone.now()
    finished = MorningDevotionSession.objects.filter(
        status=MorningDevotionSession.STATUS_PUBLISHED,
        end_datetime__lt=now,
        end_datetime__gte=now - timezone.timedelta(days=window_days),
    ).select_related("recording_episode", "recording_video")
    return [session for session in finished if not session.has_any_content]


def needs_attention():
    items = []
    pending_signups = User.objects.filter(is_active=False).count()
    if pending_signups:
        items.append({"label": f"{pending_signups} sign-up{'s' if pending_signups != 1 else ''} awaiting approval", "count": pending_signups, "url": reverse("dashboard:signup_queue")})

    for content_type, entry in CONTENT_REGISTRY.items():
        count = entry["model"].objects.filter(status="pending").count()
        if count:
            noun = entry["label"] + ("s" if count != 1 else "")
            items.append({"label": f"{count} {noun} awaiting review", "count": count, "url": reverse("dashboard:content_queue")})

    missing = morning_devotions_missing_archive()
    if missing:
        url = _admin_change_url("morning_devotions", "morningdevotionsession", missing[0].pk) or "/admin/morning_devotions/morningdevotionsession/"
        noun = "Morning Devotion" + ("s" if len(missing) != 1 else "")
        items.append({"label": f"{len(missing)} {noun} missing audio/archive", "count": len(missing), "url": url})

    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    if unread_messages:
        items.append({"label": f"{unread_messages} unread contact message{'s' if unread_messages != 1 else ''}", "count": unread_messages, "url": reverse("dashboard:messages")})

    pending_testimonies = Testimony.objects.filter(status=Testimony.STATUS_PENDING).count()
    if pending_testimonies:
        items.append({"label": f"{pending_testimonies} testimon{'ies' if pending_testimonies != 1 else 'y'} awaiting review", "count": pending_testimonies, "url": reverse("dashboard:pending_testimonies")})

    pending_prayers = PrayerRequest.objects.filter(status=PrayerRequest.STATUS_PENDING).count()
    if pending_prayers:
        items.append({"label": f"{pending_prayers} prayer request{'s' if pending_prayers != 1 else ''} unreviewed", "count": pending_prayers, "url": reverse("dashboard:prayer_requests")})

    return items


def publishing_pipeline():
    stages = []
    for status_value, label in STATUS_STAGES:
        count = sum(entry["model"].objects.filter(status=status_value).count() for entry in CONTENT_REGISTRY.values())
        stages.append({
            "status": status_value, "label": label, "count": count,
            "url": reverse("dashboard:content_workspace") + f"?status={status_value}",
        })
    return stages


def recent_content(limit=8):
    items = []
    for content_type, entry in CONTENT_REGISTRY.items():
        shape = _CONTENT_SHAPE[content_type]
        qs = entry["model"].objects.filter(status="published", published_at__isnull=False).order_by("-published_at")[:limit]
        for obj in qs:
            items.append({
                "type": content_type,
                "label": entry["label"],
                "title": shape["title"](obj),
                "has_en": shape["has_en"](obj),
                "has_rw": shape["has_rw"](obj),
                "published_at": obj.published_at,
                "url": getattr(obj, "get_absolute_url", lambda: None)() if hasattr(obj, "get_absolute_url") else None,
                "edit_url": reverse("dashboard:review_content", kwargs={"content_type": content_type, "pk": obj.pk}),
            })
    items.sort(key=lambda i: i["published_at"], reverse=True)
    return items[:limit]


def bilingual_health():
    complete = en_only = rw_only = missing = 0
    affected = []
    for content_type, entry in CONTENT_REGISTRY.items():
        shape = _CONTENT_SHAPE[content_type]
        for obj in entry["model"].objects.filter(status="published"):
            has_en, has_rw = shape["has_en"](obj), shape["has_rw"](obj)
            if has_en and has_rw:
                complete += 1
            elif has_en:
                en_only += 1
                affected.append(obj)
            elif has_rw:
                rw_only += 1
                affected.append(obj)
            else:
                missing += 1
                affected.append(obj)
    total = complete + en_only + rw_only + missing
    return {
        "complete": complete, "en_only": en_only, "rw_only": rw_only, "missing": missing,
        "total": total, "needs_translation": en_only + rw_only + missing,
    }


def community_summary():
    return {
        "members": User.objects.filter(is_active=True, profile__role=Profile.ROLE_MEMBER).count(),
        "authors": User.objects.filter(is_active=True, profile__role=Profile.ROLE_AUTHOR).count(),
        "subscribers": NewsletterSubscriber.objects.count(),
        "testimonies_pending": Testimony.objects.filter(status=Testimony.STATUS_PENDING).count(),
        "prayers_pending": PrayerRequest.objects.filter(status=PrayerRequest.STATUS_PENDING).count(),
        "messages_unread": ContactMessage.objects.filter(is_read=False).count(),
    }


def recent_activity(limit=10):
    """Derived strictly from fields that already exist (`published_at` +
    `reviewed_by` on ReviewableContent, `date_joined` on User) — there is no
    generic audit log in this project yet, so nothing here is fabricated or
    inferred beyond what those fields actually record."""
    events = []
    for content_type, entry in CONTENT_REGISTRY.items():
        shape = _CONTENT_SHAPE[content_type]
        qs = (
            entry["model"].objects.filter(status="published", published_at__isnull=False)
            .select_related("reviewed_by").order_by("-published_at")[:limit]
        )
        for obj in qs:
            actor = "Someone"
            if obj.reviewed_by:
                actor = obj.reviewed_by.get_full_name() or obj.reviewed_by.username
            events.append({
                "actor": actor, "verb": "published", "target": shape["title"](obj) or entry["label"],
                "at": obj.published_at,
            })
    for user in User.objects.filter(is_active=True).order_by("-date_joined")[:limit]:
        events.append({
            "actor": user.get_full_name() or user.username, "verb": "joined", "target": "Youth Time Revival",
            "at": user.date_joined,
        })
    events.sort(key=lambda e: e["at"], reverse=True)
    return events[:limit]


def command_search(query, limit_per_type=5):
    """Admin-only cross-model search for the Ctrl/Cmd+K command palette.
    Deliberately separate from `apps.core.views.search` (that endpoint is
    public/unauthenticated and only surfaces already-published content) —
    this one is only ever reachable behind `role_required(ADMIN)` and can
    show any status, so the two must never be merged."""
    query = (query or "").strip()
    if len(query) < 2:
        return []

    results = []
    for content_type, entry in CONTENT_REGISTRY.items():
        shape = _CONTENT_SHAPE[content_type]
        model = entry["model"]
        if content_type == "devotion":
            matches = model.objects.filter(verse_ref__icontains=query)
        else:
            matches = model.objects.filter(Q(title_en__icontains=query) | Q(title_rw__icontains=query))
        for obj in matches[:limit_per_type]:
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            results.append({
                "kind": entry["label"], "title": shape["title"](obj),
                "url": _admin_change_url(app_label, model_name, obj.pk),
            })

    for user in User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query),
    )[:limit_per_type]:
        results.append({"kind": "Member", "title": user.username, "url": _admin_change_url("auth", "user", user.pk)})

    for gathering in Gathering.objects.filter(title__icontains=query)[:limit_per_type]:
        results.append({"kind": "Gathering", "title": gathering.title, "url": _admin_change_url("core", "gathering", gathering.pk)})

    for session in MorningDevotionSession.objects.filter(
        Q(title_en__icontains=query) | Q(title_rw__icontains=query),
    )[:limit_per_type]:
        results.append({
            "kind": "Morning Devotion", "title": session.title_en,
            "url": _admin_change_url("morning_devotions", "morningdevotionsession", session.pk),
        })

    return [r for r in results if r["url"]]


def quick_create_actions():
    """Static list, but every URL is a real, reachable, permission-correct
    destination — not a placeholder link."""
    actions = [
        {"label": "New Article", "url": reverse("dashboard:author_content_create", kwargs={"content_type": "article"})},
        {"label": "New Devotion", "url": reverse("dashboard:author_content_create", kwargs={"content_type": "devotion"})},
        {"label": "New Podcast Episode", "url": reverse("dashboard:author_content_create", kwargs={"content_type": "episode"})},
        {"label": "New Video", "url": reverse("dashboard:author_content_create", kwargs={"content_type": "video"})},
    ]
    admin_add_targets = [
        ("Schedule Morning Devotion", "morning_devotions", "morningdevotionsession"),
        ("Create Gathering", "core", "gathering"),
        ("Add FAQ", "faq", "faq"),
        ("Add Book", "library", "book"),
    ]
    for label, app_label, model_name in admin_add_targets:
        try:
            url = reverse(f"admin:{app_label}_{model_name}_add")
        except NoReverseMatch:
            continue
        actions.append({"label": label, "url": url})
    return actions
