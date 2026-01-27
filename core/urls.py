from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    
    path('admin/', admin.site.urls),

    # 🏠 Home
    path('', views.home, name='home'),

    # 🔐 Auth system (OUR custom system)
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),



    # # 📌 Dashboards
    # path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    # path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    # path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # 📌 QR + Attendance
    # path('generate_qr/', views.generate_qr, name='generate_qr'),
    # path('show_qr/<int:session_id>/', views.show_qr, name='show_qr'),
    path('attendance/', include('attendance.urls')),
    path("", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
