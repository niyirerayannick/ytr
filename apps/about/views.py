from django.shortcuts import render

from .models import BeliefPoint, CallTimelineEntry, SevenMountain


def about(request):
    return render(request, "about/about.html", {
        "timeline": CallTimelineEntry.objects.all(),
        "beliefs": BeliefPoint.objects.all(),
        "mountains": SevenMountain.objects.all(),
    })
