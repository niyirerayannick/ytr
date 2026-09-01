import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail as django_send_mail
from django.shortcuts import redirect, render

from apps.core.rate_limit import is_rate_limited

from .forms import ContactMessageForm, NewsletterSubscriberForm

logger = logging.getLogger(__name__)


def send_mail(*args, **kwargs):
    """Notify operators without exposing mail infrastructure failures to visitors."""
    try:
        return django_send_mail(*args, **kwargs)
    except Exception:
        logger.exception("Contact notification delivery failed")
        return 0


def _rate_limit_response(request, contact_form, subscribe_form, message):
    messages.error(request, message)
    return render(request, "contact/contact.html", {
        "contact_form": contact_form,
        "subscribe_form": subscribe_form,
    }, status=429)


def contact(request):
    contact_form = ContactMessageForm()
    subscribe_form = NewsletterSubscriberForm()

    if request.method == "POST":
        if request.POST.get("form_type") == "contact":
            if is_rate_limited(
                request, scope="contact", limit=settings.RATELIMIT_CONTACT_LIMIT,
                window_seconds=settings.RATELIMIT_WINDOW_SECONDS,
            ):
                return _rate_limit_response(
                    request, contact_form, subscribe_form,
                    "Too many messages were sent from this connection. Please try again later.",
                )
            contact_form = ContactMessageForm(request.POST)
            if contact_form.is_valid():
                contact_message = contact_form.save()
                send_mail(
                    subject=f"New message from {contact_message.name} — YTR website",
                    message=(
                        f"Name: {contact_message.name}\n"
                        f"Email: {contact_message.email}\n\n"
                        f"{contact_message.message}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_FALLBACK_EMAIL],
                    fail_silently=False,
                )
                messages.success(
                    request,
                    "Thanks — your message has been sent. We'll be in touch soon. / Murakoze — ubutumwa bwawe bwoherejwe. Tuzabakomeza vuba.",
                )
                return redirect("engagement:contact")
        else:
            if is_rate_limited(
                request, scope="newsletter", limit=settings.RATELIMIT_NEWSLETTER_LIMIT,
                window_seconds=settings.RATELIMIT_WINDOW_SECONDS,
            ):
                return _rate_limit_response(
                    request, contact_form, subscribe_form,
                    "Too many subscription attempts. Please try again later.",
                )
            subscribe_form = NewsletterSubscriberForm(request.POST)
            if subscribe_form.is_valid():
                subscribe_form.save()
                messages.success(
                    request,
                    "You're subscribed for updates. / Wiyandikishije neza kugira ngo umenyeshwe ibishya.",
                )
                return redirect("engagement:contact")

    return render(request, "contact/contact.html", {
        "contact_form": contact_form,
        "subscribe_form": subscribe_form,
    })
