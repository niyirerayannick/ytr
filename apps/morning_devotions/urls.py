from django.urls import path

from . import views

app_name = "morning_devotions"

urlpatterns = [
    path("", views.morning_devotion_list, name="list"),
    path("<slug:slug>/", views.morning_devotion_detail, name="detail"),
    path("<slug:slug>/cover.png", views.morning_devotion_cover, name="cover"),
]
