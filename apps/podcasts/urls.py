from django.urls import path

from . import views

app_name = "podcasts"

urlpatterns = [
    path("", views.podcast_list, name="list"),
]
