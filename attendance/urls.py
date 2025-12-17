from django.urls import path
from . import views

app_name = 'attendance'  # namespacing for template URL usage

urlpatterns = [
    # Home page
    path('', views.home, name='home'),

    # Attendance main pages
    path('attendance/', views.attendance_home, name='attendance_home'),
    path('attendance/list/', views.attendance_list, name='attendance_list'),

    # QR Code generation
path('generate_qr/', views.generate_qr, name='generate_qr'),
path('attendance/mark/<uuid:uuid>/', views.mark_attendance, name='mark_attendance'),


    # Attendance marking via QR scan (secure UUID link)
    path('attendance/mark/<uuid:uuid>/', views.mark_attendance, name='mark_attendance'),
]
