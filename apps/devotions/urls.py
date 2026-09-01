from django.urls import path

from . import views

app_name = "devotions"

urlpatterns = [
    path("", views.devotion_list, name="list"),
]
