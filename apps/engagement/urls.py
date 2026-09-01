from django.urls import path

from . import views

app_name = "engagement"

urlpatterns = [
    path("", views.contact, name="contact"),
]
