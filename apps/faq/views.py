from django.shortcuts import render

from .models import FAQ


def faq_list(request):
    highlighted = FAQ.objects.filter(is_highlighted=True).first()
    faqs = FAQ.objects.all()
    if highlighted:
        faqs = faqs.exclude(pk=highlighted.pk)
    return render(request, "faq/faq_list.html", {
        "highlighted": highlighted,
        "faqs": faqs,
    })
