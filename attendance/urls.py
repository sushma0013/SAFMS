from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_home, name='attendance_home'),
    path('list/', views.attendance_list, name='attendance_list'),
    path('mark/<int:student_id>/', views.mark_attendance, name='mark_attendance'),
]
