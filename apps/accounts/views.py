from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
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
