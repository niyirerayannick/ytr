from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),

    # --- admin ---
    path("admin/", views.admin_dashboard, name="admin"),
    path("admin/signups/", views.signup_queue, name="signup_queue"),
    path("admin/signups/<int:user_id>/approve/", views.approve_signup, name="approve_signup"),
    path("admin/signups/<int:user_id>/reject/", views.reject_signup, name="reject_signup"),
    path("admin/users/", views.user_management, name="user_management"),
    path("admin/users/<int:user_id>/role/", views.update_user_role, name="update_user_role"),
    path("admin/content/", views.pending_content_queue, name="content_queue"),
    path("admin/content/<str:content_type>/<int:pk>/", views.review_content, name="review_content"),
    path("admin/testimonies/", views.pending_testimonies, name="pending_testimonies"),
    path("admin/testimonies/<int:pk>/approve/", views.approve_testimony, name="approve_testimony"),
    path("admin/testimonies/<int:pk>/reject/", views.reject_testimony, name="reject_testimony"),
    path("admin/prayer-requests/", views.prayer_requests_queue, name="prayer_requests"),
    path("admin/prayer-requests/<int:pk>/reviewed/", views.mark_prayer_reviewed, name="mark_prayer_reviewed"),
    path("admin/messages/", views.contact_messages_list, name="messages"),

    # --- author ---
    path("author/", views.author_dashboard, name="author"),
    path("author/home/", views.author_dashboard, name="author_home"),
    path("author/<str:content_type>/new/", views.author_content_create, name="author_content_create"),
    path("author/<str:content_type>/<int:pk>/edit/", views.author_content_edit, name="author_content_edit"),
    path("author/<str:content_type>/<int:pk>/submit/", views.author_content_submit, name="author_content_submit"),

    # --- member ---
    path("member/", views.member_dashboard, name="member"),
    path("member/home/", views.member_dashboard, name="member_home"),
    path("member/testimonies/new/", views.new_testimony, name="new_testimony"),
    path("member/prayer-requests/new/", views.new_prayer_request, name="new_prayer_request"),

    # --- shared actions, triggered from public pages ---
    path("bookmarks/<int:article_id>/toggle/", views.toggle_bookmark, name="toggle_bookmark"),
    path("rsvp/<int:gathering_id>/toggle/", views.toggle_rsvp, name="toggle_rsvp"),
]
