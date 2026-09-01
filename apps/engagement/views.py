from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import ContactMessageForm, NewsletterSubscriberForm


def contact(request):
    contact_form = ContactMessageForm()
    subscribe_form = NewsletterSubscriberForm()

    if request.method == "POST":
        if request.POST.get("form_type") == "contact":
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
                    fail_silently=True,
                )
                messages.success(
                    request,
                    "Thanks — your message has been sent. We'll be in touch soon. / Murakoze — ubutumwa bwawe bwoherejwe. Tuzabakomeza vuba.",
                )
                return redirect("engagement:contact")
        else:
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
