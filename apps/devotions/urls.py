from django.urls import path

from . import views

app_name = "devotions"

urlpatterns = [
    path("", views.devotion_list, name="list"),
    path("<slug:slug>/", views.devotion_detail, name="detail"),
    path("<slug:slug>/share-image.png", views.devotion_share_image, name="share_image"),
]
