from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from apps.accounts.models import Bookmark, PrayerRequest, Profile, RSVP, Testimony
from apps.articles.models import Article
from apps.core.i18n import bilingual_field, viewer_language
from apps.core.models import Gathering
from apps.devotions.models import Devotion
from apps.engagement.models import ContactMessage, NewsletterSubscriber
from apps.morning_devotions.models import MorningDevotionSession
from apps.podcasts.models import Episode
from apps.videos.models import Video

from . import services
from .access import role_required
from .forms import (
    CONTENT_REGISTRY,
    PrayerRequestForm,
    RejectContentForm,
    TestimonyForm,
    UserRoleForm,
)
from .services import _CONTENT_SHAPE

User = get_user_model()


def _safe_next_url(request, fallback):
    """Return only a same-host, safe redirect target supplied by a POST form."""
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback


# --------------------------------------------------------------------------- home
@login_required
def dashboard_home(request):
    profile = getattr(request.user, "profile", None)
    role = profile.role if profile else Profile.ROLE_MEMBER
    return redirect(f"dashboard:{role}")


# ------------------------------------------------------------------------- admin
@role_required(Profile.ROLE_ADMIN)
def admin_dashboard(request):
    needs_attention_items = services.needs_attention()
    local_hour = timezone.localtime().hour
    greeting = "Good morning" if local_hour < 12 else "Good afternoon" if local_hour < 18 else "Good evening"
    context = {
        "greeting": greeting,
        "kpis": services.overview_kpis(),
        "morning_devotion": services.admin_morning_devotion_focus(),
        "morning_devotions_missing_archive": services.morning_devotions_missing_archive(),
        "needs_attention": needs_attention_items,
        "needs_attention_count": sum(item["count"] for item in needs_attention_items),
        "pipeline": services.publishing_pipeline(),
        "recent_content": services.recent_content(),
        "bilingual_health": services.bilingual_health(),
        "community": services.community_summary(),
        "activity": services.recent_activity(),
    }
    return render(request, "dashboard/admin/home.html", context)


@role_required(Profile.ROLE_ADMIN)
def command_search_view(request):
    query = request.GET.get("q", "")
    results = services.command_search(query)
    if request.headers.get("HX-Request"):
        return render(request, "dashboard/admin/_palette_results.html", {"results": results, "query": query})
    return JsonResponse({"results": results})


@role_required(Profile.ROLE_ADMIN)
def content_workspace(request):
    """Cross-type browsing/filtering over every ReviewableContent type
    (Article/Devotion/Episode/Video) — complements, not replaces, the
    existing pending-review action queue (`content_queue`/`review_content`).
    Filter state lives in the query string so results are bookmarkable."""
    content_type = request.GET.get("type", "all")
    status = request.GET.get("status", "all")
    language = request.GET.get("language", "all")
    query = request.GET.get("q", "").strip()

    types_to_query = [content_type] if content_type in CONTENT_REGISTRY else list(CONTENT_REGISTRY)

    items = []
    for ct in types_to_query:
        entry = CONTENT_REGISTRY[ct]
        shape = _CONTENT_SHAPE[ct]
        qs = entry["model"].objects.all()
        if status in ("draft", "pending", "published", "rejected"):
            qs = qs.filter(status=status)
        if query:
            if ct == "devotion":
                qs = qs.filter(verse_ref__icontains=query)
            else:
                qs = qs.filter(Q(title_en__icontains=query) | Q(title_rw__icontains=query))
        for obj in qs.order_by("-updated_at")[:100]:
            has_en, has_rw = shape["has_en"](obj), shape["has_rw"](obj)
            if language == "en" and not has_en:
                continue
            if language == "rw" and not has_rw:
                continue
            if language == "missing" and (has_en and has_rw):
                continue
            items.append({
                "type": ct, "label": entry["label"], "obj": obj,
                "title": shape["title"](obj), "status": obj.status,
                "has_en": has_en, "has_rw": has_rw, "updated_at": obj.updated_at,
                "edit_url": reverse("dashboard:review_content", kwargs={"content_type": ct, "pk": obj.pk}),
                "view_url": obj.get_absolute_url() if hasattr(obj, "get_absolute_url") and obj.status == "published" else None,
            })
    items.sort(key=lambda i: i["updated_at"], reverse=True)

    paginator = Paginator(items, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "active_type": content_type,
        "active_status": status,
        "active_language": language,
        "query": query,
        "content_types": [("all", "All types")] + [(ct, entry["label"]) for ct, entry in CONTENT_REGISTRY.items()],
    }
    template = "dashboard/admin/_content_workspace_results.html" if request.headers.get("HX-Request") else "dashboard/admin/content_workspace.html"
    return render(request, template, context)


