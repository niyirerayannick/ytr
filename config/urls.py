from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

handler400 = "apps.core.views.error_400"
handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", include("apps.core.urls")),
    path("devotions/", include("apps.devotions.urls")),
    path("articles/", include("apps.articles.urls")),
    path("podcasts/", include("apps.podcasts.urls")),
    path("videos/", include("apps.videos.urls")),
    path("library/", include("apps.library.urls")),
    path("about/", include("apps.about.urls")),
    path("faq/", include("apps.faq.urls")),
    path("contact/", include("apps.engagement.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
