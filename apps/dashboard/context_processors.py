from apps.accounts.models import Profile

from . import services


def admin_notifications(request):
    """Needs-attention data for the admin top bar's notification bell.

    Scoped to admin dashboard pages only (not every page on the site) so the
    handful of `.count()` queries this runs don't fire on unrelated requests.
    Cheap enough to compute per-request rather than needing an HTMX round
    trip just to show a badge count.
    """
    if not (getattr(request, "resolver_match", None) and request.resolver_match.namespace == "dashboard"):
        return {}
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != Profile.ROLE_ADMIN:
        return {}
    items = services.needs_attention()
    return {
        "admin_notifications": items,
        "admin_notifications_count": sum(item["count"] for item in items),
        "quick_create_actions": services.quick_create_actions(),
    }
