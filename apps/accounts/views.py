from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_GET

from apps.core.rate_limit import is_rate_limited

from .forms import RegistrationForm

User = get_user_model()


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verification_url = request.build_absolute_uri(
        f"/accounts/verify-email/{uid}/{token}/"
    )
    send_mail(
        "Verify your YTR account",
        (
            f"Hi {user.profile.display_name},\n\n"
            f"Please verify your email address to activate your YTR account:\n\n{verification_url}\n\n"
            "If you did not create this account, you can safely ignore this email."
        ),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        if is_rate_limited(
            request,
            scope="registration",
            limit=settings.RATELIMIT_REGISTRATION_LIMIT,
            window_seconds=settings.RATELIMIT_WINDOW_SECONDS,
        ):
            messages.error(request, "Too many sign-up attempts. Please try again later.")
            return render(request, "accounts/register.html", {"form": RegistrationForm()}, status=429)
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_verification_email(request, user)
            messages.success(
                request,
                "Your account was created. Please check your email to verify your address and activate it.",
            )
            return redirect("accounts:login")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@require_GET
def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=uid)
    except (TypeError, ValueError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, "Your email has been verified. You can now log in.")
    else:
        messages.error(request, "This verification link is invalid or has expired.")
    return redirect("accounts:login")
