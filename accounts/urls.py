# from django.urls import path
# from . import views

# app_name = "accounts"

# urlpatterns = [
#     # after login redirect page
#     path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),

#     # STUDENT Google login start (sets role in session then redirects to allauth)
#     path("google/student/", views.google_start, {"role": "student"}, name="google_start"),

#     # If you still use this page:
#     path("choose-role/", views.choose_role, name="choose_role"),
# ]
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("google/student/", views.google_student, name="google_student"),
]
