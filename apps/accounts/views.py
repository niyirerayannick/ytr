from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render

from apps.core.rate_limit import is_rate_limited

from .forms import RegistrationForm


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
            form.save()
            messages.success(
                request,
                "Thanks for signing up — your account is pending admin approval. "
                "We'll let you know once you're able to log in.",
            )
            return redirect("accounts:login")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})
