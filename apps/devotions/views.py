from django.core.paginator import Paginator
from django.shortcuts import render

from .models import Devotion


def devotion_list(request):
    published = Devotion.objects.filter(status=Devotion.STATUS_PUBLISHED)
    today = published.filter(is_featured=True).first() or published.order_by("-date").first()

    archive_qs = published.order_by("-date")
    if today:
        archive_qs = archive_qs.exclude(pk=today.pk)

    paginator = Paginator(archive_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "devotions/devotion_list.html", {
        "today": today,
        "page_obj": page_obj,
    })
