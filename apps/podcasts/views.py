from django.db.models import Prefetch
from django.shortcuts import render

from .models import Episode, PodcastSeries


def podcast_list(request):
    published_episodes = Episode.objects.filter(status=Episode.STATUS_PUBLISHED)
    series_list = PodcastSeries.objects.prefetch_related(
        Prefetch("episodes", queryset=published_episodes, to_attr="published_episodes")
    )
    return render(request, "podcasts/podcast_list.html", {"series_list": series_list})
