from django.db.models import Prefetch
from django.shortcuts import render

from .models import Video, VideoSeries


def video_list(request):
    published_videos = Video.objects.filter(status=Video.STATUS_PUBLISHED)
    featured = published_videos.filter(is_featured=True).select_related("series").first()
    series_list = VideoSeries.objects.prefetch_related(
        Prefetch("videos", queryset=published_videos, to_attr="published_videos")
    )
    return render(request, "videos/video_list.html", {
        "featured_video": featured,
        "series_list": series_list,
    })