@role_required(Profile.ROLE_ADMIN)
def signup_queue(request):
    users = User.objects.filter(is_active=False).order_by("-date_joined")
    return render(request, "dashboard/admin/signup_queue.html", {"users": users})


@role_required(Profile.ROLE_ADMIN)
def approve_signup(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, pk=user_id, is_active=False)
        user.is_active = True
        user.save()
        messages.success(request, f"{user.username} approved — they can now log in.")
    return redirect("dashboard:signup_queue")


@role_required(Profile.ROLE_ADMIN)
def reject_signup(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, pk=user_id, is_active=False)
        username = user.username
        user.delete()
        messages.success(request, f"Sign-up from {username} was rejected and removed.")
    return redirect("dashboard:signup_queue")


@role_required(Profile.ROLE_ADMIN)
def user_management(request):
    users = (
        User.objects.filter(is_active=True, profile__role__in=[Profile.ROLE_MEMBER, Profile.ROLE_AUTHOR])
        .select_related("profile")
        .order_by("username")
    )
    return render(request, "dashboard/admin/user_management.html", {"users": users, "role_form": UserRoleForm()})


@role_required(Profile.ROLE_ADMIN)
def update_user_role(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, pk=user_id, is_active=True)
        form = UserRoleForm(request.POST)
        if form.is_valid() and hasattr(user, "profile") and user.profile.role != Profile.ROLE_ADMIN:
            user.profile.role = form.cleaned_data["role"]
            user.profile.save()
            messages.success(request, f"{user.username} is now {form.cleaned_data['role']}.")
    return redirect("dashboard:user_management")


@role_required(Profile.ROLE_ADMIN)
def pending_content_queue(request):
    items = []
    for content_type, entry in CONTENT_REGISTRY.items():
        for obj in entry["model"].objects.filter(status="pending"):
            items.append({"type": content_type, "label": entry["label"], "obj": obj})
    items.sort(key=lambda i: i["obj"].submitted_at or timezone.now())
    return render(request, "dashboard/admin/content_queue.html", {"items": items})


