from django.urls import path
from .views import dashboard_redirect

urlpatterns = [
    path("dashboard/", dashboard_redirect, name="dashboard_redirect"),
]
