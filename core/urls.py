from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views

from attendance.admin import main_admin_site, fee_admin_site

urlpatterns = [
    path('admin/', main_admin_site.urls),
    path('fee-admin/', fee_admin_site.urls),

    # Home
    path('', views.home, name='home'),

    # Auth system
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', accounts_views.dashboard_redirect, name='dashboard'),

    # Attendance app
    path('attendance/', include('attendance.urls')),

    # Accounts
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)