@role_required(Profile.ROLE_ADMIN)
def review_content(request, content_type, pk):
    entry = CONTENT_REGISTRY.get(content_type)
    if not entry:
        raise Http404
    obj = get_object_or_404(entry["model"], pk=pk)
    form = entry["form"](request.POST or None, request.FILES or None, instance=obj)
    reject_form = RejectContentForm(request.POST if request.POST.get("action") == "reject" else None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "save":
            if form.is_valid():
                form.save()
                messages.success(request, "Changes saved.")
                return redirect("dashboard:review_content", content_type=content_type, pk=pk)
        elif action == "approve":
            obj.approve(request.user)
            messages.success(request, f"{entry['label']} approved and published.")
            return redirect("dashboard:content_queue")
        elif action == "reject":
            if reject_form.is_valid():
                obj.reject(request.user, reject_form.cleaned_data["review_note"])
                messages.success(request, f"{entry['label']} rejected.")
                return redirect("dashboard:content_queue")

    return render(request, "dashboard/admin/review_content.html", {
        "content_type": content_type,
        "label": entry["label"],
        "object": obj,
        "form": form,
        "reject_form": reject_form,
    })


@role_required(Profile.ROLE_ADMIN)
def pending_testimonies(request):
    testimonies = Testimony.objects.filter(status=Testimony.STATUS_PENDING)
    return render(request, "dashboard/admin/testimonies.html", {
        "testimonies": testimonies,
        "reject_form": RejectContentForm(),
    })


@role_required(Profile.ROLE_ADMIN)
def approve_testimony(request, pk):
    if request.method == "POST":
        testimony = get_object_or_404(Testimony, pk=pk, status=Testimony.STATUS_PENDING)
        testimony.approve(request.user)
        messages.success(request, "Testimony approved.")
    return redirect("dashboard:pending_testimonies")


@role_required(Profile.ROLE_ADMIN)
def reject_testimony(request, pk):
    if request.method == "POST":
        testimony = get_object_or_404(Testimony, pk=pk, status=Testimony.STATUS_PENDING)
        form = RejectContentForm(request.POST)
        if form.is_valid():
            testimony.reject(request.user, form.cleaned_data["review_note"])
            messages.success(request, "Testimony rejected.")
    return redirect("dashboard:pending_testimonies")


@role_required(Profile.ROLE_ADMIN)
def prayer_requests_queue(request):
    prayers = PrayerRequest.objects.filter(status=PrayerRequest.STATUS_PENDING)
    return render(request, "dashboard/admin/prayer_requests.html", {"prayers": prayers})


@role_required(Profile.ROLE_ADMIN)
def mark_prayer_reviewed(request, pk):
    if request.method == "POST":
        prayer = get_object_or_404(PrayerRequest, pk=pk)
        prayer.mark_reviewed()
        messages.success(request, "Marked as reviewed.")
    return redirect("dashboard:prayer_requests")


@role_required(Profile.ROLE_ADMIN)
def contact_messages_list(request):
    return render(request, "dashboard/admin/messages.html", {"contact_messages": ContactMessage.objects.all()})


# ------------------------------------------------------------------------ author
@role_required(Profile.ROLE_AUTHOR)
def author_dashboard(request):
    items = []
    for content_type, entry in CONTENT_REGISTRY.items():
        for obj in entry["model"].objects.filter(submitted_by=request.user):
            items.append({"type": content_type, "label": entry["label"], "obj": obj})
    items.sort(key=lambda i: i["obj"].updated_at, reverse=True)
    return render(request, "dashboard/author/home.html", {"items": items})


@role_required(Profile.ROLE_AUTHOR, Profile.ROLE_ADMIN)
def author_content_create(request, content_type):
    entry = CONTENT_REGISTRY.get(content_type)
    if not entry:
        raise Http404
    if request.method == "POST":
        form = entry["form"](request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.submitted_by = request.user
            obj.save()
            messages.success(request, f"{entry['label']} saved as a draft.")
            return redirect("dashboard:author_content_edit", content_type=content_type, pk=obj.pk)
    else:
        form = entry["form"]()
    return render(request, "dashboard/author/content_form.html", {
        "content_type": content_type, "label": entry["label"], "form": form, "object": None,
    })


@role_required(Profile.ROLE_AUTHOR, Profile.ROLE_ADMIN)
def author_content_edit(request, content_type, pk):
    entry = CONTENT_REGISTRY.get(content_type)
    if not entry:
        raise Http404
    obj = get_object_or_404(entry["model"], pk=pk, submitted_by=request.user)
    if obj.status not in (obj.STATUS_DRAFT, obj.STATUS_REJECTED):
        messages.error(request, "This item is awaiting review or already published, so it can't be edited right now.")
        return redirect("dashboard:home")

    if request.method == "POST":
        form = entry["form"](request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Changes saved.")
            return redirect("dashboard:author_content_edit", content_type=content_type, pk=obj.pk)
    else:
        form = entry["form"](instance=obj)

    return render(request, "dashboard/author/content_form.html", {
        "content_type": content_type, "label": entry["label"], "form": form, "object": obj,
    })


@role_required(Profile.ROLE_AUTHOR, Profile.ROLE_ADMIN)
def author_content_submit(request, content_type, pk):
    entry = CONTENT_REGISTRY.get(content_type)
    if not entry:
        raise Http404
    if request.method == "POST":
        obj = get_object_or_404(entry["model"], pk=pk, submitted_by=request.user)
        if obj.status in (obj.STATUS_DRAFT, obj.STATUS_REJECTED):
            obj.submit_for_review(request.user)
            messages.success(request, f"{entry['label']} submitted for review.")
        return redirect("dashboard:home")
    raise Http404


# ------------------------------------------------------------------------ member
@role_required(Profile.ROLE_MEMBER)
def member_dashboard(request):
    today_devotion = (
        Devotion.objects.filter(status=Devotion.STATUS_PUBLISHED)
        .order_by("-is_featured", "-date")
        .first()
    )
    next_gathering = (
        Gathering.objects.filter(start_datetime__gte=timezone.now())
        .order_by("start_datetime")
        .first()
    )
    morning_devotion = MorningDevotionSession.current_or_next()
    featured_article = Article.objects.filter(status=Article.STATUS_PUBLISHED).order_by("-published_at").first()
    latest_episode = Episode.objects.filter(status=Episode.STATUS_PUBLISHED).order_by("-published_at").first()
    latest_video = Video.objects.filter(status=Video.STATUS_PUBLISHED).order_by("-published_at").first()
    bookmarks = Bookmark.objects.filter(member=request.user).select_related("article")[:3]
    rsvps = RSVP.objects.filter(member=request.user).select_related("gathering")[:3]
    testimonies = Testimony.objects.filter(member=request.user)[:3]
    prayer_requests = PrayerRequest.objects.filter(member=request.user)[:3]

    lang = viewer_language(request.user)
    context = {
        "profile": getattr(request.user, "profile", None),
        "today_devotion": today_devotion,
        "next_gathering": next_gathering,
        "morning_devotion": morning_devotion,
        "featured_article": featured_article,
        "featured_article_title": bilingual_field(featured_article, "title", lang) if featured_article else "",
        "latest_episode": latest_episode,
        "latest_episode_title": bilingual_field(latest_episode, "title", lang) if latest_episode else "",
        "latest_video": latest_video,
        "latest_video_title": bilingual_field(latest_video, "title", lang) if latest_video else "",
        "bookmarks": bookmarks,
        "rsvps": rsvps,
        "testimonies": testimonies,
        "prayer_requests": prayer_requests,
        "testimony_form": TestimonyForm(),
        "prayer_form": PrayerRequestForm(),
    }
    return render(request, "dashboard/member/home.html", context)


@role_required(Profile.ROLE_MEMBER)
def new_testimony(request):
    if request.method == "POST":
        form = TestimonyForm(request.POST)
        if form.is_valid():
            testimony = form.save(commit=False)
            testimony.member = request.user
            testimony.save()
            messages.success(request, "Thanks — your testimony has been submitted for review.")
        else:
            messages.error(request, "Please fill in both a title and your testimony.")
    return redirect("dashboard:member_home")


@role_required(Profile.ROLE_MEMBER)
def new_prayer_request(request):
    if request.method == "POST":
        form = PrayerRequestForm(request.POST)
        if form.is_valid():
            prayer = form.save(commit=False)
            prayer.member = request.user
            prayer.save()
            messages.success(request, "Your prayer request has been sent to the team.")
        else:
            messages.error(request, "Please write your prayer request before sending.")
    return redirect("dashboard:member_home")


# --------------------------------------------------------- shared member actions
# Bookmarking an article / RSVPing to a gathering are plain logged-in-user actions
# triggered from public pages (article detail, home) rather than dashboard-only
# screens, so these are gated by login only, not by role="member" specifically —
# an Author or Admin browsing the public site can bookmark an article too.
@login_required
def toggle_bookmark(request, article_id):
    article = get_object_or_404(Article, pk=article_id, status="published")
    if request.method == "POST":
        bookmark, created = Bookmark.objects.get_or_create(member=request.user, article=article)
        if not created:
            bookmark.delete()
            messages.success(request, "Removed from your saved articles.")
        else:
            messages.success(request, "Saved to your dashboard.")
    return redirect(_safe_next_url(request, article.get_absolute_url()))


@login_required
def toggle_rsvp(request, gathering_id):
    gathering = get_object_or_404(Gathering, pk=gathering_id)
    if request.method == "POST":
        rsvp, created = RSVP.objects.get_or_create(member=request.user, gathering=gathering)
        if not created:
            rsvp.delete()
            messages.success(request, "RSVP cancelled.")
        else:
            messages.success(request, "You're on the list — see you there!")
    return redirect(_safe_next_url(request, "core:home"))
