# from django.urls import path
# from . import views

# app_name = 'attendance'  # namespacing for template URL usage

# urlpatterns = [
#     # Home page
#     # path('', views.home, name='home'),

#     # Attendance main pages
#     # path('attendance/', views.attendance_home, name='attendance_home'),
#     # path('attendance/list/', views.attendance_list, name='attendance_list'),

#     # QR Code generation
# # path('generate_qr/', views.generate_qr, name='generate_qr'),
# # path('attendance/mark/<uuid:uuid>/', views.mark_attendance, name='mark_attendance'),

#  # Teacher URLs
#     path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
#     path('generate-qr/<int:subject_id>/', views.generate_qr, name='generate_qr'),
#     # path('subject/<int:subject_id>/report/', views.subject_attendance_report, name='subject_report'),
    
#     # Student URLs
#     path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
#     path('scan/', views.scan_qr_page, name='scan_qr'),
#     path('mark/<uuid:uuid>/', views.mark_attendance, name='mark_attendance'),
#     # attendance/urls.py
# path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
# path('teacher/classes/', views.my_classes, name='my_classes'),
# path('teacher/students/', views.teacher_students, name='teacher_students'),







#     # path('my-attendance/', views.my_attendance, name='my_attendance'),


# #     # Attendance marking via QR scan (secure UUID link)
# #     path('attendance/mark/<uuid:uuid>/', views.mark_attendance, name='mark_attendance'),

# #     path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
# #     path('teacher/generate_qr/<int:subject_id>/', views.generate_qr, name='generate_qr'),
# # 
# ]


from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('generate-qr/<int:subject_id>/', views.generate_qr, name='generate_qr'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher/classes/', views.my_classes, name='my_classes'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path("teacher/reports/", views.teacher_reports, name="teacher_reports"),
    path("teacher/settings/", views.teacher_settings, name="teacher_settings"),
    path("teacher/add-student/", views.teacher_add_student, name="teacher_add_student"),
    


    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('scan/', views.scan_qr_page, name='scan_qr'),
    path('mark/<uuid:uuid>/', views.mark_attendance, name='mark_attendance'),
    path("link-student/", views.link_student, name="link_student"),

]

