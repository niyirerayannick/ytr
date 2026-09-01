"""Role-gating for the dashboard: a function decorator for view functions and an
equivalent class-based mixin, per the spec's "RoleRequiredMixin ... or equivalent
decorator". The decorator is what's actually used by dashboard.views (function-based
views, given the number of small action endpoints); the mixin is provided for anyone
wiring up a class-based view against the same rule.

Both apply the same policy: anonymous -> redirect to login (normal auth flow);
authenticated but wrong role -> 403 Forbidden, never a silent redirect.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            if not profile or profile.role not in roles:
                raise PermissionDenied("You do not have access to this page.")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        profile = getattr(request.user, "profile", None)
        if not profile or profile.role not in self.allowed_roles:
            raise PermissionDenied("You do not have access to this page.")
        return super().dispatch(request, *args, **kwargs)
